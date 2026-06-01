/**
 * Frontend mirror of the backend agent roster (backend/app/agents/registry.py).
 * Source of truth for the AI Agents Status grid + sidebar department grouping until
 * the live /api/agents endpoint is wired (Phase 4). Keep model strings in sync with
 * the backend registry.
 */
import { departmentAccent } from '@/styles/tokens'
import type { Accent, AgentKind, AgentSummary, ProviderKey } from '@/types'

const PROVIDER_LABEL: Record<ProviderKey, string> = {
  google_ai: 'Google AI Studio',
  openrouter: 'OpenRouter',
  groq: 'Groq',
  huggingface: 'Hugging Face',
}

interface Seed {
  id: string
  name: string
  department: string
  provider: ProviderKey
  model: string
  modelLabel: string
  kind?: AgentKind
}

const SEEDS: Seed[] = [
  { id: 'ceo-manager', name: 'CEO / Manager', department: 'Executive', provider: 'google_ai', model: 'gemini-3.1-flash-lite', modelLabel: 'Gemini 3.1 Flash Lite' },
  { id: 'solution-architect', name: 'Solution Architect', department: 'Architecture', provider: 'openrouter', model: 'openai/gpt-oss-120b:free', modelLabel: 'GPT OSS 120B' },
  { id: 'uiux-designer', name: 'UI/UX Designer', department: 'Design', provider: 'google_ai', model: 'gemini-3.1-flash-lite', modelLabel: 'Gemini 3.1 Flash Lite' },
  { id: 'database-engineer', name: 'Database Engineer', department: 'Engineering', provider: 'openrouter', model: 'nvidia/nemotron-3-super-120b-a12b:free', modelLabel: 'Nemotron 120B' },
  { id: 'frontend-engineer', name: 'Frontend Engineer', department: 'Engineering', provider: 'openrouter', model: 'poolside/laguna-m.1:free', modelLabel: 'Poolside Laguna' },
  { id: 'backend-engineer', name: 'Backend Engineer', department: 'Engineering', provider: 'openrouter', model: 'z-ai/glm-4.5-air:free', modelLabel: 'GLM 4.5 Air' },
  { id: 'api-engineer', name: 'API Engineer', department: 'Engineering', provider: 'openrouter', model: 'z-ai/glm-4.5-air:free', modelLabel: 'GLM 4.5 Air' },
  { id: 'qa-engineer', name: 'QA Engineer', department: 'Quality & Security', provider: 'groq', model: 'llama-3.3-70b-versatile', modelLabel: 'Llama 3.3 70B' },
  { id: 'secops-engineer', name: 'SecOps Engineer', department: 'Quality & Security', provider: 'openrouter', model: 'openai/gpt-oss-120b:free', modelLabel: 'GPT OSS 120B' },
  { id: 'seo-researcher', name: 'SEO Researcher', department: 'Marketing', provider: 'groq', model: 'groq/compound', modelLabel: 'Groq Compound' },
  { id: 'social-strategist', name: 'Social Strategist', department: 'Marketing', provider: 'openrouter', model: 'moonshotai/kimi-k2.6:free', modelLabel: 'Kimi K2.6' },
  { id: 'reel-automation', name: 'Reel Automation', department: 'Marketing', provider: 'groq', model: 'llama-3.1-8b-instant', modelLabel: 'Llama 3.1 8B' },
  { id: 'documentation-agent', name: 'Documentation Agent', department: 'Documentation', provider: 'openrouter', model: 'google/gemma-4-31b-it:free', modelLabel: 'Gemma 4 31B' },
  { id: 'presentation-designer', name: 'Presentation Designer', department: 'Documentation', provider: 'openrouter', model: 'google/gemma-4-31b-it:free', modelLabel: 'Gemma 4 31B' },
  { id: 'recovery-agent', name: 'Recovery Agent', department: 'Recovery', provider: 'openrouter', model: 'nvidia/nemotron-3-super-120b-a12b:free', modelLabel: 'Nemotron 120B' },
  { id: 'task-classifier', name: 'Task Classifier', department: 'System Ops', provider: 'openrouter', model: 'liquid/lfm-2.5-1.2b-thinking:free', modelLabel: 'LFM 1.2B', kind: 'system' },
  { id: 'workflow-router', name: 'Workflow Router', department: 'System Ops', provider: 'openrouter', model: 'liquid/lfm-2.5-1.2b-thinking:free', modelLabel: 'LFM 1.2B', kind: 'system' },
  { id: 'memory-retrieval', name: 'Memory Retrieval', department: 'System Ops', provider: 'openrouter', model: 'liquid/lfm-2.5-1.2b-thinking:free', modelLabel: 'LFM 1.2B', kind: 'system' },
  { id: 'notification-agent', name: 'Notification Agent', department: 'System Ops', provider: 'openrouter', model: 'liquid/lfm-2.5-1.2b-thinking:free', modelLabel: 'LFM 1.2B', kind: 'system' },
  { id: 'log-analyzer', name: 'Log Analyzer', department: 'System Ops', provider: 'openrouter', model: 'liquid/lfm-2.5-1.2b-thinking:free', modelLabel: 'LFM 1.2B', kind: 'system' },
  { id: 'speech-to-text', name: 'Speech-to-Text', department: 'Media', provider: 'groq', model: 'whisper-large-v3-turbo', modelLabel: 'Whisper v3 Turbo', kind: 'media' },
  { id: 'text-to-speech', name: 'Text-to-Speech', department: 'Media', provider: 'groq', model: 'canopylabs/orpheus-v1-english', modelLabel: 'Orpheus v1', kind: 'media' },
  { id: 'image-generation', name: 'Image Generation', department: 'Media', provider: 'huggingface', model: 'black-forest-labs/FLUX.1-schnell', modelLabel: 'FLUX.1-schnell', kind: 'media' },
]

export const AGENTS: AgentSummary[] = SEEDS.map((s) => ({
  ...s,
  kind: s.kind ?? 'text',
  status: 'online',
  providerLabel: PROVIDER_LABEL[s.provider],
  accent: (departmentAccent[s.department] ?? 'cyan') as Accent,
}))

/** Text/reasoning + media agents shown as full cards in the grid. */
export const PRIMARY_AGENTS = AGENTS.filter((a) => a.kind !== 'system')

/** System-ops utilities shown as the compact chip sub-row. */
export const SYSTEM_OPS_AGENTS = AGENTS.filter((a) => a.kind === 'system')
