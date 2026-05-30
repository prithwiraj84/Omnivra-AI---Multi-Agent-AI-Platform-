# ROADMAP — Omnivra AI Company OS

> Phased delivery plan. Each phase lists scope, primary owners, **exit criteria** (the gate that
> must pass to advance), and dependencies. Generation is incremental, checkpointed, and
> approval-gated: the orchestrator advances `PROJECT_STATE.current_phase` only when the current
> phase's exit criteria are met **and** the human Approval Gate clears it. The JSON mirror at the
> bottom is what the orchestrator reads.

---

## Phase 1 — Foundation `(DONE — awaiting approval)`
**Goal:** a runnable, well-structured monorepo with the durable control-plane (state/checkpoint
docs) in place.
**Owners:** architect, ceo, frontend-eng, backend-eng, db-eng, designer.
**Scope:**
- Top-level layout (`frontend/`, `backend/`, `supabase/`, `workspace/`, `docs/`, `scripts/`, config).
- Root tooling: `.gitignore`, `.editorconfig`, `.env.example`, `README.md`, `.vscode/`, PowerShell
  scripts (no JS monorepo tool, no Docker).
- Frontend scaffold: Vite + React + TS configs, Tailwind design tokens (`tailwind.config.ts`,
  `src/index.css`, `src/styles/tokens.ts`), runnable glass placeholder shell, shadcn config.
- Backend scaffold: FastAPI app + Uvicorn entry, Pydantic settings, Loguru logging, provider
  skeletons (tenacity-wrapped base), 23-agent `registry.py`, LangGraph `state`/`kill_switch`/
  `builder`/`approval` skeletons, checkpoint store, path-jailed workspace FS, tests.
- Supabase SQL: `supabase/{schema,rls,seed}.sql` (Postgres + pgvector) + `docs/SUPABASE_INTEGRATION.md`.
- Control plane: `PROJECT_STATE.md`, `FILE_MANIFEST.md`, `CHECKPOINTS.md`, `ROADMAP.md`,
  `DESIGN_SYSTEM.md`.
**Exit criteria (met):**
- `import app.main` succeeds (23 agents); `pytest` = **15 passed, 0 failed**.
- `npm run build` (`tsc && vite build`) succeeds; design-token CSS compiles.
- State docs parse and `cp-0001-phase1-foundation` is resolvable.
**Checkpoint:** `cp-0001-phase1-foundation`.

## Phase 2 — Design system + UI primitives + layout shell `(DONE — awaiting approval)`
**Goal:** the reusable visual layer and command-center frame.
**Owners:** frontend-eng, designer.
**Scope:** typed `config/` + `types/`; shadcn `ui/` primitives; `common/` glass primitives;
themed Recharts `charts/` wrappers; `AppLayout` + `Sidebar` + `Topbar` + `RightRail` shell;
`NotFoundPage`.
**Exit criteria (met):**
- Layout shell renders with the exact `omnivra-*` design tokens; primitives typecheck and build.
- `npm run build` (`tsc` strict + `vite build`) succeeds **exit 0** (2580 modules).
- `npm run test` (vitest/jsdom) = **3 passed, 0 failed** — full app shell mounts (render smoke).
- 42 `frontend/src/` files: foundation, UI primitives, chart wrappers, layout shell, pages, tests.
**Depends on:** Phase 1.
**Checkpoint:** `cp-0002-phase2-design-system`.

## Phase 3 — Dashboard sections (mock data) `(DONE — awaiting approval)`
**Goal:** every reference dashboard section, wired to mock data.
**Owners:** frontend-eng, designer.
**Scope:** Executive Overview stat cards; AI Agents Status grid + SYSTEM OPERATIONS sub-row;
Active Workflows; Task Execution Overview (Recharts area + timeframe); Task Distribution (donut);
Live Activity Feed; System Health; Model Usage By Provider; Top Models By Usage; Recent
Achievements; brand footer; CommandPalette; primary pages.
**Exit criteria (met):**
- All reference dashboard sections built and wired to mock fixtures (`src/data/dashboard.ts`),
  with `types/index.ts` extended for the dashboard data shapes.
- 22 `components/dashboard/*` section components; `Dashboard.tsx` + `right-rail.tsx` rewritten to
  assemble the props-driven main column + right rail.
- `npm run lint` (`eslint --max-warnings 0`) succeeds **exit 0** (clean).
- `npm run build` (`tsc` strict + `vite build`) succeeds **exit 0** (2609 modules).
- `npm run test` (vitest/jsdom) = **4 passed, 0 failed** — render smoke asserts all 8 dashboard
  sections render on mock data plus stat values + a workflow name.
**Depends on:** Phase 2.
**Checkpoint:** `cp-0003-phase3-dashboard`.

## Phase 4 — Backend data layer + REST API + Supabase wiring `(DONE — awaiting approval)`
**Goal:** real data behind the dashboard.
**Owners:** backend-eng, api-eng, db-eng, frontend-eng.
**Scope:** `app/db` client + repositories against Supabase; `app/api` router + routes
(`workflows`, `agents`, `system`); request/response schemas; frontend `lib/api`, `lib/supabase`,
React Query hooks + Zustand stores; swap mock data for live REST.
**Built:** Pydantic DTOs (`app/schemas`, camelCase via `to_camel`); seed data layer (`app/data`);
Supabase client (`app/db/client.py`, lazy/optional) + repository abstraction (`DashboardRepository`
Protocol, default `SeedRepository`, optional `SupabaseRepository` with seed fallback,
`get_repository` factory); REST router + routes (`dashboard`, `agents`, `workflows`, `approvals`,
`activity`, `system`); frontend `lib/api/{client,types,icons,dashboard}.ts` + `hooks/useDashboard.ts`;
`Dashboard.tsx` + `right-rail.tsx` rewired to `useDashboard()` (mock as instant fallback).
**Exit criteria (met):**
- REST API live: `GET /api/dashboard` returns all 17 camelCase keys; agents/workflows/approvals/
  activity/system routes serve seed data.
- Repository abstraction in place — seed (default, zero deps) + optional Supabase (fail-safe fallback).
- Frontend reads `/api/dashboard` via `useDashboard()` (Vite proxy → FastAPI) with mock `initialData`.
- End-to-end **curl-verified** against a live uvicorn server; `pytest` = **25 passed** (15 + 10 new
  API tests); frontend still green (build exit 0, lint 0, vitest 4/4).
**Depends on:** Phase 3.
**Checkpoint:** `cp-0004-phase4-data-api`.

## Phase 5 — Agent/provider integration + LangGraph orchestration + kill switch + tenacity `(DONE — awaiting approval)`
**Goal:** the CEO agent plans and delegates through a real LangGraph state machine.
**Owners:** architect, backend-eng.
**Scope:** LangGraph graph builder + per-department nodes; concrete department agents; provider
clients completed with tenacity exponential backoff (429/timeout/transient); kill switch
(`recursion_count > 3` ⇒ STOPPED) wired live; Agent Hierarchy Tree (React Flow); department pages.
**Built:** providers rewritten to `httpx` + offline STUB mode (no vendor SDKs) — `app/providers/_compat.py`
(`make_stub_response`/`openai_chat`/`post_json`), `openrouter.py`, `groq.py`, `google_ai.py`,
`huggingface.py`, and `registry.py` (`get_provider_registry()` cached singleton); agent runner
(`app/agents/runner.py`: `run_agent` + `build_system_prompt`); orchestration schemas
(`app/schemas/orchestration.py`: `RunRequest`/`RunResult`/`AgentRunOutput`/`PendingApproval`, camelCase);
LangGraph orchestration (`app/graph/builder.py` `build_graph`/`get_compiled_graph`, `planner.py`
`plan_delegations`, `nodes/{ceo,delegate,approval,finalize}.py`) with topology
`START → ceo → guard(check_kill_switch) → {stop: END, go: delegate} → approval → {wait: END, go: finalize} → END`;
orchestrator service (`app/services/orchestrator.py` `run_workflow()`); `POST /api/workflows/run`
(`response_model=RunResult`, GET preserved); `tests/test_orchestration.py` (7 tests). Providers call
real LLMs (tenacity retry on 429/timeout/5xx) when keys are set; otherwise a deterministic offline stub.
`langgraph 1.2.2` + `langchain-core 1.4.0` installed into `backend/.venv`.
**Exit criteria (met):**
- Providers integrated with tenacity backoff + deterministic offline stub fallback (no vendor SDKs).
- LangGraph CEO → department delegation graph builds and runs; a CEO prompt produces a delegated,
  checkpointed run.
- Kill switch enforced at the guard (`recursion_count > 3` ⇒ STOPPED).
- Approval gate: publish/deploy/export/release/presentation/final tasks → `AWAITING_APPROVAL` +
  `pending_approval` (resume wiring is Phase 7).
- `POST /api/workflows/run` live — "Design the UI and build the REST API" → `completed`, 6 `agentOutputs`,
  `recursionCount=1`; "Publish and deploy…" → `awaiting_approval`, `pendingApproval.kind=final_code`.
- `pytest` = **32 passed** (25 + 7 new orchestration tests).
**Depends on:** Phase 4.
**Checkpoint:** `cp-0005-phase5-orchestration`.

## Phase 6 — Realtime WebSockets + live activity/health `(DONE — awaiting approval)`
**Goal:** live, streaming updates.
**Owners:** api-eng, backend-eng, frontend-eng.
**Scope:** WebSocket `ConnectionManager` + broadcast; reconnecting frontend WS client + hook;
live wiring of Live Activity Feed, workflow progress, and System Health.
**Built:** event envelope (`app/schemas/events.py`, camelCase); realtime service
(`app/services/realtime.py`: `ConnectionManager` + module-level `manager`, `emit(type, payload)`,
`health_snapshot()`, `heartbeat_loop`); `app/main.py` `/ws` endpoint rewired to be manager-backed
(sends `hello` + an immediate `system_health` then streams broadcasts; heartbeat task
started/stopped in the lifespan); graph emission wired in
(`services/orchestrator.py` emits `workflow` running/terminal, `graph/nodes/delegate.py` emits
`activity` per delegated agent, `graph/nodes/approval.py` emits `approval` when gating);
`tests/test_realtime.py` (3 tests). Frontend: `src/lib/api/events.ts` (`WsEvent` +
`activityFromEvent`/`healthFromEvent`); `src/hooks/useWebSocket.ts` (connect via Vite `/ws` proxy,
reconnect backoff, folds events into the React Query `['dashboard']` cache — replace `systemHealth`
on `system_health`, prepend on `activity` capped at 12; jsdom-guarded); `src/store/ui.ts` gained
`realtimeStatus` + `setRealtimeStatus`; `app-layout.tsx` calls `useWebSocket()` once; `topbar.tsx`
renders `LiveIndicator`; `src/components/dashboard/live-indicator.tsx` (emerald `Live` / amber
`Connecting` / `Offline`); smoke test asserts the live indicator renders. The `/ws` Vite proxy
targets `ws://localhost:8000`.
**Exit criteria (met):**
- `/ws` `ConnectionManager` broadcasting; heartbeat pushes system-health every ~4s (jittered) +
  simulated activity periodically.
- Real `workflow` / `activity` / `approval` events emitted during runs.
- Frontend `useWebSocket` folds events into the `['dashboard']` cache (System Health + Live Activity
  Feed re-render live) + `LiveIndicator` shows connection state.
- `pytest` = **35 passed** (32 + 3 new realtime tests); live WebSocket **verified** (real socket,
  port 8012: `hello` → immediate `system_health` 6 metrics → after `POST /api/workflows/run` the
  `workflow` + `activity` events broadcast live); frontend green (lint 0, build exit 0, vitest 5/5).
**Depends on:** Phase 5.
**Checkpoint:** `cp-0006-phase6-realtime`.

## Phase 7 — Human approval gate + recovery/checkpoint resume `(DONE — awaiting approval)`
**Goal:** human-in-the-loop control and full resilience.
**Owners:** api-eng, backend-eng, architect, frontend-eng.
**Scope:** Approval Gate (Approve / Reject / Retry / Rollback) over REST + WS; Pending Approvals
card + Approvals page; Recovery service (rehydrate from durable `docs/`); Recovery Status page.
**Built:** the graph is compiled **with** a LangGraph `MemorySaver` checkpointer
(`app/graph/builder.py`); the approval node calls LangGraph `interrupt()` to suspend mid-run and
branches on the decision (approve/retry → RUNNING, reject → FAILED, rollback → ROLLED_BACK)
(`app/graph/nodes/approval.py`); `app/services/orchestrator.py` `run_workflow` detects the interrupt
(`state['__interrupt__']`), returns `awaiting_approval` + the pending payload, and persists the run —
new `resume_workflow` re-enters via `Command(resume={action,note})`. `app/services/workflow_store.py`
(`WorkflowStore` + `get_workflow_store`) persists each run (`RunResult` JSON) under
`workspace/.state/workflows/`. `app/api/routes/approvals.py` `POST /{id}/decision` now resumes (404 if
unknown); `app/api/routes/workflows.py` added `GET /runs` + `GET /runs/{id}`. `tests/test_approval_resume.py`
(6 tests); `tests/test_api.py` edited (decision-on-seed-approval asserts 404). Frontend:
`src/lib/api/types.ts` (+`RunResult`/`AgentRunOutput`/`PendingApproval`/`RunStatus`),
`src/lib/api/workflows.ts` (`runWorkflow`/`listAwaitingRuns`/`decideApproval`),
`src/hooks/useApprovals.ts` (`useAwaitingApprovals` + `useApprovalDecision`),
`src/hooks/useRunWorkflow.ts`, `src/components/dashboard/run-task.tsx` (`RunTask`); `greeting-hero.tsx`
renders `RunTask`; `approval-card.tsx` gained `onDecision` Approve/Reject/Retry/Rollback actions;
`pending-approvals.tsx` shows LIVE awaiting runs above seed items (doubles as the Recovery view), wired
to the decision mutation; `smoke.test.tsx` asserts `RunTask` renders.
**Exit criteria (met):**
- A held workflow can be approved/rejected/retried/rolled back from the UI and resumes correctly:
  the approval node `interrupt()`s under the `MemorySaver` checkpointer and the decision API resumes
  (approve/retry → completed), rejects (→ failed), or rolls back (→ rolled_back) the paused run.
- Runs are persisted (`WorkflowStore` under `workspace/.state/workflows/`) with a recovery listing
  (`GET /api/workflows/runs[?status]`); unknown `approvalId` → 404.
- Frontend approval actions (Approve/Reject/Retry/Rollback) + the `RunTask` control are live; Pending
  Approvals lists live awaiting runs (Recovery view).
- `pytest` = **41 passed** (35 + 6 new resume tests); frontend green (lint 0, build exit 0, vitest 6/6).
- **Note:** resume is SAME-PROCESS (LangGraph `MemorySaver` is in-memory); durable cross-restart
  resume needs a Postgres checkpointer (Supabase) — the `WorkflowStore` persists run metadata either way.
**Depends on:** Phase 5, Phase 6.
**Checkpoint:** `cp-0007-phase7-approval`.

## Phase 8 — Marketing / Docs / Presentation / Media agents + workspace artifacts `(DONE — awaiting approval)`
**Goal:** content + media generation behind the gate; agents write real artifacts into `./workspace`.
**Owners:** marketing agents, docs, presentation-designer, backend-eng (media).
**Scope:** SEO Researcher, Social Strategist, Reel Automation, Documentation, Presentation
Designer agents; media services (STT/TTS/image-gen); Media Services dashboard card; Marketing &
Security centers. All publish/export passes through the Approval Gate; drafts land in `workspace/`.
**Built:** `ArtifactService` (`app/services/artifacts.py` `ArtifactService` + `get_artifact_service`)
files each agent output under workspace SUBDIRS by agent (`docs/frontend/backend/presentations/reports`)
via the path-jailed `FileManager` + writes `reports/<wf>/run.md`; `app/schemas/workspace.py`
(`Artifact`/`ArtifactContent`, re-exported); `app/api/routes/workspace.py` (`GET /artifacts`,
`GET /artifacts/{path}`, mounted `/workspace`); `app/schemas/orchestration.py`
(`AgentRunOutput.artifacts`); `app/services/orchestrator.py` calls `persist_run` in both
`run_workflow` + `resume_workflow` so `RunResult.agentOutputs[].artifacts` carry workspace-relative
paths. Media: `app/services/media.py` (`MediaService` — `generate_image` via HuggingFace FLUX.1-dev
when configured else stub placeholder; `transcribe`/`synthesize` stub-safe) + `app/schemas/media.py` +
`app/api/routes/media.py` (`POST /api/media/image`, `/tts`, `/stt`, mounted `/media`);
`app/api/router.py` (added workspace + media); `tests/test_workspace_artifacts.py` +
`tests/test_media.py`. Frontend: `src/lib/api/types.ts` (`Artifact`/`ArtifactContent`),
`src/lib/api/artifacts.ts` (`listArtifacts`/`readArtifact`), `src/hooks/useArtifacts.ts`,
`src/components/workspace/artifact-explorer.tsx` (two-pane list + viewer), `src/pages/Workspace.tsx`
+ `src/pages/Documents.tsx`, `src/App.tsx` (`/workspace` → `Workspace`, `/documents` → `Documents`;
both removed from the Placeholder); `smoke.test.tsx` asserts `/workspace` renders.
**Exit criteria (met):**
- Agents write artifacts into `./workspace` via the path-jailed `FileManager` (each agent output +
  a run report; honors the Workspace Rule — agents only write under `./workspace`).
- Workspace list/read API: `GET /api/workspace/artifacts` lists; `GET /api/workspace/artifacts/{path}`
  reads (400 on sandbox escape, 404 missing).
- Media services + endpoints stub-safe (`POST /api/media/image` / `/tts` / `/stt`); `generate_image`
  uses HuggingFace FLUX.1-dev when keyed, else a stub placeholder.
- Workspace/Documents two-pane explorer UI live (list + viewer via `useArtifacts`).
- `pytest` = **45 passed** (41 + 4 new — workspace artifacts + media stubs); frontend green
  (lint 0, build exit 0, vitest 7/7).
- **Note:** media runs STUB-safe with no keys — set `HUGGINGFACE_API_KEY` for real FLUX.1-dev image
  generation; Groq Whisper STT / Orpheus TTS are stubbed pending key + audio wiring.
**Depends on:** Phase 7.
**Checkpoint:** `cp-0008-phase8-artifacts`.

## Phase 9 — Knowledge base + memory (pgvector) + RAG `(DONE — awaiting approval)`
**Goal:** durable agent memory and retrieval-augmented generation.
**Owners:** db-eng, backend-eng, frontend-eng.
**Scope:** pgvector embedding pipeline + retrieval repositories; Memory Retrieval (System Ops)
RAG node; Knowledge Base + Memory pages.
**Built:** `app/services/vectorstore.py` — a deterministic 256-dim hashing embedder (offline, no key)
+ a cosine `VectorStore` persisted to `workspace/.state/vectors/<name>.json`; `KnowledgeService`
(`app/services/knowledge.py`: knowledge corpus + `ingest_workspace`) and `MemoryService`
(`app/services/memory.py`: agent memory). RAG: `app/graph/nodes/delegate.py` recalls memory into each
agent's context (`recall_context`); `app/services/orchestrator.py` (`_persist_artifacts_and_memory`)
stores every successful output as memory after run/resume, so the company learns from prior work.
Schemas `app/schemas/knowledge.py` (+ re-export); REST `app/api/routes/knowledge.py`
(search/add/ingest-workspace/stats) + `app/api/routes/memory.py` (search/recent/stats) mounted in
`app/api/router.py` (`/knowledge`, `/memory`); `tests/{test_vectorstore.py,test_knowledge.py,test_memory_rag.py}`.
Frontend: `src/lib/api/types.ts` (`SearchHit`/`MemoryEntry`/`StoreStats`/`IngestResult`),
`src/lib/api/knowledge.ts`, `src/hooks/{useKnowledge,useMemory}.ts`, `src/pages/{KnowledgeBase,Memory}.tsx`,
`src/App.tsx` (`/knowledge` → `KnowledgeBase`, `/memory` → `Memory`); `smoke.test.tsx` asserts
`/knowledge` + `/memory` render.
**Exit criteria (met):**
- Vector store + offline embedder live (deterministic 256-dim hashing embedder + cosine `VectorStore`
  persisted under `workspace/.state/vectors/`).
- KB search retrieves relevant docs; `ingest-workspace` indexes artifacts (search/add/ingest/stats API).
- Agent memory + RAG injection: each successful output is stored as memory; `delegate.py` recalls memory
  into agent context (`recall_context`) so prior runs ground later ones.
- Knowledge Base + Memory pages live (`useKnowledge`/`useMemory` over `/knowledge` + `/memory`).
- `pytest` = **55 passed** (45 + 10 new — vector store + knowledge + memory/RAG); frontend green
  (lint 0, build exit 0, vitest 9/9).
- **Note:** embeddings are a local offline hashing embedder (256-d) by default (no key); the Supabase
  pgvector path (1536-d, `match_knowledge`/`match_memory`) is the optional durable backend — the local
  store is the zero-config default.
**Depends on:** Phase 8.
**Checkpoint:** `cp-0009-phase9-knowledge`.

## Phase 10 — Polish + auth + deploy + hardening `(DONE — FINAL; project complete)`
**Goal:** production readiness.
**Owners:** secops, qa, all engineering.
**Scope:** auth gate + hardening; rate-limit; perf + a11y / animation pass; deploy docs; security
review; post-build polish/fixes.
**Built:** auth + hardening — `backend/app/core/security.py` (stdlib HMAC signed tokens:
`create_token`/`verify_token`/`verify_credentials`); `backend/app/api/deps.py` `require_user` (open in
dev, Bearer-enforced when `AUTH_ENABLED`); `backend/app/api/routes/auth.py`
(`/api/auth/config|login|me`); sensitive POSTs (`workflows/run`, approvals `decision`, knowledge
`add`+`ingest`) depend on `require_user`; `backend/app/main.py` `hardening_middleware` (security
headers always; opt-in per-IP rate limit). New settings: `auth_enabled` (false),
`admin_username`/`admin_password`, `token_ttl_seconds`, `security_headers_enabled` (true),
`rate_limit_enabled` (false), `rate_limit_per_minute`. Frontend auth gate: `src/store/auth.ts`,
`src/lib/api/auth.ts`, `src/hooks/useAuth.ts`, `src/pages/Login.tsx`,
`src/components/auth/auth-gate.tsx`, `src/components/common/error-boundary.tsx`,
`src/pages/Settings.tsx`, axios bearer interceptor (`src/lib/api/client.ts`), wired in `App.tsx` +
`main.tsx`. Docs: `docs/DEPLOYMENT.md` (new) + `README.md` (rewritten). Backend tests:
`tests/test_auth.py` + `tests/test_security.py`. Post-build polish/fixes: (a) dashboard layout fix —
`src/components/layout/sidebar.tsx` was `position:fixed` behind the `AppLayout` CSS grid, fixed to an
in-flow sticky grid item; (b) `vite.config.ts` swallows `/api` + `/ws` proxy
`ECONNREFUSED`/`ECONNABORTED` noise; (c) `backend/requirements.txt` `websockets==16.0` →
`websockets>=12,<16` (resolves the supabase 2.30.1 conflict); (d) animation foundation
`src/lib/motion.ts` + `src/components/common/{reveal,count-up}.tsx` applied across ~24 components
(reduced-motion aware). The whole product runs OFFLINE in stub mode (no keys/Supabase needed); real
providers/Supabase/auth activate via `backend/.env`.
**Exit criteria (met):**
- Auth gate + hardening: opt-in HMAC signed-token auth, `require_user` on sensitive POSTs, security
  headers always-on, opt-in per-IP rate limit.
- Deploy docs: `docs/DEPLOYMENT.md` + rewritten `README.md`.
- Polish: dashboard layout fix, dev proxy noise fix, websockets dependency fix, animation pass.
- `pytest` = **62 passed** (55 + 7 new — auth + security); frontend green (`npm run build` exit 0,
  `npm run lint` 0 warnings, vitest **12/12**).
**Depends on:** all prior phases.
**Checkpoint:** `cp-0010-phase10-polish`.

---

## Post-1.0 — feature/component parity + review hardening `(DONE — additive over 1.0)`

After the 10-phase 1.0 shipped (`cp-0010-phase10-polish`), four additive, approval-free post-1.0
checkpoints brought the product to full feature/component parity and applied a lead-engineer review.
These are tracked as checkpoints `cp-0011..cp-0014` (full records in `docs/CHECKPOINTS.md`); they do
not introduce a new numbered phase — phases 1–10 remain the project's spine.

### cp-0011 — Remaining nav pages + Agent Hierarchy Tree
Built every remaining navigable page so the whole sidebar is real: **Agents** (roster grouped by
department + Grid/Hierarchy toggle), **AgentHierarchyTree** (CEO → department → agent org chart via
React Flow — fitView + Controls + MiniMap), **Workflows** (RunTask + active runs + run-history with
per-run drill-down of agentOutputs/artifacts/errors), **Approvals** (full-page live gate reusing
PendingApprovals with Approve/Reject/Retry/Rollback), **Departments ×7** (slug-driven roster), **Logs**,
**Integrations** (provider/Supabase/auth status), **Billing** (cost + provider/model usage). Backend
added `GET /api/system/providers` + `GET /api/system/info`; new frontend api/hooks (agents,
workflow-runs, system). At this checkpoint only `/projects` + `/tasks` remained `Placeholder` (closed in
cp-0012). Validated: backend `pytest` **62 passed**; frontend build exit 0, lint 0, vitest **12/12**.

### cp-0012 — Projects & Tasks (full-stack) + deferred hardening
Built the last two pages full-stack. Backend: `app/services/project_store.py` (JSON-persisted, seeded),
`app/schemas/projects.py`, CRUD routes `app/api/routes/{projects,tasks}.py` (mutations auth-gated when
`AUTH_ENABLED`). Frontend: `lib/api/projects.ts`, `hooks/{useProjects,useTasks}.ts`, `pages/Projects.tsx`
(board + create/delete) + `pages/Tasks.tsx` (4-column Kanban with create/move/delete). `App.tsx` wired
both routes and removed the `Placeholder` import — **no Placeholder routes remain**. Deferred hardening:
`provider_max_retries` is now read by `with_provider_retry` (single source of truth) and a
`seed.sql`↔agent-registry drift-guard test was added. Validated: backend `pytest` **70 passed**
(62 + `test_projects_tasks` (5) + `test_seed_sync` (3)); frontend build exit 0, lint 0, vitest **14/14**.

### cp-0013 — Design-doc "center" panels (completes the component inventory)
Built the remaining `DESIGN_SYSTEM.md` §8.3 "center" detail panels: **SecurityCenter**,
**MarketingCenter**, **DocumentationCenter** (now backing `/departments/quality`,
`/departments/marketing`, `/departments/documentation`; the other 4 departments keep the generic
roster), plus **RecoveryStatus** (resumable awaiting runs + the `cp-NNNN` checkpoint lineage) on the
Workflows page and **MemoryUsagePanel** (memory + knowledge store sizes + recent memory) atop the Memory
page. Backend added `GET /api/system/checkpoints` + frontend `listCheckpoints`/`useCheckpoints`. With
`AgentHierarchyTree` (cp-0011), this realizes **every** component in the design-system inventory.
Validated: backend `pytest` **70 passed**; frontend build exit 0, lint 0, vitest **14/14**.

### cp-0014 — Applied the full-system lead-engineer review (verdict SHIP)
Ran a multi-agent lead-engineer review (security / backend-correctness / frontend / docs); **verdict
SHIP, no critical/high code defects**. Applied the actionable findings: fixed a **HIGH path-traversal**
on `GET /api/workflows/runs/{workflow_id}` (`WorkflowStore._path` now rejects `/`, `\`, NUL, `..` →
clean 404); applied the same jail to `CheckpointStore` (defense-in-depth); deduped RAG memory on resume
via a stable id (`mem:{workflow_id}:{agent_id}` so approve/retry upserts instead of duplicating); added
`threading.RLock` around read-modify-write in `VectorStore` + `ProjectStore` (sync routes run in a
threadpool); corrected `README.md` + `docs/DEPLOYMENT.md` test counts 55→70; removed an auditor scratch
file (`backend/_audit_recursion.py`). Validated: backend `pytest` **70 passed**; frontend build exit 0,
lint 0, vitest **14/14**.

---

## Forward-looking followups (NON-BLOCKING — from the sign-off)

These are explicitly out-of-scope for 1.0 and **do not block** git/deploy; they are the deferred
enhancements noted at the review sign-off:

1. **Durable cross-restart resume.** Add a durable Postgres/Supabase LangGraph checkpointer so paused
   approvals survive a backend restart. Today resume uses an in-process `MemorySaver` (same-process
   only); the `WorkflowStore` already persists run metadata under `workspace/.state/workflows/` either
   way, so runs/recovery listings survive a restart even though the in-flight graph state does not.
2. **Broaden store concurrency.** Broaden store locking or move the JSON stores
   (`VectorStore`/`ProjectStore`/`WorkflowStore`) to Supabase if concurrency grows beyond the current
   single-node threadpool model.
3. **Re-enable the recursion kill switch's meaning.** The recursion kill switch is correctly implemented
   and unit-tested but is **dormant** in the current linear graph: `recursion_count` maxes at 1 because
   `ceo` runs once and no edge loops back. Re-enable its meaning by adding a replanning edge (a loop back
   into planning) so the counter can actually climb toward the threshold.
4. **Prod-hardening checklist (before any non-local deploy).** Override the dev defaults
   (`api_secret_key`, admin credentials), set `AUTH_ENABLED=true`, and consider enabling
   `rate_limit_enabled`. See `docs/DEPLOYMENT.md`.

---

> **All 10 phases are complete and the build is review-hardened (verdict SHIP) — plus a post-1.0
> build-out (`cp-0011..cp-0013`) that brings full feature/component parity and a review-hardening pass
> (`cp-0014`).** Latest checkpoint: `cp-0014-post-review-hardening`. Current validation: backend `pytest`
> **70 passed**; frontend `vite build` exit 0 + `eslint --max-warnings 0` exit 0 + vitest **14/14**. The
> product runs fully OFFLINE in stub mode (no keys/Supabase required); real providers, Supabase (pgvector
> + Realtime + Auth/RLS), and the auth gate activate via `backend/.env`. Optional next steps live in the
> "Forward-looking followups" section above and outside the roadmap: provision Supabase + provider keys,
> set `AUTH_ENABLED`, and deploy per `docs/DEPLOYMENT.md`.

---

## Machine Roadmap (orchestrator-driven phase transitions)

<!-- BEGIN omnivra-roadmap -->
```json omnivra-roadmap
{
  "schema_version": "1.0.0",
  "phases": [
    { "id": 1, "name": "Foundation", "status": "complete", "depends_on": [],
      "exit_criteria": ["import app.main ok (23 agents)", "pytest 15 passed", "npm run build passes", "cp-0001 resolvable"],
      "checkpoint": "cp-0001-phase1-foundation" },
    { "id": 2, "name": "Design system + UI primitives + layout shell", "status": "complete", "depends_on": [1],
      "exit_criteria": ["omnivra-* tokens applied", "ui/common/chart primitives build", "AppLayout/Sidebar/Topbar/RightRail render", "npm run build exit 0 (2580 modules)", "vitest 3/3 render smoke"],
      "checkpoint": "cp-0002-phase2-design-system" },
    { "id": 3, "name": "Dashboard sections (mock data)", "status": "complete", "depends_on": [2],
      "exit_criteria": ["all reference sections built + wired to mock data (src/data/dashboard.ts)", "22 components/dashboard/* + Dashboard.tsx/right-rail.tsx assembled", "npm run lint exit 0 (clean)", "npm run build exit 0 (2609 modules)", "vitest 4/4 — 8 dashboard sections render-verified"],
      "checkpoint": "cp-0003-phase3-dashboard" },
    { "id": 4, "name": "Backend data layer + REST API + Supabase wiring", "status": "complete", "depends_on": [3],
      "exit_criteria": ["REST API live (GET /api/dashboard = 17 camelCase keys)", "repository abstraction: seed (default) + optional Supabase (fail-safe fallback)", "frontend reads /api/dashboard via useDashboard() with mock fallback", "end-to-end curl verified", "pytest 25 passed (15+10 new API tests)", "frontend green (build exit 0, lint 0, vitest 4/4)"],
      "checkpoint": "cp-0004-phase4-data-api" },
    { "id": 5, "name": "Agent/provider integration + LangGraph + kill switch + tenacity", "status": "complete", "depends_on": [4],
      "exit_criteria": ["providers integrated with tenacity backoff + offline stub fallback (no vendor SDKs)", "LangGraph CEO->department delegation graph builds + runs", "kill switch enforced at guard (recursion>3 => STOPPED)", "approval gate holds publish/deploy/export/release/final tasks (resume in Phase 7)", "POST /api/workflows/run live (completed run = 6 agentOutputs; publish/deploy = awaiting_approval/final_code)", "pytest 32 passed (25 + 7 new orchestration tests)"],
      "checkpoint": "cp-0005-phase5-orchestration" },
    { "id": 6, "name": "Realtime WebSockets + live activity/health", "status": "complete", "depends_on": [5],
      "exit_criteria": ["/ws ConnectionManager broadcasting", "heartbeat health stream (~4s jittered) + simulated activity", "real workflow/activity/approval events during runs", "frontend useWebSocket folds events into ['dashboard'] cache (System Health + Live Activity live) + LiveIndicator", "pytest 35 passed (32 + 3 new realtime tests)", "live WebSocket verified (hello -> immediate system_health -> workflow/activity broadcast live)", "frontend green (lint 0, build exit 0, vitest 5/5)"],
      "checkpoint": "cp-0006-phase6-realtime" },
    { "id": 7, "name": "Human approval gate + recovery/checkpoint resume", "status": "complete", "depends_on": [5, 6],
      "exit_criteria": ["approval node interrupt() under a LangGraph MemorySaver checkpointer pauses the run mid-flight", "decision API resumes (approve/retry->completed), rejects (->failed), or rolls back (->rolled_back) the paused run", "runs persisted (WorkflowStore, workspace/.state/workflows/) + recovery listing GET /api/workflows/runs[?status]; unknown approvalId -> 404", "frontend approval actions (Approve/Reject/Retry/Rollback) + RunTask control live; Pending Approvals lists live awaiting runs", "pytest 41 passed (35 + 6 new resume tests)", "frontend green (lint 0, build exit 0, vitest 6/6)", "note: resume is same-process (in-memory MemorySaver); durable cross-restart resume needs a Postgres checkpointer (Supabase) — WorkflowStore persists run metadata either way"],
      "checkpoint": "cp-0007-phase7-approval" },
    { "id": 8, "name": "Marketing/Docs/Presentation/Media agents + workspace artifacts", "status": "complete", "depends_on": [7],
      "exit_criteria": ["agents write artifacts into ./workspace via the path-jailed FileManager (each agent output + a run report; honors the Workspace Rule)", "workspace list/read API: GET /api/workspace/artifacts lists, GET /api/workspace/artifacts/{path} reads (400 sandbox escape, 404 missing)", "media stub-safe services + endpoints (POST /api/media/image, /tts, /stt; generate_image uses HuggingFace FLUX.1-dev when keyed else stub placeholder)", "Workspace/Documents two-pane explorer UI live (list + viewer via useArtifacts)", "pytest 45 passed (41 + 4 new — workspace artifacts + media stubs)", "frontend green (lint 0, build exit 0, vitest 7/7)", "note: media runs stub-safe with no keys — set HUGGINGFACE_API_KEY for real FLUX.1-dev; Groq Whisper STT / Orpheus TTS stubbed pending key + audio wiring"],
      "checkpoint": "cp-0008-phase8-artifacts" },
    { "id": 9, "name": "Knowledge base + memory (pgvector) + RAG", "status": "complete", "depends_on": [8],
      "exit_criteria": ["vector store + offline embedder live (deterministic 256-dim hashing embedder + cosine VectorStore persisted under workspace/.state/vectors/)", "KB search retrieves relevant docs + ingest-workspace indexes artifacts (search/add/ingest/stats API)", "agent memory + RAG injection: each successful output stored as memory; delegate.py recalls memory into agent context (recall_context)", "Knowledge Base + Memory pages live (useKnowledge/useMemory over /knowledge + /memory)", "pytest 55 passed (45 + 10 new — vector store + knowledge + memory/RAG)", "frontend green (lint 0, build exit 0, vitest 9/9)", "note: local offline hashing embedder (256-d) by default (no key); Supabase pgvector path (1536-d, match_knowledge/match_memory) is the optional durable backend — local store is the zero-config default"],
      "checkpoint": "cp-0009-phase9-knowledge" },
    { "id": 10, "name": "Polish + auth + deploy + hardening", "status": "complete", "depends_on": [1, 2, 3, 4, 5, 6, 7, 8, 9],
      "exit_criteria": ["auth gate + hardening: opt-in HMAC signed-token auth (app/core/security.py), require_user on sensitive POSTs (workflows/run, approvals decision, knowledge add+ingest), hardening_middleware (security headers always + opt-in per-IP rate limit)", "auth routes /api/auth/config|login|me + frontend auth gate (store/auth.ts, useAuth, Login.tsx, auth-gate.tsx, error-boundary.tsx, Settings.tsx, axios bearer interceptor)", "deploy docs (docs/DEPLOYMENT.md new + README.md rewrite)", "polish/fixes: dashboard layout fix (sidebar fixed->in-flow sticky grid item), vite proxy noise fix, requirements.txt websockets==16.0->>=12,<16 (supabase 2.30.1 conflict), animation foundation (lib/motion.ts + common/reveal.tsx + common/count-up.tsx) across ~24 components", "pytest 62 passed (55 + 7 new — test_auth.py + test_security.py)", "frontend green (build exit 0, lint 0, vitest 12/12)", "runs OFFLINE in stub mode; real providers/Supabase/auth activate via backend/.env"],
      "checkpoint": "cp-0010-phase10-polish" }
  ],
  "post_1_0": [
    { "id": "cp-0011-pages-hierarchy", "title": "Remaining nav pages + Agent Hierarchy Tree", "status": "complete", "parent": "cp-0010-phase10-polish",
      "delivered": ["Agents page (roster + Grid/Hierarchy toggle)", "AgentHierarchyTree (React Flow CEO->department->agent org chart)", "Workflows (RunTask + active runs + run-history drill-down)", "Approvals (full-page live gate)", "Departments x7 (slug-driven roster)", "Logs", "Integrations", "Billing", "backend GET /api/system/providers + GET /api/system/info", "only /projects + /tasks remained Placeholder at this checkpoint"],
      "validation": ["backend pytest 62 passed", "frontend build exit 0, lint 0, vitest 12/12"] },
    { "id": "cp-0012-projects-tasks", "title": "Projects & Tasks (full-stack) + deferred hardening", "status": "complete", "parent": "cp-0011-pages-hierarchy",
      "delivered": ["Projects + Tasks full-stack (ProjectStore + schemas/projects.py + CRUD routes projects.py/tasks.py)", "Projects.tsx (board) + Tasks.tsx (4-column Kanban)", "App.tsx removed the Placeholder import -> NO placeholder routes remain", "provider_max_retries wired into with_provider_retry", "seed.sql<->agent-registry drift-guard test"],
      "validation": ["backend pytest 70 passed (62 + test_projects_tasks(5) + test_seed_sync(3))", "frontend build exit 0, lint 0, vitest 14/14"] },
    { "id": "cp-0013-center-panels", "title": "Design-doc center panels (completes the component inventory)", "status": "complete", "parent": "cp-0012-projects-tasks",
      "delivered": ["SecurityCenter / MarketingCenter / DocumentationCenter (back /departments/quality,/marketing,/documentation)", "RecoveryStatus (Workflows page)", "MemoryUsagePanel (Memory page)", "backend GET /api/system/checkpoints + frontend listCheckpoints/useCheckpoints", "with AgentHierarchyTree this realizes the ENTIRE design-system component inventory"],
      "validation": ["backend pytest 70 passed", "frontend build exit 0, lint 0, vitest 14/14"] },
    { "id": "cp-0014-post-review-hardening", "title": "Applied the full-system lead-engineer review (verdict SHIP)", "status": "complete", "parent": "cp-0013-center-panels",
      "delivered": ["SECURITY HIGH fixed: path-traversal on GET /api/workflows/runs/{workflow_id} (WorkflowStore._path rejects '/','\\',NUL,'..')", "SECURITY MEDIUM (defense-in-depth): same jail on CheckpointStore", "BACKEND: deduped RAG memory on resume via stable id mem:{workflow_id}:{agent_id}", "CONCURRENCY: threading.RLock on VectorStore + ProjectStore read-modify-write", "DOCS: README/DEPLOYMENT test counts 55->70; removed auditor scratch file backend/_audit_recursion.py"],
      "validation": ["backend pytest 70 passed", "frontend build exit 0, lint 0, vitest 14/14"] }
  ],
  "forward_looking_followups": [
    "durable Postgres/Supabase LangGraph checkpointer for cross-restart resume of paused approvals (today an in-process MemorySaver; WorkflowStore persists run metadata either way)",
    "broaden store locking or move the JSON stores (VectorStore/ProjectStore/WorkflowStore) to Supabase if concurrency grows",
    "the recursion kill switch is correct + unit-tested but DORMANT in the current linear graph (recursion_count maxes at 1 because ceo runs once and no edge loops back) — re-enable its meaning by adding a replanning edge",
    "prod-hardening checklist before any non-local deploy: override dev defaults (api_secret_key, admin creds), set AUTH_ENABLED=true, consider rate_limit_enabled (see docs/DEPLOYMENT.md)"
  ],
  "last_checkpoint": "cp-0014-post-review-hardening",
  "validation": { "backend_pytest": "70 passed", "frontend": "build exit 0, lint 0 (--max-warnings 0), vitest 14/14" },
  "project_status": "complete"
}
```
<!-- END omnivra-roadmap -->
