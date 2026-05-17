# Srečko Kosovel AI Chat

Minimal RAG chat application for Srečko Kosovel's works.

## Development Setup

### Requirements

- Python 3.12+
- Node.js 20+
- PostgreSQL with `pgvector`
- Ollama, or another configured LLM provider

### Configure

```bash
cp .env.example .env
```

Edit `.env` with database and model settings.

### Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python scripts/01_create_schema.py
python scripts/02_import_data.py
python scripts/03_generate_embeddings.py

uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

API health check:

```bash
curl http://localhost:8000/api/health
```

### Frontend

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`.

## Docker Deploy

Docker Compose runs Ollama, the FastAPI backend, and the Next.js frontend.
PostgreSQL is not included; configure `.env` to point to a reachable database.

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull llama3.2:3b
```

Services:

- Web: `http://localhost:3001`
- API: `http://localhost:8000`

Useful commands:

```bash
docker compose logs -f
docker compose restart api web
docker compose down
```

## Environment Reference

### Database

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | Full PostgreSQL connection string. Preferred for production. |
| `DB_HOST` | PostgreSQL host when `DATABASE_URL` is not set. |
| `DB_PORT` | PostgreSQL port. |
| `DB_NAME` | Database name. |
| `DB_USER` | Database user. |
| `DB_PASSWORD` | Database password. |

### LLM

| Variable | Description |
| --- | --- |
| `LLM_PROVIDER` | `ollama`, `openrouter`, `github-copilot`, `github`, or `anthropic`. |
| `OLLAMA_BASE_URL` | Ollama API URL. Use `http://ollama:11434` in Docker. |
| `OLLAMA_CHAT_MODEL` | Ollama chat model. |
| `OLLAMA_EMBEDDING_MODEL` | Ollama embedding model. |
| `OLLAMA_CHAT_TIMEOUT` | Optional chat timeout in seconds. |
| `OLLAMA_EMBEDDING_TIMEOUT` | Optional embedding timeout in seconds. |
| `OPENROUTER_API_KEY` | OpenRouter API key. |
| `OPENROUTER_MODEL` | OpenRouter model name. |
| `OPENROUTER_MAX_TOKENS` | Optional OpenRouter response token limit. |
| `GITHUB_TOKEN` | GitHub Models or Copilot token. |
| `GITHUB_COPILOT_TOKEN` | Optional GitHub Copilot token override. |
| `GITHUB_COPILOT_MODEL` | GitHub Copilot model name. |
| `GITHUB_MODEL` | GitHub Models model name. |
| `ANTHROPIC_API_KEY` | Anthropic API key. |
| `ANTHROPIC_MODEL` | Anthropic model name. |

### App

| Variable | Description |
| --- | --- |
| `EMBEDDING_DIMENSION` | Embedding vector size. |
| `EMBEDDING_BATCH_SIZE` | Embedding batch size. |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins. |
| `LOG_LEVEL` | Application log level. |
| `ENVIRONMENT` | Runtime environment label. |
