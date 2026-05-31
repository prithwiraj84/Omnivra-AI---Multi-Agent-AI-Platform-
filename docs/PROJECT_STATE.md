# PROJECT STATE — Omnivra AI Company OS

> **Authoritative, resumable project state.** This file is both human-readable (tables) and
> machine-readable (the fenced `omnivra-state` JSON block below). The orchestrator and (from
> Phase 2) the in-product Recovery Agent read the JSON block to resume from the last checkpoint.
> Always update the JSON block and `meta.updated_at` whenever state changes; the prose tables are a
> rendered mirror.
>
> **Runtime mirror:** the live, volatile copy is `workspace/.state/project_state.json` (git-ignored),
> inspected via `scripts/state.ps1`. This durable doc is the source of truth on resume; if the
> volatile workspace is wiped, rehydrate from here.
>
> **Update protocol:** writers acquire the state lock (`workspace/.state/state.lock`), mutate the
> runtime mirror `workspace/.state/project_state.json`, then flush the canonical copy here.
> `meta.revision` is a monotonically increasing integer; bump it on every write.

---

## Snapshot

| Field | Value |
|---|---|
| Project | Omnivra AI Company OS |
| Version | v2.0 (`2.0.0`) |
| Current Phase | **10 — Polish + auth + deploy + hardening (FINAL)** — `COMPLETE` |
| Build Status | **PROJECT COMPLETE** — all 10 phases done, **plus** a post-1.0 build-out (cp-0011..cp-0013), a review-hardening pass (cp-0014), per-project workspace isolation (cp-0015), a full social content pipeline (cp-0016..cp-0020), and a second full-system review + concurrency hardening (cp-0021) |
| Next Phase | **none — project complete** (forward-looking, non-blocking followups in `docs/ROADMAP.md`) |
| Last Checkpoint | `cp-0021-fullsystem-review-hardening` |
| Recursion Count | 0 / 3 (kill-switch threshold) |
| Updated At | 2026-05-31T00:00:00Z |
| Revision | 14 |

## Stack (as built)

| Layer | Technology |
|---|---|
| Frontend | Vite + React 18 + TypeScript 5, TailwindCSS 3.4 (+ shadcn/ui), framer-motion, React Flow (`reactflow`), Recharts, Lucide. `npm` only — no JS monorepo tool. |
| Backend | Python 3.11+, FastAPI, Uvicorn, LangGraph, Pydantic v2, Tenacity, Loguru. Python **venv** only. |
| Database | Supabase Cloud — PostgreSQL + `pgvector`. SQL lives flat under `supabase/{schema,rls,seed}.sql`. |
| Realtime / Queue | WebSockets (FastAPI) + Supabase Realtime; Redis / Upstash (later phases). |
| Runtime | **No Docker.** Windows + PowerShell helper scripts under `scripts/`. |

## Workspace Rule

AI agents may write artifacts **only** under `./workspace` (`workspace/{frontend,backend,docs,presentations,reports}`).
They must never modify project source (`frontend/`, `backend/`, `supabase/`, `docs/`, root configs) directly.
The boundary is enforced by the path-jailed `backend/app/workspace_fs/file_manager.py` and reviewed at the
Human Approval Gate before promotion. The volatile runtime state lives under `workspace/.state/`.

## Phase 1 Validation (foundation)

| Check | Result |
|---|---|
| Backend imports (`python -c "import app.main"`) | OK — 23 agents registered in `app/agents/registry.py`. |
| Backend tests (`pytest`) | **15 passed, 0 failed.** |
| Frontend build (`npm run build` = `tsc && vite build`) | **Passes** — design-token CSS compiled. |
| Known non-fatal warnings | FastAPI deprecation of `ORJSONResponse` as `default_response_class`; Starlette TestClient httpx warning (ignored). |

## Phase 2 Validation (design system + UI primitives + layout shell)

| Check | Result |
|---|---|
| Frontend build (`npm run build` = `tsc` strict + `vite build`) | **Exit 0** — 2580 modules transformed. |
| Frontend tests (`npm run test` = vitest, jsdom) | **3 / 3 passed** — full app shell mounts without crashing (render smoke). |
| Source surface | **42 files** under `frontend/src/`: foundation (types/config/store/styles), UI primitives, Recharts chart wrappers, layout shell, pages, test harness. |
| Render verification | `AppLayout` + Sidebar/Topbar/RightRail render with `omnivra-*` tokens; Dashboard showcase + 2 live demos (AI Agents Status tile grid, Task Distribution donut) mount. |

## Phase 3 Validation (dashboard sections + mock data)

| Check | Result |
|---|---|
| Frontend lint (`npm run lint` = `eslint --max-warnings 0`) | **Exit 0** — clean, zero warnings. |
| Frontend build (`npm run build` = `tsc` strict + `vite build`) | **Exit 0** — 2609 modules transformed. |
| Frontend tests (`npm run test` = vitest, jsdom) | **4 / 4 passed** — render smoke asserts all 8 dashboard sections render on mock data + stat values + a workflow name. |
| Render verification | All 8 sections render bound to `src/data/dashboard.ts` mock fixtures: AI Agents Status, Active Workflows, Task Execution Overview, Task Distribution, Live Activity Feed, Pending Approvals, System Health, Recent Achievements. |
| Source surface | 22 `components/dashboard/*` section components + `data/dashboard.ts` + extended `types/index.ts`; `Dashboard.tsx` + `right-rail.tsx` rewritten to assemble props-driven sections. |

## Phase 4 Validation (backend data layer + REST API + Supabase wiring)

| Check | Result |
|---|---|
| Backend tests (`pytest`) | **25 passed, 0 failed** — 15 prior + 10 new `tests/test_api.py` API tests. |
| Live server (uvicorn + curl) | **Verified end-to-end.** `GET /health` (23 agents); `GET /api/dashboard` returns all 17 camelCase keys (`agents=18`, `systemOps=5`, `totalTasks=124`, `totalPendingApprovals=7`); `GET /api/agents` (23); `/api/agents/ceo-manager` (`google_ai`/`gemini-2.5-flash`); `/api/agents/nope` → 404; `POST /api/approvals/{id}/decision` stub → status `"received"`; `/api/workflows` (5); `/api/activity` (6); `/api/system/health` (6). |
| Frontend (unchanged-green) | `npm run build` **exit 0**; `npm run lint` **0 warnings**; `npm run test` (vitest) **4 / 4 passed**. |
| Architecture | frontend → `/api` (Vite proxy) → FastAPI → repository → seed data (Supabase optional). Dashboard is now LIVE-data-driven via `useDashboard()` with the bundled mock as instant fallback/`initialData`. |

### Phase 4 operational notes (caveats)
1. **Supabase SDK not installed in the venv.** `supabase` is listed in `backend/requirements.txt` but is **not** installed in `backend/.venv` (the Phase-1 install was a core subset). The app runs fine on the `SeedRepository` with zero external deps. To activate the Supabase path:
   `backend/.venv/Scripts/python.exe -m pip install supabase==2.30.1`, set `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`, then run `supabase/{schema,rls,seed}.sql` in the Supabase project.
2. **`SupabaseRepository` is fail-safe.** It assumes tables `agents`/`departments`/`providers`/`models` with the relationships in `supabase/schema.sql` (maps DB enum `google_ai_studio` → `google_ai`, composes the seed). On any query error it logs and falls back to the seed — it never 500s.

## Phase 5 Validation (agent/provider integration + LangGraph orchestration + kill switch + tenacity)

| Check | Result |
|---|---|
| Backend tests (`pytest`) | **32 passed, 0 failed** — 25 prior + 7 new `tests/test_orchestration.py` orchestration tests. |
| Live server (uvicorn + curl) | **Verified end-to-end.** `POST /api/workflows/run` "Design the UI and build the REST API" → `status=completed`, **6 `agentOutputs`**, `recursionCount=1`, `plan=[solution-architect, uiux-designer, frontend-engineer, api-engineer, backend-engineer]`; "Publish and deploy…" → `status=awaiting_approval`, `pendingApproval.kind=final_code`. |
| Orchestration + kill switch | Direct orchestration confirmed; kill switch trips at the guard (`recursion_count > settings.max_recursion` = 3 → STOPPED). |
| LangGraph topology | `START → ceo → guard(check_kill_switch) → {stop: END, go: delegate} → approval → {wait: END, go: finalize} → END`. |
| Frontend (unchanged-green) | Untouched in Phase 5; remains green from Phase 4 (`npm run build` exit 0, `npm run lint` 0 warnings, vitest 4/4). |

### Phase 5 operational notes
1. **Provider keys (real vs. stub mode).** Providers call real LLMs (tenacity retry on 429/timeout/5xx) **when keys are set**; otherwise they return a deterministic offline STUB so the graph runs and tests pass fully offline. To run REAL agents, set `GOOGLE_AI_STUDIO_API_KEY` / `OPENROUTER_API_KEY` / `GROQ_API_KEY` / `HUGGINGFACE_API_KEY` in `backend/.env` (else stub mode).
2. **LangGraph now installed.** `langgraph 1.2.2` + `langchain-core 1.4.0` were installed into `backend/.venv` (previously absent). Providers were rewritten to plain `httpx` + offline STUB mode (no vendor SDKs).
3. **Approval gate (partial).** Tasks mentioning publish/deploy/export/release/presentation/final → `AWAITING_APPROVAL` + `pending_approval`; the resume wiring lands in Phase 7.

## Phase 6 Validation (realtime — WebSockets + live activity/health streaming)

| Check | Result |
|---|---|
| Backend tests (`pytest`) | **35 passed, 0 failed** — 32 prior + 3 new `tests/test_realtime.py` realtime tests. |
| Live WebSocket (real socket, port 8012) | **Verified end-to-end.** Client received `hello` → `system_health` (6 metrics, pushed immediately on connect) → then after `POST /api/workflows/run` (200, `status=completed`) the `workflow` + `activity` events broadcast live over the socket. |
| Realtime fanout | `ConnectionManager` (`app/services/realtime.py`, module-level `manager`) broadcasts `emit(type, payload)`; the heartbeat task pushes system-health every ~4s (jittered) + simulated activity periodically; real `workflow`/`activity`/`approval` events emit during runs. |
| Frontend (live + green) | `npm run lint` **exit 0**; `npm run build` **exit 0**; `npm run test` (vitest) **5 / 5 passed** (smoke now asserts the live indicator renders). `useWebSocket` folds events into the React Query `['dashboard']` cache (replace `systemHealth` on `system_health`, prepend on `activity` capped at 12), so System Health + Live Activity Feed re-render live; `LiveIndicator` shows emerald `Live` / amber `Connecting` / `Offline`. |
| Architecture | Server `/ws` (manager-backed) → broadcasts → frontend `useWebSocket()` (via Vite `/ws` proxy → `ws://localhost:8000`) → React Query `['dashboard']` cache that `useDashboard()` already reads. |

## Phase 7 Validation (human approval gate resume + recovery)

| Check | Result |
|---|---|
| Backend tests (`pytest`) | **41 passed, 0 failed** — 35 prior + 6 new `tests/test_approval_resume.py` resume tests; `tests/test_api.py` edited (decision-on-seed-approval now asserts 404). |
| End-to-end via API (TestClient + live) | **Verified.** `POST /api/workflows/run` on a gated task → `status='awaiting_approval'` + `pendingApproval{approvalId,...}`; `POST /api/approvals/{approvalId}/decision` → approve/retry → `'completed'` (`result.ok`), reject → `'failed'`, rollback → `'rolled_back'`; unknown `approvalId` → 404; `GET /api/workflows/runs[?status]` lists persisted runs. |
| Mechanism | Graph compiled **with** a LangGraph `MemorySaver` checkpointer; the approval node calls LangGraph `interrupt()` to suspend mid-run; `orchestrator.run_workflow` detects the interrupt (`state['__interrupt__']`) and returns `awaiting_approval` + the pending payload; `orchestrator.resume_workflow` re-enters via `Command(resume={action,note})`. `WorkflowStore` persists each run (`RunResult` JSON) under `workspace/.state/workflows/`. |
| Frontend (live + green) | `npm run lint` **exit 0**; `npm run build` **exit 0**; `npm run test` (vitest) **6 / 6 passed** (smoke now asserts `RunTask` renders). `RunTask` control runs a task; `PendingApprovals` shows LIVE awaiting runs above seed items (doubles as the Recovery view) wired to the decision mutation; `ApprovalCard` exposes Approve/Reject/Retry/Rollback actions. |

### Phase 7 operational notes
1. **Resume is SAME-PROCESS.** LangGraph `MemorySaver` is in-memory, so approve/reject/retry/rollback resumes only within the same running backend process. Durable cross-restart resume needs a Postgres checkpointer (Supabase); the `WorkflowStore` persists run metadata (under `workspace/.state/workflows/`) either way, so runs/recovery listings survive a restart even though the in-flight graph state does not.
2. **Benign LangGraph msgpack note.** A benign msgpack note appears when deserializing the str-enum `WorkflowStatus`; the status comparisons still hold.

## Phase 8 Validation (Marketing/Docs/Presentation/Media agents + workspace artifacts)

| Check | Result |
|---|---|
| Backend tests (`pytest`) | **45 passed, 0 failed** — 41 prior + 4 new (`tests/test_workspace_artifacts.py` workspace artifacts + `tests/test_media.py` media stubs). |
| Live (artifacts written + served) | **Verified.** Running a workflow writes each agent output **plus** a run report into `./workspace` via the path-jailed `FileManager`; `GET /api/workspace/artifacts` lists them; `GET /api/workspace/artifacts/{path}` reads (400 on sandbox escape, 404 missing). |
| Media (stub endpoints) | `POST /api/media/image` / `/tts` / `/stt` live and **stub-safe** (no keys) — `MediaService.generate_image` calls HuggingFace FLUX.1-dev when configured else returns a stub placeholder; transcribe/synthesize are stub-safe. |
| Mechanism | `ArtifactService` (`app/services/artifacts.py`) files each agent output under workspace SUBDIRS by agent (`docs/frontend/backend/presentations/reports`) + writes `reports/<wf>/run.md`; `orchestrator.run_workflow` + `resume_workflow` call `persist_run` so `RunResult.agentOutputs[].artifacts` carry workspace-relative paths. Honors the Workspace Rule (agents only write under `./workspace`). |
| Frontend (live + green) | `npm run lint` **exit 0**; `npm run build` **exit 0**; `npm run test` (vitest) **7 / 7 passed** (smoke now asserts `/workspace` renders). Two-pane `artifact-explorer` (list + viewer) wired via `useArtifacts`; `/workspace` → `Workspace`, `/documents` → `Documents` (both removed from the Placeholder). |

### Phase 8 operational notes
1. **Media runs STUB-safe (no keys).** Set `HUGGINGFACE_API_KEY` for real FLUX.1-dev image generation; Groq Whisper STT / Orpheus TTS are stubbed pending key + audio wiring. Artifacts are written under `workspace/{docs,frontend,backend,presentations,reports}`.

## Phase 9 Validation (knowledge base + memory (pgvector) + RAG)

| Check | Result |
|---|---|
| Backend tests (`pytest`) | **55 passed, 0 failed** — 45 prior + 10 new (`tests/test_vectorstore.py` + `tests/test_knowledge.py` + `tests/test_memory_rag.py`: vector store + knowledge + memory/RAG). |
| Live (KB search + RAG + ingest + recall) | **Verified.** KB search retrieves relevant docs; a workflow run stores each agent output as memory; `ingest-workspace` indexes artifacts; memory recall returns prior-run content (the company learns from prior work). |
| Mechanism | `app/services/vectorstore.py` = a deterministic 256-dim hashing embedder (offline, no key) + cosine `VectorStore` persisted to `workspace/.state/vectors/<name>.json`. `KnowledgeService` (knowledge corpus + `ingest_workspace`) and `MemoryService` (agent memory). RAG: `app/graph/nodes/delegate.py` recalls memory into each agent's context (`recall_context`); `app/services/orchestrator.py` (`_persist_artifacts_and_memory`) stores every successful output as memory after run/resume. |
| API | `app/api/routes/knowledge.py` (search/add/ingest-workspace/stats) + `app/api/routes/memory.py` (search/recent/stats) mounted in `app/api/router.py` (`/knowledge`, `/memory`). |
| Frontend (live + green) | `npm run lint` **exit 0**; `npm run build` **exit 0**; `npm run test` (vitest) **9 / 9 passed** (smoke now asserts `/knowledge` + `/memory` render). `src/pages/KnowledgeBase.tsx` + `src/pages/Memory.tsx` wired via `useKnowledge`/`useMemory` hooks + `src/lib/api/knowledge.ts`; `src/App.tsx` routes `/knowledge` → `KnowledgeBase`, `/memory` → `Memory`. |

### Phase 9 operational notes
1. **Local offline embedder by default.** Embeddings are a local offline hashing embedder (256-d) by default — no key required; stores persist under `workspace/.state/vectors/`. The Supabase pgvector path (1536-d, `match_knowledge`/`match_memory`) is the optional durable backend and needs a real embedding model + Supabase; the local store is the zero-config default.

## Phase 10 Validation (polish + auth + deploy + hardening — FINAL)

| Check | Result |
|---|---|
| Backend tests (`pytest`) | **62 passed, 0 failed** — 55 prior + 7 new (`tests/test_auth.py` + `tests/test_security.py`: signed-token auth + `require_user` gating + hardening middleware). |
| Frontend build (`npm run build` = `tsc` strict + `vite build`) | **Exit 0.** |
| Frontend lint (`npm run lint` = `eslint --max-warnings 0`) | **Exit 0** — clean, zero warnings. |
| Frontend tests (`npm run test` = vitest, jsdom) | **12 / 12 passed.** |
| Auth + hardening | `app/core/security.py` (stdlib HMAC signed tokens: `create_token`/`verify_token`/`verify_credentials`); `app/api/deps.py` `require_user` (open in dev, Bearer-enforced when `AUTH_ENABLED`); `app/api/routes/auth.py` (`/api/auth/config|login|me`); sensitive POSTs (`workflows/run`, approvals `decision`, knowledge `add`+`ingest`) depend on `require_user`; `app/main.py` `hardening_middleware` (security headers always; opt-in per-IP rate limit). Frontend auth gate (`store/auth.ts`, `lib/api/auth.ts`, `hooks/useAuth.ts`, `pages/Login.tsx`, `components/auth/auth-gate.tsx`, `components/common/error-boundary.tsx`, `pages/Settings.tsx`) + axios bearer interceptor; deploy docs (`docs/DEPLOYMENT.md` new + `README.md` rewritten). |
| Polish/fixes (a–d) | See operational notes below — dashboard layout fix, dev proxy noise suppression, websockets dependency fix, animation foundation across ~24 components. |
| Runs OFFLINE | The whole product runs OFFLINE in stub mode (no keys/Supabase needed); real providers/Supabase/auth activate via `backend/.env`. |

### Phase 10 operational notes
1. **Auth + hardening (opt-in).** New settings: `auth_enabled` (false), `admin_username`/`admin_password`, `token_ttl_seconds`, `security_headers_enabled` (true), `rate_limit_enabled` (false), `rate_limit_per_minute`. `require_user` is open in dev and Bearer-enforced once `AUTH_ENABLED`; tokens are stdlib HMAC signed (no external dep). Security headers are sent always; per-IP rate limiting is opt-in.
2. **(a) BUG FIX — dashboard not visible in a real browser.** `src/components/layout/sidebar.tsx` was `position:fixed` but `AppLayout` lays it out as a CSS grid column, so the main content was placed/hidden behind the fixed sidebar. Fixed: the sidebar is now an in-flow sticky grid item (`md:flex`, fills its 248px/72px track). jsdom tests didn't catch it since `getByText` ignores CSS.
3. **(b) DEV NOISE.** `vite.config.ts` now swallows `/api` + `/ws` proxy `ECONNREFUSED`/`ECONNABORTED` logs that appeared when the backend dev server isn't running (the SPA degrades to fallback data).
4. **(c) DEPENDENCY FIX.** `backend/requirements.txt` pinned `websockets==16.0`, which conflicts with `supabase 2.30.1` (realtime needs `websockets<16`); changed to `websockets>=12,<16` (resolves to 15.0.1; full-tree dry-run resolves cleanly).
5. **(d) ANIMATION POLISH.** New motion foundation `src/lib/motion.ts` + `src/components/common/reveal.tsx` (`Reveal`/`Stagger`/`StaggerItem`) + `src/components/common/count-up.tsx` (all reduced-motion aware), applied across ~24 components (Dashboard section cascade, ExecutiveOverview/StatCard count-up + stagger, AgentStatusGrid/AgentCard stagger + hover, WorkflowList, chart reveals, usage/media/achievements stagger+hover, AppLayout route-change motion, RightRail + ActivityFeed stagger, BrandFooterCard float, Sidebar nav micro-motion via `MotionNavLink`, Login entrance).

## Phase Status

| Phase | Name | Status | Exit Criteria (summary) |
|---|---|---|---|
| 1 | Foundation | `complete` | Monorepo + FE shell + BE shell + Supabase SQL + state/checkpoint docs; builds + tests pass |
| 2 | Design system + UI primitives + layout shell | `complete` | Tokens, shadcn/common/chart primitives, Sidebar/Topbar/RightRail shell |
| 3 | Dashboard sections (mock data) | `complete` | All reference dashboard sections render on mock data |
| 4 | Backend data layer + REST API + Supabase wiring | `complete` | Repositories + REST routes live; dashboard reads `/api/dashboard` (Supabase optional) |
| 5 | Agent/provider integration + LangGraph + kill switch + tenacity | `complete` | CEO delegates via LangGraph; providers wrapped (tenacity + stub fallback); kill switch active; run endpoint + approval gate |
| 6 | Realtime WebSockets + live activity/health | `complete` | WS fanout drives live activity/progress/health |
| 7 | Human approval gate + recovery/checkpoint resume | `complete` | Approve/Reject/Retry/Rollback resume/reject/roll-back the run; runs persisted + recovery listing |
| 8 | Marketing/Docs/Presentation/Media agents + workspace artifacts | `complete` | Agents write artifacts into `./workspace` via the jailed FileManager; workspace list/read API; media stub-safe services + endpoints; Workspace/Documents explorer UI |
| 9 | Knowledge base + memory (pgvector) + RAG | `complete` | Vector store + offline embedder; KB search + ingest; agent memory + RAG injection; KB/Memory UI; pytest 55; frontend green (pgvector optional) |
| 10 | Polish + auth + deploy + hardening (FINAL) | `complete` | Opt-in HMAC auth gate + `require_user` on sensitive POSTs; hardening middleware (security headers + opt-in rate limit); deploy docs (DEPLOYMENT.md + README rewrite); dashboard layout fix + dev proxy noise fix + websockets dep fix; animation polish across ~24 components; pytest 62; frontend build/lint/test 12/12 |

## Post-1.0 Build-out + Review Hardening + Social Pipeline (cp-0011 .. cp-0021)

After the 10-phase 1.0 shipped (`cp-0010-phase10-polish`), eleven additive, approval-free post-1.0
checkpoints brought the product to full feature/component parity, applied two lead-engineer reviews,
partitioned the workspace per project, and built the full social content pipeline (compose → render →
human-approve → publish, with a real YouTube uploader). These did **not** add a phase 11+ to the 10-phase
plan — phases 1–10 remain the project's spine; the post-1.0 work is tracked as checkpoints
`cp-0011..cp-0021` (see `docs/CHECKPOINTS.md` for the full records and `docs/ROADMAP.md` for the Post-1.0
section).

| Checkpoint | Title | Summary |
|---|---|---|
| `cp-0011-pages-hierarchy` | Remaining nav pages + Agent Hierarchy Tree | Built every remaining navigable page so the whole sidebar is real: Agents (roster + Grid/Hierarchy toggle), **AgentHierarchyTree** (CEO → department → agent org chart via React Flow), Workflows (RunTask + active runs + run-history drill-down), Approvals (full-page live gate), Departments ×7 (slug-driven roster), Logs, Integrations, Billing. Backend added `GET /api/system/providers` + `GET /api/system/info`. |
| `cp-0012-projects-tasks` | Projects & Tasks (full-stack) + deferred hardening | Projects + Tasks full-stack: `ProjectStore` (JSON-persisted, seeded) + `app/schemas/projects.py` + CRUD routes `projects.py`/`tasks.py`; frontend `Projects.tsx` (board + create/delete) + `Tasks.tsx` (4-column Kanban). `App.tsx` wired both and removed the `Placeholder` import — **no Placeholder routes remain**. Also wired `provider_max_retries` into `with_provider_retry` and added a `seed.sql`↔agent-registry drift-guard test. |
| `cp-0013-center-panels` | Design-doc "center" detail panels | Built `DESIGN_SYSTEM.md` §8.3 "center" panels: `SecurityCenter`/`MarketingCenter`/`DocumentationCenter` (back `/departments/quality`, `/marketing`, `/documentation`), `RecoveryStatus` (Workflows page), `MemoryUsagePanel` (Memory page) + `GET /api/system/checkpoints`. With `AgentHierarchyTree` this realizes the **entire** design-system component inventory. |
| `cp-0014-post-review-hardening` | Applied full-system lead-engineer review (verdict SHIP) | No critical/high code defects; applied actionable findings: fixed a **HIGH path-traversal** on `GET /api/workflows/runs/{workflow_id}` (`WorkflowStore._path` now rejects `/`, `\`, NUL, `..`); applied the same jail to `CheckpointStore` (defense-in-depth); deduped RAG memory on resume via a stable id (`mem:{workflow_id}:{agent_id}`); added `threading.RLock` to `VectorStore` + `ProjectStore` read-modify-write; corrected README/DEPLOYMENT test counts 55→70; removed an auditor scratch file (`backend/_audit_recursion.py`). |
| `cp-0015-per-project-workspaces` | Per-project workspace partition + cascade hard-delete + project switcher | Partitioned the workspace per project: each project owns an isolated `workspace/projects/<project_id>/` subtree (artifacts `docs/frontend/backend/presentations/reports` + RAG memory/knowledge `.state/vectors` + workflow runs `.state/workflows` + `.checkpoints`); GLOBAL bits stay shared (the project catalog `.state/projects.json`+`tasks.json` and the build-checkpoint lineage `.state/checkpoints`). New `app/workspace_fs/paths.py` (layout, path-jailed `safe_project_id`, `purge_project_workspace`, `reset_caches`, one-time `migrate_flat_workspace`). Store singletons became `@lru_cache` project-keyed factories; the orchestrator threads the project through run + resume (`RunResult.projectId`). Routes scope via an `X-Project-Id` header resolved by `get_project_id` (`app/api/deps.py`) which path-jails AND 404s unknown/deleted projects; `/workflows/run` uses the header only (the body `projectId` override was removed). A seeded, never-deletable **Default Workspace** (`__default__`); deleting any other project HARD-DELETES its whole subtree (UI confirm). One-time startup migration moves the legacy flat layout into `projects/__default__/` (idempotent via `.state/.migrated_v2_projects`; verified end-to-end). Frontend: active-project zustand store (persisted) + axios `X-Project-Id` interceptor + project-scoped React Query keys + topbar `ProjectSwitcher` (switch / inline create / two-step delete-confirm); Tasks board scoped to the active project. Two adversarial review rounds (7-dimension fan-out then a focused fix-verification): 17 round-1 findings, actionable ones fixed, multi-tenant authorization findings consciously declined (single-admin offline OS); round 2 `allClosed=true`. `.gitignore` extended to `workspace/projects/` + `.state/.migrated_v2_projects`. |
| `cp-0016-social-pipeline-foundation` | Social content pipeline — backend foundation (offline/stub-first) | Phase 1 of the social pipeline: the generate → human-approve → publish FLOW for **reels** and **posts**, fully offline/stub-first. New `app/schemas/social.py` (`ReelScene`/`ReelStoryboard`, `SocialDraft`, `PublishResult`, request + decision DTOs); a per-project `SocialDraftStore` (`app/services/social_store.py`, `.state/social/`, path-jailed ids, added to `reset_caches`); `SocialService` (`app/services/social.py`: `draft_reel` storyboard + stub voiceover + `storyboard.json`/`reel.md`; `draft_post` caption+hashtags + stub-safe FLUX image; `decide(approve|reject)`); stub publishers (`app/services/publishers.py`: youtube/instagram for reels, facebook/linkedin/twitter for posts; `is_configured` from new optional config keys); `/api/social` routes (reel, post, drafts list/get, decision), project-scoped via `X-Project-Id`. Reels default to YouTube+Instagram, posts to Facebook+LinkedIn+Twitter. Real render + uploads deferred to cp-0018/cp-0020. |
| `cp-0017-social-studio-frontend` | Social Studio frontend (compose → draft → preview → approve/reject) | New `/social` **Social Studio** page (`pages/Social.tsx`): a composer (brief + reel|post toggle + selectable target-platform chips) generates draft cards previewing the storyboard (reels) or caption+hashtags (posts), with Approve & publish / Reject + per-platform publish results. New `lib/api/social.ts` (`draftReel`/`draftPost`/`listDrafts`/`decideDraft`), `hooks/useSocial.ts` (`useSocialDrafts` polled + `useDraftReel`/`useDraftPost`/`useDecideDraft`, project-scoped keys), social wire types in `lib/api/types.ts`, a sidebar nav entry (Clapperboard, violet) + the `/social` route + a smoke test. Project-scoped + offline-safe. Adversarial 5-lens review → 2 a11y fixes (empty-targets guard, content-derived scene keys). |
| `cp-0018-reel-render-engine` | Real reel render engine (MoviePy + Pexels + Orpheus, async, stub-safe) | Real vertical `.mp4` with a 3-level degradation ladder: stub → offline `ColorClip` + Pillow caption-PNG overlay `.mp4` (**no ImageMagick**) → + Pexels b-roll + Orpheus voiceover. New `app/services/reel_render.py` (import-guarded, pure/sync, closes every clip before unlinking temp PNGs for Windows file-handle safety) + `app/services/pexels.py` + `MediaService.generate_voiceover` + `HuggingFaceProvider.generate_audio`. Async render: `POST /api/social/drafts/{id}/render` `BackgroundTask` runs `render_reel` via `asyncio.to_thread`, `render_status` rendering → rendered/failed with `/ws` progress; `SocialDraft` gained `render_status`/`video_path`/`render_note`. OPTIONAL `backend/requirements-render.txt` (core install stays lean). Adversarial 5-lens review → 1 critical (always-terminal emit) + 3 high (Windows clip/handle cleanup) + a test gap fixed; real `.mp4` verified end-to-end then the engine uninstalled so the committed suite runs stub. |
| `cp-0019-render-ux` | Frontend render UX + binary media endpoint | Reel cards get a **Render** button → live render-status → an inline `<video>` player for the `.mp4`; post cards show the FLUX image inline. New backend `GET /api/workspace/media/{path:path}` streams a binary artifact (`FileResponse`) via a new path-jailed `FileManager.media_file` (violation→400, missing→404), project-scoped via `?projectId=` because native `<video>`/`<img>` can't send `X-Project-Id`. `SocialDraft` gained `renderStatus`/`videoPath`/`renderNote`; new `renderDraft()` + `mediaUrl(path, projectId)` + `useRenderDraft`. Adversarial 4-lens review (all passed) → a11y fixes (video aria-label, status aria-live, unexpected-status fallback) + media path-traversal route tests; declined GlassCard-nesting (inner-panel idiom matches `TaskCard`). |
| `cp-0020-youtube-uploader` | Real platform uploader #1 — YouTube (OAuth resumable upload) | First **REAL** platform uploader. `app/services/youtube.py` exchanges an OAuth2 refresh token for an access token, then does a YouTube Data API v3 **resumable** `.mp4` upload (`privacyStatus=private`), fully guarded + stub-safe + never-raises (no creds → stub `ok=true`; no rendered video / missing / >1GB → `ok=false`; failures → `ok=false` + sanitized note). `publishers.publish_to(platform, draft)` dispatch (youtube → real, the other four → stubs); `social.decide` passes the full draft. YouTube OAuth config trio replacing the unused `youtube_api_key`; new `docs/SOCIAL_PUBLISHING.md`. Real path static-reviewed (no Google creds to run live); tests run in stub mode. Adversarial 4-lens review → 2 critical (concrete `video/mp4` MIME, sanitized error note) + high (Content-Length) + lows (1GB size guard, defensive id parse) fixed. |
| `cp-0021-fullsystem-review-hardening` | Full-system review (cp-0015..cp-0020) + concurrency hardening | 6-domain full-system review since cp-0014 (the per-project partition + the whole social pipeline). PASSED: security, frontend, cross-cutting integration + per-project isolation, regression. Backend-correctness FAILED on concurrency; fixed: (HIGH) `threading.RLock` on `WorkflowStore` + `SocialDraftStore` guarding all JSON read/write (both missed when cp-0014 locked `ProjectStore` + `VectorStore`) — closes TOCTOU/corruption under the FastAPI threadpool; (HIGH/MED) `begin_render` + the `/render` route only render a draft still `status='awaiting_approval'` (closes the render-vs-decide race); (MED test gap) a social cascade-delete test. Render failure-injection + concurrent-render stress noted as followups. **Verdict: SHIP.** |

## Current Validation (as of cp-0021)

| Check | Result |
|---|---|
| Backend tests (`pytest`) | **112 passed, 1 skipped** — the skipped test is a guarded real-render test that runs only when the optional render engine (`backend/requirements-render.txt`) is installed. Counts grew 95 → 112 across cp-0016..cp-0021 (`tests/test_social.py` draft/decide/publish/render/youtube/cascade-delete + media-traversal tests in `tests/test_workspace_artifacts.py`). |
| Frontend build (`npm run build` = `tsc` strict + `vite build`) | **Exit 0.** |
| Frontend lint (`npm run lint` = `eslint --max-warnings 0`) | **Exit 0** — clean, zero warnings. |
| Frontend tests (`npm run test` = vitest, jsdom) | **17 / 17 passed** (16 prior + the `/social` Social Studio render smoke). |
| Runs OFFLINE | The whole product runs OFFLINE in stub mode (no keys/Supabase needed): providers stub without keys; `SeedRepository` without Supabase; local hashing embedder; in-process `MemorySaver` checkpointer; the social pipeline drafts/renders/publishes stub-safe (reel render degrades to a stub when the optional engine is absent; publishers stub without keys). Real providers/Supabase/auth + the render engine + the YouTube uploader activate via `backend/.env`. |
| Go-live | Set provider keys + Supabase + `AUTH_ENABLED` in `backend/.env` (plus the YouTube OAuth trio + `pip install -r backend/requirements-render.txt` for real reels/uploads); run `supabase/{schema,rls,seed}.sql`; deploy per `docs/DEPLOYMENT.md`. |

## Workflow Registry (live runs)

| Workflow ID | Type | Status | Current Node | Checkpoint |
|---|---|---|---|---|
| `bootstrap` | system | `complete` | `post1.fullsystem_review_hardening` | `cp-0021-fullsystem-review-hardening` |

---

## Machine State

<!-- BEGIN omnivra-state — do not edit outside the orchestrator/Recovery Agent -->
```json omnivra-state
{
  "schema_version": "1.0.0",
  "meta": {
    "project": "omnivra-ai-company-os",
    "version": "2.0.0",
    "revision": 14,
    "updated_at": "2026-05-31T00:00:00Z",
    "updated_by": "ceo-manager"
  },
  "current_phase": 10,
  "current_phase_name": "Polish + auth + deploy + hardening (FINAL)",
  "build_status": "complete",
  "project_status": "complete",
  "next_phase": null,
  "next_phase_name": "none — project complete",
  "phases": [
    { "id": 1, "name": "Foundation", "status": "complete" },
    { "id": 2, "name": "Design system + UI primitives + layout shell", "status": "complete" },
    { "id": 3, "name": "Dashboard sections (mock data)", "status": "complete" },
    { "id": 4, "name": "Backend data layer + REST API + Supabase wiring", "status": "complete" },
    { "id": 5, "name": "Agent/provider integration + LangGraph + kill switch + tenacity", "status": "complete" },
    { "id": 6, "name": "Realtime WebSockets + live activity/health", "status": "complete" },
    { "id": 7, "name": "Human approval gate + recovery/checkpoint resume", "status": "complete" },
    { "id": 8, "name": "Marketing/Docs/Presentation/Media agents + workspace artifacts", "status": "complete" },
    { "id": 9, "name": "Knowledge base + memory (pgvector) + RAG", "status": "complete" },
    { "id": 10, "name": "Polish + auth + deploy + hardening", "status": "complete" }
  ],
  "post_1_0_checkpoints": [
    { "id": "cp-0011-pages-hierarchy", "title": "Remaining nav pages + Agent Hierarchy Tree", "summary": "All remaining nav pages built (Agents + Agent Hierarchy Tree via React Flow, Workflows, Approvals, Departments x7, Logs, Integrations, Billing) + backend GET /api/system/providers + /api/system/info. No Placeholder routes remain." },
    { "id": "cp-0012-projects-tasks", "title": "Projects & Tasks (full-stack) + deferred hardening", "summary": "Projects + Tasks full-stack (ProjectStore + CRUD API + board + Kanban). Removed the Placeholder import. Wired provider_max_retries; added a seed.sql<->agent-registry drift-guard test." },
    { "id": "cp-0013-center-panels", "title": "Design-doc center detail panels", "summary": "DESIGN_SYSTEM.md 8.3 'center' panels: SecurityCenter/MarketingCenter/DocumentationCenter (back /departments/quality,/marketing,/documentation), RecoveryStatus (Workflows), MemoryUsagePanel (Memory), GET /api/system/checkpoints. With AgentHierarchyTree this realizes the ENTIRE design-system component inventory." },
    { "id": "cp-0014-post-review-hardening", "title": "Applied full-system lead-engineer review (verdict SHIP)", "summary": "No critical/high code defects. Fixed a HIGH path-traversal on GET /api/workflows/runs/{workflow_id} (WorkflowStore._path rejects '/','\\',NUL,'..'); same jail on CheckpointStore (defense-in-depth); deduped RAG memory on resume via stable id (mem:{workflow_id}:{agent_id}); added threading.RLock to VectorStore + ProjectStore; corrected README/DEPLOYMENT test counts 55->70; removed an auditor scratch file." },
    { "id": "cp-0015-per-project-workspaces", "title": "Per-project workspace partition + cascade hard-delete + project switcher", "summary": "Partitioned the workspace per project: each project owns an isolated workspace/projects/<project_id>/ subtree (artifacts + RAG memory/knowledge .state/vectors + workflow runs .state/workflows + .checkpoints); GLOBAL bits stay shared (the project catalog .state/projects.json + tasks.json and the build-checkpoint lineage .state/checkpoints). New app/workspace_fs/paths.py (layout, path-jailed safe_project_id, purge_project_workspace, reset_caches, one-time migrate_flat_workspace). Store singletons became @lru_cache project-keyed factories; the orchestrator threads the project through run + resume (RunResult.projectId). Routes scope via an X-Project-Id header resolved by get_project_id (app/api/deps.py) which path-jails AND 404s unknown/deleted projects; /workflows/run uses the header only (the body projectId override was removed). A seeded, never-deletable Default Workspace (__default__); deleting any other project HARD-DELETES its whole subtree (UI confirm). One-time startup migration moves the legacy flat layout into projects/__default__/ (idempotent via .state/.migrated_v2_projects; verified end-to-end). Frontend: active-project zustand store (persisted) + axios X-Project-Id interceptor + project-scoped React Query keys + topbar ProjectSwitcher (switch / inline create / two-step delete-confirm); Tasks board scoped to the active project. Two adversarial review rounds; round 2 allClosed=true. Validation 95 pytest / 16 vitest." },
    { "id": "cp-0016-social-pipeline-foundation", "title": "Social content pipeline — backend foundation (offline/stub-first)", "summary": "Phase 1 of the social pipeline: the generate -> human-approve -> publish FLOW for reels + posts, fully offline/stub-first. New schemas/social.py (ReelScene/ReelStoryboard, SocialDraft, PublishResult, request + decision DTOs); per-project SocialDraftStore (services/social_store.py, .state/social/, path-jailed ids, added to reset_caches); SocialService (services/social.py: draft_reel storyboard + stub voiceover + storyboard.json/reel.md; draft_post caption+hashtags + stub-safe FLUX image; decide(approve|reject)); stub publishers.py (youtube/instagram for reels; facebook/linkedin/twitter for posts; is_configured from new optional config keys); /api/social routes (reel, post, drafts list/get, decision) project-scoped via X-Project-Id. Reels default YouTube+Instagram, posts Facebook+LinkedIn+Twitter. Real render + uploads deferred to cp-0018/cp-0020. Validation 102 pytest." },
    { "id": "cp-0017-social-studio-frontend", "title": "Social Studio frontend (compose -> draft -> preview -> approve/reject)", "summary": "New /social Social Studio page (pages/Social.tsx): composer (brief + reel|post toggle + selectable target chips) -> draft cards previewing the storyboard (reels) or caption+hashtags (posts) -> Approve & publish / Reject + per-platform publish results. New lib/api/social.ts (draftReel/draftPost/listDrafts/decideDraft), hooks/useSocial.ts (useSocialDrafts polled + useDraftReel/useDraftPost/useDecideDraft, project-scoped keys), social wire types in lib/api/types.ts, sidebar nav entry (Clapperboard, violet) + /social route + smoke test. Project-scoped + offline-safe. Adversarial 5-lens review -> 2 a11y fixes (empty-targets guard, content-derived scene keys). Validation frontend build exit 0 / lint 0 / vitest 17; backend unchanged 102." },
    { "id": "cp-0018-reel-render-engine", "title": "Real reel render engine (MoviePy + Pexels + Orpheus, async, stub-safe)", "summary": "Real vertical .mp4 with a 3-level degradation ladder: stub -> offline ColorClip + Pillow caption-PNG overlay .mp4 (NO ImageMagick) -> + Pexels b-roll + Orpheus voiceover. New services/reel_render.py (import-guarded, pure/sync, closes every clip before unlinking temp PNGs for Windows file-handle safety) + services/pexels.py + MediaService.generate_voiceover + HuggingFaceProvider.generate_audio. Async render: POST /api/social/drafts/{id}/render BackgroundTask runs render_reel via asyncio.to_thread, render_status rendering -> rendered/failed with /ws progress; SocialDraft render_status/video_path/render_note. OPTIONAL backend/requirements-render.txt (core install stays lean). Adversarial 5-lens review -> 1 critical (always-terminal emit) + 3 high (Windows clip/handle cleanup) + a test gap fixed; real .mp4 verified end-to-end then engine uninstalled so the committed suite runs stub. Validation 106 pytest, 1 skipped." },
    { "id": "cp-0019-render-ux", "title": "Frontend render UX + binary media endpoint", "summary": "Reel cards get a Render button -> live render-status -> inline <video> player for the .mp4; post cards show the FLUX image inline. New backend GET /api/workspace/media/{path:path} streams a binary artifact (FileResponse) via a new path-jailed FileManager.media_file (violation->400, missing->404), project-scoped via ?projectId= because native <video>/<img> can't send X-Project-Id. SocialDraft renderStatus/videoPath/renderNote; renderDraft() + mediaUrl(path, projectId) + useRenderDraft. Adversarial 4-lens review (all passed) -> a11y fixes (video aria-label, status aria-live, unexpected-status fallback) + media path-traversal route tests; declined GlassCard-nesting (inner-panel idiom matches TaskCard). Validation backend 110/1skip, frontend lint 0/build/vitest 17." },
    { "id": "cp-0020-youtube-uploader", "title": "Real platform uploader #1 — YouTube (OAuth resumable upload)", "summary": "First REAL platform uploader: YouTube. services/youtube.py exchanges an OAuth2 refresh token for an access token, then does a YouTube Data API v3 resumable .mp4 upload (privacyStatus=private), fully guarded + stub-safe + never-raises (no creds -> stub ok=true; no rendered video / missing / >1GB -> ok=false; failures -> ok=false + sanitized note). publishers.publish_to(platform, draft) dispatch (youtube -> real, the other four -> stubs); social.decide passes the full draft. YouTube OAuth config trio replacing the unused youtube_api_key; new docs/SOCIAL_PUBLISHING.md. Real path static-reviewed (no Google creds to run live); tests run in stub mode. Adversarial 4-lens review -> 2 critical (concrete video/mp4 MIME, sanitized error note) + high (Content-Length) + lows (1GB size guard, defensive id parse) fixed. Validation 111/1skip." },
    { "id": "cp-0021-fullsystem-review-hardening", "title": "Full-system review (cp-0015..cp-0020) + concurrency hardening", "summary": "6-domain full-system review since cp-0014 (per-project partition + the whole social pipeline): security/frontend/integration-isolation/regression PASSED; backend-correctness found 2 HIGH concurrency gaps. Fixed: threading.RLock on WorkflowStore + SocialDraftStore (were missed by cp-0014); begin_render/render route only render awaiting_approval drafts (render-vs-decide race); social cascade-delete test. Render failure-injection + concurrent-render stress noted as followups. Verdict SHIP. Validation 112/1skip, frontend 17." }
  ],
  "active_workflow": {
    "id": "bootstrap",
    "type": "system",
    "status": "complete",
    "current_node": "post1.fullsystem_review_hardening",
    "recursion_count": 0,
    "recursion_limit": 3,
    "started_at": "2026-05-29T00:00:00Z",
    "last_checkpoint_id": "cp-0021-fullsystem-review-hardening"
  },
  "last_checkpoint_id": "cp-0021-fullsystem-review-hardening",
  "runtime_mirror": "workspace/.state/project_state.json",
  "manifest_ref": "docs/FILE_MANIFEST.md",
  "manifest_hash": "sha256:PENDING",
  "validation": {
    "backend_import": "ok",
    "backend_tests": "112 passed, 1 skipped",
    "backend_pytest": 112,
    "post_1_0_note": "Post-1.0 build-out + review-hardening + per-project isolation + social content pipeline (cp-0011..cp-0021) over the 10-phase 1.0. Current validation: backend pytest 112 passed, 1 skipped (the skipped test is a guarded real-render test that runs only when the optional render engine in backend/requirements-render.txt is installed); frontend vite build exit 0, eslint --max-warnings 0 exit 0, vitest 17/17. cp-0016: social pipeline backend foundation (offline/stub-first) — schemas/social.py + per-project SocialDraftStore + SocialService (draft_reel/draft_post -> decide approve|reject) + stub publishers + /api/social routes; reels default YouTube+Instagram, posts Facebook+LinkedIn+Twitter. cp-0017: /social Social Studio frontend (composer -> draft cards -> approve/reject + publish results) + useSocial hooks + lib/api/social + social wire types + nav entry + route. cp-0018: real reel render engine (MoviePy+FFmpeg via imageio-ffmpeg + Pillow caption PNG overlays, no ImageMagick + Pexels b-roll + Orpheus voiceover) with a 3-level degradation ladder; async render via BackgroundTask + asyncio.to_thread + /ws progress; render_status/video_path on SocialDraft; OPTIONAL backend/requirements-render.txt. cp-0019: frontend render UX (Render button + status + inline <video> + inline post <img>) served by a new path-jailed project-scoped binary media endpoint GET /api/workspace/media/{path}?projectId= (FileManager.media_file). cp-0020: first REAL platform uploader — app/services/youtube.py (OAuth2 refresh-token -> YouTube Data API v3 resumable .mp4 upload, private by default, guarded + stub-safe); publish_to(platform, draft) dispatch (youtube real, others stub); YouTube OAuth config trio replacing youtube_api_key; docs/SOCIAL_PUBLISHING.md. cp-0021: full-system review (cp-0015..cp-0020) — security/frontend/integration-isolation/regression PASSED; backend-correctness fixed 2 HIGH concurrency gaps (threading.RLock on WorkflowStore + SocialDraftStore, missed by cp-0014; begin_render/render route only render awaiting_approval drafts; social cascade-delete test). Verdict SHIP. cp-0011: all remaining nav pages (Agents + AgentHierarchyTree React Flow, Workflows, Approvals, Departments x7, Logs, Integrations, Billing) + GET /api/system/providers + /api/system/info; no Placeholder routes remain. cp-0012: Projects + Tasks full-stack (ProjectStore + CRUD API + board + Kanban), removed the Placeholder import, wired provider_max_retries, added a seed.sql<->registry drift-guard test. cp-0013: DESIGN_SYSTEM.md 8.3 center panels (SecurityCenter/MarketingCenter/DocumentationCenter back /departments/quality,/marketing,/documentation; RecoveryStatus on Workflows; MemoryUsagePanel on Memory) + GET /api/system/checkpoints — completes the full component inventory. cp-0014: applied the lead-engineer review (verdict SHIP, no critical/high code defects) — fixed a HIGH path-traversal on GET /api/workflows/runs/{workflow_id} (WorkflowStore._path rejects '/','\\',NUL,'..'), same jail on CheckpointStore (defense-in-depth), deduped RAG memory on resume via stable id (mem:{workflow_id}:{agent_id}), added threading.RLock to VectorStore + ProjectStore, corrected README/DEPLOYMENT test counts 55->70, removed an auditor scratch file (backend/_audit_recursion.py). cp-0015: partitioned the workspace per project (workspace/projects/<project_id>/ isolates artifacts + RAG memory/knowledge + workflow runs + checkpoints; GLOBAL = the project catalog .state/projects.json+tasks.json + the build-checkpoint lineage .state/checkpoints). New app/workspace_fs/paths.py (layout, path-jailed safe_project_id, purge_project_workspace, reset_caches, one-time migrate_flat_workspace); store singletons -> @lru_cache project-keyed factories (get_artifact/memory/knowledge_service + get_workflow_store(project_id) + workflow_store.find_run/find_by_approval); orchestrator threads the project through run + resume (RunResult.projectId); X-Project-Id header resolved by get_project_id (app/api/deps.py path-jails AND 404s unknown/deleted projects); /workflows/run uses the header only (body projectId override removed; RunRequest no longer has project_id). Seeded never-deletable Default Workspace (__default__); deleting any other project HARD-DELETES its subtree (project_store.delete_project -> purge_project_workspace) with a UI confirm. One-time startup migration migrate_flat_workspace moves the legacy flat layout into projects/__default__/ (idempotent via .state/.migrated_v2_projects; verified end-to-end on the real workspace). Frontend: active-project zustand store (persisted to localStorage), axios X-Project-Id interceptor (lib/api/client.ts), project-scoped React Query keys in hooks/{useArtifacts,useMemory,useKnowledge,useWorkflowRuns,useApprovals}.ts, topbar ProjectSwitcher (components/layout/project-switcher.tsx), Tasks board scoped to the active project, useProjects.deleteProject falls back to Default. Two adversarial review rounds (7-dimension fan-out then a focused fix-verification): 17 round-1 findings, actionable ones fixed, multi-tenant authorization findings consciously declined (single-admin offline OS, no per-user/per-project ownership by design); round 2 allClosed=true (both CRITICALs closed, no regressions). .gitignore extended to workspace/projects/ + .state/.migrated_v2_projects.",
    "backend_auth_hardening_note": "7 new tests (55 prior + 7): tests/test_auth.py (signed-token auth + require_user gating) + tests/test_security.py (HMAC token create/verify + hardening middleware). Auth + hardening: app/core/security.py (stdlib HMAC signed tokens: create_token/verify_token/verify_credentials), app/api/deps.py require_user (open in dev, Bearer-enforced when AUTH_ENABLED), app/api/routes/auth.py (/api/auth/config|login|me); sensitive POSTs (workflows/run, approvals decision, knowledge add+ingest) depend on require_user; app/main.py hardening_middleware (security headers always; opt-in per-IP rate limit). Settings: auth_enabled(false), admin_username/admin_password, token_ttl_seconds, security_headers_enabled(true), rate_limit_enabled(false), rate_limit_per_minute. Frontend: store/auth.ts, lib/api/auth.ts, hooks/useAuth.ts, pages/Login.tsx, components/auth/auth-gate.tsx, components/common/error-boundary.tsx, pages/Settings.tsx, axios bearer interceptor (lib/api/client.ts), wired in App.tsx + main.tsx. Docs: docs/DEPLOYMENT.md (new) + README.md (rewritten). The whole product runs OFFLINE in stub mode (no keys/Supabase needed); real providers/Supabase/auth activate via backend/.env.",
    "backend_polish_fixes_note": "Post-build polish/fixes (Phase 10): (a) BUG FIX — dashboard not visible in a real browser: src/components/layout/sidebar.tsx was position:fixed but AppLayout lays it out as a CSS grid column so main content was hidden behind it; fixed to an in-flow sticky grid item (md:flex, fills its 248px/72px track); jsdom tests didn't catch it since getByText ignores CSS. (b) DEV NOISE — vite.config.ts now swallows /api + /ws proxy ECONNREFUSED/ECONNABORTED logs when the backend dev server isn't running (SPA degrades to fallback data). (c) DEPENDENCY FIX — backend/requirements.txt pinned websockets==16.0 which conflicts with supabase 2.30.1 (realtime needs websockets<16); changed to websockets>=12,<16 (resolves to 15.0.1; full-tree dry-run resolves cleanly). (d) ANIMATION POLISH — new motion foundation src/lib/motion.ts + src/components/common/reveal.tsx (Reveal/Stagger/StaggerItem) + src/components/common/count-up.tsx (all reduced-motion aware), applied across ~24 components (Dashboard section cascade, ExecutiveOverview/StatCard count-up + stagger, AgentStatusGrid/AgentCard stagger + hover, WorkflowList, chart reveals, usage/media/achievements stagger+hover, AppLayout route-change motion, RightRail + ActivityFeed stagger, BrandFooterCard float, Sidebar nav micro-motion via MotionNavLink, Login entrance).",
    "backend_knowledge_rag_note": "10 new tests (45 prior + 10): tests/test_vectorstore.py (vector store) + tests/test_knowledge.py (knowledge) + tests/test_memory_rag.py (memory/RAG). Live: KB search retrieves relevant docs; a workflow run stores each agent output as memory; ingest-workspace indexes artifacts; memory recall returns prior-run content (the company learns from prior work). Mechanism: app/services/vectorstore.py = a deterministic 256-dim hashing embedder (offline, no key) + cosine VectorStore persisted to workspace/.state/vectors/<name>.json. KnowledgeService (knowledge corpus + ingest_workspace) and MemoryService (agent memory). RAG: app/graph/nodes/delegate.py recalls memory into each agent's context (recall_context); app/services/orchestrator.py (_persist_artifacts_and_memory) stores every successful output as memory after run/resume. API: app/api/routes/knowledge.py (search/add/ingest-workspace/stats) + app/api/routes/memory.py (search/recent/stats) mounted in app/api/router.py (/knowledge, /memory).",
    "backend_local_embedder_note": "Embeddings are a local offline hashing embedder (256-d) by default — no key required; stores persist under workspace/.state/vectors/. The Supabase pgvector path (1536-d, match_knowledge/match_memory) is the optional durable backend and needs a real embedding model + Supabase; the local store is the zero-config default.",
    "backend_artifacts_note": "4 new tests (41 prior + 4): tests/test_workspace_artifacts.py (workspace artifacts) + tests/test_media.py (media stubs). Live: running a workflow writes each agent output + a run report into ./workspace via the path-jailed FileManager; GET /api/workspace/artifacts lists them, GET /api/workspace/artifacts/{path} reads (400 on sandbox escape, 404 missing). Mechanism: ArtifactService (app/services/artifacts.py) files each agent output under workspace SUBDIRS by agent (docs/frontend/backend/presentations/reports) + writes reports/<wf>/run.md; orchestrator.run_workflow + resume_workflow call persist_run so RunResult.agentOutputs[].artifacts carry workspace-relative paths. Honors the Workspace Rule (agents only write under ./workspace).",
    "backend_media_note": "Media runs STUB-safe (no keys): POST /api/media/image, /tts, /stt live; MediaService.generate_image calls HuggingFace FLUX.1-dev when HUGGINGFACE_API_KEY is set else returns a stub placeholder; transcribe/synthesize are stub-safe. Set HUGGINGFACE_API_KEY for real FLUX.1-dev image generation; Groq Whisper STT / Orpheus TTS are stubbed pending key + audio wiring.",
    "backend_approval_resume_note": "6 new tests/test_approval_resume.py resume tests (35 prior + 6); tests/test_api.py edited (decision-on-seed-approval now asserts 404). Resume mechanism: graph compiled WITH a LangGraph MemorySaver checkpointer; the approval node calls interrupt() to suspend mid-run; orchestrator.run_workflow detects the interrupt (state['__interrupt__']) and returns awaiting_approval + the pending payload; orchestrator.resume_workflow re-enters via Command(resume={action,note}). WorkflowStore persists each run (RunResult JSON) under workspace/.state/workflows/.",
    "backend_realtime_note": "3 new tests/test_realtime.py realtime tests (32 prior + 3). Live WebSocket verified on a real socket (port 8012): client received hello -> system_health (6 metrics, immediate on connect) -> then after POST /api/workflows/run (200 completed) the workflow + activity events broadcast live. Server pushes system-health every ~4s (jittered) + simulated activity periodically via the heartbeat task, plus real workflow/activity/approval events during runs.",
    "backend_approval_resume_run": "verified end-to-end (TestClient + live): POST /api/workflows/run on a gated task -> status='awaiting_approval' + pendingApproval{approvalId,...}; POST /api/approvals/{approvalId}/decision -> approve/retry='completed' (result.ok), reject='failed', rollback='rolled_back'; unknown approvalId -> 404; GET /api/workflows/runs[?status] lists persisted runs",
    "backend_live_run": "verified (POST /api/workflows/run 'Design the UI and build the REST API' -> status=completed, 6 agentOutputs, recursionCount=1, plan=[solution-architect, uiux-designer, frontend-engineer, api-engineer, backend-engineer]; 'Publish and deploy...' -> status=awaiting_approval, pendingApproval.kind=final_code; kill switch recursion>3 -> STOPPED)",
    "backend_live_curl": "verified (GET /health 23 agents; /api/dashboard 17 camelCase keys; /api/agents 23; /api/agents/ceo-manager google_ai/gemini-2.5-flash; /api/agents/nope 404; /api/workflows 5; /api/activity 6; /api/system/health 6)",
    "frontend_lint": "pass (exit 0, eslint --max-warnings 0, clean)",
    "frontend_build": "pass (exit 0)",
    "frontend_tests": "17 passed, 0 failed (vitest render smoke — dashboard sections + live indicator + RunTask + /workspace + /knowledge + /memory + auth gate / Login + the post-1.0 pages + /social Social Studio render; + project-switcher.test.tsx: switch / inline create / two-step delete-confirm)",
    "per_project_workspaces_note": "cp-0015 partitioned the workspace per project. Each project owns workspace/projects/<project_id>/ with isolated artifacts (docs/frontend/backend/presentations/reports), RAG memory + knowledge base (.state/vectors), workflow run records (.state/workflows) and checkpoints (.checkpoints). GLOBAL (shared): the project catalog workspace/.state/projects.json + tasks.json, and the build-checkpoint lineage workspace/.state/checkpoints. app/workspace_fs/paths.py owns the layout (DEFAULT_PROJECT='__default__', safe_project_id per-project path jail, project_root, list_project_dir_ids, purge_project_workspace, reset_caches, migrate_flat_workspace). Store singletons became @lru_cache project-keyed factories get_artifact_service/get_memory_service/get_knowledge_service/get_workflow_store(project_id=DEFAULT_PROJECT); workflow_store also gained module-level find_run/find_by_approval that scan all projects (resume/approval only know an id, not the project). The orchestrator threads the project through run + resume; resume persists artifacts/memory back to the OWNING project. API dependency app/api/deps.py:get_project_id reads X-Project-Id (or ?projectId=), path-jails it AND rejects unknown/deleted projects with 404; scoped routes: workspace, memory, knowledge, workflows (runs + run), media. The Default Workspace (__default__) is seeded and never-deletable; deleting any other project HARD-DELETES its entire workspace subtree (project_store.delete_project -> purge_project_workspace) with a UI confirm. A one-time startup migration migrate_flat_workspace moves the legacy flat layout into projects/__default__/ (idempotent via a .state/.migrated_v2_projects marker; verified end-to-end). Adversarial review: 2 rounds; multi-tenant AUTHORIZATION findings consciously DECLINED because this is a single-admin offline OS with no per-user/per-project ownership by design; round 2 allClosed=true.",
    "social_pipeline_note": "cp-0016..cp-0021 built the social content pipeline (reels + posts): compose -> render -> human-approve -> publish, project-scoped + offline/stub-first. Backend: app/schemas/social.py (ReelScene/ReelStoryboard, SocialDraft, PublishResult, request + decision DTOs); per-project SocialDraftStore (app/services/social_store.py, .state/social/, project-keyed factory, path-jailed ids, threading.RLock added cp-0021, in reset_caches); SocialService (app/services/social.py: draft_reel storyboard + stub voiceover + storyboard.json/reel.md via the jailed FileManager; draft_post caption+hashtags + stub-safe FLUX image; begin_render/run_render async render only for awaiting_approval drafts; decide approve|reject); /api/social routes (reel, post, drafts list/get, decision, POST /drafts/{id}/render BackgroundTask) project-scoped via get_project_id. Real reel render: app/services/reel_render.py (MoviePy+FFmpeg via imageio-ffmpeg + Pillow caption PNG overlays — NO ImageMagick + Pexels b-roll via services/pexels.py + Orpheus voiceover via MediaService.generate_voiceover/HuggingFaceProvider.generate_audio) with a 3-level degradation ladder (stub -> offline color+caption .mp4 -> full), import-guarded, OPTIONAL backend/requirements-render.txt; render_status/video_path/render_note on SocialDraft; /ws progress. Render UX served by GET /api/workspace/media/{path:path}?projectId= (FileManager.media_file, path-jailed, FileResponse). Publishers (app/services/publishers.py): publish_to(platform, draft) dispatches youtube -> real (app/services/youtube.py OAuth2 refresh-token -> YouTube Data API v3 resumable .mp4 upload, private by default, guarded + stub-safe + never-raises) and the other four -> stubs; reels default YouTube+Instagram, posts Facebook+LinkedIn+Twitter. Config gained PEXELS/YOUTUBE OAuth trio/INSTAGRAM/FACEBOOK/LINKEDIN/TWITTER keys (youtube_api_key removed). docs/SOCIAL_PUBLISHING.md documents the setup + per-platform status. Frontend: /social Social Studio (pages/Social.tsx), lib/api/social.ts, hooks/useSocial.ts, social wire types in lib/api/types.ts, nav entry + /social route. Tests: tests/test_social.py (draft/decide/publish/render/youtube-stub/cascade-delete) + media-traversal tests in tests/test_workspace_artifacts.py. All adversarially reviewed (cp-0017/18/19/20 per-feature 4-5 lens + the cp-0021 6-domain full-system review, verdict SHIP).",
    "agent_count": 23,
    "same_process_resume_note": "Resume is SAME-PROCESS: LangGraph MemorySaver is in-memory, so approve/reject/retry/rollback resumes only within the same running backend process. Durable cross-restart resume needs a Postgres checkpointer (Supabase); the WorkflowStore persists run metadata (workspace/.state/workflows/) either way. Also a benign LangGraph msgpack note when deserializing the str-enum WorkflowStatus (comparisons still hold).",
    "provider_keys_note": "Providers call real LLMs (tenacity retry on 429/timeout/5xx) when GOOGLE_AI_STUDIO_API_KEY/OPENROUTER_API_KEY/GROQ_API_KEY/HUGGINGFACE_API_KEY are set in backend/.env; otherwise deterministic offline stub mode so the graph runs/tests fully offline.",
    "langgraph_install_note": "langgraph 1.2.2 + langchain-core 1.4.0 installed into backend/.venv (previously absent); providers rewritten to httpx + offline STUB (no vendor SDKs)."
  },
  "pending_approvals": [],
  "kill_switch": { "tripped": false, "reason": null },
  "project_complete": true
}
```
<!-- END omnivra-state -->

### Field reference
- `build_status` ∈ `not_started | in_progress | blocked | failed | complete`.
- `phases[].status` ∈ `pending | in_progress | blocked | failed | complete`.
- `active_workflow.status` ∈ `idle | in_progress | awaiting_approval | failed | complete`.
- `recursion_count > recursion_limit` ⇒ orchestrator trips the **kill switch**, sets
  `build_status = failed`, `kill_switch.tripped = true`, and stops the run.
- `manifest_hash` is the SHA-256 of `docs/FILE_MANIFEST.md`; a mismatch on resume forces the
  Recovery Agent to re-reconcile the manifest before continuing.
- `runtime_mirror` is the volatile, git-ignored live copy; `scripts/state.ps1` reads it.
- To **resume**: load this block → read `last_checkpoint_id` → fetch that entry from
  `docs/CHECKPOINTS.md` (or `workspace/.state/checkpoints/<id>.json`) → restore LangGraph state.
