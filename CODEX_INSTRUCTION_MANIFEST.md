# Codex Instruction Manifest

Project template: production-grade Responsible AI full-stack applications.

Use this manifest as a reusable build contract for new projects. Replace bracketed values such as `[PROJECT_NAME]`, `[LLM_PROVIDER]`, and `[DATABASE_URL]` when starting a new application.

## 1. Product Objective Template

Build a full-stack AI application that:

- accepts user input through a polished frontend
- calls an LLM provider through a backend service
- returns the model answer plus Responsible AI metadata
- persists governance policy and audit events in a database
- exposes observability through OpenTelemetry and Jaeger
- supports framework integrations such as Langfuse, Presidio, Guardrails AI, and extension hooks for evaluators such as TruLens and Ragas

Default implementation for this repo:

- `[PROJECT_NAME]`: Responsible AI Chat Agent
- `[BACKEND]`: FastAPI
- `[FRONTEND]`: React + Vite
- `[LLM_PROVIDER]`: Groq-compatible chat completions
- `[DATABASE]`: SQLAlchemy with SQLite local default
- `[TRACE_BACKEND]`: Jaeger
- `[LLM_OBSERVABILITY]`: Langfuse decorators in framework mode

## 2. Reusable Architecture Template

```text
[project-root]/
├── backend/
│   ├── app/
│   │   ├── main.py                      # API routes and startup wiring
│   │   ├── config.py                    # environment settings
│   │   ├── schemas.py                   # request/response contracts
│   │   ├── database.py                  # SQLAlchemy models and repositories
│   │   ├── telemetry.py                 # OpenTelemetry and Jaeger
│   │   ├── [provider]_client.py         # LLM provider abstraction
│   │   ├── responsible_ai/              # local policy/evaluation modules
│   │   ├── framework_mode/              # framework integrations
│   │   └── storage/                     # local SQLite and seed files
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── package.json
│   ├── index.html
│   └── src/
│       ├── api.js
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/
│       └── styles.css
├── docs/
│   ├── RESPONSIBLE_AI_DESIGN.md
│   ├── GOVERNANCE_POLICY.md
│   └── TEST_PLAN.md
├── docker-compose.yml
├── README.md
└── CODEX_INSTRUCTION_MANIFEST.md
```

## 3. Backend Component Template

### 3.1 Configuration

Every production-grade backend must centralize settings in `config.py`.

Required environment variables:

```env
PROJECT_NAME=[PROJECT_NAME]
GROQ_API_KEY=[secret]
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_API_URL=https://api.groq.com/openai/v1
DATABASE_URL=sqlite:///app/storage/responsible_ai.db
OTEL_SERVICE_NAME=[service-name]
JAEGER_HOST=localhost
JAEGER_PORT=6831
JAEGER_ENDPOINT=
JAEGER_UI_URL=http://localhost:16686
LANGFUSE_PUBLIC_KEY=optional
LANGFUSE_SECRET_KEY=optional
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3.2 API Contract

Required endpoints:

- `GET /health`: service health
- `GET /observability`: tracing/exporter status
- `POST /chat`: model response plus Responsible AI assessment
- `GET /audit`: recent governance audit events
- `GET /policy`: active governance policy

### 3.3 Persistence

Use SQLAlchemy for runtime persistence.

Minimum tables:

- `policy_configs`
  - active policy payload
  - timestamps
- `audit_events`
  - request ID
  - timestamp
  - mode
  - provider
  - model
  - answer summary
  - Responsible AI assessment JSON

Rules:

- do not use JSON/JSONL as runtime storage in production
- allow local SQLite for development
- make `DATABASE_URL` portable to Postgres
- seed from legacy files only when the DB is empty
- add Alembic before production schema changes become frequent

### 3.4 LLM Provider Adapter

The provider adapter must:

- keep provider-specific HTTP details out of route handlers
- apply a responsible system prompt
- return consistent metadata
- support safe fallback behavior when credentials are absent
- expose token usage when the provider returns it
- avoid logging secrets or raw credentials

### 3.5 Responsible AI Evaluator Template

Each evaluator returns a plain JSON-compatible dict.

Required pillars:

- privacy
- safety
- fairness
- explainability
- verifiability
- transparency
- governance
- controllability

Code mode should work without external services. Framework mode may call external tools when configured.

## 4. Observability Template

### 4.1 OpenTelemetry

Instrument:

- FastAPI request lifecycle
- outbound HTTP calls
- DB initialization
- policy reads
- audit inserts
- audit reads
- LLM provider calls

Expose observability status through `GET /observability`.

### 4.2 Jaeger

Local Docker service template:

```yaml
jaeger:
  image: jaegertracing/all-in-one:1.57
  ports:
    - "16686:16686"
    - "6831:6831/udp"
    - "14268:14268"
```

Backend container settings:

```env
JAEGER_HOST=jaeger
JAEGER_PORT=6831
JAEGER_UI_URL=http://localhost:16686
```

### 4.3 Langfuse

Use Langfuse decorators for LLM calls in framework mode:

```python
from langfuse.decorators import observe, langfuse_context

@observe(name='llm_generation', as_type='generation')
def call_model(...):
    ...
    langfuse_context.update_current_trace(...)
    langfuse_context.update_current_observation(...)
    langfuse_context.flush()
```

Rules:

- import decorators from `langfuse.decorators`
- update trace input/output and metadata
- capture usage when available
- keep decorator tracing conditional on framework mode or explicit configuration

## 5. Frontend Component Template

Frontend must include:

- API client module
- chat window
- message bubble
- settings panel
- Responsible AI panel
- observability/tracing status badge

API client functions:

- `sendChat(payload)`
- `fetchPolicy()`
- `fetchObservability()`

Frontend behavior:

- load policy on startup
- poll observability status periodically
- keep code/framework mode visible and controllable
- show Responsible AI assessment with each assistant response
- link tracing badge to Jaeger UI when enabled

## 6. Security And Governance Template

Required controls before production:

- authenticated access for audit and policy endpoints
- request ID correlation across logs, traces, and audit rows
- no secrets in traces, logs, frontend state, or audit summaries
- CORS restricted to known frontend origins
- retention policy for audit events
- structured errors that do not leak internal stack traces
- DB backups for production databases

## 7. Testing Template

Minimum checks:

```bash
python -m compileall backend/app
npm --prefix frontend run build
```

Backend smoke:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/observability
curl http://localhost:8000/policy
curl http://localhost:8000/audit
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","mode":"code","max_tokens":20}'
```

Frontend smoke:

- start backend
- start frontend
- open frontend URL
- confirm policy loads
- confirm observability badge reflects `/observability`
- send code-mode chat
- send framework-mode chat when external framework keys are configured

## 8. Definition Of Done Template

A feature is done when:

- backend routes compile and smoke-test successfully
- frontend builds successfully
- persistence writes through SQLAlchemy
- observability status is visible from the API and frontend
- docs describe setup, configuration, and operational behavior
- no unrelated user changes are reverted
- startup instructions are accurate for local and Docker Compose workflows

## 9. Current Project Implementation Notes

This repository currently implements:

- SQLAlchemy persistence in `backend/app/database.py`
- JSON/JSONL migration into SQLite at startup
- DB-backed `/policy` and `/audit`
- audit insertion from `/chat`
- OpenTelemetry + Jaeger in `backend/app/telemetry.py`
- `/observability` endpoint
- Docker Compose Jaeger service
- Langfuse decorators for framework-mode Groq calls
- Presidio framework-mode privacy redaction with regex fallback
- Guardrails AI framework-mode safety validation and policy blocking
- local starter Guardrails safety policy rules that should move to versioned metadata before production use
- frontend observability badge wired to `/observability`
