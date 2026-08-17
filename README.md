# AskBase

Your documents, instantly answerable. Upload any document and get accurate AI-powered answers in seconds.

Built with FastAPI, Next.js, PostgreSQL, Qdrant, and Google Gemini.

## Features

- **Document Upload** — PDF, DOCX, TXT, MD, HTML (up to 50 MB)
- **Smart Chunking** — Recursive splitting with overlap context for better retrieval
- **Natural Language Queries** — Ask questions and get cited, structured answers
- **User Authentication** — Email/password with JWT sessions
- **Bring Your Own Key** — Use the platform default or configure your own Gemini API key
- **Knowledge Bases** — Organize documents into separate collections
- **Source Citations** — See exactly which document chunks informed each answer

## Quick Start (Local)

### Prerequisites

- Python 3.11+, Node.js 18+
- Docker (for PostgreSQL & Qdrant)
- Google Gemini API key from [AI Studio](https://aistudio.google.com/apikey)

### 1. Start infrastructure

```bash
docker run -d --name postgres -e POSTGRES_USER=ragops -e POSTGRES_PASSWORD=ragops -e POSTGRES_DB=ragops -p 5432:5432 postgres:16-alpine
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 2. Backend

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate  # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env  # Edit with your Google API key
alembic upgrade head
uvicorn app.main:app --reload
```

API docs available at http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local  # Edit API URL if needed
npm run dev
```

Open http://localhost:3000

## Deployment

### Backend → Render

1. Push repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com) → New → Blueprint
3. Connect your repo — Render reads `render.yaml`
4. Set environment variables:
   - `DATABASE_URL` — PostgreSQL connection string (e.g., from Neon.tech)
   - `DATABASE_SYNC_URL` — Same DB, sync driver format
   - `GOOGLE_API_KEY` — Gemini API key
   - `QDRANT_URL` — Qdrant Cloud URL (free at [cloud.qdrant.io](https://cloud.qdrant.io))
   - `QDRANT_API_KEY` — Qdrant Cloud API key
   - `JWT_SECRET` — Random secret for auth tokens

### Frontend → Vercel

1. Import the repo on [Vercel](https://vercel.com)
2. Set **Root Directory** to `frontend`
3. Set environment variables:
   - `NEXT_PUBLIC_API_URL` — Your Render backend URL (e.g., `https://your-app.onrender.com/api/v1`)
   - `NEXTAUTH_URL` — Your Vercel domain (e.g., `https://your-app.vercel.app`)
   - `NEXTAUTH_SECRET` — Random secret string

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, NextAuth.js |
| Backend | Python, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL (Neon / Render / local) |
| Vector DB | Qdrant |
| AI | Google Gemini (embeddings + LLM) |
| Auth | NextAuth.js (frontend) + JWT (backend) |

## Architecture

```
User → Next.js (Vercel) → FastAPI (Render) → PostgreSQL + Qdrant
                                           → Google Gemini API
```

1. User uploads a document → backend parses, chunks, embeds, stores vectors
2. User asks a question → backend embeds query, searches Qdrant, sends context to Gemini
3. Gemini generates an answer citing the relevant document chunks
