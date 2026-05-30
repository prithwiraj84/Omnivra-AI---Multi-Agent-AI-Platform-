# Omnivra AI Company OS - Backend

Python 3.11+ - FastAPI - Uvicorn - LangGraph - Pydantic - Tenacity. venv only (no Docker).

## Quickstart (Windows / PowerShell)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then fill in keys
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Visit http://localhost:8000/health and http://localhost:8000/docs.

## Layout
```
backend/
  app/
    main.py            FastAPI app: lifespan, CORS, /health, /api include, /ws stub
    core/              config (pydantic-settings) + logging (loguru)
    providers/         BaseProvider + tenacity retry; google_ai/openrouter/groq/huggingface + registry
    agents/            typed AGENT_REGISTRY (dashboard source of truth)
    graph/             LangGraph state (recursion_count kill switch), kill_switch, builder, approval models
    workspace_fs/      FileManager: sandbox under ./workspace
    checkpoint/        ProjectState + file manifest + checkpoints (resume-on-interrupt)
    api/ services/ schemas/ db/ models/   (Phase 2+, see manifest)
  db/                  schema.sql (pgvector) + Supabase integration plan
  requirements.txt  .env.example
```

## Safety rails
- Workspace rule: agents may ONLY write under `./workspace` (enforced by FileManager).
- Retry: every provider call uses tenacity exponential backoff on 429/timeout/transient.
- Kill switch: `recursion_count > MAX_RECURSION` (default 3) stops the workflow.
- Checkpointing: project state + manifest + checkpoints enable resume.

See `db/README.md` for the Supabase plan and the manifest for the phase roadmap.
```
