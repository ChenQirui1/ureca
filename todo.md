# Project TODOs

## Quick Start

Run both frontend and backend in development mode:

```bash
./dev.sh
```

Or manually:

```bash
# Terminal 1 - Backend
cd backend
source ../.venv/bin/activate
fastapi dev app.py

# Terminal 2 - Frontend
cd platform
npm run dev
```

## Architecture

- **Backend**: FastAPI server at `http://localhost:8000`
  - Location: `/backend/app.py`
  - Features: LlamaIndex RAG, Miro API integration, OpenAI agent

- **Frontend**: Next.js app at `http://localhost:3000`
  - Location: `/platform`
  - Features: Chat interface, Miro board embed, responsive UI

## Environment Setup

### Backend (.env in /backend)

```
OPENAI_API_KEY=your_key_here
MIRO_TOKEN=your_token_here
MIRO_BOARD_ID=your_board_id_here
```

### Frontend (.env.local in /platform)

```
BACKEND_URL=http://localhost:8000
```

## Features Implemented

- [x] Chat interface with AI assistant
- [x] Miro board integration (read)
- [x] Miro board integration (write sticky notes)
- [x] Local document RAG (data folder)

## TODO

- [ ] make the chat more responsive/contextual
- [ ] ingest documents
- [ ] setup database(NoSQL preferably) to collect response from participant
- [ ] create a set up prompt that will pop up and auto sets the enviroment with a key
- [ ] set up recording of the screen
- [ ] add timing and other stuff (if needed)

## Development Notes

- Backend uses LlamaIndex for RAG and agent orchestration
- Frontend is built with Next.js 16.1.6 and React 19
- Styling uses Tailwind CSS v4
- CORS is configured for localhost:3000
