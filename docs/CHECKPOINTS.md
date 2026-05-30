# CHECKPOINTS — Omnivra AI Company OS

> **Append-only** log of orchestration checkpoints. A checkpoint captures enough state to resume a
> LangGraph run (or a phased build) after an interruption (crash, kill-switch, manual pause, or
> Approval Gate hold).
>
> **Durability model:**
> - **Runtime (volatile, git-ignored):** the orchestrator writes the full state snapshot to
>   `workspace/.state/checkpoints/<checkpoint_id>.json` and updates
>   `workspace/.state/project_state.json`.
> - **Durable (git-tracked):** a compact summary row + JSON record is appended to THIS file so the
>   resume point survives even if the volatile workspace is wiped. On resume, prefer the runtime
>   snapshot; if absent, fall back to the JSON record here and have the Recovery Agent rehydrate.
>
> **Checkpoint ID format:** `cp-NNNN-<slug>` where `NNNN` is a zero-padded monotonic counter and
> `<slug>` is a short label (e.g. `cp-0001-phase1-foundation`, `cp-0002-design-shell`).
>
> **Never edit or delete past entries.** To invalidate one, append a new entry with `supersedes`
> pointing at it. Resume always uses the latest non-superseded checkpoint whose `status =
> "committed"`.

---

## Checkpoint Log

| # | Checkpoint ID | Workflow | Node | Phase | Status | Recursion | Created At |
|---|---|---|---|---|---|---|---|
| 1 | `cp-0001-phase1-foundation` | `bootstrap` | `phase1.foundation` | 1 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 2 | `cp-0002-phase2-design-system` | `bootstrap` | `phase2.design_system` | 2 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 3 | `cp-0003-phase3-dashboard` | `bootstrap` | `phase3.dashboard` | 3 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 4 | `cp-0004-phase4-data-api` | `bootstrap` | `phase4.data_api` | 4 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 5 | `cp-0005-phase5-orchestration` | `bootstrap` | `phase5.orchestration` | 5 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 6 | `cp-0006-phase6-realtime` | `bootstrap` | `phase6.realtime` | 6 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 7 | `cp-0007-phase7-approval` | `bootstrap` | `phase7.approval` | 7 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 8 | `cp-0008-phase8-artifacts` | `bootstrap` | `phase8.artifacts` | 8 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 9 | `cp-0009-phase9-knowledge` | `bootstrap` | `phase9.knowledge` | 9 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 10 | `cp-0010-phase10-polish` | `bootstrap` | `phase10.polish` | 10 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 11 | `cp-0011-pages-hierarchy` | `bootstrap` | `post1.pages_hierarchy` | post-1.0 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 12 | `cp-0012-projects-tasks` | `bootstrap` | `post1.projects_tasks` | post-1.0 | committed | 0/3 | 2026-05-30T00:00:00Z |
| 13 | `cp-0013-center-panels` | `bootstrap` | `post1.center_panels` | post-1.0 | committed | 0/3 | 2026-05-31T00:00:00Z |
| 14 | `cp-0014-post-review-hardening` | `bootstrap` | `post1.review_hardening` | post-1.0 | committed | 0/3 | 2026-05-31T00:00:00Z |

> **PROJECT COMPLETE — all 10 phases shipped, plus a post-1.0 build-out and a review-hardening pass.**
> `cp-0014-post-review-hardening` is the latest, committed checkpoint. After 1.0 (`cp-0010`), four
> additive, approval-free post-1.0 checkpoints (`cp-0011..cp-0014`) brought the product to full
> feature/component parity (every sidebar route is a real page; the entire `DESIGN_SYSTEM.md` component
> inventory is realized) and applied a full-system lead-engineer review (verdict SHIP). Current
> validation: backend `pytest` **70 passed**; frontend `vite build` exit 0 + `eslint --max-warnings 0`
> exit 0 + vitest **14/14**.

**Status legend:** `pending` (in flight) · `committed` (safe resume point) · `failed` ·
`superseded` · `rolled_back`.

---

## Checkpoint Records

Each committed checkpoint has a JSON record below. Fields:

| Field | Meaning |
|---|---|
| `id` | Checkpoint ID (`cp-NNNN-<slug>`). |
| `workflow_id` | Owning workflow (matches `PROJECT_STATE` active workflow). |
| `node` | Node / phase label that produced this checkpoint. |
| `status` | See status legend. |
| `recursion_count` / `recursion_limit` | Kill-switch counters at checkpoint time. |
| `phase` | Project phase active at checkpoint time. |
| `covers` | What this checkpoint guarantees (deliverables validated). |
| `state_ref` | Path to the volatile full-state snapshot. |
| `manifest_hash` | SHA-256 of `docs/FILE_MANIFEST.md` at checkpoint time. |
| `parent` | Previous checkpoint ID (chain), or `null` for the first. |
| `supersedes` | Checkpoint ID this entry invalidates, or `null`. |
| `approval` | `{ required, status }` for Approval-Gate-held checkpoints. |
| `resume_hint` | Human/agent note describing how to continue. |
| `rollback_hint` | How to roll back to / from this checkpoint. |
| `created_at` | ISO-8601 UTC timestamp. |

<!-- BEGIN omnivra-checkpoint cp-0001-phase1-foundation -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0001-phase1-foundation",
  "workflow_id": "bootstrap",
  "node": "phase1.foundation",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": 1,
  "covers": {
    "summary": "Phase 1 (Foundation) complete and validated: monorepo layout, frontend scaffold + design tokens, backend scaffold (FastAPI + provider/agent skeleton + LangGraph state/kill-switch + checkpoint store + path-jailed workspace FS), Supabase SQL (schema/rls/seed), and the durable control-plane docs.",
    "validation": {
      "backend_import": "ok (23 agents in app/agents/registry.py)",
      "backend_tests": "15 passed, 0 failed",
      "frontend_build": "pass (tsc && vite build)"
    },
    "key_paths": [
      "frontend/ (Vite+React+TS shell, tailwind.config.ts, src/index.css, src/styles/tokens.ts)",
      "backend/app/{main.py,core,providers,agents/registry.py,graph,checkpoint/store.py,workspace_fs/file_manager.py}",
      "supabase/{schema,rls,seed}.sql",
      "docs/{PROJECT_STATE,FILE_MANIFEST,CHECKPOINTS,ROADMAP,DESIGN_SYSTEM,SUPABASE_INTEGRATION}.md",
      "scripts/{setup,dev,state}.ps1"
    ]
  },
  "state_ref": "workspace/.state/checkpoints/cp-0001-phase1-foundation.json",
  "manifest_hash": "sha256:PENDING",
  "parent": null,
  "supersedes": null,
  "approval": { "required": true, "status": "awaiting" },
  "resume_hint": "Phase 1 is committed and awaiting human approval. On approval, advance PROJECT_STATE current_phase to 2 and begin 'Design system + UI primitives + layout shell': generate frontend/src/{config,types}, components/ui (shadcn), components/common, components/charts, and the AppLayout/Sidebar/Topbar/RightRail shell per FILE_MANIFEST Phase 2.",
  "rollback_hint": "This is the first checkpoint (parent=null); there is nothing earlier to roll back to. Re-validating Phase 1 (pytest + npm run build) re-establishes this point.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0001-phase1-foundation -->

<!-- BEGIN omnivra-checkpoint cp-0002-phase2-design-system -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0002-phase2-design-system",
  "workflow_id": "bootstrap",
  "node": "phase2.design_system",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": 2,
  "covers": {
    "summary": "Phase 2 (Design system + UI primitives + layout shell) complete and validated: typed foundation (types/config/store/styles), shadcn-style UI primitives, themed Recharts chart wrappers (OmniAreaChart/OmniDonutChart/BarMeter), and the AppLayout + Sidebar/Topbar/RightRail command-center shell. Dashboard page renders the Phase-2 showcase (previews/EmptyStates for upcoming sections) plus two live demos: an AI Agents Status tile grid from PRIMARY_AGENTS and a Task Distribution donut.",
    "validation": {
      "frontend_build": "exit 0 (tsc strict + vite build, 2580 modules)",
      "frontend_tests": "3 passed, 0 failed (vitest/jsdom render smoke — full app shell mounts)",
      "frontend_src_files": 42
    },
    "key_paths": [
      "frontend/src/{types/index.ts,lib/accents.ts,config/{navigation,agents}.ts,store/ui.ts,styles/tokens.ts}",
      "frontend/src/components/ui/* (glass-card,button,tooltip,scroll-area,dropdown-menu,avatar,separator,neon-badge,status-dot,icon-tile,chip,kbd-hint,progress-bar,section-header,sparkline,icon-button,timeframe-select,empty-state)",
      "frontend/src/components/ui/charts/{area-chart,donut-chart,bar-meter}.tsx",
      "frontend/src/components/layout/{brand-logo,sidebar,topbar,right-rail,app-layout}.tsx",
      "frontend/src/pages/{Dashboard,Placeholder}.tsx, App.tsx, providers/AppProviders.tsx, main.tsx",
      "frontend/{vitest.config.ts}, frontend/src/test/{setup.ts,smoke.test.tsx}"
    ]
  },
  "state_ref": "workspace/.state/checkpoints/cp-0002-phase2-design-system.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0001-phase1-foundation",
  "supersedes": null,
  "approval": { "required": true, "status": "awaiting" },
  "resume_hint": "Phase 2 is committed and awaiting human approval. On approval, advance PROJECT_STATE current_phase to 3 and begin 'Dashboard sections (mock data)': build every reference-dashboard section component (Executive Overview, AI Agents Status grid + System Ops row, Active Workflows, Task Execution Overview area chart, Task Distribution donut, Live Activity Feed, System Health, Model Usage By Provider, Top Models By Usage, Recent Achievements, brand footer, CommandPalette) bound to mock fixtures, replacing the Phase-2 previews/EmptyStates on the Dashboard page.",
  "rollback_hint": "To roll back to Phase 1, restore parent cp-0001-phase1-foundation: append a rolled_back entry superseding cp-0002, restore its state_ref, set PROJECT_STATE last_checkpoint_id to cp-0001 and revision++, and revert Phase-2 FILE_MANIFEST rows to PENDING (do not delete source files without an Approval-Gate decision). Re-validating Phase 2 (npm run build + npm run test) re-establishes this point.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0002-phase2-design-system -->

<!-- BEGIN omnivra-checkpoint cp-0003-phase3-dashboard -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0003-phase3-dashboard",
  "workflow_id": "bootstrap",
  "node": "phase3.dashboard",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": 3,
  "covers": {
    "summary": "Phase 3 (Dashboard sections, mock data) complete and validated: all reference dashboard sections built as props-driven components and wired to mock fixtures in src/data/dashboard.ts (types/index.ts extended for the dashboard data shapes). 22 components/dashboard/* sections; Dashboard.tsx rewritten to assemble the full main-column layout and layout/right-rail.tsx rewritten to host ActivityFeed + PendingApprovals + SystemHealth + BrandFooterCard (clock moved into GreetingHero). All 8 sections render on mock data: AI Agents Status, Active Workflows, Task Execution Overview, Task Distribution, Live Activity Feed, Pending Approvals, System Health, Recent Achievements.",
    "validation": {
      "frontend_lint": "exit 0 (eslint --max-warnings 0, clean)",
      "frontend_build": "exit 0 (tsc strict + vite build, 2609 modules)",
      "frontend_tests": "4 passed, 0 failed (vitest/jsdom render smoke — all 8 dashboard sections render on mock data + stat values + a workflow name)"
    },
    "key_paths": [
      "frontend/src/components/dashboard/* (date-time-status,stat-card,executive-overview,greeting-hero,agent-card,system-ops-row,agent-status-grid,workflow-row,workflow-list,task-execution-chart,task-distribution,provider-usage,model-usage,media-service-card,media-services,achievement-card,achievements,activity-feed,approval-card,pending-approvals,system-health,brand-footer-card)",
      "frontend/src/data/dashboard.ts (mock fixtures)",
      "frontend/src/types/index.ts (extended dashboard data shapes)",
      "frontend/src/pages/Dashboard.tsx (rewritten main-column assembler)",
      "frontend/src/components/layout/right-rail.tsx (rewritten right rail)",
      "frontend/.eslintrc.cjs, frontend/src/test/{setup.ts,smoke.test.tsx}"
    ]
  },
  "state_ref": "workspace/.state/checkpoints/cp-0003-phase3-dashboard.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0002-phase2-design-system",
  "supersedes": null,
  "approval": { "required": true, "status": "awaiting" },
  "resume_hint": "Phase 3 is committed and awaiting human approval. On approval, advance PROJECT_STATE current_phase to 4 and begin 'Backend data layer + REST API + Supabase wiring': build app/db client + repositories + app/api router/routes against Supabase, request/response schemas, frontend lib/api + lib/supabase + React Query hooks, then replace the frontend mock data in src/data/dashboard.ts with live /api endpoints. The dashboard sections are props-driven, so Phase 4 only swaps the data source at the assembler level.",
  "rollback_hint": "To roll back to Phase 2, restore parent cp-0002-phase2-design-system: append a rolled_back entry superseding cp-0003, restore its state_ref, set PROJECT_STATE last_checkpoint_id to cp-0002 and revision++, and revert Phase-3 FILE_MANIFEST rows to PENDING (do not delete source files without an Approval-Gate decision). Re-validating Phase 3 (npm run lint + npm run build + npm run test) re-establishes this point.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0003-phase3-dashboard -->

<!-- BEGIN omnivra-checkpoint cp-0004-phase4-data-api -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0004-phase4-data-api",
  "workflow_id": "bootstrap",
  "node": "phase4.data_api",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": 4,
  "covers": {
    "summary": "Phase 4 (Backend data layer + REST API + Supabase wiring) complete and validated. Pydantic DTOs (app/schemas, camelCase via to_camel; aggregate DashboardPayload); seed data layer (app/data: build_dashboard() + seed_agents()); Supabase client (app/db/client.py, lazy/optional) + repository abstraction (DashboardRepository Protocol, default SeedRepository, optional fail-safe SupabaseRepository, get_repository factory); REST router + routes (dashboard, agents, workflows, approvals, activity, system). Frontend lib/api/{client,types,icons,dashboard}.ts + hooks/useDashboard.ts; src/data/dashboard.ts gained a fallbackDashboard aggregate; Dashboard.tsx + layout/right-rail.tsx rewired to useDashboard(). Architecture: frontend -> /api (Vite proxy) -> FastAPI -> repository -> seed data (Supabase optional); the dashboard is now LIVE-data-driven with the bundled mock as instant fallback/initialData.",
    "validation": {
      "backend_tests": "25 passed, 0 failed (15 prior + 10 new tests/test_api.py)",
      "backend_live_curl": "verified end-to-end (GET /health 23 agents; GET /api/dashboard 17 camelCase keys agents=18/systemOps=5/totalTasks=124/totalPendingApprovals=7; /api/agents 23; /api/agents/ceo-manager google_ai/gemini-2.5-flash; /api/agents/nope 404; POST /api/approvals/{id}/decision stub received; /api/workflows 5; /api/activity 6; /api/system/health 6)",
      "frontend_build": "exit 0",
      "frontend_lint": "exit 0 (0 warnings)",
      "frontend_tests": "4 passed, 0 failed (vitest)"
    },
    "key_paths": [
      "backend/app/schemas/{__init__,dashboard}.py (Pydantic DTOs, camelCase via to_camel; DashboardPayload)",
      "backend/app/data/{__init__,seed}.py (build_dashboard() + seed_agents(); PROVIDER_LABEL/DEPARTMENT_ACCENT/MODEL_LABEL)",
      "backend/app/db/{__init__,client}.py (get_supabase_client()->Client|None, lazy; supabase_configured())",
      "backend/app/db/repositories/{__init__ (get_repository),base.py (Protocol),seed_repo.py (default),supabase_repo.py (optional, fail-safe)}",
      "backend/app/api/{__init__,deps (get_repo),router}.py + routes/{dashboard,agents,workflows,approvals,activity,system}.py",
      "backend/tests/test_api.py (10 new API tests)",
      "frontend/src/lib/api/{client,types,icons,dashboard}.ts, frontend/src/hooks/useDashboard.ts",
      "frontend/src/data/dashboard.ts (added fallbackDashboard), frontend/src/pages/Dashboard.tsx + components/layout/right-rail.tsx (consume useDashboard())"
    ],
    "supabase_optional_note": "The `supabase` Python SDK is listed in backend/requirements.txt but is NOT installed in backend/.venv (Phase-1 install was a core subset). The app runs fine on the SeedRepository with zero external deps. To activate the Supabase path: `backend/.venv/Scripts/python.exe -m pip install supabase==2.30.1`, set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY in backend/.env, then run supabase/{schema,rls,seed}.sql. SupabaseRepository assumes the supabase/schema.sql tables (maps DB enum 'google_ai_studio'->'google_ai') and on any query error logs + falls back to seed (never 500s)."
  },
  "state_ref": "workspace/.state/checkpoints/cp-0004-phase4-data-api.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0003-phase3-dashboard",
  "supersedes": null,
  "approval": { "required": true, "status": "awaiting" },
  "resume_hint": "Phase 4 is committed and awaiting human approval. On approval, advance PROJECT_STATE current_phase to 5 and begin 'Agent/provider integration + LangGraph orchestration + kill switch + tenacity': wire the providers/registry clients to real LLM calls, build the LangGraph CEO->department delegation graph using app/graph/, enforce the recursion_count kill switch (recursion_count > 3 => FAILED), and add tenacity retries (429/timeout/transient).",
  "rollback_hint": "To roll back to Phase 3, restore parent cp-0003-phase3-dashboard: append a rolled_back entry superseding cp-0004, restore its state_ref, set PROJECT_STATE last_checkpoint_id to cp-0003 and revision++, and revert Phase-4 FILE_MANIFEST rows to PENDING (do not delete source files without an Approval-Gate decision). The app remains runnable on the SeedRepository regardless. Re-validating Phase 4 (pytest + live curl + frontend build/lint/test) re-establishes this point.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0004-phase4-data-api -->

<!-- BEGIN omnivra-checkpoint cp-0005-phase5-orchestration -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0005-phase5-orchestration",
  "workflow_id": "bootstrap",
  "node": "phase5.orchestration",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": 5,
  "covers": {
    "summary": "Phase 5 (Agent/provider integration + LangGraph orchestration + kill switch + tenacity) complete and validated. Providers rewritten to httpx + offline STUB mode (no vendor SDKs): app/providers/_compat.py (make_stub_response + openai_chat + post_json), openrouter.py/groq.py (OpenAI-compatible REST), google_ai.py (Gemini generateContent REST), huggingface.py (image via Inference API + stub text); registry.py gained get_provider_registry() cached singleton. Agent runner app/agents/runner.py (run_agent + build_system_prompt). Orchestration schemas app/schemas/orchestration.py (RunRequest/RunResult/AgentRunOutput/PendingApproval, camelCase; re-exported in schemas/__init__.py). LangGraph orchestration: app/graph/builder.py (build_graph + get_compiled_graph), planner.py (plan_delegations heuristic), nodes/{__init__,ceo,delegate,approval,finalize}.py; topology START->ceo->guard(check_kill_switch)->{stop:END, go:delegate}->approval->{wait:END, go:finalize}->END. Orchestrator service app/services/orchestrator.py (run_workflow()). app/api/routes/workflows.py gained POST /run (response_model=RunResult), GET preserved. Providers call real LLMs (tenacity retry on 429/timeout/5xx) when keys are set; otherwise a deterministic offline stub so the graph runs/tests fully offline. Kill switch: recursion_count > settings.max_recursion (3) -> STOPPED at the guard. Approval gate: publish/deploy/export/release/presentation/final tasks -> AWAITING_APPROVAL + pending_approval (resume wiring is Phase 7). langgraph 1.2.2 + langchain-core 1.4.0 installed into backend/.venv.",
    "validation": {
      "backend_tests": "32 passed, 0 failed (25 prior + 7 new tests/test_orchestration.py)",
      "backend_live_run": "verified end-to-end (POST /api/workflows/run 'Design the UI and build the REST API' -> status=completed, 6 agentOutputs, recursionCount=1, plan=[solution-architect, uiux-designer, frontend-engineer, api-engineer, backend-engineer]; 'Publish and deploy...' -> status=awaiting_approval, pendingApproval.kind=final_code)",
      "kill_switch": "confirmed (recursion_count > 3 -> STOPPED at the guard)",
      "approval_gate": "confirmed (publish/deploy/export/release/presentation/final -> awaiting_approval + pending_approval; resume wiring Phase 7)"
    },
    "key_paths": [
      "backend/app/providers/* (rewritten: _compat.py [make_stub_response/openai_chat/post_json], openrouter.py, groq.py, google_ai.py, huggingface.py; registry.py get_provider_registry() singleton)",
      "backend/app/agents/runner.py (run_agent + build_system_prompt)",
      "backend/app/schemas/orchestration.py (RunRequest/RunResult/AgentRunOutput/PendingApproval, camelCase) + schemas/__init__.py re-exports",
      "backend/app/graph/{builder.py (build_graph/get_compiled_graph),planner.py (plan_delegations),nodes/{__init__,ceo,delegate,approval,finalize}.py}",
      "backend/app/services/{__init__,orchestrator.py (run_workflow())}",
      "backend/app/api/routes/workflows.py (POST /run, response_model=RunResult; GET preserved)",
      "backend/tests/test_orchestration.py (7 new tests)"
    ],
    "provider_keys_note": "Providers call real LLMs (tenacity retry on 429/timeout/5xx) when GOOGLE_AI_STUDIO_API_KEY / OPENROUTER_API_KEY / GROQ_API_KEY / HUGGINGFACE_API_KEY are set in backend/.env; otherwise they return a deterministic offline STUB so the graph runs and tests pass fully offline. Providers were rewritten to plain httpx + STUB mode (no vendor SDKs). langgraph 1.2.2 + langchain-core 1.4.0 are now installed in backend/.venv (previously absent)."
  },
  "state_ref": "workspace/.state/checkpoints/cp-0005-phase5-orchestration.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0004-phase4-data-api",
  "supersedes": null,
  "approval": { "required": true, "status": "awaiting" },
  "resume_hint": "Phase 5 is committed and awaiting human approval. On approval, advance PROJECT_STATE current_phase to 6 and begin 'Realtime WebSockets + live activity/health': replace the /ws echo stub with a ConnectionManager broadcasting agent/workflow/approval events, add the reconnecting frontend WS client + hook, and wire the Live Activity Feed, workflow progress, and System Health to stream live over WS.",
  "rollback_hint": "To roll back to Phase 4, restore parent cp-0004-phase4-data-api: append a rolled_back entry superseding cp-0005, restore its state_ref, set PROJECT_STATE last_checkpoint_id to cp-0004 and revision++, and revert Phase-5 FILE_MANIFEST rows to PENDING (do not delete source files without an Approval-Gate decision). The app remains runnable on the SeedRepository + offline stub providers regardless. Re-validating Phase 5 (pytest + live POST /api/workflows/run) re-establishes this point.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0005-phase5-orchestration -->

<!-- BEGIN omnivra-checkpoint cp-0006-phase6-realtime -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0006-phase6-realtime",
  "workflow_id": "bootstrap",
  "node": "phase6.realtime",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": 6,
  "covers": {
    "summary": "Phase 6 (Realtime — WebSockets + live activity/health streaming) complete and validated. Backend: event envelope app/schemas/events.py (camelCase); realtime service app/services/realtime.py (ConnectionManager + module-level manager, emit(type, payload), health_snapshot(), heartbeat_loop); app/main.py /ws endpoint rewired to be manager-backed (sends hello + an immediate system_health then streams broadcasts; heartbeat task started/stopped in the lifespan); graph emission wired in — services/orchestrator.py emits workflow running/terminal, graph/nodes/delegate.py emits activity per delegated agent, graph/nodes/approval.py emits approval when gating; tests/test_realtime.py (3 tests). Frontend: src/lib/api/events.ts (WsEvent + activityFromEvent/healthFromEvent); src/hooks/useWebSocket.ts (connect via Vite /ws proxy, reconnect backoff, folds events into the React Query ['dashboard'] cache — replace systemHealth on system_health, prepend on activity capped at 12; jsdom-guarded); src/store/ui.ts gained realtimeStatus + setRealtimeStatus; app-layout.tsx calls useWebSocket() once; topbar.tsx renders LiveIndicator; src/components/dashboard/live-indicator.tsx (emerald Live / amber Connecting / Offline); smoke.test.tsx asserts the live indicator renders. Behavior: the server pushes system-health every ~4s (jittered) + simulated activity periodically, plus real workflow/activity/approval events during runs; the dashboard folds them into the same ['dashboard'] cache useDashboard() reads, so System Health + Live Activity Feed re-render live. The /ws Vite proxy targets ws://localhost:8000.",
    "validation": {
      "backend_tests": "35 passed, 0 failed (32 prior + 3 new tests/test_realtime.py)",
      "backend_live_ws": "verified end-to-end on a real socket (port 8012): client received hello -> system_health (6 metrics, pushed immediately on connect) -> then after POST /api/workflows/run (200, status=completed) the workflow + activity events broadcast live over the socket",
      "frontend_lint": "exit 0",
      "frontend_build": "exit 0",
      "frontend_tests": "5 passed, 0 failed (vitest — smoke now asserts the live indicator renders)"
    },
    "key_paths": [
      "backend/app/services/realtime.py (ConnectionManager + module-level manager, emit(type, payload), health_snapshot(), heartbeat_loop)",
      "backend/app/schemas/events.py (Event envelope, camelCase)",
      "backend/app/main.py (/ws manager-backed: hello + immediate system_health then streams broadcasts; heartbeat task in lifespan)",
      "backend/app/services/orchestrator.py (emits workflow running/terminal), backend/app/graph/nodes/{delegate.py (emits activity per delegated agent),approval.py (emits approval when gating)}",
      "backend/tests/test_realtime.py (3 new tests)",
      "frontend/src/hooks/useWebSocket.ts (Vite /ws proxy, reconnect backoff, folds events into ['dashboard'] cache; jsdom-guarded), frontend/src/lib/api/events.ts (WsEvent + activityFromEvent/healthFromEvent)",
      "frontend/src/components/dashboard/live-indicator.tsx (LiveIndicator), frontend/src/store/ui.ts (realtimeStatus + setRealtimeStatus), frontend/src/components/layout/{app-layout.tsx (calls useWebSocket() once),topbar.tsx (renders LiveIndicator)}, frontend/src/test/smoke.test.tsx"
    ]
  },
  "state_ref": "workspace/.state/checkpoints/cp-0006-phase6-realtime.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0005-phase5-orchestration",
  "supersedes": null,
  "approval": { "required": true, "status": "awaiting" },
  "resume_hint": "Phase 6 is committed and awaiting human approval. On approval, advance PROJECT_STATE current_phase to 7 and begin 'Human approval gate + recovery/checkpoint resume': wire Approve/Reject/Retry/Rollback to actually resume/roll back the paused LangGraph workflow via the approval API/WebSocket, and add the Recovery service (rehydrate from durable docs/) + checkpoint resume so a held or killed workflow restores from the last checkpoint.",
  "rollback_hint": "To roll back to Phase 5, restore parent cp-0005-phase5-orchestration: append a rolled_back entry superseding cp-0006, restore its state_ref, set PROJECT_STATE last_checkpoint_id to cp-0005 and revision++, and revert Phase-6 FILE_MANIFEST rows to PENDING (do not delete source files without an Approval-Gate decision). The app remains runnable on the SeedRepository + offline stub providers, and the /ws endpoint still serves over the manager. Re-validating Phase 6 (pytest + live WebSocket + frontend lint/build/test) re-establishes this point.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0006-phase6-realtime -->

<!-- BEGIN omnivra-checkpoint cp-0007-phase7-approval -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0007-phase7-approval",
  "workflow_id": "bootstrap",
  "node": "phase7.approval",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": 7,
  "covers": {
    "summary": "Phase 7 (Human Approval Gate resume + Recovery) complete and validated. The graph is compiled WITH a LangGraph MemorySaver checkpointer (app/graph/builder.py compile(checkpointer=...)); the approval node calls LangGraph interrupt() to suspend mid-run and branches on the decision (app/graph/nodes/approval.py: approve/retry->RUNNING, reject->FAILED, rollback->ROLLED_BACK). app/services/orchestrator.py run_workflow detects the interrupt (state['__interrupt__']), returns awaiting_approval + the pending payload, and persists the run; new resume_workflow re-enters via Command(resume={action,note}). app/services/workflow_store.py (WorkflowStore + get_workflow_store) persists each run (RunResult JSON) under workspace/.state/workflows/. app/api/routes/approvals.py POST /{id}/decision now resumes (404 if unknown approvalId); app/api/routes/workflows.py added GET /runs and GET /runs/{id} (recovery listing). tests/test_approval_resume.py (6 tests); tests/test_api.py edited (decision-on-seed-approval now asserts 404). Frontend: src/lib/api/types.ts (added RunResult/AgentRunOutput/PendingApproval/RunStatus), src/lib/api/workflows.ts (runWorkflow/listAwaitingRuns/decideApproval), src/hooks/useApprovals.ts (useAwaitingApprovals + useApprovalDecision), src/hooks/useRunWorkflow.ts, src/components/dashboard/run-task.tsx (RunTask); greeting-hero.tsx renders RunTask; approval-card.tsx gained onDecision Approve/Reject/Retry/Rollback actions; pending-approvals.tsx shows LIVE awaiting runs above seed items, wired to the decision mutation (doubles as the Recovery view); smoke.test.tsx asserts RunTask renders.",
    "validation": {
      "backend_tests": "41 passed, 0 failed (35 prior + 6 new tests/test_approval_resume.py; tests/test_api.py edited — decision-on-seed-approval asserts 404)",
      "backend_api_resume_flow": "verified end-to-end (TestClient + live): POST /api/workflows/run on a gated task -> status='awaiting_approval' + pendingApproval{approvalId,...}; POST /api/approvals/{approvalId}/decision -> approve/retry='completed' (result.ok), reject='failed', rollback='rolled_back'; unknown approvalId -> 404; GET /api/workflows/runs[?status] lists persisted runs",
      "frontend_lint": "exit 0",
      "frontend_build": "exit 0",
      "frontend_tests": "6 passed, 0 failed (vitest — smoke now asserts RunTask renders)"
    },
    "key_paths": [
      "backend/app/graph/builder.py (MemorySaver checkpointer + compile(checkpointer=...))",
      "backend/app/graph/nodes/approval.py (interrupt() + decision branch: approve/retry->RUNNING, reject->FAILED, rollback->ROLLED_BACK)",
      "backend/app/services/orchestrator.py (run_workflow interrupt-detect + persist; new resume_workflow via Command(resume={action,note}))",
      "backend/app/services/workflow_store.py (WorkflowStore + get_workflow_store; persists RunResult JSON under workspace/.state/workflows/)",
      "backend/app/api/routes/approvals.py (POST /{id}/decision now resumes; 404 if unknown), backend/app/api/routes/workflows.py (added GET /runs + GET /runs/{id})",
      "backend/tests/test_approval_resume.py (6 new tests), backend/tests/test_api.py (edited — 404 assertion)",
      "frontend/src/lib/api/workflows.ts (runWorkflow/listAwaitingRuns/decideApproval), frontend/src/lib/api/types.ts (added RunResult/AgentRunOutput/PendingApproval/RunStatus)",
      "frontend/src/hooks/useApprovals.ts (useAwaitingApprovals + useApprovalDecision), frontend/src/hooks/useRunWorkflow.ts",
      "frontend/src/components/dashboard/run-task.tsx (RunTask), frontend/src/components/dashboard/{greeting-hero.tsx (renders RunTask),approval-card.tsx (onDecision Approve/Reject/Retry/Rollback),pending-approvals.tsx (live awaiting runs + decision mutation; Recovery view)}, frontend/src/test/smoke.test.tsx"
    ],
    "same_process_resume_note": "Resume is SAME-PROCESS: LangGraph MemorySaver is in-memory, so approve/reject/retry/rollback resumes only within the same running backend process. Durable cross-restart resume needs a Postgres checkpointer (Supabase); the WorkflowStore persists run metadata (workspace/.state/workflows/) either way, so runs/recovery listings survive a restart even though the in-flight graph state does not. A benign LangGraph msgpack note appears when deserializing the str-enum WorkflowStatus (comparisons still hold)."
  },
  "state_ref": "workspace/.state/checkpoints/cp-0007-phase7-approval.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0006-phase6-realtime",
  "supersedes": null,
  "approval": { "required": true, "status": "awaiting" },
  "resume_hint": "Phase 7 is committed and awaiting human approval. On approval, advance PROJECT_STATE current_phase to 8 and begin 'Marketing / Documentation / Presentation / Media agents + workspace artifacts': build the marketing/docs/presentation/media agents so they produce real artifacts written into ./workspace (honoring the workspace-isolation rule via the FileManager), surfaced in the Workspace/Documents views; all export/publish passes through the Approval Gate.",
  "rollback_hint": "To roll back to Phase 6, restore parent cp-0006-phase6-realtime: append a rolled_back entry superseding cp-0007, restore its state_ref, set PROJECT_STATE last_checkpoint_id to cp-0006 and revision++, and revert Phase-7 FILE_MANIFEST rows to PENDING (do not delete source files without an Approval-Gate decision). The app remains runnable on the SeedRepository + offline stub providers, the /ws endpoint still serves over the manager, and runs already persisted by the WorkflowStore remain on disk. Re-validating Phase 7 (pytest + the API resume flow + frontend lint/build/test) re-establishes this point.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0007-phase7-approval -->

<!-- BEGIN omnivra-checkpoint cp-0008-phase8-artifacts -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0008-phase8-artifacts",
  "workflow_id": "bootstrap",
  "node": "phase8.artifacts",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": 8,
  "covers": {
    "summary": "Phase 8 (Marketing/Documentation/Presentation/Media agents + workspace artifacts) complete and validated. ArtifactService (app/services/artifacts.py: ArtifactService + get_artifact_service) files each agent output under workspace SUBDIRS by agent (docs/frontend/backend/presentations/reports) via the path-jailed FileManager + writes reports/<wf>/run.md; app/schemas/workspace.py (Artifact, ArtifactContent) re-exported in schemas/__init__.py; app/api/routes/workspace.py (GET /artifacts, GET /artifacts/{path}) mounted /workspace; app/schemas/orchestration.py gained AgentRunOutput.artifacts; app/services/orchestrator.py calls persist_run in both run_workflow + resume_workflow so RunResult.agentOutputs[].artifacts carry workspace-relative paths (honors the Workspace Rule — agents only write under ./workspace). Media: app/services/media.py (MediaService: generate_image via HuggingFace FLUX.1-dev when configured else stub placeholder; transcribe/synthesize stub-safe) + app/schemas/media.py + app/api/routes/media.py (POST /api/media/image, /tts, /stt) mounted /media; app/api/router.py added workspace + media. tests/test_workspace_artifacts.py + tests/test_media.py. Frontend: src/lib/api/types.ts (Artifact, ArtifactContent), src/lib/api/artifacts.ts (listArtifacts, readArtifact), src/hooks/useArtifacts.ts, src/components/workspace/artifact-explorer.tsx (two-pane list + viewer), src/pages/Workspace.tsx + src/pages/Documents.tsx, src/App.tsx (/workspace -> Workspace, /documents -> Documents; both removed from the Placeholder); smoke.test.tsx asserts /workspace renders.",
    "validation": {
      "backend_tests": "45 passed, 0 failed (41 prior + 4 new: tests/test_workspace_artifacts.py workspace artifacts + tests/test_media.py media stubs)",
      "backend_artifacts_serve": "verified — running a workflow writes each agent output + a run report into ./workspace via the path-jailed FileManager; GET /api/workspace/artifacts lists them; GET /api/workspace/artifacts/{path} reads (400 on sandbox escape, 404 missing)",
      "backend_media": "stub-safe — POST /api/media/image, /tts, /stt live; MediaService.generate_image uses HuggingFace FLUX.1-dev when keyed else a stub placeholder; transcribe/synthesize stub-safe",
      "frontend_lint": "exit 0",
      "frontend_build": "exit 0",
      "frontend_tests": "7 passed, 0 failed (vitest — smoke now asserts /workspace renders)"
    },
    "key_paths": [
      "backend/app/services/artifacts.py (ArtifactService + get_artifact_service; files each agent output under workspace SUBDIRS by agent + writes reports/<wf>/run.md via the path-jailed FileManager)",
      "backend/app/services/media.py (MediaService: generate_image via HuggingFace FLUX.1-dev when configured else stub placeholder; transcribe/synthesize stub-safe)",
      "backend/app/schemas/{workspace.py (Artifact/ArtifactContent),media.py} + schemas/__init__.py re-exports, backend/app/schemas/orchestration.py (AgentRunOutput.artifacts)",
      "backend/app/api/routes/{workspace.py (GET /artifacts, GET /artifacts/{path}; mounted /workspace),media.py (POST /api/media/image, /tts, /stt; mounted /media)}, backend/app/api/router.py (added workspace + media)",
      "backend/app/services/orchestrator.py (persist_run in run_workflow + resume_workflow)",
      "backend/tests/{test_workspace_artifacts.py,test_media.py}",
      "frontend/src/lib/api/artifacts.ts (listArtifacts/readArtifact) + types.ts (Artifact/ArtifactContent), frontend/src/hooks/useArtifacts.ts",
      "frontend/src/components/workspace/artifact-explorer.tsx (two-pane list + viewer), frontend/src/pages/{Workspace,Documents}.tsx, frontend/src/App.tsx (/workspace + /documents routes), frontend/src/test/smoke.test.tsx"
    ],
    "media_stub_note": "Media runs STUB-safe with no keys: set HUGGINGFACE_API_KEY for real FLUX.1-dev image generation; Groq Whisper STT / Orpheus TTS are stubbed pending key + audio wiring. Artifacts are written under workspace/{docs,frontend,backend,presentations,reports}."
  },
  "state_ref": "workspace/.state/checkpoints/cp-0008-phase8-artifacts.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0007-phase7-approval",
  "supersedes": null,
  "approval": { "required": true, "status": "awaiting" },
  "resume_hint": "Phase 8 is committed and awaiting human approval. On approval, advance PROJECT_STATE current_phase to 9 and begin 'Knowledge base + memory (pgvector) + RAG': add an embeddings pipeline + a knowledge_base/memory store (pgvector when Supabase is configured, in-memory/seed otherwise), a Knowledge Base view, and Memory Retrieval feeding agent context (RAG).",
  "rollback_hint": "To roll back to Phase 7, restore parent cp-0007-phase7-approval: append a rolled_back entry superseding cp-0008, restore its state_ref, set PROJECT_STATE last_checkpoint_id to cp-0007 and revision++, and revert Phase-8 FILE_MANIFEST rows to PENDING (do not delete source files without an Approval-Gate decision). The app remains runnable on the SeedRepository + offline stub providers; media runs stub-safe and any artifacts already written under ./workspace remain on disk. Re-validating Phase 8 (pytest + artifact write/serve + media endpoints + frontend lint/build/test) re-establishes this point.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0008-phase8-artifacts -->

<!-- BEGIN omnivra-checkpoint cp-0009-phase9-knowledge -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0009-phase9-knowledge",
  "workflow_id": "bootstrap",
  "node": "phase9.knowledge",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": 9,
  "covers": {
    "summary": "Phase 9 (Knowledge base + memory (pgvector) + RAG) complete and validated. app/services/vectorstore.py = a deterministic 256-dim hashing embedder (offline, no key) + a cosine VectorStore persisted to workspace/.state/vectors/<name>.json. KnowledgeService (app/services/knowledge.py: knowledge corpus + ingest_workspace) and MemoryService (app/services/memory.py: agent memory). RAG: app/graph/nodes/delegate.py recalls memory into each agent's context (recall_context); app/services/orchestrator.py (_persist_artifacts_and_memory) stores every successful output as memory after run/resume, so the company learns from prior work. Schemas app/schemas/knowledge.py (+ re-export in schemas/__init__.py); REST app/api/routes/knowledge.py (search/add/ingest-workspace/stats) + app/api/routes/memory.py (search/recent/stats) mounted in app/api/router.py (/knowledge, /memory). tests/{test_vectorstore.py,test_knowledge.py,test_memory_rag.py}. Frontend: src/lib/api/types.ts (SearchHit/MemoryEntry/StoreStats/IngestResult), src/lib/api/knowledge.ts, src/hooks/{useKnowledge,useMemory}.ts, src/pages/{KnowledgeBase,Memory}.tsx, src/App.tsx (/knowledge -> KnowledgeBase, /memory -> Memory); smoke.test.tsx asserts /knowledge + /memory render.",
    "validation": {
      "backend_tests": "55 passed, 0 failed (45 prior + 10 new: tests/test_vectorstore.py vector store + tests/test_knowledge.py knowledge + tests/test_memory_rag.py memory/RAG)",
      "backend_rag_e2e": "verified — KB search retrieves relevant docs; a workflow run stores each agent output as memory; ingest-workspace indexes artifacts; memory recall returns prior-run content (the company learns from prior work)",
      "frontend_lint": "exit 0",
      "frontend_build": "exit 0",
      "frontend_tests": "9 passed, 0 failed (vitest — smoke now asserts /knowledge + /memory render)"
    },
    "key_paths": [
      "backend/app/services/vectorstore.py (deterministic 256-dim hashing embedder + cosine VectorStore persisted to workspace/.state/vectors/<name>.json)",
      "backend/app/services/knowledge.py (KnowledgeService: knowledge corpus + ingest_workspace), backend/app/services/memory.py (MemoryService: agent memory)",
      "backend/app/schemas/knowledge.py (+ re-export in schemas/__init__.py)",
      "backend/app/api/routes/knowledge.py (search/add/ingest-workspace/stats; /knowledge) + backend/app/api/routes/memory.py (search/recent/stats; /memory), backend/app/api/router.py (added knowledge + memory)",
      "backend/app/graph/nodes/delegate.py (recall_context recalls memory into each agent's context for RAG), backend/app/services/orchestrator.py (_persist_artifacts_and_memory stores every successful output as memory after run/resume)",
      "backend/tests/{test_vectorstore.py,test_knowledge.py,test_memory_rag.py}",
      "frontend/src/lib/api/knowledge.ts + types.ts (SearchHit/MemoryEntry/StoreStats/IngestResult), frontend/src/hooks/{useKnowledge,useMemory}.ts",
      "frontend/src/pages/{KnowledgeBase,Memory}.tsx, frontend/src/App.tsx (/knowledge + /memory routes), frontend/src/test/smoke.test.tsx"
    ],
    "local_embedder_note": "Embeddings are a local offline hashing embedder (256-d) by default — no key required; stores persist under workspace/.state/vectors/. The Supabase pgvector path (1536-d, match_knowledge/match_memory) is the optional durable backend and needs a real embedding model + Supabase; the local store is the zero-config default."
  },
  "state_ref": "workspace/.state/checkpoints/cp-0009-phase9-knowledge.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0008-phase8-artifacts",
  "supersedes": null,
  "approval": { "required": true, "status": "awaiting" },
  "resume_hint": "Phase 9 is committed and awaiting human approval. On approval, advance PROJECT_STATE current_phase to 10 (the FINAL phase) and begin 'Polish + auth + deploy + hardening': add an auth/login gate, env/secrets + production config, security headers/rate limiting, error boundaries + loading/empty-state polish, README/deploy docs, and a final QA/security pass.",
  "rollback_hint": "To roll back to Phase 8, restore parent cp-0008-phase8-artifacts: append a rolled_back entry superseding cp-0009, restore its state_ref, set PROJECT_STATE last_checkpoint_id to cp-0008 and revision++, and revert Phase-9 FILE_MANIFEST rows to PENDING (do not delete source files without an Approval-Gate decision). The app remains runnable on the SeedRepository + offline stub providers; the local vector store under workspace/.state/vectors/ and any persisted memories remain on disk. Re-validating Phase 9 (pytest + KB search/RAG/ingest/recall + frontend lint/build/test) re-establishes this point.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0009-phase9-knowledge -->

<!-- BEGIN omnivra-checkpoint cp-0010-phase10-polish -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0010-phase10-polish",
  "workflow_id": "bootstrap",
  "node": "phase10.polish",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": 10,
  "covers": {
    "summary": "Phase 10 (Polish + auth + deploy + hardening — FINAL) complete and validated; the whole 10-phase Omnivra build is done. Auth + hardening: app/core/security.py (stdlib HMAC signed tokens: create_token/verify_token/verify_credentials); app/api/deps.py require_user (open in dev, Bearer-enforced when AUTH_ENABLED); app/api/routes/auth.py (/api/auth/config|login|me); sensitive POSTs (workflows/run, approvals decision, knowledge add+ingest) depend on require_user; app/main.py hardening_middleware (security headers always; opt-in per-IP rate limit). New settings: auth_enabled(false), admin_username/admin_password, token_ttl_seconds, security_headers_enabled(true), rate_limit_enabled(false), rate_limit_per_minute. Frontend auth gate: store/auth.ts, lib/api/auth.ts, hooks/useAuth.ts, pages/Login.tsx, components/auth/auth-gate.tsx, components/common/error-boundary.tsx, pages/Settings.tsx, axios bearer interceptor (lib/api/client.ts), wired in App.tsx + main.tsx. Deploy docs: docs/DEPLOYMENT.md (new) + README.md (rewritten). Backend tests: tests/test_auth.py + tests/test_security.py. Post-build polish/fixes: (a) dashboard layout fix — src/components/layout/sidebar.tsx was position:fixed but AppLayout lays it out as a CSS grid column so main content was hidden behind it; fixed to an in-flow sticky grid item (md:flex, fills its 248px/72px track); jsdom tests didn't catch it since getByText ignores CSS. (b) dev noise — vite.config.ts now swallows /api + /ws proxy ECONNREFUSED/ECONNABORTED logs when the backend dev server isn't running (SPA degrades to fallback data). (c) dependency fix — backend/requirements.txt websockets==16.0 -> websockets>=12,<16 (resolves the supabase 2.30.1 conflict; resolves to 15.0.1, full-tree dry-run clean). (d) animation polish — new motion foundation src/lib/motion.ts + src/components/common/reveal.tsx (Reveal/Stagger/StaggerItem) + src/components/common/count-up.tsx (all reduced-motion aware), applied across ~24 components. The whole product runs OFFLINE in stub mode (no keys/Supabase needed); real providers/Supabase/auth activate via backend/.env.",
    "validation": {
      "backend_tests": "62 passed, 0 failed (55 prior + 7 new: tests/test_auth.py signed-token auth + require_user gating + tests/test_security.py HMAC token create/verify + hardening middleware)",
      "frontend_build": "exit 0 (tsc strict + vite build)",
      "frontend_lint": "exit 0 (eslint --max-warnings 0, clean)",
      "frontend_tests": "12 passed, 0 failed (vitest — smoke now asserts the auth gate / Login render)"
    },
    "key_paths": [
      "backend/app/core/security.py (stdlib HMAC signed tokens: create_token/verify_token/verify_credentials)",
      "backend/app/api/deps.py (require_user: open in dev, Bearer-enforced when AUTH_ENABLED), backend/app/api/routes/auth.py (/api/auth/config|login|me)",
      "backend/app/api/routes/{workflows.py,approvals.py,knowledge.py} (sensitive POSTs depend on require_user), backend/app/api/router.py (added auth router)",
      "backend/app/main.py (hardening_middleware: security headers always + opt-in per-IP rate limit), backend/app/core/config.py (auth_enabled/admin_username/admin_password/token_ttl_seconds/security_headers_enabled/rate_limit_enabled/rate_limit_per_minute)",
      "backend/requirements.txt (websockets==16.0 -> websockets>=12,<16), backend/tests/{test_auth.py,test_security.py}",
      "frontend/src/store/auth.ts, frontend/src/lib/api/auth.ts, frontend/src/hooks/useAuth.ts, frontend/src/pages/{Login,Settings}.tsx, frontend/src/components/auth/auth-gate.tsx, frontend/src/components/common/error-boundary.tsx, frontend/src/lib/api/client.ts (bearer interceptor), frontend/src/{App,main}.tsx",
      "frontend/src/lib/motion.ts + frontend/src/components/common/{reveal,count-up}.tsx (animation foundation), frontend/src/components/layout/sidebar.tsx (layout fix + MotionNavLink), frontend/vite.config.ts (proxy noise fix), ~24 animated components (Dashboard/components/dashboard/* + layout/{app-layout,right-rail})",
      "docs/DEPLOYMENT.md (new), README.md (rewritten)"
    ],
    "offline_auth_note": "The whole product runs OFFLINE in stub mode (no keys/Supabase needed). Auth is opt-in: require_user is open in dev and Bearer-enforced only when AUTH_ENABLED; tokens are stdlib HMAC signed (no external dep). Security headers are sent always; per-IP rate limiting is opt-in (rate_limit_enabled). Real providers/Supabase/auth activate via backend/.env."
  },
  "state_ref": "workspace/.state/checkpoints/cp-0010-phase10-polish.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0009-phase9-knowledge",
  "supersedes": null,
  "approval": { "required": false, "status": "project_complete" },
  "resume_hint": "Project complete — all 10 phases shipped. Optional next: provision Supabase + provider keys, enable AUTH_ENABLED, deploy per docs/DEPLOYMENT.md.",
  "rollback_hint": "To roll back to Phase 9, restore parent cp-0009-phase9-knowledge: append a rolled_back entry superseding cp-0010, restore its state_ref, set PROJECT_STATE last_checkpoint_id to cp-0009 and revision++, and revert Phase-10 FILE_MANIFEST rows to PENDING (do not delete source files without an Approval-Gate decision). The app remains runnable on the SeedRepository + offline stub providers with auth disabled by default. Re-validating Phase 10 (pytest 62 + frontend build/lint/test 12/12) re-establishes this point.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0010-phase10-polish -->

<!-- BEGIN omnivra-checkpoint cp-0011-pages-hierarchy -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0011-pages-hierarchy",
  "workflow_id": "bootstrap",
  "node": "post1.pages_hierarchy",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": "post-1.0",
  "phase_title": "Post-1.0 enhancement — remaining nav pages + Agent Hierarchy Tree",
  "covers": {
    "summary": "Built out every remaining navigable page so the whole sidebar is real (only /projects + /tasks remained Placeholder at this checkpoint — no backend yet; closed in cp-0012), plus the spec's flagship Agent Hierarchy Tree (React Flow). Pages: Agents (roster grouped by department + Grid/Hierarchy toggle), AgentHierarchyTree (CEO -> department -> agent org chart, accent-tinted glass nodes, fitView + Controls + MiniMap), Workflows (RunTask + active workflows + run-history with per-run drill-down of agentOutputs/artifacts/errors), Approvals (full-page live gate reusing PendingApprovals with Approve/Reject/Retry/Rollback), Departments x7 (slug-driven agent roster), Logs (recent activity + memory), Integrations (provider/Supabase/auth status), Billing (cost + provider/model usage). Backend added GET /api/system/providers + GET /api/system/info. New frontend api/hooks: agents, workflow-runs, system.",
    "validation": {
      "backend_tests": "62 passed, 0 failed",
      "frontend_build": "exit 0",
      "frontend_lint": "exit 0 (eslint --max-warnings 0)",
      "frontend_tests": "12 passed, 0 failed (vitest)"
    },
    "key_paths": [
      "frontend/src/pages/{Agents,Workflows,Approvals,Logs,Integrations,Billing}.tsx, frontend/src/pages/departments/Department.tsx",
      "frontend/src/components/agents/agent-hierarchy-tree.tsx (React Flow)",
      "frontend/src/lib/api/{agents,system}.ts + workflows.ts (listRuns/getRun/listActiveWorkflows), frontend/src/hooks/{useAgents,useWorkflowRuns,useSystem}.ts",
      "frontend/src/App.tsx (routes wired; only /projects + /tasks remained Placeholder at this checkpoint)",
      "backend/app/api/routes/system.py (/providers + /info)"
    ]
  },
  "state_ref": "workspace/.state/checkpoints/cp-0011-pages-hierarchy.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0010-phase10-polish",
  "supersedes": null,
  "approval": { "required": false, "status": "shipped" },
  "resume_hint": "Optional remaining: build /projects + /tasks (needs new backend projects/tasks endpoints + tables); add the design-doc 'center' panels (MemoryUsage, SecurityCenter, DocumentationCenter, MarketingCenter, RecoveryStatus); wire settings.provider_max_retries into the tenacity decorators; add a seed.sql<->registry sync guard. Then go-live: Supabase + provider keys + AUTH_ENABLED + deploy per docs/DEPLOYMENT.md.",
  "rollback_hint": "Additive enhancement over cp-0010; rollback = revert these pages/endpoints to restore the cp-0010 state.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0011-pages-hierarchy -->

<!-- BEGIN omnivra-checkpoint cp-0012-projects-tasks -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0012-projects-tasks",
  "workflow_id": "bootstrap",
  "node": "post1.projects_tasks",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": "post-1.0",
  "phase_title": "Post-1.0 enhancement — Projects & Tasks (full-stack) + deferred hardening",
  "covers": {
    "summary": "Built the last two pages full-stack: Projects + Tasks. Backend: app/services/project_store.py (JSON-persisted, seeded 3 projects/7 tasks), app/schemas/projects.py, CRUD routes app/api/routes/projects.py + tasks.py (mutations auth-gated when AUTH_ENABLED). Frontend: lib/api/projects.ts, hooks useProjects/useTasks, pages/Projects.tsx (project board + create/delete) + pages/Tasks.tsx (4-column Kanban with create/move/delete). App.tsx wired both routes and removed the PLACEHOLDER_ROUTES + unused Placeholder import -> NO placeholder routes remain. Deferred hardening also done: provider_max_retries is now read by with_provider_retry (single source of truth) and a seed.sql<->registry drift-guard test was added.",
    "validation": {
      "backend_tests": "70 passed, 0 failed (62 + test_projects_tasks(5) + test_seed_sync(3))",
      "frontend_build": "exit 0",
      "frontend_lint": "exit 0 (eslint --max-warnings 0)",
      "frontend_tests": "14 passed, 0 failed (vitest)"
    },
    "key_paths": [
      "backend/app/services/project_store.py, backend/app/schemas/projects.py, backend/app/api/routes/{projects,tasks}.py, backend/app/api/router.py",
      "backend/app/providers/base.py (provider_max_retries wired), backend/tests/{test_projects_tasks,test_seed_sync}.py",
      "frontend/src/lib/api/projects.ts, frontend/src/hooks/{useProjects,useTasks}.ts, frontend/src/pages/{Projects,Tasks}.tsx, frontend/src/App.tsx"
    ],
    "drift_guard_note": "Registry agent ids are kebab-case (ceo-manager) while supabase/seed.sql uses snake_case keys (ceo_manager); the seed-sync test normalizes hyphens->underscores for ids (model strings match verbatim). Harmless representation difference; a backend mapping already handles google_ai<->google_ai_studio similarly."
  },
  "state_ref": "workspace/.state/checkpoints/cp-0012-projects-tasks.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0011-pages-hierarchy",
  "supersedes": null,
  "approval": { "required": false, "status": "shipped" },
  "resume_hint": "Optional remaining: design-doc 'center' detail panels (MemoryUsage, SecurityCenter, DocumentationCenter, MarketingCenter, RecoveryStatus); persist Projects/Tasks (and the approval checkpointer) to Supabase Postgres when configured. Then go-live: Supabase + provider keys + AUTH_ENABLED + deploy per docs/DEPLOYMENT.md.",
  "rollback_hint": "Additive over cp-0011; rollback = revert the projects/tasks files + base.py retry change.",
  "created_at": "2026-05-30T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0012-projects-tasks -->

<!-- BEGIN omnivra-checkpoint cp-0013-center-panels -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0013-center-panels",
  "workflow_id": "bootstrap",
  "node": "post1.center_panels",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": "post-1.0",
  "phase_title": "Post-1.0 enhancement — design-doc center panels (completes the component inventory)",
  "covers": {
    "summary": "Built the remaining DESIGN_SYSTEM.md section 8.3 'center' detail panels: SecurityCenter (Quality & Security dept — agents + security posture + API quotas + recent security activity), MarketingCenter (agents + campaigns + content artifacts + activity), DocumentationCenter (agents + docs/presentations artifacts + activity). These now back /departments/quality, /departments/marketing, /departments/documentation (the other 4 departments keep the generic roster). RecoveryStatus component (resumable awaiting runs + the cp-NNNN checkpoint lineage) added to the Workflows page; MemoryUsagePanel (memory + knowledge store sizes + recent memory) added atop the Memory page. Backend added GET /api/system/checkpoints + frontend listCheckpoints/useCheckpoints. With AgentHierarchyTree (cp-0011) this realizes EVERY component in the design-system inventory.",
    "validation": {
      "backend_tests": "70 passed, 0 failed",
      "frontend_build": "exit 0",
      "frontend_lint": "exit 0 (eslint --max-warnings 0)",
      "frontend_tests": "14 passed, 0 failed (vitest)"
    },
    "key_paths": [
      "frontend/src/pages/centers/{SecurityCenter,MarketingCenter,DocumentationCenter}.tsx, frontend/src/App.tsx",
      "frontend/src/components/dashboard/{recovery-status,memory-usage-panel}.tsx + frontend/src/pages/{Workflows,Memory}.tsx",
      "frontend/src/lib/api/system.ts (listCheckpoints) + frontend/src/hooks/useSystem.ts (useCheckpoints)",
      "backend/app/api/routes/system.py (GET /checkpoints)"
    ]
  },
  "state_ref": "workspace/.state/checkpoints/cp-0013-center-panels.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0012-projects-tasks",
  "supersedes": null,
  "approval": { "required": false, "status": "shipped" },
  "resume_hint": "Component inventory complete. Optional remaining: persist Projects/Tasks + the approval checkpointer to Supabase Postgres when configured; otherwise go-live (Supabase + provider keys + AUTH_ENABLED + deploy per docs/DEPLOYMENT.md).",
  "rollback_hint": "Additive over cp-0012; rollback = revert center pages/components + the /api/system/checkpoints endpoint.",
  "created_at": "2026-05-31T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0013-center-panels -->

<!-- BEGIN omnivra-checkpoint cp-0014-post-review-hardening -->
```json omnivra-checkpoint
{
  "schema_version": "1.0.0",
  "id": "cp-0014-post-review-hardening",
  "workflow_id": "bootstrap",
  "node": "post1.review_hardening",
  "status": "committed",
  "recursion_count": 0,
  "recursion_limit": 3,
  "phase": "post-1.0",
  "phase_title": "Post-1.0 hardening — applied findings from the full-system lead-engineer review",
  "covers": {
    "summary": "Ran a full multi-agent lead-engineer review (security / backend-correctness / frontend / docs). Verdict: SHIP (no critical/high code defects). Applied the actionable findings: (1) SECURITY HIGH — path traversal / arbitrary .json read on GET /api/workflows/runs/{workflow_id}: WorkflowStore._path now rejects '/', '\\', NUL and '..' (raises ValueError; .get() -> clean 404). (2) SECURITY MEDIUM (defense-in-depth) — applied the same workflow_id jail to CheckpointStore._state_file + checkpoint(). (3) BACKEND — RAG memory duplication on resume fixed: orchestrator persists each agent output with a stable id (mem:{workflow_id}:{agent_id}) so approve/retry upserts instead of duplicating; MemoryService.remember/VectorStore.add accept id. (4) CONCURRENCY MEDIUM — added threading.RLock around read-modify-write in VectorStore (add/clear) and ProjectStore (create/update/delete) since sync routes run in a threadpool. (5) DOCS — README.md + docs/DEPLOYMENT.md test counts corrected 55 -> 70; removed an auditor scratch file (backend/_audit_recursion.py). The four durable control docs (PROJECT_STATE/FILE_MANIFEST/CHECKPOINTS/ROADMAP) reconciled current through cp-0014.",
    "validation": {
      "backend_tests": "70 passed, 0 failed",
      "frontend_build": "exit 0",
      "frontend_lint": "exit 0 (eslint --max-warnings 0)",
      "frontend_tests": "14 passed, 0 failed (vitest)"
    },
    "key_paths": [
      "backend/app/services/workflow_store.py (_path jail + get() 404)",
      "backend/app/checkpoint/store.py (_safe_id jail)",
      "backend/app/services/orchestrator.py + backend/app/services/memory.py + backend/app/services/vectorstore.py (stable memory id + RLock)",
      "backend/app/services/project_store.py (RLock)",
      "README.md, docs/DEPLOYMENT.md (test counts), docs/{PROJECT_STATE,FILE_MANIFEST,CHECKPOINTS,ROADMAP}.md"
    ]
  },
  "state_ref": "workspace/.state/checkpoints/cp-0014-post-review-hardening.json",
  "manifest_hash": "sha256:PENDING",
  "parent": "cp-0013-center-panels",
  "supersedes": null,
  "approval": { "required": false, "status": "shipped" },
  "resume_hint": "1.0 is complete + review-hardened and ready for git. Deferred (forward-looking, non-blocking) followups: durable Postgres/Supabase LangGraph checkpointer for cross-restart resume of paused approvals (today it uses an in-process MemorySaver); broaden store locking / move JSON stores to Supabase if concurrency grows; the recursion kill switch is correct + unit-tested but DORMANT in the current linear graph (recursion_count maxes at 1 — re-enable its meaning by adding a replanning edge); prod-hardening checklist before any non-local deploy (override dev defaults api_secret_key/admin creds, set AUTH_ENABLED=true, consider rate_limit_enabled).",
  "rollback_hint": "All changes are surgical hardening over cp-0013 (input validation + locks + stable ids + doc text). Rollback = revert the listed files; no schema or behavioral change to the happy path.",
  "created_at": "2026-05-31T00:00:00Z"
}
```
<!-- END omnivra-checkpoint cp-0014-post-review-hardening -->

---

## Resume Procedure (orchestrator / Recovery Agent)
1. Read `docs/PROJECT_STATE.md` → `omnivra-state.last_checkpoint_id`.
2. Locate that ID here; confirm `status = committed` and it is not `superseded`/`rolled_back`.
3. Load the full snapshot from `state_ref` (`workspace/.state/checkpoints/<id>.json`). If missing,
   rehydrate from this JSON record + `docs/FILE_MANIFEST.md`.
4. Verify `manifest_hash` against the live `docs/FILE_MANIFEST.md`; on mismatch, run manifest
   reconciliation before continuing.
5. If `approval.required` is true and `approval.status` is not `approved`, **stop and wait** for the
   human Approval Gate decision before advancing the phase.
6. Restore state and resume at `node` / next phase. Increment nothing unless a node re-executes.
7. If `recursion_count > recursion_limit` at any point ⇒ trip kill switch: set workflow `failed`,
   append a `failed` checkpoint, stop.

## Rollback Procedure
1. Choose the target prior checkpoint `cp-XXXX`.
2. Append a new checkpoint with `status = rolled_back` and `supersedes` listing every checkpoint
   after the target.
3. Restore `state_ref` of the target, update `PROJECT_STATE` `last_checkpoint_id`, bump revision.
4. Roll back manifest entries created after the target to `PENDING` (do not delete source files
   without a human Approval-Gate decision).

---

**PROJECT COMPLETE — all 10 phases shipped, plus a post-1.0 build-out and a review-hardening pass.**
`cp-0014-post-review-hardening` is the latest, committed checkpoint (no approval pending); the post-1.0
chain `cp-0011..cp-0014` is additive over the 1.0 release at `cp-0010-phase10-polish`. Current
validation: backend `pytest` **70 passed**; frontend `vite build` exit 0 + `eslint --max-warnings 0`
exit 0 + vitest **14/14**. Optional next: provision Supabase + provider keys, enable `AUTH_ENABLED`, and
deploy per `docs/DEPLOYMENT.md` (forward-looking, non-blocking followups in `docs/ROADMAP.md`).
