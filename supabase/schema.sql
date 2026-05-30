-- =============================================================================
-- Omnivra AI Company OS - Database Schema
-- Target: Supabase (PostgreSQL 15+) with pgvector
-- Phase: 1 (core data model)
-- Run order: 1) schema.sql  2) rls.sql  3) seed.sql
-- =============================================================================
-- This file is idempotent-friendly where practical. It assumes a clean schema
-- in the `public` namespace. Vector dimension is standardized to 1536 to match
-- common embedding models; adjust EMBED_DIM below if you change embedders.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Extensions
-- ---------------------------------------------------------------------------
create extension if not exists pgcrypto;      -- gen_random_uuid()
create extension if not exists vector;        -- pgvector embeddings
create extension if not exists pg_trgm;       -- fuzzy text search on names/titles

-- ---------------------------------------------------------------------------
-- 1. Enum types (created defensively so re-runs do not error)
-- ---------------------------------------------------------------------------
do $$ begin
  create type app_role            as enum ('owner','admin','member','viewer');
  create type plan_tier           as enum ('free','pro','team','enterprise');
  create type project_status       as enum ('active','paused','archived','completed');
  create type provider_kind        as enum ('google_ai_studio','openrouter','groq','huggingface','openai','anthropic','internal');
  create type model_modality       as enum ('text','vision','audio_stt','audio_tts','image','embedding','multimodal');
  create type agent_status         as enum ('online','offline','busy','degraded','error');
  create type task_status          as enum ('queued','running','blocked','awaiting_approval','completed','failed','cancelled');
  create type task_priority        as enum ('low','medium','high','critical');
  create type workflow_status      as enum ('draft','running','paused','awaiting_approval','completed','failed','cancelled');
  create type step_status          as enum ('pending','running','succeeded','failed','skipped','awaiting_approval');
  create type approval_status      as enum ('pending','approved','rejected','retry','rollback');
  create type approval_kind        as enum ('content_publish','code_artifact','presentation_export','workflow_gate','custom');
  create type notification_level   as enum ('info','success','warning','error','critical');
  create type activity_kind        as enum ('task','workflow','agent','approval','system','media','security','memory');
  create type document_kind        as enum ('doc','report','presentation','spec','diagram','other');
  create type media_job_type       as enum ('stt','tts','image');
  create type media_job_status     as enum ('queued','processing','completed','failed');
  create type checkpoint_kind      as enum ('workflow','task','manual','auto');
  create type health_resource      as enum ('cpu','memory','storage','network','api_quota');
exception
  when duplicate_object then null;
end $$;

-- ---------------------------------------------------------------------------
-- 2. Shared updated_at trigger function
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ===========================================================================
-- 3. Identity & Org
-- ===========================================================================

-- Mirrors auth.users (Supabase Auth) with app-level profile data.
create table if not exists public.profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       text unique not null,
  full_name   text,
  avatar_url  text,
  role        app_role not null default 'member',
  plan        plan_tier not null default 'free',
  storage_used_bytes  bigint not null default 0,
  storage_quota_bytes bigint not null default 5368709120, -- 5 GB
  settings    jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create table if not exists public.projects (
  id           uuid primary key default gen_random_uuid(),
  owner_id     uuid not null references public.profiles(id) on delete cascade,
  name         text not null,
  slug         text unique not null,
  description  text,
  status       project_status not null default 'active',
  metadata     jsonb not null default '{}'::jsonb,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index if not exists idx_projects_owner  on public.projects(owner_id);
create index if not exists idx_projects_status on public.projects(status);

-- Multi-user access to a project (basis for RLS membership checks).
create table if not exists public.project_members (
  project_id  uuid not null references public.projects(id) on delete cascade,
  user_id     uuid not null references public.profiles(id) on delete cascade,
  role        app_role not null default 'member',
  created_at  timestamptz not null default now(),
  primary key (project_id, user_id)
);
create index if not exists idx_project_members_user on public.project_members(user_id);

-- ===========================================================================
-- 4. Agent System: departments, providers, models, agents
-- ===========================================================================

create table if not exists public.departments (
  id          uuid primary key default gen_random_uuid(),
  key         text unique not null,           -- 'executive','architecture',...
  name        text not null,
  description text,
  icon        text,                           -- lucide icon name
  accent      text,                           -- hex accent for UI
  sort_order  int not null default 0,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create table if not exists public.providers (
  id          uuid primary key default gen_random_uuid(),
  key         provider_kind not null,
  name        text not null,                  -- 'OpenRouter', 'Groq', ...
  base_url    text,
  docs_url    text,
  is_active   boolean not null default true,
  metadata    jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  unique (key, name)
);

create table if not exists public.models (
  id                 uuid primary key default gen_random_uuid(),
  provider_id        uuid not null references public.providers(id) on delete restrict,
  model_id           text not null,           -- e.g. 'openai/gpt-oss-120b:free'
  display_name       text not null,
  modality           model_modality not null default 'text',
  context_window     int,
  input_cost_per_1k  numeric(12,6) not null default 0,   -- USD
  output_cost_per_1k numeric(12,6) not null default 0,   -- USD
  is_free            boolean not null default false,
  is_active          boolean not null default true,
  metadata           jsonb not null default '{}'::jsonb,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  unique (provider_id, model_id)
);
create index if not exists idx_models_provider on public.models(provider_id);
create index if not exists idx_models_modality on public.models(modality);

create table if not exists public.agents (
  id            uuid primary key default gen_random_uuid(),
  key           text unique not null,          -- 'ceo_manager','solution_architect',...
  name          text not null,
  title         text,                          -- 'CEO / Manager'
  department_id uuid not null references public.departments(id) on delete restrict,
  provider_id   uuid references public.providers(id) on delete set null,
  model_id      uuid references public.models(id) on delete set null,
  status        agent_status not null default 'online',
  icon          text,
  description   text,
  system_prompt text,
  capabilities  jsonb not null default '[]'::jsonb,
  config        jsonb not null default '{}'::jsonb,
  is_system     boolean not null default false, -- System Ops / Media helpers
  sort_order    int not null default 0,
  last_active_at timestamptz,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index if not exists idx_agents_department on public.agents(department_id);
create index if not exists idx_agents_status     on public.agents(status);
create index if not exists idx_agents_model      on public.agents(model_id);

-- Periodic point-in-time snapshots for the Agents Status grid / sparklines.
create table if not exists public.agent_status_snapshots (
  id          uuid primary key default gen_random_uuid(),
  agent_id    uuid not null references public.agents(id) on delete cascade,
  status      agent_status not null,
  active_tasks int not null default 0,
  captured_at timestamptz not null default now()
);
create index if not exists idx_agent_snap_agent_time on public.agent_status_snapshots(agent_id, captured_at desc);

-- ===========================================================================
-- 5. Execution: workflows, steps, tasks, logs, checkpoints
-- ===========================================================================

create table if not exists public.workflows (
  id              uuid primary key default gen_random_uuid(),
  project_id      uuid not null references public.projects(id) on delete cascade,
  name            text not null,
  description     text,
  status          workflow_status not null default 'draft',
  progress        int not null default 0 check (progress between 0 and 100),
  recursion_count int not null default 0,      -- kill switch: STOP if > 3
  langgraph_state jsonb not null default '{}'::jsonb,
  current_step_id uuid,                         -- FK added after workflow_steps
  started_at      timestamptz,
  completed_at    timestamptz,
  created_by      uuid references public.profiles(id) on delete set null,
  metadata        jsonb not null default '{}'::jsonb,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists idx_workflows_project on public.workflows(project_id);
create index if not exists idx_workflows_status  on public.workflows(status);

create table if not exists public.workflow_steps (
  id           uuid primary key default gen_random_uuid(),
  workflow_id  uuid not null references public.workflows(id) on delete cascade,
  agent_id     uuid references public.agents(id) on delete set null,
  name         text not null,
  step_index   int not null,
  status       step_status not null default 'pending',
  input        jsonb not null default '{}'::jsonb,
  output       jsonb not null default '{}'::jsonb,
  error        text,
  retries      int not null default 0,
  started_at   timestamptz,
  completed_at timestamptz,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  unique (workflow_id, step_index)
);
create index if not exists idx_steps_workflow on public.workflow_steps(workflow_id);
create index if not exists idx_steps_agent    on public.workflow_steps(agent_id);

-- Deferred FK: workflows.current_step_id -> workflow_steps.id
do $$ begin
  alter table public.workflows
    add constraint fk_workflows_current_step
    foreign key (current_step_id) references public.workflow_steps(id) on delete set null;
exception
  when duplicate_object then null;
end $$;

create table if not exists public.tasks (
  id           uuid primary key default gen_random_uuid(),
  project_id   uuid not null references public.projects(id) on delete cascade,
  workflow_id  uuid references public.workflows(id) on delete set null,
  step_id      uuid references public.workflow_steps(id) on delete set null,
  agent_id     uuid references public.agents(id) on delete set null,
  parent_task_id uuid references public.tasks(id) on delete set null, -- delegation tree
  title        text not null,
  description  text,
  status       task_status not null default 'queued',
  priority     task_priority not null default 'medium',
  progress     int not null default 0 check (progress between 0 and 100),
  input        jsonb not null default '{}'::jsonb,
  result       jsonb not null default '{}'::jsonb,
  error        text,
  retries      int not null default 0,
  started_at   timestamptz,
  completed_at timestamptz,
  created_by   uuid references public.profiles(id) on delete set null,
  metadata     jsonb not null default '{}'::jsonb,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index if not exists idx_tasks_project  on public.tasks(project_id);
create index if not exists idx_tasks_workflow on public.tasks(workflow_id);
create index if not exists idx_tasks_agent    on public.tasks(agent_id);
create index if not exists idx_tasks_status   on public.tasks(status);
create index if not exists idx_tasks_parent   on public.tasks(parent_task_id);
create index if not exists idx_tasks_created  on public.tasks(created_at desc);

-- Append-only execution logs per task (feeds Log Analyzer + activity).
create table if not exists public.task_logs (
  id         uuid primary key default gen_random_uuid(),
  task_id    uuid not null references public.tasks(id) on delete cascade,
  level      notification_level not null default 'info',
  message    text not null,
  data       jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_task_logs_task_time on public.task_logs(task_id, created_at desc);

-- Checkpoints: resume-from-last-checkpoint + file manifest snapshot.
create table if not exists public.checkpoints (
  id            uuid primary key default gen_random_uuid(),
  project_id    uuid not null references public.projects(id) on delete cascade,
  workflow_id   uuid references public.workflows(id) on delete cascade,
  task_id       uuid references public.tasks(id) on delete set null,
  kind          checkpoint_kind not null default 'auto',
  label         text,
  state         jsonb not null default '{}'::jsonb,   -- full LangGraph/project state
  file_manifest jsonb not null default '[]'::jsonb,   -- [{path,hash,size,phase}]
  is_latest     boolean not null default true,
  created_at    timestamptz not null default now()
);
create index if not exists idx_checkpoints_project  on public.checkpoints(project_id, created_at desc);
create index if not exists idx_checkpoints_workflow on public.checkpoints(workflow_id, created_at desc);
create index if not exists idx_checkpoints_latest   on public.checkpoints(workflow_id) where is_latest;

-- ===========================================================================
-- 6. Governance: approvals, notifications, activity feed
-- ===========================================================================

create table if not exists public.approvals (
  id           uuid primary key default gen_random_uuid(),
  project_id   uuid not null references public.projects(id) on delete cascade,
  workflow_id  uuid references public.workflows(id) on delete cascade,
  step_id      uuid references public.workflow_steps(id) on delete set null,
  task_id      uuid references public.tasks(id) on delete set null,
  kind         approval_kind not null default 'workflow_gate',
  title        text not null,
  summary      text,
  payload      jsonb not null default '{}'::jsonb,    -- artifact preview/diff
  status       approval_status not null default 'pending',
  priority     task_priority not null default 'medium',
  requested_by uuid references public.agents(id) on delete set null,
  decided_by   uuid references public.profiles(id) on delete set null,
  decision_note text,
  decided_at   timestamptz,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index if not exists idx_approvals_project on public.approvals(project_id);
create index if not exists idx_approvals_status  on public.approvals(status);
create index if not exists idx_approvals_pending on public.approvals(created_at desc) where status = 'pending';

create table if not exists public.notifications (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references public.profiles(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  level      notification_level not null default 'info',
  title      text not null,
  body       text,
  link       text,
  is_read    boolean not null default false,
  data       jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_notifications_user on public.notifications(user_id, created_at desc);
create index if not exists idx_notifications_unread on public.notifications(user_id) where is_read = false;

-- Live Activity Feed (events from agents/system).
create table if not exists public.activity_events (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references public.projects(id) on delete cascade,
  kind        activity_kind not null default 'system',
  agent_id    uuid references public.agents(id) on delete set null,
  task_id     uuid references public.tasks(id) on delete set null,
  workflow_id uuid references public.workflows(id) on delete set null,
  title       text not null,
  message     text,
  level       notification_level not null default 'info',
  data        jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now()
);
create index if not exists idx_activity_project_time on public.activity_events(project_id, created_at desc);
create index if not exists idx_activity_kind on public.activity_events(kind);

-- ===========================================================================
-- 7. Knowledge & Memory (pgvector)
-- ===========================================================================

-- Generated artifacts and uploaded files (Supabase Storage references).
create table if not exists public.documents (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid not null references public.projects(id) on delete cascade,
  agent_id    uuid references public.agents(id) on delete set null,
  task_id     uuid references public.tasks(id) on delete set null,
  kind        document_kind not null default 'doc',
  title       text not null,
  description text,
  storage_bucket text,                          -- e.g. 'documents'
  storage_path   text,                          -- object key inside bucket
  mime_type   text,
  size_bytes  bigint,
  version     int not null default 1,
  is_published boolean not null default false,
  metadata    jsonb not null default '{}'::jsonb,
  created_by  uuid references public.profiles(id) on delete set null,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists idx_documents_project on public.documents(project_id);
create index if not exists idx_documents_kind    on public.documents(kind);

-- Knowledge Base: chunked, embedded content for RAG. EMBED_DIM = 1536.
create table if not exists public.knowledge_base (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references public.projects(id) on delete cascade,
  document_id uuid references public.documents(id) on delete cascade,
  title       text,
  content     text not null,
  chunk_index int not null default 0,
  source      text,
  embedding   vector(1536),
  metadata    jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists idx_kb_project  on public.knowledge_base(project_id);
create index if not exists idx_kb_document on public.knowledge_base(document_id);
-- HNSW index for cosine similarity (pgvector >= 0.5, available on Supabase).
create index if not exists idx_kb_embedding_hnsw
  on public.knowledge_base using hnsw (embedding vector_cosine_ops);

-- Agent/long-term memory vector store (episodic + semantic memory).
create table if not exists public.memory (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references public.projects(id) on delete cascade,
  agent_id    uuid references public.agents(id) on delete set null,
  scope       text not null default 'project',  -- 'global','project','agent','task'
  content     text not null,
  importance  numeric(4,3) not null default 0.5,
  embedding   vector(1536),
  metadata    jsonb not null default '{}'::jsonb,
  last_accessed_at timestamptz,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists idx_memory_project on public.memory(project_id);
create index if not exists idx_memory_agent   on public.memory(agent_id);
create index if not exists idx_memory_embedding_hnsw
  on public.memory using hnsw (embedding vector_cosine_ops);

-- Similarity search RPCs (callable via supabase.rpc(...)).
create or replace function public.match_knowledge(
  query_embedding vector(1536),
  match_count int default 5,
  p_project_id uuid default null,
  similarity_threshold float default 0.0
)
returns table (
  id uuid, document_id uuid, title text, content text,
  similarity float, metadata jsonb
)
language sql stable
as $$
  select kb.id, kb.document_id, kb.title, kb.content,
         1 - (kb.embedding <=> query_embedding) as similarity,
         kb.metadata
  from public.knowledge_base kb
  where kb.embedding is not null
    and (p_project_id is null or kb.project_id = p_project_id)
    and 1 - (kb.embedding <=> query_embedding) >= similarity_threshold
  order by kb.embedding <=> query_embedding
  limit match_count;
$$;

create or replace function public.match_memory(
  query_embedding vector(1536),
  match_count int default 5,
  p_project_id uuid default null,
  p_agent_id uuid default null
)
returns table (
  id uuid, agent_id uuid, content text, importance numeric,
  similarity float, metadata jsonb
)
language sql stable
as $$
  select m.id, m.agent_id, m.content, m.importance,
         1 - (m.embedding <=> query_embedding) as similarity,
         m.metadata
  from public.memory m
  where m.embedding is not null
    and (p_project_id is null or m.project_id = p_project_id)
    and (p_agent_id is null or m.agent_id = p_agent_id)
  order by m.embedding <=> query_embedding
  limit match_count;
$$;

-- ===========================================================================
-- 8. Observability: token usage / cost, system health
-- ===========================================================================

create table if not exists public.token_usage (
  id            uuid primary key default gen_random_uuid(),
  project_id    uuid references public.projects(id) on delete cascade,
  agent_id      uuid references public.agents(id) on delete set null,
  provider_id   uuid references public.providers(id) on delete set null,
  model_id      uuid references public.models(id) on delete set null,
  task_id       uuid references public.tasks(id) on delete set null,
  workflow_id   uuid references public.workflows(id) on delete set null,
  input_tokens  int not null default 0,
  output_tokens int not null default 0,
  total_tokens  int generated always as (input_tokens + output_tokens) stored,
  cost_usd      numeric(14,6) not null default 0,
  latency_ms    int,
  status        text not null default 'success',
  created_at    timestamptz not null default now()
);
create index if not exists idx_usage_project_time on public.token_usage(project_id, created_at desc);
create index if not exists idx_usage_provider on public.token_usage(provider_id);
create index if not exists idx_usage_model    on public.token_usage(model_id);
create index if not exists idx_usage_agent    on public.token_usage(agent_id);

-- Pre-aggregated daily cost rollups (drives stat cards / charts cheaply).
create table if not exists public.cost_rollups (
  id           uuid primary key default gen_random_uuid(),
  project_id   uuid references public.projects(id) on delete cascade,
  provider_id  uuid references public.providers(id) on delete set null,
  model_id     uuid references public.models(id) on delete set null,
  day          date not null,
  total_tokens bigint not null default 0,
  total_cost_usd numeric(14,6) not null default 0,
  request_count int not null default 0,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  unique (project_id, provider_id, model_id, day)
);
create index if not exists idx_rollups_project_day on public.cost_rollups(project_id, day desc);

create table if not exists public.system_health_metrics (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references public.projects(id) on delete cascade,
  resource    health_resource not null,
  value       numeric(6,2) not null,            -- percent 0..100 (or usage)
  unit        text not null default 'percent',
  label       text,                             -- e.g. provider name for api_quota
  captured_at timestamptz not null default now()
);
create index if not exists idx_health_resource_time on public.system_health_metrics(resource, captured_at desc);
create index if not exists idx_health_project on public.system_health_metrics(project_id, captured_at desc);

-- ===========================================================================
-- 9. Media jobs (STT / TTS / Image)
-- ===========================================================================

create table if not exists public.media_jobs (
  id            uuid primary key default gen_random_uuid(),
  project_id    uuid references public.projects(id) on delete cascade,
  agent_id      uuid references public.agents(id) on delete set null,
  task_id       uuid references public.tasks(id) on delete set null,
  job_type      media_job_type not null,
  status        media_job_status not null default 'queued',
  prompt        text,
  input_storage_path  text,
  output_storage_path text,
  output_url    text,
  duration_ms   int,
  error         text,
  metadata      jsonb not null default '{}'::jsonb,
  created_by    uuid references public.profiles(id) on delete set null,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  completed_at  timestamptz
);
create index if not exists idx_media_project on public.media_jobs(project_id);
create index if not exists idx_media_type    on public.media_jobs(job_type);
create index if not exists idx_media_status  on public.media_jobs(status);

-- ===========================================================================
-- 10. Achievements (Recent Achievements row on dashboard)
-- ===========================================================================

create table if not exists public.achievements (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid references public.projects(id) on delete cascade,
  agent_id    uuid references public.agents(id) on delete set null,
  title       text not null,
  description text,
  icon        text,
  accent      text,
  metadata    jsonb not null default '{}'::jsonb,
  achieved_at timestamptz not null default now(),
  created_at  timestamptz not null default now()
);
create index if not exists idx_achievements_project on public.achievements(project_id, achieved_at desc);

-- ===========================================================================
-- 11. Attach updated_at triggers to every mutable table
-- ===========================================================================
do $$
declare
  t text;
  mutable_tables text[] := array[
    'profiles','projects','departments','providers','models','agents',
    'workflows','workflow_steps','tasks','checkpoints','approvals',
    'documents','knowledge_base','memory','cost_rollups','media_jobs'
  ];
begin
  foreach t in array mutable_tables loop
    execute format(
      'drop trigger if exists trg_set_updated_at on public.%I;', t);
    execute format(
      'create trigger trg_set_updated_at before update on public.%I
         for each row execute function public.set_updated_at();', t);
  end loop;
end $$;

-- =============================================================================
-- End schema.sql
-- =============================================================================
