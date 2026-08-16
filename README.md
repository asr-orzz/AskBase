# RAGOps

**A production platform for building, deploying, evaluating, and operating continuously updated RAG applications from configurable data sources.**

## Architecture

```
Control Plane (FastAPI)          Data Plane
├── Knowledge Base Service       ├── Connectors (GitHub, S3, Postgres, REST)
├── RAG Configuration            ├── Kafka Event Streaming
├── Evaluation Service           ├── Stream Processing
├── Experiment Service           ├── Chunking + Embedding
└── Deployment Service           └── Vector Indexing (Qdrant)

Observability                    Infrastructure
├── OpenTelemetry                ├── PostgreSQL
├── Prometheus + Grafana         ├── Qdrant
├── Loki (Logs)                  ├── Redis
├── Tempo (Traces)               ├── Kafka
└── Cost Tracking                └── MinIO / S3
```

## Tech Stack

| Layer             | Technology               |
|-------------------|--------------------------|
| Frontend          | Next.js + TypeScript     |
| UI                | Tailwind + shadcn/ui     |
| Backend           | FastAPI + Python         |
| Primary DB        | PostgreSQL               |
| Vector DB         | Qdrant                   |
| Object Storage    | S3 / MinIO               |
| Streaming         | Kafka                    |
| Background Jobs   | Celery + Redis           |
| Workflow          | Temporal                 |
| Cache             | Redis                    |
| Tracing           | OpenTelemetry            |
| Metrics           | Prometheus               |
| Auth              | Keycloak                 |
| Containers        | Docker + Kubernetes      |
| CI/CD             | GitHub Actions           |

## Project Structure

```
RAGops/
├── backend/            # FastAPI application
│   ├── app/
│   │   ├── api/        # API routes
│   │   ├── core/       # Config, security, dependencies
│   │   ├── models/     # SQLAlchemy models
│   │   ├── schemas/    # Pydantic schemas
│   │   ├── services/   # Business logic
│   │   ├── connectors/ # Data source connectors
│   │   ├── rag/        # RAG engine (retrieval, reranking, generation)
│   │   ├── evaluation/ # Evaluation & experiment framework
│   │   └── workers/    # Background job workers
│   ├── alembic/        # Database migrations
│   ├── tests/          # Backend tests
│   └── requirements.txt
├── frontend/           # Next.js application
├── docker/             # Dockerfiles
├── k8s/                # Kubernetes manifests
├── .github/            # CI/CD workflows
└── docker-compose.yml
```

## Quick Start

```bash
# Clone
git clone <repo-url>
cd RAGops

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Development

See individual README files in `backend/` and `frontend/` for detailed setup instructions.
