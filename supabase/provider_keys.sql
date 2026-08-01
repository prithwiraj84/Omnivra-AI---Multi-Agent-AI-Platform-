-- ===========================================================================
-- Per-user provider API keys (cp-0069)
-- ---------------------------------------------------------------------------
-- Run this in Supabase -> SQL Editor (after schema.sql). It makes in-app API
-- keys DURABLE and PER USER.
--
-- Why it's required for any hosted deployment: container filesystems on
-- Hugging Face Spaces / Render / Fly are EPHEMERAL, so keys written to
-- workspace/.state/provider_keys.json vanish on the next restart — which is
-- exactly the "I saved my keys and they say Not configured again" symptom.
--
-- owner_id is the Supabase auth user id (text) in per-user mode, or the admin
-- username in single-admin mode. `provider` is a catalog id ('openrouter',
-- 'groq', …) or a social connector field ('twitter_api_key', …).
-- ===========================================================================

create table if not exists public.provider_keys (
  owner_id    text        not null,
  provider    text        not null,
  value       text        not null,
  updated_at  timestamptz not null default now(),
  primary key (owner_id, provider)
);

comment on table public.provider_keys is
  'Per-user LLM/media/social credentials set from the app. Server-only: the backend reads and writes these with the service-role key; never expose to the browser.';

create index if not exists idx_provider_keys_owner on public.provider_keys (owner_id);

-- Keep updated_at honest on upsert.
create or replace function public.touch_provider_keys()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end; $$;

drop trigger if exists trg_provider_keys_touch on public.provider_keys;
create trigger trg_provider_keys_touch
  before update on public.provider_keys
  for each row execute function public.touch_provider_keys();

-- ---------------------------------------------------------------------------
-- RLS: DENY ALL to anon/authenticated. These are secrets — only the backend,
-- which uses the service-role key (and therefore bypasses RLS), may touch them.
-- Enabling RLS with no permissive policy is the lockdown.
-- ---------------------------------------------------------------------------
alter table public.provider_keys enable row level security;
revoke all on public.provider_keys from anon, authenticated;

-- Verify:
--   select count(*) from public.provider_keys;                        -- works as service_role
--   select relrowsecurity from pg_class where relname='provider_keys'; -- must be true
