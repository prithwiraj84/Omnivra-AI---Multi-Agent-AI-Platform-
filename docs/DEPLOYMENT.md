# DEPLOYMENT — Omnivra AI Company OS

Production deployment guide for Omnivra. This covers deploying the **FastAPI + LangGraph**
backend and the **Vite/React** frontend to a production host. There is **no Docker** — the
backend runs from a Python **venv** under a process manager, and the frontend ships as static
files served by any web server / CDN with a reverse proxy to the backend for `/api` and `/ws`.

> Omnivra runs fully **offline / stub-safe** with zero external services (deterministic provider
> stubs, a local hashing embedder, an in-memory checkpointer, the bundled seed data layer). To run
> in **real** production mode you add provider keys, a strong secret, auth, rate limiting, and
> (optionally) a Supabase project for durable storage. See the
> [Production Hardening Checklist](#production-hardening-checklist).

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Backend deployment](#2-backend-deployment)
3. [Frontend deployment](#3-frontend-deployment)
4. [Reverse proxy (`/api` + `/ws`)](#4-reverse-proxy-api--ws)
5. [Environment variables](#5-environment-variables)
6. [Supabase setup (optional, durable backend)](#6-supabase-setup-optional-durable-backend)
7. [Production hardening checklist](#7-production-hardening-checklist)
8. [Quick local run recap](#8-quick-local-run-recap)

---

## 1. Prerequisites

| Requirement | Notes |
|---|---|
| **Node.js ≥ 20**, npm ≥ 10 | To build the frontend (`npm ci && npm run build`). Not needed on the server if you build elsewhere and copy `dist/`. |
| **Python ≥ 3.11** | For the backend venv + Uvicorn/Gunicorn workers. |
| **No Docker** | Omnivra is venv + static files by design. Use a system process manager (systemd, NSSM on Windows, Supervisor, PM2, etc.). |
| A reverse proxy / web server | Nginx, Caddy, Apache, IIS, or a CDN/static host that supports path-based proxying and WebSocket upgrade. |
| (Optional) Supabase Cloud project | For durable Postgres + `pgvector` storage and a durable graph checkpointer. |
| (Optional) Redis / Upstash | Reserved for queue + ephemeral run state. |
| Real provider API keys | For live LLM/media output (otherwise Omnivra runs in deterministic stub mode). |

---

## 2. Backend deployment

The backend is a standard ASGI app: `app.main:app` (FastAPI). It runs from a Python venv with
its pinned dependencies (`backend/requirements.txt`).

### 2.1 Create the venv and install dependencies

```bash
cd backend
python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell:
#   .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

> The pinned `supabase` SDK is listed in `requirements.txt`. If your install was a core subset and
> the Supabase client is not present, run `pip install supabase` to enable the optional pgvector +
> durable-checkpointer paths (see [§6](#6-supabase-setup-optional-durable-backend)). The app runs
> fine without it on the bundled seed data layer + local vector store.

### 2.2 Configure the environment

Copy the template and fill in production values (see the [env table](#5-environment-variables)):

```bash
cp backend/.env.example backend/.env
# edit backend/.env — set API_SECRET_KEY, AUTH_ENABLED=true, provider keys, CORS_ORIGINS, etc.
```

`backend/app/core/config.py` reads `backend/.env` and the process environment via
`pydantic-settings`. Any variable in the env table can be set either in `backend/.env` or as a real
environment variable (env vars win and are preferred for secrets in production).

### 2.3 Run with Uvicorn (single process)

For a small deployment or behind a proxy that handles concurrency:

```bash
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Do **not** pass `--reload` in production.

### 2.4 Run with Gunicorn + Uvicorn workers (recommended)

For multi-worker production serving, run Gunicorn with the Uvicorn ASGI worker class
(`pip install gunicorn` into the venv first):

```bash
.venv/bin/gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

> **Worker / state caveat.** The default in-process pieces — the LangGraph `MemorySaver`
> checkpointer (approval resume), the WebSocket `ConnectionManager` fan-out, and the local vector
> store — are **per-process**. With multiple workers, an approval started on one worker may not
> resume on another, and a WebSocket client only receives events broadcast by its own worker. For a
> single-node deployment, run **one worker** (`--workers 1`) for correct approval-resume + realtime
> behavior, or move to the durable Supabase checkpointer (see §6) and an external pub/sub before
> scaling out workers. CPU-bound concurrency is not the bottleneck here; the app is I/O-bound on
> provider calls.

### 2.5 Run under a process manager

Keep the backend alive across restarts with your platform's process manager.

Example **systemd** unit (`/etc/systemd/system/omnivra-backend.service`):

```ini
[Unit]
Description=Omnivra Backend (FastAPI/Uvicorn)
After=network.target

[Service]
WorkingDirectory=/srv/omnivra/backend
EnvironmentFile=/srv/omnivra/backend/.env
ExecStart=/srv/omnivra/backend/.venv/bin/gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker --workers 1 --bind 127.0.0.1:8000 --timeout 120
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

On Windows, run the same Uvicorn/Gunicorn command under **NSSM** or as a scheduled task; the venv
interpreter is `backend\.venv\Scripts\python.exe`.

### 2.6 Health check

`GET /health` returns service status and the registered agent count (23 agents). Point your load
balancer / uptime monitor at it. Interactive API docs are at `/docs` (consider disabling or
protecting these in production).

---

## 3. Frontend deployment

The frontend is a static Single-Page App. Build it once and serve the `dist/` directory from any
static host or CDN.

### 3.1 Build

```bash
cd frontend
npm ci
npm run build      # tsc && vite build -> frontend/dist/
```

The output is fully static under `frontend/dist/` (hashed JS/CSS chunks — vendor code is split into
`react`, `charts`, `flow`, and `motion` chunks per `vite.config.ts`). It can be served by Nginx,
Caddy, Apache, IIS, GitHub Pages, Netlify, Vercel (static), Cloudflare Pages, S3 + CloudFront, or
any static host.

### 3.2 SPA routing

Because the app uses client-side routing (`react-router-dom` with a `*` catch-all), the static host
**must fall back to `index.html`** for unknown paths (history-API fallback). Most static hosts have
a "SPA / rewrite all to index.html" setting; for Nginx use `try_files $uri /index.html;` (see §4).

### 3.3 Frontend configuration

In production the SPA calls the backend on **relative paths** — the axios client uses `baseURL:
/api` and the WebSocket connects to a relative `/ws`. This means **the frontend and backend should
be served under the same origin**, with the reverse proxy forwarding `/api` and `/ws` to the
backend (mirroring the dev `vite.config.ts` proxy). With that setup, no build-time API URL is
required.

`frontend/.env.example` lists the optional `VITE_*` build-time variables (e.g.
`VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` for any direct Supabase Realtime/Storage use, and
feature flags). Only variables prefixed `VITE_` are exposed to the browser — never put secrets
(service role keys, provider keys) in frontend env.

---

## 4. Reverse proxy (`/api` + `/ws`)

Serve the static `dist/` and proxy `/api` (REST) and `/ws` (WebSocket) to the backend on port 8000.
This mirrors the local Vite dev proxy:

```ts
// vite.config.ts (dev) — production must reproduce this routing at the edge
proxy: {
  '/api': { target: 'http://localhost:8000', changeOrigin: true },
  '/ws':  { target: 'ws://localhost:8000', ws: true, changeOrigin: true },
}
```

Example **Nginx** server block:

```nginx
server {
    listen 443 ssl http2;
    server_name omnivra.example.com;

    # TLS certs (e.g. from certbot / your CA)
    ssl_certificate     /etc/letsencrypt/live/omnivra.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/omnivra.example.com/privkey.pem;

    # --- Static SPA ---
    root /srv/omnivra/frontend/dist;
    index index.html;

    location / {
        try_files $uri /index.html;     # SPA history fallback
    }

    # --- REST API -> backend ---
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # --- WebSocket -> backend (Upgrade headers required) ---
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade    $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host       $host;
        proxy_read_timeout 3600s;       # keep long-lived sockets open
    }
}
```

> If you instead serve the frontend from a different origin/CDN than the backend, you must set the
> backend `CORS_ORIGINS` to the frontend origin **and** point the SPA at the backend's absolute
> URL. Same-origin (proxy) is the recommended, simplest topology.

---

## 5. Environment variables

Backend variables are read by `backend/app/core/config.py` (case-insensitive). Set them in
`backend/.env` or the process environment. Defaults below match the code.

### App / runtime

| Variable | Default | Purpose |
|---|---|---|
| `APP_NAME` | `Omnivra AI Company OS` | Display name. |
| `APP_ENV` | `development` | `development` \| `staging` \| `production`. |
| `DEBUG` | `true` | Set **`false`** in production. |
| `HOST` | `0.0.0.0` | Bind host (when launching via the app's own runner). |
| `PORT` | `8000` | Bind port. |
| `LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR`. |
| `LOG_JSON` | `false` | Set **`true`** for structured JSON logs in production. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed origins. **Restrict to your real frontend origin in prod.** |
| `WORKSPACE_ROOT` | `../workspace` | Path-jailed sandbox; agents may write **only** here. |

### Providers (LLM / media)

| Variable | Default | Purpose |
|---|---|---|
| `GOOGLE_AI_STUDIO_API_KEY` | _(unset)_ | Google AI Studio (Gemini 2.5 Flash) — CEO/Manager, UI/UX Designer. |
| `OPENROUTER_API_KEY` | _(unset)_ | OpenRouter — Architect, DB/FE/BE/API Eng, SecOps, Social, Docs, Recovery, System Ops. |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API base. |
| `OPENROUTER_SITE_URL` | `https://omnivra.local` | Sent as `HTTP-Referer` (OpenRouter attribution). |
| `OPENROUTER_APP_NAME` | `Omnivra AI Company OS` | Sent as `X-Title`. |
| `GROQ_API_KEY` | _(unset)_ | Groq — QA, SEO, Reel, Whisper STT, Orpheus TTS. |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | Groq API base. |
| `HUGGINGFACE_API_KEY` | _(unset)_ | Hugging Face — FLUX.1-dev image generation. |
| `HUGGINGFACE_INFERENCE_ENDPOINT` | `https://api-inference.huggingface.co` | HF inference base. |

> **Stub mode.** When a provider key is unset, that provider returns a deterministic offline stub so
> the graph, tests, and media endpoints all run with zero external dependencies. Set the keys above
> to switch to real LLM/media calls (each call is wrapped with tenacity backoff on 429 / timeout /
> transient errors).

### Supabase (optional, durable backend)

| Variable | Default | Purpose |
|---|---|---|
| `SUPABASE_URL` | _(unset)_ | Project URL. Enables the optional Supabase repository + vector paths. |
| `SUPABASE_ANON_KEY` | _(unset)_ | Browser-safe key (parity / direct client). |
| `SUPABASE_SERVICE_ROLE_KEY` | _(unset)_ | **Server only.** Never expose to the browser. |
| `SUPABASE_DB_PASSWORD` | _(unset)_ | DB password (direct connection / checkpointer). |
| `SUPABASE_DB_URL` | _(unset)_ | Direct Postgres DSN for the durable LangGraph checkpointer. |
| `SUPABASE_STORAGE_BUCKET` | `omnivra-artifacts` | Storage bucket for artifacts. |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis / Upstash URL (queue + ephemeral state). |

### Orchestration safety

| Variable | Default | Purpose |
|---|---|---|
| `MAX_RECURSION` | `3` | Kill switch — `recursion_count > MAX_RECURSION` ⇒ workflow STOPPED/FAILED. |
| `PROVIDER_TIMEOUT_SECONDS` | `60` | Per-provider HTTP timeout. |
| `PROVIDER_MAX_RETRIES` | `5` | Tenacity attempts on 429 / timeout / transient. |

### Security / Auth / Hardening

| Variable | Default | Purpose |
|---|---|---|
| `API_SECRET_KEY` | `change-me-in-prod` | Signs auth/resume tokens. **Set a long random value in prod.** |
| `AUTH_ENABLED` | `false` | Auth is **opt-in**. Set **`true`** to require a Bearer token on sensitive POSTs. |
| `ADMIN_USERNAME` | `admin` | Admin login (validated only when `AUTH_ENABLED=true`). |
| `ADMIN_PASSWORD` | `omnivra` | Admin password. **Set a strong value in prod.** |
| `TOKEN_TTL_SECONDS` | `86400` | Token lifetime (seconds). |
| `SECURITY_HEADERS_ENABLED` | `true` | Adds `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`. |
| `RATE_LIMIT_ENABLED` | `false` | Set **`true`** to enable per-IP rate limiting. |
| `RATE_LIMIT_PER_MINUTE` | `240` | Max requests/minute/IP when rate limiting is on. |

> **Auth behavior.** With `AUTH_ENABLED=false` (default), the API runs **open**: `require_user`
> resolves to the admin user with no token, and `POST /api/auth/login` accepts any username and
> returns a token so the SPA always has one. With `AUTH_ENABLED=true`, `/api/auth/login` validates
> the configured admin credentials, and sensitive POSTs (`workflows/run`, approval decisions,
> knowledge add + ingest) require `Authorization: Bearer <token>` (401 without a valid one).
> `GET /api/auth/config` reports `{ "authEnabled": <bool> }` so the SPA knows whether to show login.

### Frontend (build-time, `VITE_*` only)

Set these before `npm run build` if you serve the frontend on a different origin than the backend or
use direct Supabase. Only `VITE_`-prefixed vars reach the browser — **never** put secrets here.

| Variable | Example | Purpose |
|---|---|---|
| `VITE_SUPABASE_URL` | `https://xxxx.supabase.co` | Optional direct Supabase (Realtime/Storage). |
| `VITE_SUPABASE_ANON_KEY` | _public anon key_ | Browser-safe anon key. |
| `VITE_APP_NAME` / `VITE_APP_VERSION` | `Omnivra` / `2.0.0` | Display metadata. |
| `VITE_ENABLE_REALTIME` / `VITE_ENABLE_VOICE` | `true` / `false` | Feature flags. |

> The default same-origin proxy topology needs **no** frontend env: the axios client uses `/api` and
> the WebSocket uses `/ws` relatively.

---

## 6. Supabase setup (optional, durable backend)

By default Omnivra uses the bundled **seed** data layer, a **local hashing vector store** (under
`workspace/.state/vectors/`), and an **in-memory** LangGraph checkpointer — zero external services.
Supabase upgrades these to durable, multi-process backends.

1. **Create a Supabase Cloud project** and copy the Project URL + `service_role` key.
2. **Apply the SQL in order** against the project's database (Supabase SQL editor or `psql`):
   1. `supabase/schema.sql` — tables + `pgvector` (`vector(1536)`) + `match_knowledge` / `match_memory` RPCs.
   2. `supabase/rls.sql` — row-level security policies.
   3. `supabase/seed.sql` — seed agents / departments / providers / models.
   See `docs/SUPABASE_INTEGRATION.md` for the full runbook (extensions, Storage buckets, RLS approach).
3. **Install the Supabase SDK** into the backend venv to enable the optional paths:
   ```bash
   pip install supabase
   ```
4. **Set the backend env**: `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (and `SUPABASE_DB_URL` for
   the durable Postgres checkpointer). On any query error the `SupabaseRepository` logs and **falls
   back to the seed** layer — it never 500s.

> **Durable resume.** The default approval-resume uses an in-memory `MemorySaver` (same-process
> only). A Postgres checkpointer backed by Supabase (`langgraph-checkpoint-postgres`, pinned in
> `requirements.txt`) enables durable cross-restart / cross-worker resume. The `WorkflowStore`
> persists run metadata under `workspace/.state/workflows/` either way, so run/recovery listings
> survive a restart regardless.

> **Embedding dimension.** The local default embedder is 256-dim; the Supabase pgvector schema is
> standardized to **1536**-dim (`vector(1536)`). Switching to the Supabase vector path requires a
> real 1536-dim embedding model — keep the dimension consistent across `schema.sql` and the
> `match_*` RPCs.

---

## 7. Production hardening checklist

Before exposing Omnivra publicly, confirm every item:

- [ ] **Set a strong `API_SECRET_KEY`** — a long random secret (e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"`). Never ship the `change-me-in-prod` default.
- [ ] **Enable auth** — `AUTH_ENABLED=true` with a strong `ADMIN_PASSWORD` (and a non-default `ADMIN_USERNAME`). Verify `POST /api/auth/login` rejects bad creds and sensitive POSTs return 401 without a token.
- [ ] **Enable rate limiting** — `RATE_LIMIT_ENABLED=true` and tune `RATE_LIMIT_PER_MINUTE` for expected traffic.
- [ ] **Keep security headers on** — `SECURITY_HEADERS_ENABLED=true` (default) adds the frame/content-type/referrer/permissions headers.
- [ ] **Restrict CORS** — set `CORS_ORIGINS` to your exact frontend origin(s); do not leave the localhost dev defaults.
- [ ] **Real provider keys** — set `GOOGLE_AI_STUDIO_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `HUGGINGFACE_API_KEY` for live output (otherwise stub mode).
- [ ] **HTTPS + reverse proxy** — terminate TLS at the proxy; forward `/api` and `/ws` to the backend with the WebSocket `Upgrade` headers.
- [ ] **Production runtime flags** — `DEBUG=false`, `APP_ENV=production`, `LOG_JSON=true`; consider protecting or disabling `/docs`.
- [ ] **Persistent checkpointer** — use the Supabase Postgres checkpointer for durable approval resume; run a **single backend worker** until durable state + external pub/sub are in place.
- [ ] **Supabase RLS applied** — if using Supabase, run `rls.sql` and keep the `service_role` key server-side only.
- [ ] **Workspace boundary** — confirm `WORKSPACE_ROOT` points at the artifact sandbox, never at source directories (the FileManager path-jail enforces this).

---

## 8. Quick local run recap

For local development (Windows + PowerShell, no Docker):

```powershell
# One-time: create the backend venv, install both tiers, seed .env files
pwsh ./scripts/setup.ps1

# Start backend (uvicorn :8000) + frontend (vite :5173) in two windows
pwsh ./scripts/dev.ps1
```

- Frontend: <http://localhost:5173> (proxies `/api` and `/ws` to `:8000`)
- Backend docs: <http://localhost:8000/docs>
- The app runs **open** (no login) by default; set `AUTH_ENABLED=true` in `backend/.env` to require login.

### Tests / gates

```powershell
# Backend
backend\.venv\Scripts\python.exe -m pytest        # 70 passed

# Frontend
npm --prefix frontend run build                   # tsc && vite build (exit 0)
npm --prefix frontend run lint                    # eslint --max-warnings 0
npm --prefix frontend run test                    # vitest run
```

---

See also: [`docs/PROJECT_STATE.md`](PROJECT_STATE.md) (authoritative build state),
[`docs/ROADMAP.md`](ROADMAP.md) (phase plan), and
[`docs/SUPABASE_INTEGRATION.md`](SUPABASE_INTEGRATION.md) (full Supabase runbook).
