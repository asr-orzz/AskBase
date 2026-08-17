# RAGOps

Upload documents and query them with AI. Built with FastAPI, Next.js, PostgreSQL, Qdrant, and Google Gemini.

## Features

- Upload PDF, DOCX, TXT, MD, HTML documents
- Automatic chunking and vector embedding
- Query documents with natural language
- Powered by Google Gemini (embeddings + LLM)
- Simple, clean UI

## Quick Start (Local)

### Prerequisites
- Python 3.11+, Node.js 18+
- PostgreSQL, Qdrant (or use Docker)
- Google API key from [AI Studio](https://aistudio.google.com/apikey)

### 1. Start infrastructure
```bash
docker run -d --name postgres -e POSTGRES_USER=ragops -e POSTGRES_PASSWORD=ragops -e POSTGRES_DB=ragops -p 5432:5432 postgres:16-alpine
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 2. Backend
```bash
cd backend
python -m venv .venv && .venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp .env.example .env  # Edit with your Google API key
alembic upgrade head
uvicorn app.main:app --reload
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Deploy to Render (One-Click)

1. Push this repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New > Blueprint** and connect your repo
4. Render reads `render.yaml` and creates all services
5. Set environment variables:
   - `GOOGLE_API_KEY` — your Google API key
   - `QDRANT_URL` — your Qdrant Cloud URL (free at [cloud.qdrant.io](https://cloud.qdrant.io))
   - `QDRANT_API_KEY` — your Qdrant Cloud API key
   - `NEXT_PUBLIC_API_URL` — `https://ragops-api.onrender.com/api/v1`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, SQLAlchemy |
| Database | PostgreSQL |
| Vector DB | Qdrant |
| AI | Google Gemini (embeddings + LLM) |
