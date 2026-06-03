# OMNIVRA — AI Company OS `v2.0`

> A production-grade **multi-agent AI operating system** that feels like a futuristic AI company
> command center — a blend of Claude Code, Devin, Linear, Vercel, GitHub, Cursor, Palantir, and
> JARVIS.
>
> You talk to a **CEO AI** which plans and delegates to specialized **AI departments**; each
> department has expert agents powered by different LLM providers. Work is orchestrated through a
> LangGraph state machine with a kill switch, a human approval gate, durable checkpoints, live
> WebSocket streaming, workspace artifacts, and a knowledge base + agent memory (RAG).

---

## Table of Contents
1. [What Omnivra Is](#what-omnivra-is)
2. [Feature Set](#feature-set)
3. [Architecture](#architecture)
4. [Tech Stack](#tech-stack)
5. [Monorepo Layout](#monorepo-layout)
6. [The Workspace Rule](#the-workspace-rule)
7. [Agent Roster](#agent-roster)
8. [How to Run (Windows / PowerShell, no Docker)](#how-to-run)
9. [How to Test](#how-to-test)
10. [Stub Mode vs. Real Keys](#stub-mode-vs-real-keys)
11. [Auth & Hardening](#auth--hardening)
12. [Project State, Checkpoints & Resume](#project-state-checkpoints--resume)
13. [Platform Guarantees](#platform-guarantees)
14. [Docs & Deploy](#docs--deploy)

---

## What Omnivra Is

Omnivra is a self-contained **AI company operating system**. A single FastAPI/LangGraph backend
runs a roster of 23 specialized agents organized into departments (Executive, Architecture, Design,
Engineering, Quality & Security, Marketing, Documentation, Recovery, System Ops, Media). A
Vite/React command-center UI gives you a live dashboard, an approval gate, a workspace artifact
explorer, and a knowledge base + memory view.

It is designed to run **fully offline and zero-config**: with no API keys, no database, and no
Docker, every provider falls back to deterministic stubs, embeddings use a local hashing embedder,
and data comes from a bundled seed layer — so the whole system builds, runs, and tests green out of
the box. Add provider keys, a strong secret, auth, and (optionally) Supabase to flip it into real
production mode.

---

## Feature Set

The product was built incrementally across **10 phases**; all are complete. The full feature set:

- **Command-center dashboard** — Executive overview stat cards, AI Agents Status grid + System
  Operations sub-row, Active Workflows, Task Execution Overview (Recharts), Task Distribution donut,
  Live Activity Feed, Pending Approvals, System Health, Model Usage / Top Models, Recent
  Achievements, plus a command palette.
- **Agents & providers** — a 23-agent registry mapped to four providers (Google AI Studio,
  OpenRouter, Groq, Hugging Face); each external call is wrapped with **tenacity** exponential
  backoff (retries on 429 / timeout / transient), with a deterministic offline **stub fallback**.
- **LangGraph orchestration** — a CEO/Manager agent plans and delegates to department subgraphs via
  a compiled state machine (`START → ceo → guard → delegate → approval → finalize → END`), with a
  **kill switch** that stops and fails any run whose `recursion_count` exceeds `MAX_RECURSION` (3).
- **Realtime WebSockets** — a `ConnectionManager` fans out `system_health`, `activity`, `workflow`,
  and `approval` events; the frontend folds them into the React Query cache so System Health + the
  Live Activity Feed update live, with a connection-state Live indicator.
- **Human approval gate + recovery** — gated tasks (publish / deploy / export / release /
  presentation / final) `interrupt()` mid-run under a LangGraph checkpointer; **Approve / Reject /
  Retry / Rollback** resume, reject, or roll back the paused run over REST + WS. Every run is
  persisted (`WorkflowStore`) with a recovery listing that survives restarts.
- **Workspace artifacts + media** — agents write each output plus a run report into `./workspace`
  via a path-jailed FileManager; a two-pane artifact explorer lists + views them. Media services
  (image generation via Hugging Face FLUX.1-schnell, Groq Whisper STT, Orpheus TTS) are stub-safe.
- **Knowledge base + memory + RAG** — a cosine vector store (local 256-dim hashing embedder by
  default, optional Supabase pgvector) powers KB search, workspace ingest, and **agent memory**:
  every successful output is stored and recalled into later agents' context, so the company learns
  from prior work. Dedicated Knowledge Base + Memory pages.
- **Auth + hardening** — opt-in token auth (open by default; Bearer-token-gated sensitive POSTs when
  enabled), security headers, and opt-in per-IP rate limiting.

---

## Architecture

```
              +-----------------------------------------------+
  Browser --> |  Frontend (Vite + React + TS + Tailwind +     |
   (WS+REST)  |  shadcn/ui + Framer Motion + React Flow +     |
              |  Recharts)  -  the Command Center UI          |
              +----------------------+------------------------+
                                     |  REST + WebSocket  (/api, /ws)
              +----------------------v------------------------+
              |  Backend (FastAPI + Uvicorn)                  |
              |   * LangGraph orchestration (CEO -> depts)    |
              |   * Provider abstraction (tenacity retries)   |
              |   * Human Approval Gate (resume via WS/REST)  |
              |   * Kill switch (recursion_count > 3 => FAIL) |
              |   * Realtime ConnectionManager (WS fanout)    |
              |   * Workspace FileManager (path-jailed)       |
              |   * Vector store + memory/RAG                 |
              |   * Auth + hardening middleware               |
              +----------------------+------------------------+
                                     |
         +---------------------------+---------------------------+
         v                           v                           v
  Supabase Cloud (optional)    Redis / Upstash (optional)    ./workspace
  (Postgres + pgvector,        (queue + ephemeral state)     (agent output ONLY,
   Storage, Realtime)                                         + .state runtime)
```

The **CEO/Manager** agent plans and delegates. A LangGraph state machine routes work to department
subgraphs (Architecture, Design, Engineering, Quality & Security, Marketing, Documentation,
Recovery, System Ops, Media). Long-running work is **checkpointed** so an interrupted or
human-gated run resumes from the last good checkpoint.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vite 5.4, React 18.3, TypeScript 5.7, TailwindCSS 3.4 (+ shadcn/ui), Framer Motion, React Flow (`reactflow`), Recharts, Lucide, TanStack React Query v5, Zustand, axios |
| Backend | Python 3.11+, FastAPI, Uvicorn, **LangGraph** (+ langchain-core), Pydantic v2 / pydantic-settings, Tenacity, httpx, Loguru |
| Database | Supabase Cloud — PostgreSQL + `pgvector` *(optional; seed layer is the zero-config default)* |
| Storage | Supabase Storage *(optional)* |
| Realtime | WebSockets (FastAPI `ConnectionManager`) + Supabase Realtime *(optional)* |
| Queue | Redis / Upstash *(optional)* |
| Packaging | **No JS monorepo tool, no Docker** — separate `frontend/` (npm) and `backend/` (venv + pip) trees |

---

## Monorepo Layout

```
omnivra/
+- frontend/            # Vite + React + TS app (the Command Center UI)
+- backend/             # FastAPI + LangGraph multi-agent server
|  +- app/              # api/ core/ graph/ providers/ agents/ services/ schemas/ data/ db/ workspace_fs/
|  +- tests/            # pytest suite (70 tests)
+- supabase/            # Canonical SQL: schema.sql + rls.sql + seed.sql (Postgres + pgvector)
+- workspace/           # *** AI AGENT OUTPUT ONLY *** (see Workspace Rule)
|  +- frontend/  backend/  docs/  presentations/  reports/
|  +- .state/           # runtime checkpoints, workflows, vectors (git-ignored)
+- docs/                # Durable, git-tracked control plane + guides
|  +- PROJECT_STATE.md  FILE_MANIFEST.md  CHECKPOINTS.md  ROADMAP.md
|  +- DESIGN_SYSTEM.md  SUPABASE_INTEGRATION.md  DEPLOYMENT.md
+- scripts/             # PowerShell helpers: setup.ps1  dev.ps1  state.ps1 (no Docker)
+- .vscode/  .gitignore  .editorconfig  .env.example  README.md
```

See `docs/PROJECT_STATE.md` for the authoritative, machine-readable layout + state snapshot.

---

## The Workspace Rule

> **AI agents may ONLY write artifacts under `./workspace`** — specifically `workspace/frontend`,
> `workspace/backend`, `workspace/docs`, `workspace/presentations`, `workspace/reports`. Agents
> **MUST NEVER** modify project source code (`frontend/`, `backend/`, `supabase/`, `docs/`, root
> configs) directly.

This boundary is enforced in the backend's path-jailed `FileManager`
(`backend/app/workspace_fs/file_manager.py`, rooted at `WORKSPACE_ROOT`). Generated artifacts are
reviewed by a human at the **Approval Gate** before anything is promoted out of `workspace/`. The
volatile runtime state lives under `workspace/.state/`.

---

## Agent Roster

| Department | Agent | Provider / Model |
|---|---|---|
| Executive | CEO / Manager | Google AI Studio · `gemini-3.1-flash-lite` |
| Architecture | Solution Architect | Groq · `openai/gpt-oss-120b` |
| Design | UI/UX Designer | Google AI Studio · `gemini-3.1-flash-lite` |
| Engineering | Database Engineer | OpenRouter · `nvidia/nemotron-3-super-120b-a12b:free` |
| Engineering | Frontend Engineer | OpenRouter · `poolside/laguna-m.1:free` |
| Engineering | Backend Engineer | OpenRouter · `z-ai/glm-4.5-air:free` |
| Engineering | API Engineer | OpenRouter · `z-ai/glm-4.5-air:free` |
| Quality & Security | QA Engineer | Groq · `llama-3.3-70b-versatile` |
| Quality & Security | SecOps Engineer | Groq · `openai/gpt-oss-120b` |
| Marketing | SEO Researcher | Groq · `groq/compound` |
| Marketing | Social Strategist | OpenRouter · `moonshotai/kimi-k2.6:free` |
| Marketing | Reel Automation | Groq · `llama-3.1-8b-instant` |
| Documentation | Documentation Agent | Groq · `llama-3.3-70b-versatile` |
| Documentation | Presentation Designer | Groq · `llama-3.3-70b-versatile` |
| Recovery | Recovery Agent | OpenRouter · `nvidia/nemotron-3-super-120b-a12b:free` |
| System Ops | Task Classifier, Workflow Router, Memory Retrieval, Notification, Log Analyzer | OpenRouter · `liquid/lfm-2.5-1.2b-thinking:free` |
| Media | Speech-to-Text | Groq · `whisper-large-v3-turbo` |
| Media | Text-to-Speech | Groq · `canopylabs/orpheus-v1-english` |
| Media | Image Generation | Hugging Face · `black-forest-labs/FLUX.1-schnell` |

23 agents total, registered in `backend/app/agents/registry.py`.

---

## How to Run

> Windows + PowerShell. **No Docker.** Python **venv** only. Requires Node.js ≥ 20, npm ≥ 10,
> Python ≥ 3.11. Supabase and Redis are **optional** (the seed layer + local stores are the
> zero-config default).

### Helper scripts (recommended)

```powershell
# One-time: create the backend venv, install both tiers, seed .env files
pwsh ./scripts/setup.ps1

# Start backend (uvicorn :8000) + frontend (vite :5173) in two windows
pwsh ./scripts/dev.ps1
```

- Frontend: <http://localhost:5173> (proxies `/api` and `/ws` to `:8000`)
- Backend docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

The app runs **open** (no login) by default.

### Manual

```powershell
# Backend
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
Copy-Item .env.example .env          # fill in keys (optional — stub mode works without)
python -m uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
Set-Location frontend
npm install
npm run dev                          # http://localhost:5173
```

### Supabase (optional)

Create a Supabase Cloud project, then apply `supabase/schema.sql` → `supabase/rls.sql` →
`supabase/seed.sql` (in order), `pip install supabase`, and set `SUPABASE_URL` +
`SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`. See `docs/SUPABASE_INTEGRATION.md` for the full
runbook (pgvector, Storage buckets, RLS).

---

## How to Test

These gates are kept green at every phase.

```powershell
# Backend — pytest (70 tests)
backend\.venv\Scripts\python.exe -m pytest

# Frontend — build / lint / test
npm --prefix frontend run build      # tsc && vite build (exit 0)
npm --prefix frontend run lint       # eslint --max-warnings 0 (zero warnings)
npm --prefix frontend run test       # vitest run (render smoke)
```

Lint is strict: explicit `any` is forbidden, and warnings fail the build (`--max-warnings 0`). Use
`import type` for type-only imports.

---

## Stub Mode vs. Real Keys

Omnivra runs **fully offline by default**:

- **No provider keys** → every provider returns a deterministic offline **stub**, so the LangGraph
  run completes, media endpoints respond, and tests pass with zero external dependencies.
- **Real keys** → set `GOOGLE_AI_STUDIO_API_KEY` / `OPENROUTER_API_KEY` / `GROQ_API_KEY` /
  `HUGGINGFACE_API_KEY` in `backend/.env` to call the real LLM/media providers (each call wrapped
  with tenacity backoff on 429 / timeout / transient).
- **No Supabase** → the bundled **seed** data layer + a **local hashing vector store** (under
  `workspace/.state/vectors/`) + an **in-memory** checkpointer back the app. Supabase upgrades these
  to durable, multi-process backends (optional).

---

## Auth & Hardening

Auth is **opt-in** (`AUTH_ENABLED`, default `false`):

- **Open mode (default)** — the API runs without login; `require_user` resolves to the admin user,
  and `POST /api/auth/login` accepts any username and returns a token so the SPA always has one.
- **Enabled mode (`AUTH_ENABLED=true`)** — `POST /api/auth/login` validates the configured admin
  credentials (`ADMIN_USERNAME` / `ADMIN_PASSWORD`) and returns a signed token; sensitive POSTs
  (`workflows/run`, approval decisions, knowledge add + ingest) require
  `Authorization: Bearer <token>` (401 without one). `GET /api/auth/config` reports
  `{ "authEnabled": <bool> }` so the SPA knows whether to show login.

Hardening: a middleware adds security headers (`X-Frame-Options`, `X-Content-Type-Options`,
`Referrer-Policy`, `Permissions-Policy`) when `SECURITY_HEADERS_ENABLED` (default on), plus opt-in
per-IP rate limiting (`RATE_LIMIT_ENABLED`, `RATE_LIMIT_PER_MINUTE`). See
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the full production hardening checklist.

---

## Project State, Checkpoints & Resume

Generation is **resumable**. The system maintains four durable, git-tracked documents in `docs/`
that double as machine-readable state:

| File | Role |
|---|---|
| `docs/PROJECT_STATE.md` | Current phase, build status, and an `omnivra-state` JSON block (single source of truth for resume). |
| `docs/FILE_MANIFEST.md` | Every planned/generated file, its owning agent, phase, and status. |
| `docs/CHECKPOINTS.md` | Append-only log of checkpoints (id, node, status, manifest hash). |
| `docs/ROADMAP.md` | 10-phase delivery plan with exit criteria. |

At runtime the backend mirrors live state under `workspace/.state/` (volatile, git-ignored:
`project_state.json`, `workflows/`, `vectors/`, `checkpoints/`) and flushes durable snapshots back
into `docs/`. Inspect the current build state any time with `pwsh ./scripts/state.ps1`. On restart,
the orchestrator (and the **Recovery Agent**) reads the latest checkpoint and resumes.

**Current state:** all **10 phases complete** through `cp-0010-phase10-polish`, plus a post-1.0
build-out (`cp-0011`..`cp-0013`: remaining nav pages + Agent Hierarchy Tree, Projects/Tasks
full-stack, and the design-system "center" panels). Backend **70/70 pytest pass**; frontend build /
lint / test green (vitest 14/14). See each doc's header for the exact format.

---

## Platform Guarantees

- **Human Approval Gate** before publishing content / final code / exporting presentations —
  actions **Approve / Reject / Retry / Rollback**, resumed via REST + WebSocket; the run
  `interrupt()`s mid-flight under a LangGraph checkpointer.
- **Retry system** — every external provider call is wrapped with **tenacity** exponential backoff;
  retries on `429`, timeouts, and transient failures, with a deterministic offline stub fallback.
- **Kill switch** — LangGraph state carries `recursion_count`; if it exceeds `MAX_RECURSION` (3) the
  workflow **STOPS** and is marked **FAILED**.
- **Checkpointing / recovery** — file manifest + project state + per-run metadata are persisted; an
  interrupted run resumes from the last checkpoint (durable cross-restart resume via the optional
  Supabase Postgres checkpointer; run metadata persists either way).
- **Workspace jail** — agents can only write under `./workspace`; the path-jailed FileManager
  rejects any escape.

---

## Docs & Deploy

- **[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)** — production deployment guide: backend (venv +
  Uvicorn/Gunicorn-Uvicorn workers), static frontend + reverse proxy (`/api` + `/ws`), the full
  environment-variable table, the optional Supabase setup, and the production hardening checklist.
- **[`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md)** — authoritative, resumable build state.
- **[`docs/ROADMAP.md`](docs/ROADMAP.md)** — the 10-phase delivery plan with exit criteria.
- **[`docs/SUPABASE_INTEGRATION.md`](docs/SUPABASE_INTEGRATION.md)** — full Supabase runbook.
- **[`docs/DESIGN_SYSTEM.md`](docs/DESIGN_SYSTEM.md)** — design tokens + UI system.

---

© Omnivra — AI Company OS. Internal project.
#
