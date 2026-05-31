# FILE MANIFEST — Omnivra AI Company OS

> Registry of **every** file the project plans to produce. The orchestrator and Recovery Agent
> reconcile generated output against this manifest. Each row has an owner agent, the target tree
> (`source` = committed project code; `workspace` = AI agent draft output per the Workspace Rule),
> a phase, and a status.
>
> **Status legend:** `DONE` (on disk, validated) · `PENDING` (planned, not generated) ·
> `IN_PROGRESS` · `REVIEWED` · `SKIPPED` · `REMOVED` (deleted on disk by a later checkpoint) ·
> `ORPHAN` (on disk but no longer referenced — Recovery Agent review).
> **Owner legend:** see Agent Roster in `README.md` / `backend/app/agents/registry.py`
> (e.g. `architect`, `frontend-eng`, `backend-eng`, `db-eng`, `api-eng`, `designer`, `qa`,
> `secops`, `docs`, `ceo`).
>
> Phase-1 source files (`tree=source`) are committed scaffold. From later phases, AI agents draft
> into `tree=workspace` mirrors and a human promotes them via the Approval Gate. The runtime mirror
> of this manifest is `workspace/.state/file_manifest.json` (volatile, git-ignored). This durable
> doc is the source of truth on resume.

---

## Phase 1 — Foundation (DONE)

### Root tooling & config
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `.gitignore` | architect | source | 1 | DONE |
| `.editorconfig` | architect | source | 1 | DONE |
| `.env.example` | architect | source | 1 | DONE |
| `README.md` | architect | source | 1 | DONE |
| `.vscode/settings.json` | architect | source | 1 | DONE |
| `.vscode/extensions.json` | architect | source | 1 | DONE |
| `scripts/setup.ps1` | architect | source | 1 | DONE |
| `scripts/dev.ps1` | architect | source | 1 | DONE |
| `scripts/state.ps1` | architect | source | 1 | DONE |

### Control plane (durable state docs)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `docs/PROJECT_STATE.md` | ceo | source | 1 | DONE |
| `docs/FILE_MANIFEST.md` | ceo | source | 1 | DONE |
| `docs/CHECKPOINTS.md` | ceo | source | 1 | DONE |
| `docs/ROADMAP.md` | ceo | source | 1 | DONE |
| `docs/DESIGN_SYSTEM.md` | designer | source | 1 | DONE |
| `docs/SUPABASE_INTEGRATION.md` | db-eng | source | 1 | DONE |

### Workspace skeleton (Workspace Rule sandbox)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `workspace/README.md` | architect | source | 1 | DONE |
| `workspace/.state/README.md` | backend-eng | source | 1 | DONE |
| `workspace/{frontend,backend,docs,presentations,reports}/.gitkeep` | architect | workspace | 1 | DONE |
| `workspace/.state/{checkpoints,artifacts}/.gitkeep` | backend-eng | workspace | 1 | DONE |
| `workspace/.state/project_state.json` (runtime mirror) | backend-eng | workspace | 1 | DONE |
| `workspace/.state/file_manifest.json` (runtime mirror) | backend-eng | workspace | 1 | DONE |

### Frontend scaffold
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/package.json` | frontend-eng | source | 1 | DONE |
| `frontend/package-lock.json` | frontend-eng | source | 1 | DONE |
| `frontend/vite.config.ts` | frontend-eng | source | 1 | DONE |
| `frontend/tsconfig.json` | frontend-eng | source | 1 | DONE |
| `frontend/tsconfig.node.json` | frontend-eng | source | 1 | DONE |
| `frontend/postcss.config.js` | frontend-eng | source | 1 | DONE |
| `frontend/tailwind.config.ts` | designer | source | 1 | DONE |
| `frontend/components.json` | frontend-eng | source | 1 | DONE |
| `frontend/index.html` | frontend-eng | source | 1 | DONE |
| `frontend/.env.example` | frontend-eng | source | 1 | DONE |
| `frontend/.gitignore` | frontend-eng | source | 1 | DONE |
| `frontend/.eslintrc.cjs` | frontend-eng | source | 1 | DONE |
| `frontend/.prettierrc.json` | frontend-eng | source | 1 | DONE |
| `frontend/README.md` | frontend-eng | source | 1 | DONE |
| `frontend/public/favicon.svg` | designer | source | 1 | DONE |
| `frontend/src/main.tsx` | frontend-eng | source | 1 | DONE |
| `frontend/src/App.tsx` | frontend-eng | source | 1 | DONE |
| `frontend/src/index.css` | designer | source | 1 | DONE |
| `frontend/src/vite-env.d.ts` | frontend-eng | source | 1 | DONE |
| `frontend/src/lib/utils.ts` | frontend-eng | source | 1 | DONE |
| `frontend/src/providers/AppProviders.tsx` | frontend-eng | source | 1 | DONE |
| `frontend/src/styles/tokens.ts` | designer | source | 1 | DONE |

### Backend scaffold
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/pyproject.toml` | backend-eng | source | 1 | DONE |
| `backend/requirements.txt` | backend-eng | source | 1 | DONE |
| `backend/.env.example` | backend-eng | source | 1 | DONE |
| `backend/.gitignore` | backend-eng | source | 1 | DONE |
| `backend/README.md` | backend-eng | source | 1 | DONE |
| `backend/app/__init__.py` | backend-eng | source | 1 | DONE |
| `backend/app/main.py` | backend-eng | source | 1 | DONE |
| `backend/app/core/__init__.py` | backend-eng | source | 1 | DONE |
| `backend/app/core/config.py` | backend-eng | source | 1 | DONE |
| `backend/app/core/logging.py` | backend-eng | source | 1 | DONE |
| `backend/app/providers/__init__.py` | backend-eng | source | 1 | DONE |
| `backend/app/providers/base.py` | backend-eng | source | 1 | DONE |
| `backend/app/providers/openrouter.py` | backend-eng | source | 1 | DONE |
| `backend/app/providers/groq.py` | backend-eng | source | 1 | DONE |
| `backend/app/providers/google_ai.py` | backend-eng | source | 1 | DONE |
| `backend/app/providers/huggingface.py` | backend-eng | source | 1 | DONE |
| `backend/app/providers/registry.py` | backend-eng | source | 1 | DONE |
| `backend/app/agents/__init__.py` | architect | source | 1 | DONE |
| `backend/app/agents/registry.py` (23-agent roster, source of truth) | architect | source | 1 | DONE |
| `backend/app/graph/__init__.py` | architect | source | 1 | DONE |
| `backend/app/graph/state.py` | architect | source | 1 | DONE |
| `backend/app/graph/kill_switch.py` | backend-eng | source | 1 | DONE |
| `backend/app/graph/approval.py` | backend-eng | source | 1 | DONE |
| `backend/app/graph/builder.py` (CEO→department routing skeleton) | architect | source | 1 | DONE |
| `backend/app/checkpoint/__init__.py` | backend-eng | source | 1 | DONE |
| `backend/app/checkpoint/store.py` (checkpoint/manifest store) | backend-eng | source | 1 | DONE |
| `backend/app/workspace_fs/__init__.py` | backend-eng | source | 1 | DONE |
| `backend/app/workspace_fs/file_manager.py` (path-jailed Workspace Rule) | backend-eng | source | 1 | DONE |
| `backend/db/README.md` (Python data-access layer; SQL lives in `supabase/`) | db-eng | source | 1 | DONE |
| `backend/tests/__init__.py` | qa | source | 1 | DONE |
| `backend/tests/conftest.py` | qa | source | 1 | DONE |
| `backend/tests/test_agent_registry.py` | qa | source | 1 | DONE |
| `backend/tests/test_health.py` | qa | source | 1 | DONE |
| `backend/tests/test_kill_switch.py` | qa | source | 1 | DONE |
| `backend/tests/test_workspace_sandbox.py` | qa | source | 1 | DONE |

### Supabase (SQL is canonical, flat under `supabase/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `supabase/schema.sql` (tables + pgvector embeddings) | db-eng | source | 1 | DONE |
| `supabase/rls.sql` (row-level security policies) | db-eng | source | 1 | DONE |
| `supabase/seed.sql` (agents/departments seed) | db-eng | source | 1 | DONE |

---

## Phase 2 — Design system + UI primitives + layout shell (DONE)

> Built and validated: `npm run build` (`tsc` strict + `vite build`) **exit 0** (2580 modules);
> `npm run test` (vitest/jsdom) **3/3** render smoke tests pass (full app shell mounts);
> **42** `frontend/src/` files on disk. Note: `src/styles/tokens.ts` was scaffolded in Phase 1
> (listed DONE under Frontend scaffold) and is extended here.

### Foundation (types / config / store / styles)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/types/index.ts` | frontend-eng | source | 2 | DONE |
| `frontend/src/lib/accents.ts` | designer | source | 2 | DONE |
| `frontend/src/config/navigation.ts` | frontend-eng | source | 2 | DONE |
| `frontend/src/config/agents.ts` | frontend-eng | source | 2 | DONE |
| `frontend/src/store/ui.ts` | frontend-eng | source | 2 | DONE |
| `frontend/src/styles/tokens.ts` (extended; scaffolded in Phase 1) | designer | source | 2 | DONE |

### UI primitives (`frontend/src/components/ui/`)
| Path / Component | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `components/ui/{glass-card,button,tooltip,scroll-area,dropdown-menu,avatar,separator}.tsx` | frontend-eng | source | 2 | DONE |
| `components/ui/{neon-badge,status-dot,icon-tile,chip,kbd-hint,progress-bar}.tsx` | frontend-eng | source | 2 | DONE |
| `components/ui/{section-header,sparkline,icon-button,timeframe-select,empty-state}.tsx` | frontend-eng | source | 2 | DONE |

### Charts (`frontend/src/components/ui/charts/`)
| Path / Component | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `components/ui/charts/area-chart.tsx` (OmniAreaChart) | frontend-eng | source | 2 | DONE |
| `components/ui/charts/donut-chart.tsx` (OmniDonutChart) | frontend-eng | source | 2 | DONE |
| `components/ui/charts/bar-meter.tsx` (BarMeter) | frontend-eng | source | 2 | DONE |

### Layout shell (`frontend/src/components/layout/`)
| Path / Component | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `components/layout/{brand-logo,sidebar,topbar,right-rail,app-layout}.tsx` | frontend-eng | source | 2 | DONE |

### Pages & wiring
| Path / Component | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/pages/Dashboard.tsx` (Phase-2 showcase) | frontend-eng | source | 2 | DONE |
| `frontend/src/pages/Placeholder.tsx` | frontend-eng | source | 2 | DONE |
| `frontend/src/App.tsx` (routes under AppLayout) | frontend-eng | source | 2 | DONE |
| `frontend/src/providers/AppProviders.tsx` (mounts TooltipProvider) | frontend-eng | source | 2 | DONE |
| `frontend/src/main.tsx` (router v7 future flags) | frontend-eng | source | 2 | DONE |

### Test harness
| Path / Component | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/vitest.config.ts` | qa | source | 2 | DONE |
| `frontend/src/test/setup.ts` (jsdom polyfills) | qa | source | 2 | DONE |
| `frontend/src/test/smoke.test.tsx` (3 render smoke tests) | qa | source | 2 | DONE |
| `frontend/package.json` (+`test`/`test:watch`; devDeps vitest, jsdom, @testing-library/react, @testing-library/dom) | frontend-eng | source | 2 | DONE |

---

## Phase 3 — Dashboard sections (mock data) (DONE)

> Built and validated: `npm run lint` (`eslint --max-warnings 0`) **exit 0** (clean);
> `npm run build` (`tsc` strict + `vite build`) **exit 0** (2609 modules); `npm run test`
> (vitest/jsdom) **4/4** — render smoke asserts all 8 dashboard sections render on mock data
> (AI Agents Status, Active Workflows, Task Execution Overview, Task Distribution, Live Activity
> Feed, Pending Approvals, System Health, Recent Achievements) plus stat values + a workflow name.
> Section components are props-driven, so Phase 4 swaps only the data source at the assembler level.

### Mock data & types
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/data/dashboard.ts` (executiveStats, workflows, taskExecution(+series), taskDistribution(+totalTasks), activity, approvals(+totalPendingApprovals), systemHealth, providerUsage, modelUsage, mediaServices, achievements) | frontend-eng | source | 3 | DONE |
| `frontend/src/types/index.ts` (extended: StatCardData, WorkflowItem, TaskPoint, DistributionSlice, ActivityItem, ApprovalItem, HealthMetric, ProviderUsageItem, ModelUsageItem, MediaServiceItem, AchievementItem, WorkflowStatus) | frontend-eng | source | 3 | DONE |

### Dashboard section components (`frontend/src/components/dashboard/`)
| Path / Component | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `components/dashboard/{date-time-status,stat-card,executive-overview,greeting-hero,agent-card,system-ops-row,agent-status-grid}.tsx` | frontend-eng | source | 3 | DONE |
| `components/dashboard/{workflow-row,workflow-list,task-execution-chart,task-distribution,provider-usage,model-usage}.tsx` | frontend-eng | source | 3 | DONE |
| `components/dashboard/{media-service-card,media-services,achievement-card,achievements,activity-feed}.tsx` | frontend-eng | source | 3 | DONE |
| `components/dashboard/{approval-card,pending-approvals,system-health,brand-footer-card}.tsx` | frontend-eng | source | 3 | DONE |

### Assembly & rewrites
| Path / Component | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/pages/Dashboard.tsx` (rewritten — assembles the full main-column layout) | frontend-eng | source | 3 | DONE |
| `frontend/src/components/layout/right-rail.tsx` (rewritten — hosts ActivityFeed + PendingApprovals + SystemHealth + BrandFooterCard; clock moved into GreetingHero) | frontend-eng | source | 3 | DONE |

### Lint hardening & tests
| Path / Component | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/.eslintrc.cjs` (override: react-refresh off for `components/ui`) | frontend-eng | source | 3 | DONE |
| `frontend/src/test/setup.ts` (semicolons) | qa | source | 3 | DONE |
| `frontend/src/test/smoke.test.tsx` (extended — 4 tests; asserts all 8 dashboard sections + stat values + a workflow name) | qa | source | 3 | DONE |

---

## Phase 4 — Backend data layer + REST API + Supabase wiring (DONE)

> Built and validated: `pytest` = **25 passed, 0 failed** (15 prior + 10 new `tests/test_api.py`
> API tests); live uvicorn server **curl-verified** end-to-end (`GET /health` 23 agents;
> `GET /api/dashboard` returns all 17 camelCase keys — `agents=18`, `systemOps=5`, `totalTasks=124`,
> `totalPendingApprovals=7`; `/api/agents` 23; `/api/agents/ceo-manager` → `google_ai`/
> `gemini-2.5-flash`; `/api/agents/nope` → 404; `POST /api/approvals/{id}/decision` stub →
> `"received"`; `/api/workflows` 5; `/api/activity` 6; `/api/system/health` 6). Frontend still green
> (`npm run build` exit 0, `npm run lint` 0 warnings, vitest 4/4). Architecture: frontend → `/api`
> (Vite proxy) → FastAPI → repository → seed data (Supabase optional). The dashboard is now
> LIVE-data-driven via `useDashboard()` with the bundled mock as instant fallback/`initialData`.
>
> **Operational caveats:** (1) the `supabase` Python SDK is in `backend/requirements.txt` but is
> **not** installed in `backend/.venv` (Phase-1 core subset); the app runs on the `SeedRepository`
> with zero external deps — activate Supabase via
> `backend/.venv/Scripts/python.exe -m pip install supabase==2.30.1` + `SUPABASE_URL`/
> `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env` + run `supabase/{schema,rls,seed}.sql`.
> (2) `SupabaseRepository` assumes the `supabase/schema.sql` tables (maps DB enum
> `google_ai_studio` → `google_ai`); on any query error it logs + falls back to seed (never 500s).

### Schemas (`backend/app/schemas/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/schemas/__init__.py` | api-eng | source | 4 | DONE |
| `backend/app/schemas/dashboard.py` (Pydantic DTOs, camelCase via `to_camel`; aggregate `DashboardPayload`) | api-eng | source | 4 | DONE |

### Seed data layer (`backend/app/data/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/data/__init__.py` | backend-eng | source | 4 | DONE |
| `backend/app/data/seed.py` (`build_dashboard()` + `seed_agents()`; maps `PROVIDER_LABEL`/`DEPARTMENT_ACCENT`/`MODEL_LABEL`) | backend-eng | source | 4 | DONE |

### Database client + repositories (`backend/app/db/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/db/__init__.py` | db-eng | source | 4 | DONE |
| `backend/app/db/client.py` (`get_supabase_client()` → `Client | None`, lazy import; `supabase_configured()`) | db-eng | source | 4 | DONE |
| `backend/app/db/repositories/__init__.py` (`get_repository` factory) | db-eng | source | 4 | DONE |
| `backend/app/db/repositories/base.py` (`DashboardRepository` Protocol) | db-eng | source | 4 | DONE |
| `backend/app/db/repositories/seed_repo.py` (`SeedRepository`, default) | db-eng | source | 4 | DONE |
| `backend/app/db/repositories/supabase_repo.py` (`SupabaseRepository`, optional; enum map + seed fallback) | db-eng | source | 4 | DONE |

### REST API (`backend/app/api/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/api/__init__.py` | api-eng | source | 4 | DONE |
| `backend/app/api/deps.py` (`get_repo`) | api-eng | source | 4 | DONE |
| `backend/app/api/router.py` | api-eng | source | 4 | DONE |
| `backend/app/api/routes/{dashboard,agents,workflows,approvals,activity,system}.py` | api-eng | source | 4 | DONE |

### Backend tests
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/tests/test_api.py` (10 new API tests) | qa | source | 4 | DONE |

### Frontend API layer (`frontend/src/lib/api/`) + hooks
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/lib/api/client.ts` (axios) | frontend-eng | source | 4 | DONE |
| `frontend/src/lib/api/types.ts` (DTOs) | frontend-eng | source | 4 | DONE |
| `frontend/src/lib/api/icons.ts` (icon registry) | frontend-eng | source | 4 | DONE |
| `frontend/src/lib/api/dashboard.ts` (fetch + adapt) | frontend-eng | source | 4 | DONE |
| `frontend/src/hooks/useDashboard.ts` | frontend-eng | source | 4 | DONE |

### Frontend rewires (data source swap)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/data/dashboard.ts` (added `fallbackDashboard` aggregate) | frontend-eng | source | 4 | DONE |
| `frontend/src/pages/Dashboard.tsx` (now consumes `useDashboard()`) | frontend-eng | source | 4 | DONE |
| `frontend/src/components/layout/right-rail.tsx` (now consumes `useDashboard()`) | frontend-eng | source | 4 | DONE |

---

## Phase 5 — Agent/provider integration + LangGraph orchestration + kill switch + tenacity (DONE)

> Built and validated: `pytest` = **32 passed, 0 failed** (25 prior + 7 new `tests/test_orchestration.py`
> orchestration tests); live `POST /api/workflows/run` **verified end-to-end** — "Design the UI and build
> the REST API" → `status=completed`, **6 `agentOutputs`**, `recursionCount=1`,
> `plan=[solution-architect, uiux-designer, frontend-engineer, api-engineer, backend-engineer]`;
> "Publish and deploy…" → `status=awaiting_approval`, `pendingApproval.kind=final_code`; direct
> orchestration + kill switch (recursion>3 → STOPPED) confirmed. LangGraph topology:
> `START → ceo → guard(check_kill_switch) → {stop: END, go: delegate} → approval → {wait: END, go: finalize} → END`.
> `langgraph 1.2.2` + `langchain-core 1.4.0` were installed into `backend/.venv` (previously absent).
>
> **Operational note (provider keys):** Providers call real LLMs (tenacity retry on 429/timeout/5xx)
> when `GOOGLE_AI_STUDIO_API_KEY` / `OPENROUTER_API_KEY` / `GROQ_API_KEY` / `HUGGINGFACE_API_KEY` are set
> in `backend/.env`; otherwise they return a deterministic offline STUB so the graph runs and tests pass
> fully offline. Providers were rewritten to plain `httpx` + STUB mode (no vendor SDKs). The approval gate
> holds publish/deploy/export/release/presentation/final tasks (`AWAITING_APPROVAL` + `pending_approval`);
> resume wiring is Phase 7.

### Providers (rewritten — `backend/app/providers/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/providers/_compat.py` (`make_stub_response` + `openai_chat` + `post_json`; httpx + tenacity) | backend-eng | source | 5 | DONE |
| `backend/app/providers/openrouter.py` (OpenAI-compatible REST; rewritten) | backend-eng | source | 5 | DONE |
| `backend/app/providers/groq.py` (OpenAI-compatible REST; rewritten) | backend-eng | source | 5 | DONE |
| `backend/app/providers/google_ai.py` (Gemini `generateContent` REST; rewritten) | backend-eng | source | 5 | DONE |
| `backend/app/providers/huggingface.py` (image via Inference API + stub text; rewritten) | backend-eng | source | 5 | DONE |
| `backend/app/providers/registry.py` (added `get_provider_registry()` cached singleton) | backend-eng | source | 5 | DONE |

### Agent runner (`backend/app/agents/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/agents/runner.py` (`run_agent` + `build_system_prompt`) | backend-eng | source | 5 | DONE |

### Orchestration schemas (`backend/app/schemas/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/schemas/orchestration.py` (`RunRequest`/`RunResult`/`AgentRunOutput`/`PendingApproval`, camelCase) | api-eng | source | 5 | DONE |
| `backend/app/schemas/__init__.py` (re-exports orchestration schemas) | api-eng | source | 5 | DONE |

### LangGraph orchestration (`backend/app/graph/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/graph/builder.py` (`build_graph` + `get_compiled_graph`; rewritten) | architect | source | 5 | DONE |
| `backend/app/graph/planner.py` (`plan_delegations` heuristic) | architect | source | 5 | DONE |
| `backend/app/graph/nodes/{__init__,ceo,delegate,approval,finalize}.py` | backend-eng | source | 5 | DONE |

### Orchestrator service (`backend/app/services/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/services/__init__.py` | backend-eng | source | 5 | DONE |
| `backend/app/services/orchestrator.py` (`run_workflow()`) | backend-eng | source | 5 | DONE |

### REST + tests
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/api/routes/workflows.py` (added `POST /run` `response_model=RunResult`; GET preserved) | api-eng | source | 5 | DONE |
| `backend/tests/test_orchestration.py` (7 new orchestration tests) | qa | source | 5 | DONE |

---

## Phase 6 — Realtime WebSockets + live activity/health streaming (DONE)

> Built and validated: `pytest` = **35 passed, 0 failed** (32 prior + 3 new `tests/test_realtime.py`
> realtime tests); live WebSocket **verified end-to-end** on a real socket (port 8012) — client
> received `hello` → `system_health` (6 metrics, pushed immediately on connect) → then after
> `POST /api/workflows/run` (200, `status=completed`) the `workflow` + `activity` events broadcast
> live over the socket. Frontend still green (`npm run lint` exit 0, `npm run build` exit 0,
> `npm run test` vitest **5/5** — smoke now asserts the live indicator renders). Behavior: the server
> heartbeat pushes system-health every ~4s (jittered) + simulated activity periodically, plus real
> `workflow`/`activity`/`approval` events during runs; `useWebSocket` folds them into the same React
> Query `['dashboard']` cache `useDashboard()` reads (replace `systemHealth` on `system_health`,
> prepend on `activity` capped at 12), so System Health + Live Activity Feed re-render live. The `/ws`
> Vite proxy targets `ws://localhost:8000`.

### Realtime backend (`backend/app/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/schemas/events.py` (Event envelope, camelCase) | api-eng | source | 6 | DONE |
| `backend/app/services/realtime.py` (`ConnectionManager` + module-level `manager`, `emit(type, payload)`, `health_snapshot()`, `heartbeat_loop`) | backend-eng | source | 6 | DONE |
| `backend/app/main.py` (`/ws` rewired manager-backed: `hello` + immediate `system_health` then streams broadcasts; heartbeat task started/stopped in lifespan) | api-eng | source | 6 | DONE |
| `backend/app/services/orchestrator.py` (emits `workflow` running/terminal events) | backend-eng | source | 6 | DONE |
| `backend/app/graph/nodes/delegate.py` (emits `activity` per delegated agent) | backend-eng | source | 6 | DONE |
| `backend/app/graph/nodes/approval.py` (emits `approval` when gating) | backend-eng | source | 6 | DONE |
| `backend/tests/test_realtime.py` (3 new realtime tests) | qa | source | 6 | DONE |

### Realtime frontend (`frontend/src/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/lib/api/events.ts` (`WsEvent` + `activityFromEvent`/`healthFromEvent`) | frontend-eng | source | 6 | DONE |
| `frontend/src/hooks/useWebSocket.ts` (connect via Vite `/ws` proxy, reconnect backoff, folds events into the React Query `['dashboard']` cache; jsdom-guarded) | frontend-eng | source | 6 | DONE |
| `frontend/src/components/dashboard/live-indicator.tsx` (`LiveIndicator`: emerald `Live` / amber `Connecting` / `Offline`) | frontend-eng | source | 6 | DONE |
| `frontend/src/store/ui.ts` (added `realtimeStatus` + `setRealtimeStatus`) | frontend-eng | source | 6 | DONE |
| `frontend/src/components/layout/app-layout.tsx` (calls `useWebSocket()` once) | frontend-eng | source | 6 | DONE |
| `frontend/src/components/layout/topbar.tsx` (renders `LiveIndicator`) | frontend-eng | source | 6 | DONE |
| `frontend/src/test/smoke.test.tsx` (asserts the live indicator renders) | qa | source | 6 | DONE |

---

## Phase 7 — Human approval gate resume + recovery (DONE)

> Built and validated: `pytest` = **41 passed, 0 failed** (35 prior + 6 new
> `tests/test_approval_resume.py` resume tests; `tests/test_api.py` edited — decision-on-seed-approval
> now asserts 404). End-to-end **verified** via API (TestClient + live): `POST /api/workflows/run` on a
> gated task → `status='awaiting_approval'` + `pendingApproval{approvalId,...}`;
> `POST /api/approvals/{approvalId}/decision` → approve/retry → `'completed'` (`result.ok`),
> reject → `'failed'`, rollback → `'rolled_back'`; unknown `approvalId` → 404;
> `GET /api/workflows/runs[?status]` lists persisted runs. Frontend green (`npm run lint` exit 0,
> `npm run build` exit 0, `npm run test` vitest **6/6**). Mechanism: the graph is compiled **with** a
> LangGraph `MemorySaver` checkpointer; the approval node calls LangGraph `interrupt()` to suspend
> mid-run; `orchestrator.run_workflow` detects the interrupt (`state['__interrupt__']`) and returns
> `awaiting_approval` + the pending payload; `orchestrator.resume_workflow` re-enters via
> `Command(resume={action,note})`. `WorkflowStore` persists each run (`RunResult` JSON) under
> `workspace/.state/workflows/`.
>
> **Operational note (same-process resume):** LangGraph `MemorySaver` is in-memory, so
> approve/reject/retry/rollback resumes only within the same running backend process. Durable
> cross-restart resume needs a Postgres checkpointer (Supabase); the `WorkflowStore` persists run
> metadata either way (runs/recovery listings survive a restart even though the in-flight graph state
> does not). A benign LangGraph msgpack note appears when deserializing the str-enum `WorkflowStatus`
> (comparisons still hold).

### Resume backend (`backend/app/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/graph/builder.py` (added `MemorySaver` checkpointer + `compile(checkpointer=...)`) | architect | source | 7 | DONE |
| `backend/app/graph/nodes/approval.py` (`interrupt()` + decision branch: approve/retry→RUNNING, reject→FAILED, rollback→ROLLED_BACK) | backend-eng | source | 7 | DONE |
| `backend/app/services/orchestrator.py` (`run_workflow` interrupt-detect + persist; new `resume_workflow` via `Command(resume=...)`) | backend-eng | source | 7 | DONE |
| `backend/app/services/workflow_store.py` (`WorkflowStore` + `get_workflow_store`; persists each run RunResult JSON under `workspace/.state/workflows/`) | backend-eng | source | 7 | DONE |
| `backend/app/api/routes/approvals.py` (`POST /{id}/decision` now resumes; 404 if unknown) | api-eng | source | 7 | DONE |
| `backend/app/api/routes/workflows.py` (added `GET /runs` + `GET /runs/{id}`) | api-eng | source | 7 | DONE |
| `backend/tests/test_approval_resume.py` (6 new resume tests) | qa | source | 7 | DONE |
| `backend/tests/test_api.py` (edited — decision-on-seed-approval now asserts 404) | qa | source | 7 | DONE |

### Resume frontend (`frontend/src/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/lib/api/types.ts` (added `RunResult`/`AgentRunOutput`/`PendingApproval`/`RunStatus`) | frontend-eng | source | 7 | DONE |
| `frontend/src/lib/api/workflows.ts` (`runWorkflow`/`listAwaitingRuns`/`decideApproval`) | frontend-eng | source | 7 | DONE |
| `frontend/src/hooks/useApprovals.ts` (`useAwaitingApprovals` + `useApprovalDecision`) | frontend-eng | source | 7 | DONE |
| `frontend/src/hooks/useRunWorkflow.ts` | frontend-eng | source | 7 | DONE |
| `frontend/src/components/dashboard/run-task.tsx` (`RunTask`) | frontend-eng | source | 7 | DONE |
| `frontend/src/components/dashboard/greeting-hero.tsx` (edited — renders `RunTask`) | frontend-eng | source | 7 | DONE |
| `frontend/src/components/dashboard/approval-card.tsx` (edited — added `onDecision` Approve/Reject/Retry/Rollback actions) | frontend-eng | source | 7 | DONE |
| `frontend/src/components/dashboard/pending-approvals.tsx` (edited — shows LIVE awaiting runs above seed items, wired to the decision mutation; doubles as the Recovery view) | frontend-eng | source | 7 | DONE |
| `frontend/src/test/smoke.test.tsx` (asserts `RunTask` renders) | qa | source | 7 | DONE |

---

## Phase 8 — Marketing/Docs/Presentation/Media agents + workspace artifacts (DONE)

> Built and validated: `pytest` = **45 passed, 0 failed** (41 prior + 4 new —
> `tests/test_workspace_artifacts.py` workspace artifacts + `tests/test_media.py` media stubs);
> live **verified** — running a workflow writes each agent output **plus** a run report into
> `./workspace` via the path-jailed `FileManager`; `GET /api/workspace/artifacts` lists them,
> `GET /api/workspace/artifacts/{path}` reads (400 on sandbox escape, 404 missing). Media
> endpoints (`POST /api/media/image` / `/tts` / `/stt`) are live and **stub-safe**. Frontend still
> green (`npm run lint` exit 0, `npm run build` exit 0, `npm run test` vitest **7/7** — smoke now
> asserts `/workspace` renders). Mechanism: `ArtifactService` files each agent output under workspace
> SUBDIRS by agent (`docs/frontend/backend/presentations/reports`) + writes `reports/<wf>/run.md`;
> `orchestrator.run_workflow` + `resume_workflow` call `persist_run` so
> `RunResult.agentOutputs[].artifacts` carry workspace-relative paths. Honors the Workspace Rule
> (agents only write under `./workspace`).
>
> **Operational note (media stub-safe):** media runs stub-safe with no keys — set
> `HUGGINGFACE_API_KEY` for real FLUX.1-dev image generation; Groq Whisper STT / Orpheus TTS are
> stubbed pending key + audio wiring. Artifacts are written under
> `workspace/{docs,frontend,backend,presentations,reports}`.

### Artifacts + media backend (`backend/app/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/services/artifacts.py` (`ArtifactService` + `get_artifact_service`; files each agent output under workspace SUBDIRS by agent + writes `reports/<wf>/run.md` via the path-jailed FileManager) | backend-eng | source | 8 | DONE |
| `backend/app/schemas/workspace.py` (`Artifact`, `ArtifactContent`) + re-export in `schemas/__init__.py` | api-eng | source | 8 | DONE |
| `backend/app/api/routes/workspace.py` (`GET /artifacts`, `GET /artifacts/{path}`; mounted `/workspace`) | api-eng | source | 8 | DONE |
| `backend/app/schemas/orchestration.py` (added `AgentRunOutput.artifacts`) | api-eng | source | 8 | DONE |
| `backend/app/services/orchestrator.py` (edited — `persist_run` in `run_workflow` + `resume_workflow`) | backend-eng | source | 8 | DONE |
| `backend/app/services/media.py` (`MediaService`: `generate_image` via HuggingFace FLUX.1-dev when configured else stub placeholder; `transcribe`/`synthesize` stub-safe) | backend-eng | source | 8 | DONE |
| `backend/app/schemas/media.py` (media request/response DTOs) | api-eng | source | 8 | DONE |
| `backend/app/api/routes/media.py` (`POST /api/media/image`, `/tts`, `/stt`; mounted `/media`) | api-eng | source | 8 | DONE |
| `backend/app/api/router.py` (edited — added workspace + media routers) | api-eng | source | 8 | DONE |
| `backend/tests/test_workspace_artifacts.py` (workspace artifacts tests) | qa | source | 8 | DONE |
| `backend/tests/test_media.py` (media stub tests) | qa | source | 8 | DONE |

### Artifacts explorer frontend (`frontend/src/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/lib/api/types.ts` (added `Artifact`, `ArtifactContent`) | frontend-eng | source | 8 | DONE |
| `frontend/src/lib/api/artifacts.ts` (`listArtifacts`, `readArtifact`) | frontend-eng | source | 8 | DONE |
| `frontend/src/hooks/useArtifacts.ts` | frontend-eng | source | 8 | DONE |
| `frontend/src/components/workspace/artifact-explorer.tsx` (two-pane list + viewer) | frontend-eng | source | 8 | DONE |
| `frontend/src/pages/Workspace.tsx` | frontend-eng | source | 8 | DONE |
| `frontend/src/pages/Documents.tsx` | frontend-eng | source | 8 | DONE |
| `frontend/src/App.tsx` (edited — `/workspace` → `Workspace`, `/documents` → `Documents`; both removed from Placeholder) | frontend-eng | source | 8 | DONE |
| `frontend/src/test/smoke.test.tsx` (asserts `/workspace` renders) | qa | source | 8 | DONE |

### Drafted content/media artifacts (Workspace Rule sandbox)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `workspace/{docs,frontend,backend,presentations,reports}/*` (per-agent outputs + `reports/<wf>/run.md`) | various | workspace | 8 | DONE |

---

## Phase 9 — Knowledge base + memory (pgvector) + RAG (DONE)

> Built and validated: `pytest` = **55 passed, 0 failed** (45 prior + 10 new —
> `tests/test_vectorstore.py` + `tests/test_knowledge.py` + `tests/test_memory_rag.py`: vector store +
> knowledge + memory/RAG); live **verified** — KB search retrieves relevant docs; a workflow run stores
> each agent output as memory; `ingest-workspace` indexes artifacts; memory recall returns prior-run
> content (the company learns from prior work). Frontend still green (`npm run lint` exit 0,
> `npm run build` exit 0, `npm run test` vitest **9/9** — smoke now asserts `/knowledge` + `/memory`
> render). Mechanism: `app/services/vectorstore.py` = a deterministic 256-dim hashing embedder (offline,
> no key) + a cosine `VectorStore` persisted to `workspace/.state/vectors/<name>.json`;
> `KnowledgeService` (knowledge corpus + `ingest_workspace`) and `MemoryService` (agent memory). RAG:
> `app/graph/nodes/delegate.py` recalls memory into each agent's context (`recall_context`);
> `app/services/orchestrator.py` (`_persist_artifacts_and_memory`) stores every successful output as
> memory after run/resume.
>
> **Operational note (local offline embedder):** embeddings are a local offline hashing embedder (256-d)
> by default — no key required; stores persist under `workspace/.state/vectors/`. The Supabase pgvector
> path (1536-d, `match_knowledge`/`match_memory`) is the optional durable backend and needs a real
> embedding model + Supabase; the local store is the zero-config default.

### Knowledge + memory + RAG backend (`backend/app/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/services/vectorstore.py` (deterministic 256-dim hashing embedder + cosine `VectorStore` persisted to `workspace/.state/vectors/<name>.json`) | backend-eng | source | 9 | DONE |
| `backend/app/services/knowledge.py` (`KnowledgeService`: knowledge corpus + `ingest_workspace`) | backend-eng | source | 9 | DONE |
| `backend/app/services/memory.py` (`MemoryService`: agent memory) | backend-eng | source | 9 | DONE |
| `backend/app/schemas/knowledge.py` (knowledge/memory DTOs) + re-export in `schemas/__init__.py` | api-eng | source | 9 | DONE |
| `backend/app/api/routes/knowledge.py` (search/add/ingest-workspace/stats; mounted `/knowledge`) | api-eng | source | 9 | DONE |
| `backend/app/api/routes/memory.py` (search/recent/stats; mounted `/memory`) | api-eng | source | 9 | DONE |
| `backend/app/api/router.py` (edited — added knowledge + memory routers) | api-eng | source | 9 | DONE |
| `backend/app/graph/nodes/delegate.py` (edited — `recall_context` recalls memory into each agent's context for RAG) | backend-eng | source | 9 | DONE |
| `backend/app/services/orchestrator.py` (edited — `_persist_artifacts_and_memory` stores every successful output as memory after run/resume) | backend-eng | source | 9 | DONE |
| `backend/tests/test_vectorstore.py` (vector store tests) | qa | source | 9 | DONE |
| `backend/tests/test_knowledge.py` (knowledge tests) | qa | source | 9 | DONE |
| `backend/tests/test_memory_rag.py` (memory/RAG tests) | qa | source | 9 | DONE |

### Knowledge + memory frontend (`frontend/src/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/lib/api/types.ts` (added `SearchHit`, `MemoryEntry`, `StoreStats`, `IngestResult`) | frontend-eng | source | 9 | DONE |
| `frontend/src/lib/api/knowledge.ts` (knowledge + memory API) | frontend-eng | source | 9 | DONE |
| `frontend/src/hooks/useKnowledge.ts` | frontend-eng | source | 9 | DONE |
| `frontend/src/hooks/useMemory.ts` | frontend-eng | source | 9 | DONE |
| `frontend/src/pages/KnowledgeBase.tsx` | frontend-eng | source | 9 | DONE |
| `frontend/src/pages/Memory.tsx` | frontend-eng | source | 9 | DONE |
| `frontend/src/App.tsx` (edited — `/knowledge` → `KnowledgeBase`, `/memory` → `Memory`) | frontend-eng | source | 9 | DONE |
| `frontend/src/test/smoke.test.tsx` (asserts `/knowledge` + `/memory` render) | qa | source | 9 | DONE |

---

## Phase 10 — Polish + auth + deploy + hardening (DONE — FINAL)

> Built and validated: `pytest` = **62 passed, 0 failed** (55 prior + 7 new —
> `tests/test_auth.py` + `tests/test_security.py`: signed-token auth + `require_user` gating +
> hardening middleware); frontend green (`npm run build` exit 0, `npm run lint` 0 warnings,
> `npm run test` vitest **12/12**). Auth + hardening: `app/core/security.py` (stdlib HMAC signed
> tokens), `app/api/deps.py` `require_user` (open in dev, Bearer-enforced when `AUTH_ENABLED`),
> `app/api/routes/auth.py` (`/api/auth/config|login|me`); sensitive POSTs (`workflows/run`, approvals
> `decision`, knowledge `add`+`ingest`) depend on `require_user`; `app/main.py` `hardening_middleware`
> (security headers always; opt-in per-IP rate limit). Frontend auth gate + axios bearer interceptor;
> deploy docs (`docs/DEPLOYMENT.md` new + `README.md` rewrite). Post-build polish/fixes: dashboard
> layout fix (`sidebar.tsx` `position:fixed` → in-flow sticky grid item), dev proxy noise fix
> (`vite.config.ts`), websockets dependency fix (`requirements.txt`), and an animation foundation
> (`lib/motion.ts` + `common/{reveal,count-up}.tsx`) applied across ~24 components.
>
> **Operational note (offline-first; auth opt-in):** the whole product runs OFFLINE in stub mode (no
> keys/Supabase needed). Real providers/Supabase/auth activate via `backend/.env`. New settings:
> `auth_enabled` (false), `admin_username`/`admin_password`, `token_ttl_seconds`,
> `security_headers_enabled` (true), `rate_limit_enabled` (false), `rate_limit_per_minute`.

### Auth + hardening backend (`backend/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `backend/app/core/security.py` (stdlib HMAC signed tokens: `create_token`/`verify_token`/`verify_credentials`) | secops | source | 10 | DONE |
| `backend/app/api/deps.py` (edited — `require_user`: open in dev, Bearer-enforced when `AUTH_ENABLED`) | secops | source | 10 | DONE |
| `backend/app/api/routes/auth.py` (`/api/auth/config`, `/api/auth/login`, `/api/auth/me`; mounted `/auth`) | api-eng | source | 10 | DONE |
| `backend/app/api/routes/workflows.py` (edited — `POST /run` depends on `require_user`) | api-eng | source | 10 | DONE |
| `backend/app/api/routes/approvals.py` (edited — `POST /{id}/decision` depends on `require_user`) | api-eng | source | 10 | DONE |
| `backend/app/api/routes/knowledge.py` (edited — `add` + `ingest-workspace` depend on `require_user`) | api-eng | source | 10 | DONE |
| `backend/app/api/router.py` (edited — added auth router) | api-eng | source | 10 | DONE |
| `backend/app/main.py` (edited — `hardening_middleware`: security headers always; opt-in per-IP rate limit) | secops | source | 10 | DONE |
| `backend/app/core/config.py` (edited — `auth_enabled`, `admin_username`/`admin_password`, `token_ttl_seconds`, `security_headers_enabled`, `rate_limit_enabled`, `rate_limit_per_minute`) | secops | source | 10 | DONE |
| `backend/requirements.txt` (edited — `websockets==16.0` → `websockets>=12,<16`; resolves the supabase 2.30.1 conflict) | backend-eng | source | 10 | DONE |
| `backend/tests/test_auth.py` (signed-token auth + `require_user` gating tests) | qa | source | 10 | DONE |
| `backend/tests/test_security.py` (HMAC token create/verify + hardening middleware tests) | qa | source | 10 | DONE |

### Auth gate + error boundary + settings frontend (`frontend/src/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/store/auth.ts` (auth Zustand store) | frontend-eng | source | 10 | DONE |
| `frontend/src/lib/api/auth.ts` (auth config/login/me API) | frontend-eng | source | 10 | DONE |
| `frontend/src/hooks/useAuth.ts` | frontend-eng | source | 10 | DONE |
| `frontend/src/pages/Login.tsx` | frontend-eng | source | 10 | DONE |
| `frontend/src/components/auth/auth-gate.tsx` | frontend-eng | source | 10 | DONE |
| `frontend/src/components/common/error-boundary.tsx` | frontend-eng | source | 10 | DONE |
| `frontend/src/pages/Settings.tsx` | frontend-eng | source | 10 | DONE |
| `frontend/src/lib/api/client.ts` (edited — axios bearer interceptor) | frontend-eng | source | 10 | DONE |
| `frontend/src/App.tsx` (edited — wires auth gate + error boundary + Settings route) | frontend-eng | source | 10 | DONE |
| `frontend/src/main.tsx` (edited — auth gate / error-boundary wiring) | frontend-eng | source | 10 | DONE |
| `frontend/src/test/smoke.test.tsx` (edited — asserts auth gate / Login render; 12 tests total) | qa | source | 10 | DONE |

### Animation foundation + polish/fixes frontend (`frontend/src/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `frontend/src/lib/motion.ts` (motion foundation; reduced-motion aware) | designer | source | 10 | DONE |
| `frontend/src/components/common/reveal.tsx` (`Reveal`/`Stagger`/`StaggerItem`) | designer | source | 10 | DONE |
| `frontend/src/components/common/count-up.tsx` (`CountUp`; reduced-motion aware) | designer | source | 10 | DONE |
| `frontend/src/components/layout/sidebar.tsx` (FIX — `position:fixed` → in-flow sticky grid item, `md:flex`, fills its 248px/72px track; + nav micro-motion via `MotionNavLink`) | frontend-eng | source | 10 | DONE |
| `frontend/vite.config.ts` (FIX — swallows `/api` + `/ws` proxy `ECONNREFUSED`/`ECONNABORTED` noise when the backend dev server isn't running) | frontend-eng | source | 10 | DONE |
| `frontend/src/{pages/Dashboard,components/dashboard/*,components/layout/{app-layout,right-rail}}.tsx` (~24 components animated — section cascade, ExecutiveOverview/StatCard count-up + stagger, AgentStatusGrid/AgentCard, WorkflowList, chart reveals, usage/media/achievements stagger+hover, route-change motion, ActivityFeed stagger, BrandFooterCard float, Login entrance) | frontend-eng / designer | source | 10 | DONE |

### Deploy docs (`docs/`)
| Path | Owner | Tree | Phase | Status |
|---|---|---|---|---|
| `docs/DEPLOYMENT.md` (new — deploy/run/hardening guide) | secops / docs | source | 10 | DONE |
| `README.md` (rewritten — product overview + run/deploy quickstart) | docs | source | 10 | DONE |

---

## Post-1.0 — feature/component parity + review hardening (DONE)

> Additive over the 10-phase 1.0 (`cp-0010-phase10-polish`). Eleven approval-free post-1.0 checkpoints
> (`cp-0011..cp-0021`, see `docs/CHECKPOINTS.md`) brought the product to full feature/component parity,
> applied two lead-engineer reviews, partitioned the workspace per project, and built the social content
> pipeline (compose → render → human-approve → publish, with a real YouTube uploader). These are tagged
> `phase = post-1.0` and `cp` = the originating checkpoint. Current validation across the post-1.0 work:
> backend `pytest` **112 passed, 1 skipped** (the skipped test is a guarded real-render test that runs
> only when the optional render engine is installed); frontend `vite build` exit 0 +
> `eslint --max-warnings 0` exit 0 + vitest **17/17**. All files below were enumerated from the live
> source tree.

### cp-0011 — Remaining nav pages + Agent Hierarchy Tree (`frontend/src/` + `backend/`)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `frontend/src/pages/Agents.tsx` (roster grouped by department + Grid/Hierarchy toggle) | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/components/agents/agent-hierarchy-tree.tsx` (React Flow CEO → department → agent org chart; fitView + Controls + MiniMap) | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/pages/Workflows.tsx` (RunTask + active workflows + run-history drill-down) | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/pages/Approvals.tsx` (full-page live gate reusing PendingApprovals) | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/pages/departments/Department.tsx` (slug-driven agent roster; backs Departments ×7) | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/pages/Logs.tsx` (recent activity + memory) | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/pages/Integrations.tsx` (provider/Supabase/auth status) | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/pages/Billing.tsx` (cost + provider/model usage) | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/lib/api/agents.ts` | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/lib/api/system.ts` (providers/info; `listCheckpoints` added in cp-0013) | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/lib/api/workflows.ts` (edited — `listRuns`/`getRun`/`listActiveWorkflows`) | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/hooks/useAgents.ts` | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/hooks/useWorkflowRuns.ts` | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/hooks/useSystem.ts` (`useCheckpoints` added in cp-0013) | frontend-eng | source | cp-0011 | DONE |
| `frontend/src/App.tsx` (edited — wired the new routes; only `/projects` + `/tasks` remained Placeholder at this checkpoint) | frontend-eng | source | cp-0011 | DONE |
| `backend/app/api/routes/system.py` (edited — `GET /api/system/providers` + `GET /api/system/info`; `GET /checkpoints` added in cp-0013) | api-eng | source | cp-0011 | DONE |

### cp-0012 — Projects & Tasks (full-stack) + deferred hardening (`backend/` + `frontend/src/`)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `backend/app/services/project_store.py` (`ProjectStore`; JSON-persisted, seeded 3 projects/7 tasks; `threading.RLock` added in cp-0014) | backend-eng | source | cp-0012 | DONE |
| `backend/app/schemas/projects.py` (Projects/Tasks DTOs) | api-eng | source | cp-0012 | DONE |
| `backend/app/api/routes/projects.py` (CRUD; mutations auth-gated when `AUTH_ENABLED`) | api-eng | source | cp-0012 | DONE |
| `backend/app/api/routes/tasks.py` (CRUD; mutations auth-gated when `AUTH_ENABLED`) | api-eng | source | cp-0012 | DONE |
| `backend/app/api/router.py` (edited — added projects + tasks routers) | api-eng | source | cp-0012 | DONE |
| `backend/app/providers/base.py` (edited — `provider_max_retries` wired into `with_provider_retry`, single source of truth) | backend-eng | source | cp-0012 | DONE |
| `backend/tests/test_projects_tasks.py` (5 new tests) | qa | source | cp-0012 | DONE |
| `backend/tests/test_seed_sync.py` (3 new tests — `seed.sql`↔agent-registry drift-guard) | qa | source | cp-0012 | DONE |
| `frontend/src/lib/api/projects.ts` (projects + tasks API) | frontend-eng | source | cp-0012 | DONE |
| `frontend/src/hooks/useProjects.ts` | frontend-eng | source | cp-0012 | DONE |
| `frontend/src/hooks/useTasks.ts` | frontend-eng | source | cp-0012 | DONE |
| `frontend/src/pages/Projects.tsx` (project board + create/delete) | frontend-eng | source | cp-0012 | DONE |
| `frontend/src/pages/Tasks.tsx` (4-column Kanban; create/move/delete) | frontend-eng | source | cp-0012 | DONE |
| `frontend/src/App.tsx` (edited — wired `/projects` + `/tasks`; **removed the `Placeholder` import** → no Placeholder routes remain) | frontend-eng | source | cp-0012 | DONE |

### cp-0013 — Design-doc "center" panels (completes the component inventory) (`frontend/src/` + `backend/`)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `frontend/src/pages/centers/SecurityCenter.tsx` (Quality & Security dept; backs `/departments/quality`) | frontend-eng | source | cp-0013 | DONE |
| `frontend/src/pages/centers/MarketingCenter.tsx` (backs `/departments/marketing`) | frontend-eng | source | cp-0013 | DONE |
| `frontend/src/pages/centers/DocumentationCenter.tsx` (backs `/departments/documentation`) | frontend-eng | source | cp-0013 | DONE |
| `frontend/src/components/dashboard/recovery-status.tsx` (`RecoveryStatus`; resumable awaiting runs + `cp-NNNN` checkpoint lineage; on Workflows page) | frontend-eng | source | cp-0013 | DONE |
| `frontend/src/components/dashboard/memory-usage-panel.tsx` (`MemoryUsagePanel`; memory + knowledge store sizes + recent memory; atop Memory page) | frontend-eng | source | cp-0013 | DONE |
| `frontend/src/pages/Workflows.tsx` (edited — hosts `RecoveryStatus`) | frontend-eng | source | cp-0013 | DONE |
| `frontend/src/pages/Memory.tsx` (edited — hosts `MemoryUsagePanel`) | frontend-eng | source | cp-0013 | DONE |
| `frontend/src/lib/api/system.ts` (edited — `listCheckpoints`) | frontend-eng | source | cp-0013 | DONE |
| `frontend/src/hooks/useSystem.ts` (edited — `useCheckpoints`) | frontend-eng | source | cp-0013 | DONE |
| `frontend/src/App.tsx` (edited — `/departments/quality` → `SecurityCenter`, `/departments/marketing` → `MarketingCenter`, `/departments/documentation` → `DocumentationCenter`) | frontend-eng | source | cp-0013 | DONE |
| `backend/app/api/routes/system.py` (edited — `GET /api/system/checkpoints`) | api-eng | source | cp-0013 | DONE |

### cp-0014 — Applied the full-system lead-engineer review (verdict SHIP) (`backend/` + `docs/`)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `backend/app/services/workflow_store.py` (edited — `_path` jail rejects `/`, `\`, NUL, `..`; `get()` → clean 404; fixes a **HIGH** path-traversal on `GET /api/workflows/runs/{workflow_id}`) | secops / backend-eng | source | cp-0014 | DONE |
| `backend/app/checkpoint/store.py` (edited — `_safe_id` jail on `_state_file` + `checkpoint()`; defense-in-depth) | secops / backend-eng | source | cp-0014 | DONE |
| `backend/app/services/orchestrator.py` (edited — stable memory id `mem:{workflow_id}:{agent_id}` so approve/retry upserts instead of duplicating) | backend-eng | source | cp-0014 | DONE |
| `backend/app/services/memory.py` (edited — `MemoryService.remember` accepts `id`) | backend-eng | source | cp-0014 | DONE |
| `backend/app/services/vectorstore.py` (edited — `VectorStore.add` accepts `id`; `threading.RLock` around `add`/`clear`) | backend-eng | source | cp-0014 | DONE |
| `backend/app/services/project_store.py` (edited — `threading.RLock` around `create`/`update`/`delete`) | backend-eng | source | cp-0014 | DONE |
| `README.md` (edited — test counts 55 → 70) | docs | source | cp-0014 | DONE |
| `docs/DEPLOYMENT.md` (edited — test counts 55 → 70) | docs | source | cp-0014 | DONE |
| `docs/{PROJECT_STATE,FILE_MANIFEST,CHECKPOINTS,ROADMAP}.md` (reconciled current through cp-0014) | ceo / docs | source | cp-0014 | DONE |
| `backend/_audit_recursion.py` (auditor scratch file) | qa | source | cp-0014 | REMOVED |

### cp-0015 — Per-project workspace partition + cascade hard-delete + project switcher (`backend/` + `frontend/src/`)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `backend/app/workspace_fs/paths.py` (NEW — per-project layout: `DEFAULT_PROJECT="__default__"`, path-jailed `safe_project_id`, `project_root`, `list_project_dir_ids`, `purge_project_workspace`, `reset_caches`, one-time `migrate_flat_workspace`) | backend-eng | source | cp-0015 | DONE |
| `backend/app/services/{artifacts,memory,knowledge,workflow_store}.py` (edited — store singletons → `@lru_cache` project-keyed factories `get_*_service`/`get_workflow_store(project_id=DEFAULT_PROJECT)`; `workflow_store` gained module-level `find_run`/`find_by_approval` that scan all projects) | backend-eng | source | cp-0015 | DONE |
| `backend/app/services/orchestrator.py` (edited — threads the project through run + resume; `RunResult` carries `projectId`; resume persists artifacts/memory back to the OWNING project) | backend-eng | source | cp-0015 | DONE |
| `backend/app/services/project_store.py` (edited — `delete_project` → `purge_project_workspace` cascade hard-delete; seeds the never-deletable Default Workspace `__default__`) | backend-eng | source | cp-0015 | DONE |
| `backend/app/api/deps.py` (edited — new `get_project_id`: reads `X-Project-Id` header / `?projectId=`, path-jails it, AND rejects unknown/deleted projects with 404) | api-eng | source | cp-0015 | DONE |
| `backend/app/api/routes/{workspace,memory,knowledge,workflows,media}.py` (edited — scope via `get_project_id`; `/workflows/run` uses ONLY the header — the body `projectId` override was removed) | api-eng | source | cp-0015 | DONE |
| `backend/app/schemas/orchestration.py` (edited — `RunResult.projectId`; `RunRequest` no longer has `project_id`) | api-eng | source | cp-0015 | DONE |
| `backend/app/graph/nodes/delegate.py` (edited — project-scoped memory recall) | backend-eng | source | cp-0015 | DONE |
| `backend/app/main.py` (edited — runs `migrate_flat_workspace` once on startup, idempotent via `.state/.migrated_v2_projects`) | backend-eng | source | cp-0015 | DONE |
| `backend/tests/test_project_isolation.py` (NEW — per-project isolation + cascade hard-delete + unknown-project-404 + default-not-deletable + path-jail) | qa | source | cp-0015 | DONE |
| `backend/tests/test_workspace_paths.py` (NEW — `safe_project_id`, purge jail, `_merge_move`, migration with real data + idempotence + fresh-install no-op) | qa | source | cp-0015 | DONE |
| `frontend/src/store/project.ts` (NEW — active-project zustand store, persisted to localStorage) | frontend-eng | source | cp-0015 | DONE |
| `frontend/src/lib/api/client.ts` (edited — axios interceptor sends `X-Project-Id` on every request) | frontend-eng | source | cp-0015 | DONE |
| `frontend/src/hooks/{useArtifacts,useMemory,useKnowledge,useWorkflowRuns,useApprovals}.ts` (edited — project-scoped React Query keys) | frontend-eng | source | cp-0015 | DONE |
| `frontend/src/hooks/useProjects.ts` (edited — `deleteProject` falls back to Default when the active project is deleted) | frontend-eng | source | cp-0015 | DONE |
| `frontend/src/components/layout/project-switcher.tsx` (NEW — topbar `ProjectSwitcher`: switch / inline create / two-step delete-confirm) | frontend-eng | source | cp-0015 | DONE |
| `frontend/src/pages/Tasks.tsx` (edited — Tasks board scoped to the active project) | frontend-eng | source | cp-0015 | DONE |
| `frontend/src/lib/api/types.ts` (edited — `RunResult` type gained `projectId`) | frontend-eng | source | cp-0015 | DONE |
| `frontend/src/test/project-switcher.test.tsx` (NEW — switch / inline create / two-step delete-confirm) | qa | source | cp-0015 | DONE |
| `.gitignore` (edited — added `workspace/projects/` + `workspace/.state/.migrated_v2_projects`; per-project runtime trees are not tracked) | architect | source | cp-0015 | DONE |
| `docs/{PROJECT_STATE,FILE_MANIFEST,CHECKPOINTS,ROADMAP}.md` (reconciled current through cp-0015) | ceo / docs | source | cp-0015 | DONE |

### cp-0016 — Social content pipeline backend foundation (offline/stub-first) (`backend/`)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `backend/app/schemas/social.py` (NEW — `ReelScene`/`ReelStoryboard`, `SocialDraft`, `PublishResult`, request + decision DTOs) | api-eng | source | cp-0016 | DONE |
| `backend/app/services/social.py` (NEW — `SocialService`: `draft_reel` storyboard + stub voiceover + `storyboard.json`/`reel.md`; `draft_post` caption+hashtags + stub-safe FLUX image; `decide(approve|reject)`) | backend-eng | source | cp-0016 | DONE |
| `backend/app/services/social_store.py` (NEW — per-project `SocialDraftStore` under `.state/social/`, project-keyed factory, path-jailed ids; `threading.RLock` added in cp-0021) | backend-eng | source | cp-0016 | DONE |
| `backend/app/services/publishers.py` (NEW — stub platform publishers youtube/instagram for reels, facebook/linkedin/twitter for posts; `is_configured` from the optional config keys; `publish_to` dispatch added in cp-0020) | backend-eng | source | cp-0016 | DONE |
| `backend/app/api/routes/social.py` (NEW — `POST /reel`, `POST /post`, `GET /drafts`, `GET /drafts/{id}`, decision; project-scoped via `get_project_id`) | api-eng | source | cp-0016 | DONE |
| `backend/app/api/router.py` (edited — mounted `/social`) | api-eng | source | cp-0016 | DONE |
| `backend/app/core/config.py` (edited — PEXELS/YOUTUBE/INSTAGRAM/FACEBOOK/LINKEDIN/TWITTER keys) | backend-eng | source | cp-0016 | DONE |
| `backend/.env.example` (edited — social/publisher key placeholders) | backend-eng | source | cp-0016 | DONE |
| `backend/app/workspace_fs/paths.py` (edited — `reset_caches` now evicts the social store) | backend-eng | source | cp-0016 | DONE |
| `backend/tests/test_social.py` (NEW — draft/decide/publish flow; render + youtube + cascade-delete tests added in cp-0018/cp-0020/cp-0021) | qa | source | cp-0016 | DONE |

### cp-0017 — Social Studio frontend (compose → draft → preview → approve/reject) (`frontend/src/`)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `frontend/src/pages/Social.tsx` (NEW — Social Studio: composer + draft cards w/ storyboard or caption preview + Approve & publish / Reject + publish results; render UX added in cp-0019) | frontend-eng | source | cp-0017 | DONE |
| `frontend/src/lib/api/social.ts` (NEW — `draftReel`/`draftPost`/`listDrafts`/`decideDraft`; `renderDraft`/`mediaUrl` added in cp-0019) | frontend-eng | source | cp-0017 | DONE |
| `frontend/src/hooks/useSocial.ts` (NEW — `useSocialDrafts` polled + `useDraftReel`/`useDraftPost`/`useDecideDraft`, project-scoped keys; `useRenderDraft` added in cp-0019) | frontend-eng | source | cp-0017 | DONE |
| `frontend/src/lib/api/types.ts` (edited — social wire types; render fields added in cp-0019) | frontend-eng | source | cp-0017 | DONE |
| `frontend/src/config/navigation.ts` (edited — Social Studio nav entry, Clapperboard/violet) | frontend-eng | source | cp-0017 | DONE |
| `frontend/src/App.tsx` (edited — `/social` → `Social`) | frontend-eng | source | cp-0017 | DONE |
| `frontend/src/test/smoke.test.tsx` (edited — asserts `/social` renders; 17 tests total) | qa | source | cp-0017 | DONE |

### cp-0018 — Real reel render engine (MoviePy + Pexels + Orpheus, async, stub-safe) (`backend/`)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `backend/app/services/reel_render.py` (NEW — MoviePy+Pillow engine, import-guarded, 3-level degradation ladder; closes every clip before unlinking temp PNGs for Windows file-handle safety) | backend-eng | source | cp-0018 | DONE |
| `backend/app/services/pexels.py` (NEW — stub-safe Pexels Video API stock-clip fetch) | backend-eng | source | cp-0018 | DONE |
| `backend/app/services/media.py` (edited — `generate_voiceover`) | backend-eng | source | cp-0018 | DONE |
| `backend/app/providers/huggingface.py` (edited — `generate_audio`, Orpheus, guarded) | backend-eng | source | cp-0018 | DONE |
| `backend/app/services/social.py` (edited — async `begin_render`/`run_render`) | backend-eng | source | cp-0018 | DONE |
| `backend/app/api/routes/social.py` (edited — `POST /drafts/{id}/render` BackgroundTask) | api-eng | source | cp-0018 | DONE |
| `backend/app/schemas/social.py` (edited — `render_status`/`video_path`/`render_note`) | api-eng | source | cp-0018 | DONE |
| `backend/requirements-render.txt` (NEW — OPTIONAL render engine deps: moviepy, imageio-ffmpeg, Pillow; core install stays lean) | backend-eng | source | cp-0018 | DONE |
| `backend/requirements.txt` (edited — note pointing at the optional render extras) | backend-eng | source | cp-0018 | DONE |
| `backend/tests/test_social.py` (edited — render flow + guarded real-render (skipped without the engine) + deletion-race tests) | qa | source | cp-0018 | DONE |

### cp-0019 — Frontend render UX + binary media endpoint (`backend/` + `frontend/src/`)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `backend/app/api/routes/workspace.py` (edited — `GET /api/workspace/media/{path:path}` streams a binary artifact via `FileResponse`, project-scoped via `?projectId=`) | api-eng | source | cp-0019 | DONE |
| `backend/app/workspace_fs/file_manager.py` (edited — `media_file` path-jailed lookup; `WorkspaceViolationError`→400, missing→404) | backend-eng | source | cp-0019 | DONE |
| `backend/tests/test_workspace_artifacts.py` (edited — media serve + parametrized path-traversal route tests) | qa | source | cp-0019 | DONE |
| `frontend/src/pages/Social.tsx` (edited — Render button + render status + inline `<video>` player + inline post `<img>`) | frontend-eng | source | cp-0019 | DONE |
| `frontend/src/lib/api/social.ts` (edited — `renderDraft` + `mediaUrl(path, projectId)`) | frontend-eng | source | cp-0019 | DONE |
| `frontend/src/hooks/useSocial.ts` (edited — `useRenderDraft`, invalidates the social queries) | frontend-eng | source | cp-0019 | DONE |
| `frontend/src/lib/api/types.ts` (edited — `SocialDraft` gained `renderStatus`/`videoPath`/`renderNote`) | frontend-eng | source | cp-0019 | DONE |

### cp-0020 — Real platform uploader #1: YouTube (OAuth resumable upload) (`backend/` + `docs/`)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `backend/app/services/youtube.py` (NEW — OAuth2 refresh-token → access token → YouTube Data API v3 resumable `.mp4` upload, `privacyStatus=private`, guarded + stub-safe + never-raises) | backend-eng | source | cp-0020 | DONE |
| `backend/app/services/publishers.py` (edited — `publish_to(platform, draft)` dispatch: youtube → real, the other four → stubs) | backend-eng | source | cp-0020 | DONE |
| `backend/app/services/social.py` (edited — `decide` passes the full draft to `publish_to`) | backend-eng | source | cp-0020 | DONE |
| `backend/app/core/config.py` (edited — YouTube OAuth trio `youtube_client_id`/`youtube_client_secret`/`youtube_refresh_token`, replacing the unused `youtube_api_key`) | backend-eng | source | cp-0020 | DONE |
| `backend/.env.example` (edited — YouTube OAuth trio) | backend-eng | source | cp-0020 | DONE |
| `docs/SOCIAL_PUBLISHING.md` (NEW — one-time refresh-token setup, quota notes, per-platform status) | docs / secops | source | cp-0020 | DONE |
| `backend/tests/test_social.py` (edited — youtube stub-mode test) | qa | source | cp-0020 | DONE |

### cp-0021 — Full-system review (cp-0015..cp-0020) + concurrency hardening (`backend/`)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `backend/app/services/workflow_store.py` (edited — `threading.RLock` guarding all JSON read/write; missed by cp-0014) | backend-eng | source | cp-0021 | DONE |
| `backend/app/services/social_store.py` (edited — `threading.RLock` guarding all JSON read/write) | backend-eng | source | cp-0021 | DONE |
| `backend/app/services/social.py` (edited — `begin_render` only renders a draft still `status='awaiting_approval'`; closes the render-vs-decide race) | backend-eng | source | cp-0021 | DONE |
| `backend/app/api/routes/social.py` (edited — `/render` returns 400 unless the draft is awaiting approval) | api-eng | source | cp-0021 | DONE |
| `backend/tests/test_social.py` (edited — social cascade-delete test: deleting a project purges its `.state/social` subtree) | qa | source | cp-0021 | DONE |
| `docs/{PROJECT_STATE,FILE_MANIFEST,CHECKPOINTS,ROADMAP}.md` (reconciled current through cp-0021) | ceo / docs | source | cp-0021 | DONE |

### Orphan note (audit follow-up)
| Path | Owner | Tree | cp | Status |
|---|---|---|---|---|
| `frontend/src/pages/Placeholder.tsx` (orphaned after cp-0012 when `App.tsx` dropped the import; **deleted in cp-0014** — every route is now a real page) | frontend-eng | source | cp-0014 | REMOVED |

---

> **MANIFEST CURRENT THROUGH cp-0021.** All 10 phases plus the post-1.0 build-out (`cp-0011..cp-0013`),
> the first review-hardening pass (`cp-0014`), the per-project workspace partition (`cp-0015`), the full
> social content pipeline (`cp-0016..cp-0020`: backend foundation, Social Studio frontend, real reel
> render engine, render UX + binary media endpoint, the YouTube uploader), and the second full-system
> review + concurrency hardening (`cp-0021`) are on disk and validated; no rows remain `PENDING`. Every
> sidebar route is a real page and the entire `DESIGN_SYSTEM.md` component inventory is realized. The
> former `Placeholder.tsx` orphan was deleted in cp-0014, so no unused source files remain. The
> per-project runtime trees under `workspace/projects/` (and the `.state/.migrated_v2_projects` marker)
> are git-ignored, not manifest-tracked; `backend/requirements-render.txt` is the OPTIONAL render-engine
> extras (the core install stays lean). Current validation: backend `pytest` **112 passed, 1 skipped**
> (the skipped test is a guarded real-render test that runs only when the optional render engine is
> installed); frontend `vite build` exit 0 + `eslint --max-warnings 0` exit 0 + vitest **17/17**.

---

## Reconciliation rules
1. On resume, the orchestrator compares each file's stored hash to the actual file on disk.
2. Files present on disk but absent here ⇒ flagged `orphan` (Recovery Agent review).
3. Files here with status `DONE` but missing/changed on disk ⇒ flagged `drift`.
4. The aggregate SHA-256 of this file is written to `PROJECT_STATE` `omnivra-state.manifest_hash`.
5. `tree=workspace` entries must resolve under `WORKSPACE_DIR`; any path escaping it is rejected
   (Workspace Rule enforcement by `backend/app/workspace_fs/file_manager.py`).
6. The volatile mirror `workspace/.state/file_manifest.json` is regenerated from this durable doc;
   on conflict, this doc wins.
