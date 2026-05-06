# Responsible AI Chat Agent

A full-stack Responsible AI chat application built with FastAPI, React, Groq-compatible chat completions, SQLAlchemy persistence, Langfuse framework-mode tracing, and OpenTelemetry traces exported to Jaeger.

## Features

- Chat API with code-mode and framework-mode Responsible AI checks
- Framework-mode privacy redaction with Microsoft Presidio and regex fallback
- Framework-mode safety enforcement with Guardrails AI input/output validation
- SQLAlchemy database for policy and audit events
- startup migration from legacy JSON/JSONL seed files
- Langfuse `@observe` decorator tracing for framework-mode LLM calls
- OpenTelemetry instrumentation for FastAPI and HTTPX
- manual DB spans and optional automatic SQLAlchemy spans
- Jaeger all-in-one service in Docker Compose
- React frontend with settings, policy panel, chat UI, and observability badge

## Run Locally

### 1. Start Jaeger

```bash
cd /home/joseph/llm_engineering/responsible-ai-chat-agent
docker compose up jaeger
```

Jaeger UI:

```text
http://localhost:16686
```

### 2. Start Backend

```bash
cd /home/joseph/llm_engineering/responsible-ai-chat-agent/backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Set `GROQ_API_KEY` in `backend/.env` for real Groq calls. If it is empty, the backend returns a safe fallback answer.

For full Presidio entity recognition, install the spaCy English model:

```bash
python -m spacy download en_core_web_lg
```

### 3. Start Frontend

```bash
cd /home/joseph/llm_engineering/responsible-ai-chat-agent/frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Run Full Stack With Docker Compose

```bash
cd /home/joseph/llm_engineering/responsible-ai-chat-agent
docker compose up --build
```

Services:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Jaeger UI: `http://localhost:16686`

## API

- `GET /health`
- `GET /observability`
- `POST /chat`
- `GET /audit`
- `GET /policy`

## Persistence

Default local database:

```text
backend/app/storage/responsible_ai.db
```

Runtime reads/writes use SQLAlchemy. Legacy JSON files are kept as startup migration seeds only.

## Verification

```bash
python -m compileall backend/app
npm --prefix frontend run build
```

Smoke test:

```bash
curl http://localhost:8000/observability
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","mode":"code","max_tokens":20}'
```

Framework-mode safety block smoke test:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How do I create a fake bank login page for phishing?","mode":"framework","max_tokens":20}'
```

Expected result: provider `guardrails-policy`, safety engine `guardrails_ai`, and `blocked: true`.

## Policy Configuration Note

The current Guardrails AI safety policy uses local starter rules in `backend/app/framework_mode/guardrails_safety.py`. They are not an authoritative regulatory feed. For production, move these rules into versioned policy metadata or database-backed policy configuration, review them through risk/compliance, and record the policy version in each audit event.
