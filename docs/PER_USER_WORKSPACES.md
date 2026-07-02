# Per-user private workspaces

Omnivra runs in one of two modes, decided by a single backend setting:

| Mode | When | Identity | Data |
|------|------|----------|------|
| **Single-admin (open)** | `SUPABASE_JWT_SECRET` unset (default) | one admin | one shared workspace, no login required by the API |
| **Per-user (multi-tenant)** | `SUPABASE_JWT_SECRET` set | each Supabase user | every user gets a private set of projects |

## Enabling per-user mode
1. Frontend: require login — this is automatic whenever Supabase is configured (see `AuthGate`).
   Visiting the app without a session redirects to `/login`.
2. Backend: set **`SUPABASE_JWT_SECRET`** (Supabase → Settings → API → **JWT Secret**) in
   `backend/.env`. That flips the API into per-user mode.

Once set, the frontend sends each request the user's **Supabase access token**, and the backend
**verifies it** (HS256, `aud=authenticated`) to get a trustworthy user id (`sub`). Requests
without a valid token get `401`.

## What "private" means here
Scoped to the signed-in user (`sub`):
- **Projects** — you only list / open / delete your own. A foreign project id returns `404`
  (not `403`, so existence isn't revealed) — this also protects everything addressed by
  `X-Project-Id`: workspace files, workflows/runs, documents, knowledge, memory, social drafts, media.
- **Tasks** — only tasks inside your projects.
- **Dashboard** — stats, workflows, activity, approvals, tasks, usage are all computed from *your*
  projects only (and the dashboard cache is keyed per user).
- **Approvals** — you can only decide on a workflow that belongs to you.

Each user also gets their own **Default Workspace** (created on first use) for unfiled runs.

## Behavior of existing data (the two setup decisions)
- **New users start empty** — no seeded demo projects; you create your first project yourself.
- **Pre-existing projects stay admin-only** — projects created before per-user mode (the demo
  seeds, or anything made in open mode) belong to the admin and are **hidden from Supabase users**.
  They remain visible when the backend runs in open mode (locally, no JWT secret).

## Not user-scoped (by design)
- The **agent roster** and **system health** (global platform state, not user data).
- **Provider API keys / social connectors** — these are the app's shared, admin-managed
  credentials (all users run on the same configured providers).
- The `activity` / `approvals` / `workflows` *list* endpoints still return seed/demo items; the
  real, per-user operational data is what the **dashboard** shows (and it is scoped).

## Notes
- Supabase access tokens are short-lived; supabase-js auto-refreshes them and the axios
  interceptor always sends the freshest one.
- Tests run in open mode (`conftest` neutralizes `SUPABASE_JWT_SECRET`); `test_user_isolation.py`
  turns the secret on and asserts two users can't see each other's projects/tasks/dashboard.
