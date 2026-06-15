-- =============================================================================
-- Omnivra AI Company OS - Seed Data
-- Run AFTER schema.sql and rls.sql. Idempotent (ON CONFLICT upserts).
-- Seeds: departments, providers, models, full agent roster, demo project.
-- NOTE: inserts run as the migration owner (service role / postgres) which
-- bypasses RLS.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Departments
-- ---------------------------------------------------------------------------
insert into public.departments (key, name, description, icon, accent, sort_order) values
  ('executive',     'Executive',           'Planning, orchestration, delegation, approvals', 'crown',      '#a855f7', 1),
  ('architecture',  'Architecture',        'System design and file manifest',                'layout-grid', '#22d3ee', 2),
  ('design',        'Design',              'UI/UX design',                                   'palette',    '#3b82f6', 3),
  ('engineering',   'Engineering',         'Database, frontend, backend, API',               'code',       '#10b981', 4),
  ('quality_security','Quality & Security', 'QA and SecOps',                                  'shield-check','#f59e0b', 5),
  ('marketing',     'Marketing',           'SEO, social, reels',                             'megaphone',  '#ec4899', 6),
  ('documentation', 'Documentation',       'Docs and presentations',                         'file-text',  '#8b5cf6', 7),
  ('recovery',      'Recovery',            'Checkpoint recovery and resume',                 'life-buoy',  '#ef4444', 8),
  ('system_ops',    'System Ops',          'Classification, routing, memory, logs',          'cpu',        '#64748b', 9),
  ('media',         'Media',               'Speech, voice, image generation',                'image',      '#06b6d4', 10)
on conflict (key) do update set
  name=excluded.name, description=excluded.description, icon=excluded.icon,
  accent=excluded.accent, sort_order=excluded.sort_order;

-- ---------------------------------------------------------------------------
-- Providers
-- ---------------------------------------------------------------------------
insert into public.providers (key, name, base_url, docs_url) values
  ('google_ai_studio','Google AI Studio','https://generativelanguage.googleapis.com','https://ai.google.dev'),
  ('openrouter',      'OpenRouter',      'https://openrouter.ai/api/v1',            'https://openrouter.ai/docs'),
  ('groq',            'Groq',            'https://api.groq.com/openai/v1',          'https://console.groq.com/docs'),
  ('huggingface',     'Hugging Face',    'https://router.huggingface.co/hf-inference','https://huggingface.co/docs')
on conflict (key, name) do update set base_url=excluded.base_url, docs_url=excluded.docs_url;

-- ---------------------------------------------------------------------------
-- Models (referenced by the roster). is_free reflects ':free' tier models.
-- ---------------------------------------------------------------------------
insert into public.models (provider_id, model_id, display_name, modality, is_free)
select p.id, m.model_id, m.display_name, m.modality::model_modality, m.is_free
from (values
  ('google_ai_studio','gemini-3.1-flash-lite',                    'Gemini 3.1 Flash Lite',     'multimodal', false),
  ('groq',            'openai/gpt-oss-120b',                      'GPT-OSS 120B',              'text',       false),
  ('openrouter',      'nvidia/nemotron-3-super-120b-a12b:free',   'Nemotron 3 Super 120B (free)','text',     true),
  ('openrouter',      'poolside/laguna-m.1:free',                 'Poolside Laguna M.1 (free)','text',       true),
  ('openrouter',      'z-ai/glm-4.5-air:free',                    'GLM 4.5 Air (free)',        'text',       true),
  ('openrouter',      'moonshotai/kimi-k2.6:free',                'Kimi K2.6 (free)',          'text',       true),
  ('openrouter',      'google/gemma-4-31b-it:free',               'Gemma 4 31B IT (free)',     'text',       true),
  ('groq',            'llama-3.3-70b-versatile',                  'Llama 3.3 70B Versatile',   'text',       false),
  ('groq',            'groq/compound',                            'Groq Compound',             'text',       false),
  ('groq',            'llama-3.1-8b-instant',                     'Llama 3.1 8B Instant',      'text',       false),
  ('groq',            'whisper-large-v3-turbo',                   'Whisper Large v3 Turbo',    'audio_stt',  false),
  ('groq',            'canopylabs/orpheus-v1-english',            'Orpheus v1 (English TTS)',  'audio_tts',  false),
  ('huggingface',     'black-forest-labs/FLUX.1-schnell',         'FLUX.1-schnell',            'image',      false),
  ('openrouter',      'liquid/lfm-2.5-1.2b-thinking:free',        'LFM 2.5 1.2B Thinking (free)','text',     true)
) as m(provider_key, model_id, display_name, modality, is_free)
join public.providers p on p.key = m.provider_key::provider_kind
on conflict (provider_id, model_id) do update set
  display_name=excluded.display_name, modality=excluded.modality, is_free=excluded.is_free;

-- ---------------------------------------------------------------------------
-- Agents (full roster). model_key disambiguated by provider via the join.
-- ---------------------------------------------------------------------------
insert into public.agents
  (key, name, title, department_id, provider_id, model_id, icon, is_system, sort_order)
select a.key, a.name, a.title, d.id, p.id, mo.id, a.icon, a.is_system, a.sort_order
from (values
  -- key, name, title, dept_key, provider_key, model_id, icon, is_system, sort
  ('ceo_manager',        'CEO / Manager',        'Chief Executive',     'executive',      'google_ai_studio','gemini-3.1-flash-lite',                  'crown',        false, 1),
  ('solution_architect', 'Solution Architect',   'System Design',       'architecture',   'openrouter',      'openai/gpt-oss-120b:free',               'layout-grid',  false, 2),
  ('uiux_designer',      'UI/UX Designer',       'Product Design',      'design',         'google_ai_studio','gemini-3.1-flash-lite',                  'palette',      false, 3),
  ('database_engineer',  'Database Engineer',    'Data Platform',       'engineering',    'openrouter',      'nvidia/nemotron-3-super-120b-a12b:free', 'database',     false, 4),
  ('frontend_engineer',  'Frontend Engineer',    'UI Engineering',      'engineering',    'openrouter',      'poolside/laguna-m.1:free',               'monitor',      false, 5),
  ('backend_engineer',   'Backend Engineer',     'Services',            'engineering',    'openrouter',      'z-ai/glm-4.5-air:free',                  'server',       false, 6),
  ('api_engineer',       'API Engineer',         'Integrations',        'engineering',    'openrouter',      'z-ai/glm-4.5-air:free',                  'plug',         false, 7),
  ('qa_engineer',        'QA Engineer',          'Quality Assurance',   'quality_security','google_ai_studio','gemini-3.1-flash-lite',                  'bug',          false, 8),
  ('secops_engineer',    'SecOps Engineer',      'Security',            'quality_security','openrouter',     'openai/gpt-oss-120b:free',               'shield-check', false, 9),
  ('seo_researcher',     'SEO Researcher',       'Search',              'marketing',      'groq',            'groq/compound',                          'search',       false, 10),
  ('social_strategist',  'Social Strategist',    'Social',              'marketing',      'openrouter',      'moonshotai/kimi-k2.6:free',              'share-2',      false, 11),
  ('reel_automation',    'Reel Automation',      'Video',               'marketing',      'groq',            'llama-3.1-8b-instant',                   'film',         false, 12),
  ('documentation_agent','Documentation Agent',  'Docs',                'documentation',  'openrouter',      'google/gemma-4-31b-it:free',             'file-text',    false, 13),
  ('presentation_designer','Presentation Designer','Decks',             'documentation',  'openrouter',      'google/gemma-4-31b-it:free',             'presentation', false, 14),
  ('recovery_agent',     'Recovery Agent',       'Resume & Recovery',   'recovery',       'openrouter',      'nvidia/nemotron-3-super-120b-a12b:free', 'life-buoy',    false, 15),
  ('task_classifier',    'Task Classifier',      'System Ops',          'system_ops',     'openrouter',      'liquid/lfm-2.5-1.2b-thinking:free',      'tags',         true,  16),
  ('workflow_router',    'Workflow Router',      'System Ops',          'system_ops',     'openrouter',      'liquid/lfm-2.5-1.2b-thinking:free',      'git-branch',   true,  17),
  ('memory_retrieval',   'Memory Retrieval',     'System Ops',          'system_ops',     'openrouter',      'liquid/lfm-2.5-1.2b-thinking:free',      'brain',        true,  18),
  ('notification_agent', 'Notification Agent',   'System Ops',          'system_ops',     'openrouter',      'liquid/lfm-2.5-1.2b-thinking:free',      'bell',         true,  19),
  ('log_analyzer',       'Log Analyzer',         'System Ops',          'system_ops',     'openrouter',      'liquid/lfm-2.5-1.2b-thinking:free',      'scroll-text',  true,  20),
  ('speech_to_text',     'Speech-to-Text',       'Media',               'media',          'groq',            'whisper-large-v3-turbo',                 'mic',          true,  21),
  ('text_to_speech',     'Text-to-Speech',       'Media',               'media',          'groq',            'canopylabs/orpheus-v1-english',          'volume-2',     true,  22),
  ('image_generation',   'Image Generation',     'Media',               'media',          'huggingface',     'black-forest-labs/FLUX.1-schnell',       'image',        true,  23)
) as a(key, name, title, dept_key, provider_key, model_id, icon, is_system, sort_order)
join public.departments d on d.key = a.dept_key
join public.providers   p on p.key = a.provider_key::provider_kind
join public.models     mo on mo.provider_id = p.id and mo.model_id = a.model_id
on conflict (key) do update set
  name=excluded.name, title=excluded.title, department_id=excluded.department_id,
  provider_id=excluded.provider_id, model_id=excluded.model_id, icon=excluded.icon,
  is_system=excluded.is_system, sort_order=excluded.sort_order;

-- ---------------------------------------------------------------------------
-- Demo project (optional, for live dashboard data before real auth users exist)
-- Creates a placeholder profile only if no profiles exist yet.
-- In production, profiles are created by an auth.users trigger (see docs).
-- ---------------------------------------------------------------------------
do $$
declare demo_user uuid;
begin
  select id into demo_user from public.profiles limit 1;
  if demo_user is null then
    -- Cannot insert into profiles without a matching auth.users row.
    -- Skip demo project creation; it will be created post-signup.
    raise notice 'No profiles found; skipping demo project seed. Create a user first.';
  else
    insert into public.projects (owner_id, name, slug, description, status)
    values (demo_user, 'Omnivra Demo', 'omnivra-demo',
            'Seeded demo project for the AI Company OS dashboard', 'active')
    on conflict (slug) do nothing;
  end if;
end $$;

-- =============================================================================
-- End seed.sql
-- =============================================================================
