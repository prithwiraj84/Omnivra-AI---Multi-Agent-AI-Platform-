# backend/db — database access layer

This package will hold the **Python** data-access layer (Phase 2+): a cached Supabase
client and repository modules. It does **not** contain SQL.

## Where the schema lives

The canonical database schema, policies, and seed data live under **`supabase/`** at the
repo root (single source of truth):

| File | Purpose |
|---|---|
| `supabase/schema.sql` | Extensions (`vector`, `pgcrypto`), all tables, enums, indexes (incl. the vector index), `updated_at` triggers. |
| `supabase/rls.sql` | Row Level Security: enable RLS + baseline policies (service-role full access, authenticated reads). |
| `supabase/seed.sql` | Seed departments, the full agent roster, and providers/models so the dashboard has live data. |
| `docs/SUPABASE_INTEGRATION.md` | Step-by-step setup: create project, enable pgvector, migration order, env wiring, Storage, Realtime. |

Run order in the Supabase SQL editor: **`schema.sql` → `rls.sql` → `seed.sql`**.

## Phase 2 — client wiring (planned)

- `backend/app/db/client.py` — a cached `create_client(SUPABASE_URL, SERVICE_ROLE_KEY)` for
  server-side reads/writes (the anon key is for the frontend only).
- `backend/app/db/repositories/` — typed repository modules (projects, workflows, tasks,
  approvals, activity) that replace direct table access.

Env vars are defined in `backend/.env.example` (`SUPABASE_URL`, `SUPABASE_ANON_KEY`,
`SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL`, `SUPABASE_STORAGE_BUCKET`).
