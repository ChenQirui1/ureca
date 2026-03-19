from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import requests
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI
from llama_index.core.tools import QueryEngineTool, ToolMetadata, FunctionTool
from llama_index.agent.openai import OpenAIAgent

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware to allow requests from Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],  # Next.js default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# if not os.path.exists("static"):
#     os.makedirs("static")
# app.mount("/static", StaticFiles(directory="static"), name="static")


# ==========================================
# 1. DEFINE YOUR TOOLS
# ==========================================


# Tool A: Miro API
def fetch_my_miro_board() -> str:
    """Automatically fetches sticky notes and text from the primary Miro board."""
    token = os.environ.get("MIRO_TOKEN")
    board_id = os.environ.get("MIRO_BOARD_ID")

    if not token or not board_id:
        return "Error: MIRO_TOKEN or MIRO_BOARD_ID is missing from the .env file."

    url = f"https://api.miro.com/v2/boards/{board_id}/items"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return f"Failed to retrieve board. Status: {response.status_code}"

    items = response.json().get("data", [])
    board_text = []
    for item in items:
        if item["type"] in ["sticky_note", "text", "shape", "card"]:
            content = item.get("data", {}).get("content", "")
            if content:
                clean_content = content.replace("<p>", "").replace("</p>", "\n")
                board_text.append(f"- {item['type'].upper()}: {clean_content}")

    if not board_text:
        return "The board was successfully accessed, but no text or sticky notes were found."

    return "Here is the content of the Miro Board:\n" + "\n".join(board_text)


miro_context_tool = FunctionTool.from_defaults(fn=fetch_my_miro_board)


def create_miro_sticky_note(content: str) -> str:
    """Creates a sticky note on the primary Miro board with the given content.

    Args:
        content: The text content to write on the sticky note.

    Returns:
        A message indicating success or failure.
    """
    token = os.environ.get("MIRO_TOKEN")
    board_id = os.environ.get("MIRO_BOARD_ID")

    if not token or not board_id:
        return "Error: MIRO_TOKEN or MIRO_BOARD_ID is missing from the .env file."

    # First, fetch all items to find the rightmost position
    items_url = f"https://api.miro.com/v2/boards/{board_id}/items"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    items_response = requests.get(items_url, headers=headers)

    # Default position if board is empty or fetch fails
    new_x = 0
    new_y = 0

    if items_response.status_code == 200:
        items = items_response.json().get("data", [])
        if items:
            # Find the rightmost item
            rightmost_x = max(item.get("position", {}).get("x", 0) for item in items)
            rightmost_item = next(
                (
                    item
                    for item in items
                    if item.get("position", {}).get("x", 0) == rightmost_x
                ),
                None,
            )

            if rightmost_item:
                # Place new note 300 pixels to the right of the rightmost note
                new_x = rightmost_x + 300
                new_y = rightmost_item.get("position", {}).get("y", 0)

    # Create the sticky note
    url = f"https://api.miro.com/v2/boards/{board_id}/sticky_notes"
    payload = {
        "data": {"content": content, "shape": "square"},
        "position": {
            "x": new_x,
            "y": new_y,
        },
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        return f"Successfully created sticky note with content: '{content}' at position (x={new_x}, y={new_y})"
    else:
        return f"Failed to create sticky note. Status: {response.status_code}, Error: {response.text}"


miro_write_tool = FunctionTool.from_defaults(fn=create_miro_sticky_note)


# Tool B: Local Documents (RAG)
def create_rag_tool():
    if not os.path.exists("./data") or not os.listdir("./data"):
        return None

    reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
    docs = reader.load_data()
    index = VectorStoreIndex.from_documents(docs)
    query_engine = index.as_query_engine()

    return QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="local_documents_tool",
            description="Useful for answering questions based on the uploaded local text documents in the data folder.",
        ),
    )


# ==========================================
# 2. INITIALIZE THE AGENT
# ==========================================
rag_tool = create_rag_tool()

all_tools = [miro_context_tool, miro_write_tool]
if rag_tool:
    all_tools.append(rag_tool)

# The Agent acts as the brain, deciding which tool to use based on the user's prompt
agent = OpenAIAgent.from_tools(
    tools=all_tools,
    llm=OpenAI(model="gpt-4o"),
    system_prompt=(
        "You are a helpful assistant. You have access to local documents and the user's primary Miro board. "
        "If the user asks a question about their whiteboard or projects, use the fetch_my_miro_board tool. "
        "If the user asks you to create, add, or write a sticky note to the board, use the create_miro_sticky_note tool."
    ),
    verbose=True,
)


# ==========================================
# 3. FASTAPI ENDPOINTS
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("static/index.html", "r") as f:
        return f.read()


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # Pass the user's message to the LlamaIndex Agent
    # The agent will automatically call the Miro API or search the RAG docs if needed
    response = agent.chat(request.message)

    # Return the final string to the HTML frontend
    return {"response": response.response}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
