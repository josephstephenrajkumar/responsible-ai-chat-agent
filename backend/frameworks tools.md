# Responsible AI Framework Tools

This project supports two implementation modes:

- `code`: local Python checks for privacy, safety, fairness, explainability, verifiability, transparency, governance, and controllability.
- `framework`: framework-oriented integrations for observability, tracing, privacy, safety, and evaluation.

## Current Tooling Map

| Tool | Implementation Status | Purpose | Responsible AI Pillars |
| --- | --- | --- | --- |
| Langfuse | Implemented for framework-mode chat calls with `@observe` decorators | LLM trace, generation metadata, usage, answer visibility | Transparency, Governance |
| OpenTelemetry | Implemented for FastAPI, HTTPX, manual DB spans, optional SQLAlchemy instrumentation | Distributed tracing across API, LLM HTTP calls, and persistence | Transparency, Governance, Reliability |
| Jaeger | Implemented via local/Docker exporter target | Trace collection and visual inspection | Transparency, Operations |
| SQLAlchemy | Implemented with SQLite default and portable `DATABASE_URL` | Policy and audit persistence replacing JSON/JSONL runtime storage | Governance, Auditability |
| Presidio | Framework-mode placeholder | PII detection and redaction | Privacy |
| Guardrails | Framework-mode placeholder | Input/output validation and policy enforcement | Safety, Controllability |
| TruLens | Framework-mode placeholder | LLM answer/explanation evaluation | Explainability, Verifiability |
| Ragas | Framework-mode placeholder | RAG/fairness-style evaluation hooks | Verifiability, Fairness |

## Implemented Backend Shape

```text
backend/app/
├── database.py                         # SQLAlchemy models, migration, DB helpers
├── telemetry.py                        # OpenTelemetry + Jaeger setup
├── framework_mode/
│   ├── langfuse_observability.py       # Langfuse decorators and context updates
│   ├── presidio_privacy.py
│   ├── guardrails_safety.py
│   ├── trulens_eval.py
│   └── ragas_eval.py
└── storage/
    ├── responsible_ai.db               # SQLite DB created at startup
    ├── audit_log.jsonl                 # legacy seed source only
    └── policy_config.json              # legacy seed source only
```

## Runtime Responsibilities

- `startup_event()` configures OpenTelemetry, instruments SQLAlchemy when available, creates DB tables, and migrates legacy JSON data once.
- `/chat` writes audit events to SQLAlchemy, not JSONL.
- `/audit` reads recent audit events from SQLAlchemy.
- `/policy` reads governance policy from SQLAlchemy.
- `/observability` reports tracing status, Jaeger endpoint, Jaeger UI URL, and SQLAlchemy instrumentation status.

## Production Upgrade Path

1. Replace SQLite with Postgres by setting `DATABASE_URL=postgresql+psycopg://...`.
2. Add Alembic migrations once the schema needs versioned production changes.
3. Run Jaeger or an OTLP collector outside the app container.
4. Replace simulated Presidio, Guardrails, TruLens, and Ragas modules with real framework calls.
5. Add authentication and role-based access before exposing `/audit` in shared environments.
