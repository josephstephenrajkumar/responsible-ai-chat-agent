# Test Plan

## Backend

1. Install backend dependencies:

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Start Jaeger when testing trace export:

   ```bash
   docker compose up jaeger
   ```

3. Start the backend:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. Verify health:

   ```bash
   curl http://localhost:8000/health
   ```

5. Verify observability:

   ```bash
   curl http://localhost:8000/observability
   ```

6. Verify DB-backed policy:

   ```bash
   curl http://localhost:8000/policy
   ```

7. Verify DB-backed audit:

   ```bash
   curl http://localhost:8000/audit
   ```

8. Verify chat and audit insertion:

   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"test responsible ai flow","mode":"code","max_tokens":20}'
   ```

## Frontend

1. Install frontend dependencies:

   ```bash
   cd frontend
   npm install
   ```

2. Run the frontend:

   ```bash
   npm run dev
   ```

3. Open `http://localhost:5173`.
4. Confirm the policy panel loads from `/policy`.
5. Confirm the tracing badge reads `/observability` and links to Jaeger.
6. Send a chat message in `code` mode and confirm an answer is displayed.
7. Switch to `framework` mode and confirm the answer still returns and Langfuse tracing is flushed when Langfuse keys are configured.

## Regression Checks

```bash
python -m compileall backend/app
npm --prefix frontend run build
```

## Expected Local Artifacts

- SQLite DB: `backend/app/storage/responsible_ai.db`
- Jaeger UI: `http://localhost:16686`
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
