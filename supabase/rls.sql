-- =============================================================================
-- Omnivra AI Company OS - Row Level Security (RLS)
-- Run AFTER schema.sql.
-- Model: the FastAPI backend uses the SERVICE_ROLE key (bypasses RLS entirely
-- by default in Supabase). These policies exist so that if/when the frontend
-- (anon/authenticated) reads directly, access is correctly constrained.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Helper: is the current user a member (or owner) of a project?
-- ---------------------------------------------------------------------------
create or replace function public.is_project_member(p_project_id uuid)
returns boolean
language sql stable security definer set search_path = public
as $$
  select exists (
    select 1 from public.projects p
    where p.id = p_project_id and p.owner_id = auth.uid()
  ) or exists (
    select 1 from public.project_members m
    where m.project_id = p_project_id and m.user_id = auth.uid()
  );
$$;

-- ---------------------------------------------------------------------------
-- Enable RLS on every table
-- ---------------------------------------------------------------------------
do $$
declare t text;
  all_tables text[] := array[
    'profiles','projects','project_members','departments','providers','models',
    'agents','agent_status_snapshots','workflows','workflow_steps','tasks',
    'task_logs','checkpoints','approvals','notifications','activity_events',
    'documents','knowledge_base','memory','token_usage','cost_rollups',
    'system_health_metrics','media_jobs','achievements'
  ];
begin
  foreach t in array all_tables loop
    execute format('alter table public.%I enable row level security;', t);
    execute format('alter table public.%I force row level security;', t);
  end loop;
end $$;

-- ---------------------------------------------------------------------------
-- Service role: full access on every table (backend trusted key)
-- ---------------------------------------------------------------------------
do $$
declare t text;
  all_tables text[] := array[
    'profiles','projects','project_members','departments','providers','models',
    'agents','agent_status_snapshots','workflows','workflow_steps','tasks',
    'task_logs','checkpoints','approvals','notifications','activity_events',
    'documents','knowledge_base','memory','token_usage','cost_rollups',
    'system_health_metrics','media_jobs','achievements'
  ];
begin
  foreach t in array all_tables loop
    execute format($f$drop policy if exists service_all on public.%I;$f$, t);
    execute format(
      $f$create policy service_all on public.%I
           as permissive for all to service_role
           using (true) with check (true);$f$, t);
  end loop;
end $$;

-- ---------------------------------------------------------------------------
-- Catalog tables: readable by any authenticated user (global, non-sensitive)
-- ---------------------------------------------------------------------------
do $$
declare t text;
  catalog_tables text[] := array['departments','providers','models','agents'];
begin
  foreach t in array catalog_tables loop
    execute format($f$drop policy if exists auth_read_catalog on public.%I;$f$, t);
    execute format(
      $f$create policy auth_read_catalog on public.%I
           as permissive for select to authenticated using (true);$f$, t);
  end loop;
end $$;

-- ---------------------------------------------------------------------------
-- Profiles: self read/update
-- ---------------------------------------------------------------------------
drop policy if exists profiles_self_select on public.profiles;
create policy profiles_self_select on public.profiles
  for select to authenticated using (id = auth.uid());

drop policy if exists profiles_self_update on public.profiles;
create policy profiles_self_update on public.profiles
  for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- ---------------------------------------------------------------------------
-- Projects + membership
-- ---------------------------------------------------------------------------
drop policy if exists projects_member_select on public.projects;
create policy projects_member_select on public.projects
  for select to authenticated
  using (owner_id = auth.uid() or public.is_project_member(id));

drop policy if exists projects_owner_write on public.projects;
create policy projects_owner_write on public.projects
  for all to authenticated
  using (owner_id = auth.uid()) with check (owner_id = auth.uid());

drop policy if exists project_members_select on public.project_members;
create policy project_members_select on public.project_members
  for select to authenticated
  using (user_id = auth.uid() or public.is_project_member(project_id));

-- ---------------------------------------------------------------------------
-- Project-scoped tables: authenticated members can READ rows of their projects.
-- (Writes go through the backend service role.)
-- ---------------------------------------------------------------------------
do $$
declare t text;
  scoped_tables text[] := array[
    'workflows','workflow_steps','tasks','task_logs','checkpoints','approvals',
    'activity_events','documents','knowledge_base','memory','token_usage',
    'cost_rollups','system_health_metrics','media_jobs','achievements'
  ];
begin
  foreach t in array scoped_tables loop
    execute format($f$drop policy if exists member_read on public.%I;$f$, t);
  end loop;
end $$;

-- Tables that carry project_id directly
create policy member_read on public.workflows for select to authenticated
  using (public.is_project_member(project_id));
create policy member_read on public.tasks for select to authenticated
  using (public.is_project_member(project_id));
create policy member_read on public.checkpoints for select to authenticated
  using (public.is_project_member(project_id));
create policy member_read on public.approvals for select to authenticated
  using (public.is_project_member(project_id));
create policy member_read on public.activity_events for select to authenticated
  using (project_id is null or public.is_project_member(project_id));
create policy member_read on public.documents for select to authenticated
  using (public.is_project_member(project_id));
create policy member_read on public.knowledge_base for select to authenticated
  using (project_id is null or public.is_project_member(project_id));
create policy member_read on public.memory for select to authenticated
  using (project_id is null or public.is_project_member(project_id));
create policy member_read on public.token_usage for select to authenticated
  using (public.is_project_member(project_id));
create policy member_read on public.cost_rollups for select to authenticated
  using (public.is_project_member(project_id));
create policy member_read on public.system_health_metrics for select to authenticated
  using (project_id is null or public.is_project_member(project_id));
create policy member_read on public.media_jobs for select to authenticated
  using (public.is_project_member(project_id));
create policy member_read on public.achievements for select to authenticated
  using (public.is_project_member(project_id));

-- workflow_steps / task_logs join through their parent for the project check
create policy member_read on public.workflow_steps for select to authenticated
  using (exists (
    select 1 from public.workflows w
    where w.id = workflow_id and public.is_project_member(w.project_id)));
create policy member_read on public.task_logs for select to authenticated
  using (exists (
    select 1 from public.tasks tk
    where tk.id = task_id and public.is_project_member(tk.project_id)));

-- agent_status_snapshots are catalog-ish (no project), readable by authenticated
drop policy if exists snap_read on public.agent_status_snapshots;
create policy snap_read on public.agent_status_snapshots
  for select to authenticated using (true);

-- ---------------------------------------------------------------------------
-- Notifications: user-scoped read + mark-as-read update
-- ---------------------------------------------------------------------------
drop policy if exists notifications_self_select on public.notifications;
create policy notifications_self_select on public.notifications
  for select to authenticated using (user_id = auth.uid());

drop policy if exists notifications_self_update on public.notifications;
create policy notifications_self_update on public.notifications
  for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- =============================================================================
-- End rls.sql
-- =============================================================================
