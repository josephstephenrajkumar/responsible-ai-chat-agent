# Governance Policy

## Policy Scope

The application enforces governance across:

- user request handling
- model provider access
- Responsible AI evaluation
- audit event persistence
- trace and observability metadata
- operational review through Jaeger and Langfuse

## Storage Policy

Runtime governance data is stored in SQLAlchemy tables:

- `policy_configs`: active policy payload
- `audit_events`: request-level audit events

Legacy files are retained only as migration seed sources:

- `backend/app/storage/policy_config.json`
- `backend/app/storage/audit_log.jsonl`

New runtime writes go to the database configured by `DATABASE_URL`.

## Audit Policy

Each chat request stores:

- `request_id`
- timestamp
- mode: `code` or `framework`
- model
- provider
- cache flag
- answer summary
- full Responsible AI pillar assessment

The `/audit` endpoint returns recent events and should be protected by authentication before production exposure.

## Observability Policy

OpenTelemetry traces are exported to Jaeger for backend API, HTTP client, and DB workflow visibility. Framework-mode LLM calls also use Langfuse decorator tracing.

Required production controls:

- avoid storing secrets in trace attributes
- use request IDs for correlation
- configure retention in Jaeger or the OpenTelemetry backend
- restrict Jaeger and audit access to authorized operators

## Responsible AI Policy

Every response includes assessments for:

- privacy
- safety
- fairness
- explainability
- verifiability
- transparency
- governance
- controllability

Framework mode should progressively replace placeholders with real framework engines such as Presidio, Guardrails, TruLens, and Ragas.
