# Supabase Integration Plan - Omnivra AI Company OS

This runbook wires the Omnivra backend (FastAPI) and frontend (Vite/React) to a
Supabase Cloud project: Postgres + pgvector for data and embeddings, Storage for
artifacts, and Realtime for live dashboard updates.

> Embedding dimension is standardized to **1536** across `knowledge_base` and
> `memory`. If you switch embedders, change `vector(1536)` in `schema.sql` and the
> two `match_*` RPCs, then re-run the migration.

---

## 1. Create the Supabase project

1. Go to https://supabase.com/dashboard and create a new project.
2. Choose a region close to your backend host. Save the **database password**.
3. From **Project Settings -> API**, copy:
   - `Project URL` (e.g. `https://xxxx.supabase.co`)
   - `anon` public key (frontend)
   - `service_role` secret key (backend only — never ship to the browser)
4. From **Project Settings -> Database**, copy the connection string (for psql /
   migration tooling).

---

## 2. Enable extensions (pgvector + pgcrypto)

The migrations call `create extension if not exists vector;` so running them is
enough. To enable manually first: **Dashboard -> Database -> Extensions**, enable
`vector`, `pgcrypto`, and `pg_trgm`. (`vector` is preinstalled on Supabase; you
just enable it.)

---

## 3. Run migrations (strict order)

Apply the SQL files **in this order** — later files depend on earlier ones:

| Order | File                     | Purpose                                   |
|-------|--------------------------|-------------------------------------------|
| 1     | `supabase/schema.sql`    | Extensions, enums, tables, indexes, RPCs  |
| 2     | `supabase/rls.sql`       | Enable RLS + baseline policies            |
| 3     | `supabase/seed.sql`      | Departments, providers, models, agents    |

### Option A — Supabase SQL Editor (fastest)
Paste each file's contents into **Dashboard -> SQL Editor** and run, in order.

### Option B — psql
```powershell
$env:PGPASSWORD = "<db-password>"
$DB = "postgresql://postgres.<ref>:<db-password>@aws-0-<region>.pooler.supabase.com:5432/postgres"
psql $DB -f supabase/schema.sql
psql $DB -f supabase/rls.sql
psql $DB -f supabase/seed.sql
```

### Option C - Supabase CLI (optional, for repeatable migrations)
> The canonical layout is the flat `supabase/{schema,rls,seed}.sql` (Options A/B). The CLI
> workflow below is an optional alternative: it copies those same three files into the CLI's
> `supabase/migrations/` folder with timestamp prefixes. It does not replace the flat files.
```powershell
supabase init
# copy the three canonical files into supabase/migrations/ with timestamp prefixes, e.g.:
#   20260101000001_schema.sql, 20260101000002_rls.sql, 20260101000003_seed.sql
supabase link --project-ref <ref>
supabase db push
```

---

## 4. auth.users -> profiles trigger

`profiles.id` references `auth.users(id)`. Create a profile automatically on
signup (run once, after `schema.sql`):

```sql
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, full_name, avatar_url)
  values (new.id, new.email,
          new.raw_user_meta_data->>'full_name',
          new.raw_user_meta_data->>'avatar_url')
  on conflict (id) do nothing;
  return new;
end; $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
```

After your first user signs up, re-run `seed.sql` to create the demo project, or
create projects via the backend.

---

## 5. Backend env wiring (FastAPI + supabase-py)

`workspace`-external backend config lives in the project `.env` (Phase 1 backend
scaffold). Required variables:

```env
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service_role secret>   # backend only
SUPABASE_ANON_KEY=<anon public key>               # passed to frontend build
SUPABASE_DB_URL=postgresql://postgres.<ref>:<pw>@...pooler.supabase.com:5432/postgres
SUPABASE_STORAGE_BUCKET_DOCUMENTS=documents
SUPABASE_STORAGE_BUCKET_PRESENTATIONS=presentations
SUPABASE_STORAGE_BUCKET_MEDIA=media
EMBED_DIM=1536
```

Client (service role — bypasses RLS, used by all agent/DB writes):
```python
# backend/app/db/supabase_client.py
from functools import lru_cache
from supabase import create_client, Client
from app.core.config import settings

@lru_cache
def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
```

Vector search via RPC:
```python
res = get_supabase().rpc("match_knowledge", {
    "query_embedding": embedding,        # list[float] length 1536
    "match_count": 5,
    "p_project_id": project_id,
}).execute()
```

> The backend uses the **service_role** key, so RLS does not block it. The RLS
> policies in `rls.sql` exist to protect any direct frontend (anon/authenticated)
> reads.

---

## 6. Storage buckets

Create four buckets (**Dashboard -> Storage**, or via API):

| Bucket          | Public | Used by                                  |
|-----------------|--------|------------------------------------------|
| `avatars`       | public | profile images                           |
| `documents`     | private| documents/reports/specs (Documentation) |
| `presentations` | private| exported decks (Presentation Designer)   |
| `media`         | private| STT inputs, TTS/image outputs (media_jobs)|

Rows in `documents` / `media_jobs` store `storage_bucket` + `storage_path` keys;
the backend generates **signed URLs** for downloads. Example policy for a private
bucket (members of the owning project):
```sql
create policy "members read documents" on storage.objects
  for select to authenticated
  using (bucket_id = 'documents' /* + path-based project scoping in app layer */);
```
The backend (service role) handles uploads/signed URLs, so strict object-level
RLS is optional for Phase 1.

---

## 7. Realtime channels

Enable Realtime on the tables that drive the live dashboard. **Dashboard ->
Database -> Replication**, add these to the `supabase_realtime` publication
(or via SQL):
```sql
alter publication supabase_realtime add table
  public.tasks, public.workflows, public.workflow_steps,
  public.approvals, public.activity_events, public.notifications,
  public.agent_status_snapshots, public.system_health_metrics, public.media_jobs;
```
Frontend subscription example:
```ts
const ch = supabase
  .channel('dashboard')
  .on('postgres_changes',
      { event: '*', schema: 'public', table: 'activity_events' },
      (p) => pushActivity(p.new))
  .on('postgres_changes',
      { event: 'UPDATE', schema: 'public', table: 'tasks' },
      (p) => updateTask(p.new))
  .subscribe();
```

---

## 8. How FastAPI WebSockets relate to Supabase Realtime

Two complementary live channels:

- **Supabase Realtime** broadcasts raw DB row changes (INSERT/UPDATE/DELETE) to
  the frontend. Best for dashboard widgets that mirror table state: activity
  feed, task/workflow progress, agent status, pending approvals badge.
- **FastAPI WebSockets** (`/ws`) carry *application* events the backend owns and
  that are not 1:1 with a single row write: streaming LLM token output, the
  human approval gate handshake (Approve/Reject/Retry/Rollback resume), kill-
  switch notices (recursion_count > 3 -> FAILED), and checkpoint/resume status.

Recommended split:
1. Persist every meaningful event to Postgres (`activity_events`, `tasks`,
   `approvals`, `checkpoints`). Realtime fans these out automatically.
2. Use FastAPI WS for low-latency streaming + the interactive approval loop. When
   a user clicks Approve/Reject/Retry/Rollback, the frontend POSTs (or sends a WS
   message); the backend updates the `approvals` row (status, decided_by,
   decided_at) which both resumes the LangGraph workflow and triggers a Realtime
   update for other viewers.

This keeps Postgres as the single source of truth, with Realtime for state
mirroring and FastAPI WS for interactive/streaming control.

---

## 9. Verification checklist

- [ ] `select extname from pg_extension;` includes `vector`, `pgcrypto`, `pg_trgm`.
- [ ] `select count(*) from public.agents;` returns 23 (full roster).
- [ ] `select count(*) from public.departments;` returns 10.
- [ ] `\d+ public.knowledge_base` shows the `idx_kb_embedding_hnsw` HNSW index.
- [ ] RLS enabled on all tables: `select relname, relrowsecurity from pg_class
      where relnamespace='public'::regnamespace and relkind='r';`
- [ ] A test `rpc('match_knowledge', ...)` returns rows after inserting one
      embedded chunk.
- [ ] Realtime publication lists the dashboard tables.

---

## 10. Frontend OAuth — Google / GitHub sign-in (Phase 2)

The frontend signs users in with **Google** or **GitHub** through Supabase Auth (PKCE flow).
It is **optional**: with no `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` (or placeholder
values) the client is `null`, the social buttons are disabled, and the app stays in open mode.

### 10.1 Frontend env (`frontend/.env.local`, and Vercel for prod)
```env
VITE_SUPABASE_URL=https://<ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon public key>   # browser-safe (RLS-scoped)
```
Vite inlines these at **build time** — a change needs a redeploy.

> **Backend-auth interplay.** OAuth establishes a *frontend* Supabase session; it does not
> mint a backend bearer token. The recommended deployment keeps the backend in **open mode**
> (`AUTH_ENABLED=false`, the default) and uses Supabase OAuth as the frontend gate — then
> `AuthGate` lets an OAuth session in and the API is open. If you also set backend
> `AUTH_ENABLED=true`, an OAuth user reaches the UI (AuthGate accepts the Supabase session)
> but backend API calls will 401 until the backend is taught to verify the Supabase JWT
> (future work). Don't enable backend auth alongside OAuth unless you add that verification.

### 10.2 Allow your redirect URLs
**Dashboard → Authentication → URL Configuration**:
- **Site URL**: your prod origin, e.g. `https://<your-app>.vercel.app`
- **Redirect URLs** (add every origin you use — one per line):
  - `http://localhost:5173/auth/callback`
  - `https://<your-app>.vercel.app/auth/callback`

The app always redirects back to **`<origin>/auth/callback`** (see `lib/supabase.ts` →
`authRedirectTo()`), which finalizes the session and forwards to `/dashboard`.

### 10.3 Enable the providers
**Dashboard → Authentication → Providers**:

**Google** — enable, then paste a Google OAuth **Client ID** + **Client Secret**
(Google Cloud Console → APIs & Services → Credentials → *OAuth client ID* → *Web application*).
In Google's client, set the **Authorized redirect URI** to the value Supabase shows on the
Google provider page: `https://<ref>.supabase.co/auth/v1/callback`.

**GitHub** — enable, then paste a GitHub OAuth App **Client ID** + **Client Secret**
(GitHub → Settings → Developer settings → OAuth Apps → *New OAuth App*). Set the app's
**Authorization callback URL** to `https://<ref>.supabase.co/auth/v1/callback`.

> The provider redirect URI is Supabase's `/auth/v1/callback` (NOT the app's
> `/auth/callback`). Supabase receives the provider code, then bounces the browser to your
> app's `/auth/callback` from the allow-list in 10.2.

### 10.4 Profiles
Section 4's `handle_new_user()` trigger already copies `full_name` + `avatar_url` from
`raw_user_meta_data` into `public.profiles` on first sign-in — which is exactly what the
topbar/account menu render (Google `full_name`/`picture`, GitHub `name`/`user_name`/`avatar_url`).

### 10.5 Verify
- [ ] `/login` shows **Continue with Google/GitHub** (enabled) + the credentials fallback.
- [ ] Clicking a provider redirects to it, then back to `/auth/callback`, then `/dashboard`.
- [ ] The topbar avatar shows the provider photo/initials and **Sign out** clears the session.
- [ ] A row appears in `auth.users` (and `public.profiles`) after first sign-in.
