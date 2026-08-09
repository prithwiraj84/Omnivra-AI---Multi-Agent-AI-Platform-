# Deploying Omnivra — Hugging Face Space + Vercel + Supabase (free tier)

A free, performance-tuned split:

| Piece | Host | What it is |
|---|---|---|
| **Frontend** (Vite SPA) | **Vercel** (Hobby) | static `dist/`, talks to the backend over HTTPS/WSS |
| **Backend** (FastAPI) | **Hugging Face Docker Space** (CPU-basic, ~2 vCPU / 16 GB) | the API, agents, realtime `/ws`, Document/Social studios |
| **Data** (optional) | **Supabase** (free) | Postgres + pgvector + Storage |

> **Two things to accept up front on the free tier:** (1) a free Space's disk is **ephemeral** — `workspace/` (runs, artifacts, memory) resets on rebuild/restart, so put durable state in Supabase; (2) the **universal app-runner is disabled** on the Space (`APP_RUNNER_ENABLED=false`) — its “Open app” port isn’t reachable on a shared host and running generated code there is a security/AUP risk. Generated apps with a static HTML frontend still open via **Preview** (the backend serves their files — file serving, not code execution); server-side apps use **Download-as-ZIP** and run locally.

---

## 1) Supabase (optional but recommended for durable state)

1. Create a project at <https://supabase.com> → **New project**.
2. **SQL Editor** → paste `supabase/seed.sql` → **Run** (creates tables + seeds the model/agent registry; pgvector ships enabled).
3. **Project Settings → API** → copy: `Project URL`, `anon` key, `service_role` key.
4. (Optional, for artifact durability) **Storage → New bucket** named `omnivra-artifacts`.
5. Keep these for the backend secrets below: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.

Skip this and the app still runs (file-based stores) — but data won’t survive a Space restart.

---

## 2) Backend → Hugging Face Docker Space

The `backend/` folder is **already a Space**: `backend/Dockerfile` builds it and `backend/README.md` carries the `sdk: docker` / `app_port: 7860` frontmatter.

1. <https://huggingface.co/new-space> → **SDK: Docker** → **Blank** → create.
2. Push the **contents of `backend/`** to the Space repo root (so `Dockerfile` + `README.md` are at the top):
   ```bash
   git clone https://huggingface.co/spaces/<user>/<space> hf-space
   cp -r backend/* backend/.dockerignore hf-space/      # copy backend INTO the space root
   cd hf-space && git add -A && git commit -m "Omnivra backend" && git push
   ```
3. **Space → Settings → Variables and secrets** — add (secrets for keys, variables for the rest):
   - **Provider keys** (comma-separate several free keys per provider for the key-pool failover):
     `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `GOOGLE_AI_STUDIO_API_KEY`, `HUGGINGFACE_API_KEY`
   - **Security (PUBLIC space → turn auth ON):**
     `AUTH_ENABLED=true`, `ADMIN_USERNAME=...`, `ADMIN_PASSWORD=...`, `API_SECRET_KEY=<random>`, `RATE_LIMIT_ENABLED=true`
   - **CORS** (your Vercel URL — fill after step 3, then redeploy): `CORS_ORIGINS=https://<your-app>.vercel.app`
   - **Runner off:** `APP_RUNNER_ENABLED=false`
   - **Supabase (if used):** `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
   - Already defaulted by the Dockerfile: `APP_ENV=production`, `DEBUG=false`, `WORKSPACE_ROOT=/home/user/app/workspace`, `PORT=7860`.
4. Wait for the build → your backend is at **`https://<user>-<space>.hf.space`**. Check `…/health` and `…/docs`.

---

## 3) Frontend → Vercel

1. <https://vercel.com/new> → import the repo → **Root Directory = `frontend`** (Vercel auto-detects Vite; `frontend/vercel.json` adds the SPA fallback).
2. **Environment Variables** (Production) — `VITE_API_BASE_URL` is the backend **origin** (no `/api`; the app appends it):
   ```
   VITE_API_BASE_URL = https://<user>-<space>.hf.space
   VITE_WS_URL       = wss://<user>-<space>.hf.space/ws
   ```
   (see `frontend/.env.production.example`)
3. **Deploy.** You’ll get `https://<your-app>.vercel.app`.
4. **Go back to the Space** → set `CORS_ORIGINS=https://<your-app>.vercel.app` → **Restart** the Space (CORS is read at startup). Auth on? Log in with your admin creds.

---

## Performance — what’s already tuned

- **Gzip** on all JSON/text responses (`GZipMiddleware`) — the dashboard/artifact payloads shrink ~5–10×.
- **Dashboard payload cache** (`DASHBOARD_CACHE_TTL=2.0s`): the SPA polls every few seconds across clients; one rebuild is shared instead of re-scanning every project per request. Set `0` to disable.
- **Single uvicorn worker** + `uvloop`/`httptools` (from `uvicorn[standard]`): the in-memory stores (usage counters, realtime hub, run registry) must not be duplicated — scale **out** (more Spaces), never with `--workers > 1` here.
- **`--proxy-headers --forwarded-allow-ips='*'`** so client scheme/IP are correct behind the HF + Vercel proxies.
- **Lazy heavy imports**: the PPTX/DOCX/PDF and moviepy engines import only when used, so idle RAM stays low.
- **Startup reaper**: orphaned `running` workflow runs are swept to `failed` so the dashboard never shows a stale agent “working”.

### Recommended free-tier tuning
- **Keep it warm:** a free Space sleeps after ~48 h idle. Point a free uptime pinger (UptimeRobot / cron-job.org) at `…/health` (stay within fair use).
- **Offload state to Supabase** so restarts/sleeps don’t lose data (file stores reset on the Space’s ephemeral disk).
- **More provider keys** = more agent throughput. The real ceiling is LLM **free quota**, not CPU — comma-separate several OpenRouter/Groq/Gemini keys (`KEY1,KEY2,...`); the pool rotates + cross-provider fallback keeps runs alive.
- Leave reels in **stub mode** (the image omits moviepy) unless you need real `.mp4` — it’s heavy on 2 vCPU.

## Caveats (free tier)
- **Ephemeral disk** → durable data needs Supabase (and Storage/R2 for artifacts).
- **App-runner disabled** on the Space (Download-ZIP + run locally instead).
- **Sleeps when idle** (~48 h) → first request after sleep is a cold start.
- **Public by default** → keep `AUTH_ENABLED=true` or anyone can spend your quota.

## Verify
- [ ] `https://<space>.hf.space/health` → `{"status":"ok"}`
- [ ] Vercel app loads; the dashboard shows live data (not the offline fallback)
- [ ] the live `/ws` indicator is connected (top bar)
- [ ] generating a document works; downloading the file works (media URL points at the Space)
- [ ] (auth on) login required; bad creds rejected
