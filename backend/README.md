# Responsible AI Chat Agent Backend

FastAPI backend for chat, Responsible AI assessment, SQLAlchemy persistence, Langfuse framework-mode tracing, and OpenTelemetry/Jaeger observability.

## Setup

```bash
cd /home/joseph/llm_engineering/responsible-ai-chat-agent/backend
pip install -r requirements.txt
cp .env.example .env
```

Set `GROQ_API_KEY` in `.env` for real LLM calls. Without a key, the backend returns a safe fallback response, which is useful for local smoke tests.

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Database

Default local DB:

```text
backend/app/storage/responsible_ai.db
```

Override with:

```env
DATABASE_URL=sqlite:///app/storage/responsible_ai.db
```

At startup, the backend creates SQLAlchemy tables and migrates legacy seed data from:

- `app/storage/policy_config.json`
- `app/storage/audit_log.jsonl`

## Jaeger

Start Jaeger from the repo root:

```bash
docker compose up jaeger
```

Open:

```text
http://localhost:16686
```

## Endpoints

- `GET /health`
- `GET /observability`
- `POST /chat`
- `GET /audit`
- `GET /policy`

## Smoke Test

```bash
curl http://localhost:8000/health
curl http://localhost:8000/observability
curl http://localhost:8000/policy
curl http://localhost:8000/audit
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","mode":"code","max_tokens":20}'
```
