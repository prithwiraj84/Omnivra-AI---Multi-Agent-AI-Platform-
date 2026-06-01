"""Seed dashboard data — mirrors the reference dashboard and the live agent registry.

This is the default data source (no external services required). The SeedRepository
returns this; the SupabaseRepository overrides it once a project is configured.
Values intentionally match frontend/src/data/dashboard.ts so mock and live agree.
"""
from __future__ import annotations

from app.agents.registry import AGENT_REGISTRY, AgentSpec
from app.schemas.dashboard import (
    Achievement,
    ActivityItem,
    Agent,
    ApprovalItem,
    DashboardPayload,
    DistributionSlice,
    HealthMetric,
    MediaService,
    ModelUsage,
    ProviderUsage,
    SeriesDef,
    StatCard,
    TaskPoint,
    WorkflowItem,
)

# Ordered categorical chart palette (mirrors frontend styles/tokens.ts).
CATEGORICAL = ["#22d3ee", "#a855f7", "#3b82f6", "#f59e0b", "#10b981", "#ec4899", "#8b5cf6"]
ACCENT_HEX = {"cyan": "#22d3ee", "violet": "#a855f7", "blue": "#3b82f6", "emerald": "#10b981", "amber": "#f59e0b", "pink": "#ec4899"}

PROVIDER_LABEL = {
    "google_ai": "Google AI Studio",
    "openrouter": "OpenRouter",
    "groq": "Groq",
    "huggingface": "Hugging Face",
}

# Department -> design accent (mirrors frontend departmentAccent).
DEPARTMENT_ACCENT = {
    "Executive": "cyan",
    "Architecture": "violet",
    "Design": "pink",
    "Engineering": "blue",
    "Quality & Security": "emerald",
    "Marketing": "amber",
    "Documentation": "violet",
    "Recovery": "amber",
    "System Ops": "cyan",
    "Media": "emerald",
}

MODEL_LABEL = {
    "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite",
    "openai/gpt-oss-120b:free": "GPT OSS 120B",
    "nvidia/nemotron-3-super-120b-a12b:free": "Nemotron 120B",
    "poolside/laguna-m.1:free": "Poolside Laguna",
    "z-ai/glm-4.5-air:free": "GLM 4.5 Air",
    "llama-3.3-70b-versatile": "Llama 3.3 70B",
    "groq/compound": "Groq Compound",
    "moonshotai/kimi-k2.6:free": "Kimi K2.6",
    "llama-3.1-8b-instant": "Llama 3.1 8B",
    "google/gemma-4-31b-it:free": "Gemma 4 31B",
    "liquid/lfm-2.5-1.2b-thinking:free": "LFM 1.2B",
    "whisper-large-v3-turbo": "Whisper v3 Turbo",
    "canopylabs/orpheus-v1-english": "Orpheus v1",
    "black-forest-labs/FLUX.1-schnell": "FLUX.1-schnell",
}


def _agent_dto(spec: AgentSpec) -> Agent:
    dept = spec.department.value
    return Agent(
        id=spec.id,
        name=spec.name,
        department=dept,
        accent=DEPARTMENT_ACCENT.get(dept, "cyan"),
        provider=spec.provider,
        provider_label=PROVIDER_LABEL.get(spec.provider, spec.provider),
        model=spec.model,
        model_label=MODEL_LABEL.get(spec.model, spec.model),
        kind=spec.kind.value,
        status=spec.status.value,
    )


def seed_agents() -> tuple[list[Agent], list[Agent]]:
    """Return (primary agents, system-ops agents) derived from the registry."""
    primary, system = [], []
    for spec in AGENT_REGISTRY.values():
        dto = _agent_dto(spec)
        (system if spec.kind.value == "system" else primary).append(dto)
    return primary, system


def build_dashboard() -> DashboardPayload:
    primary, system = seed_agents()
    return DashboardPayload(
        stats=[
            StatCard(label="Total Agents", value="18", sub="Online", accent="cyan", icon="Bot"),
            StatCard(label="Active Tasks", value="7", sub="Running", accent="blue", icon="Activity"),
            StatCard(label="Completed Today", value="24", delta="+142%", delta_tone="success", accent="emerald", icon="CheckCircle2"),
            StatCard(label="Success Rate", value="98.6%", sub="Excellent", accent="emerald", icon="TrendingUp"),
            StatCard(label="Total Cost (Est.)", value="$0.18", sub="Today", accent="violet", icon="DollarSign"),
        ],
        agents=primary,
        system_ops=system,
        workflows=[
            WorkflowItem(id="wf-1", name="AI Company OS Dashboard", department="Development", status="In Progress", progress=78, accent="cyan", icon="LayoutDashboard"),
            WorkflowItem(id="wf-2", name="Instagram Campaign", department="Marketing", status="In Progress", progress=30, accent="amber", icon="Instagram"),
            WorkflowItem(id="wf-3", name="API Documentation", department="Documentation", status="Review", progress=90, accent="violet", icon="FileText"),
            WorkflowItem(id="wf-4", name="Investor Pitch Deck", department="Documentation", status="In Progress", progress=40, accent="violet", icon="Presentation"),
            WorkflowItem(id="wf-5", name="Security Audit", department="Quality & Security", status="Completed", progress=100, accent="emerald", icon="ShieldCheck"),
        ],
        task_execution=[
            TaskPoint(time="12 AM", completed=12, in_progress=8, failed=2),
            TaskPoint(time="03 AM", completed=18, in_progress=11, failed=1),
            TaskPoint(time="06 AM", completed=30, in_progress=16, failed=3),
            TaskPoint(time="09 AM", completed=27, in_progress=14, failed=2),
            TaskPoint(time="12 PM", completed=41, in_progress=22, failed=4),
            TaskPoint(time="03 PM", completed=38, in_progress=19, failed=3),
            TaskPoint(time="06 PM", completed=47, in_progress=24, failed=5),
            TaskPoint(time="09 PM", completed=44, in_progress=17, failed=2),
        ],
        task_execution_series=[
            SeriesDef(key="completed", label="Completed", color="#10b981"),
            SeriesDef(key="inProgress", label="In Progress", color="#3b82f6"),
            SeriesDef(key="failed", label="Failed", color="#ef4444"),
        ],
        task_distribution=[
            DistributionSlice(name="Development", value=45, color=CATEGORICAL[0]),
            DistributionSlice(name="Marketing", value=20, color=CATEGORICAL[1]),
            DistributionSlice(name="Documentation", value=15, color=CATEGORICAL[2]),
            DistributionSlice(name="Quality & Security", value=10, color=CATEGORICAL[3]),
            DistributionSlice(name="System Ops", value=10, color=CATEGORICAL[4]),
        ],
        total_tasks=124,
        activity=[
            ActivityItem(id="a1", agent="Backend Engineer", action="Created 12 files", time="2m ago", accent="blue", icon="Code2"),
            ActivityItem(id="a2", agent="Frontend Engineer", action="Updated Dashboard.tsx", time="3m ago", accent="blue", icon="LayoutGrid"),
            ActivityItem(id="a3", agent="Database Engineer", action="Created 8 tables", time="5m ago", accent="blue", icon="Database"),
            ActivityItem(id="a4", agent="QA Engineer", action="Completed test suite", time="8m ago", accent="emerald", icon="CheckCircle2"),
            ActivityItem(id="a5", agent="SecOps Engineer", action="Security scan passed", time="10m ago", accent="emerald", icon="ShieldCheck"),
            ActivityItem(id="a6", agent="Documentation Agent", action="Updated README.md", time="12m ago", accent="violet", icon="FileText"),
        ],
        approvals=[
            ApprovalItem(id="ap1", title="API Endpoints", source="by API Engineer", priority="high", accent="blue", icon="Webhook"),
            ApprovalItem(id="ap2", title="Database Schema", source="by Database Engineer", priority="high", accent="blue", icon="Database"),
            ApprovalItem(id="ap3", title="UI Components", source="by Frontend Engineer", priority="medium", accent="amber", icon="LayoutGrid"),
            ApprovalItem(id="ap4", title="Security Report", source="by SecOps Engineer", priority="high", accent="emerald", icon="ShieldCheck"),
        ],
        total_pending_approvals=7,
        system_health=[
            HealthMetric(label="CPU Usage", pct=32, display="32%", accent="cyan"),
            HealthMetric(label="Memory Usage", pct=58, display="58%", accent="blue"),
            HealthMetric(label="Storage Usage", pct=68, display="68%", accent="emerald"),
            HealthMetric(label="Network", pct=None, display="Good", accent="emerald"),
            HealthMetric(label="API Quota (OpenRouter)", pct=89, display="89%", accent="amber"),
            HealthMetric(label="API Quota (Groq)", pct=76, display="76%", accent="emerald"),
        ],
        provider_usage=[
            ProviderUsage(name="Google AI Studio", pct=28, calls=892, color=ACCENT_HEX["cyan"]),
            ProviderUsage(name="OpenRouter", pct=42, calls=1228, color=ACCENT_HEX["pink"]),
            ProviderUsage(name="Groq", pct=18, calls=561, color=ACCENT_HEX["amber"]),
            ProviderUsage(name="Hugging Face", pct=12, calls=384, color=ACCENT_HEX["violet"]),
        ],
        model_usage=[
            ModelUsage(id="openai/gpt-oss-120b:free", pct=32, calls=512, color=CATEGORICAL[0]),
            ModelUsage(id="z-ai/glm-4.5-air:free", pct=24, calls=1384, color=CATEGORICAL[1]),
            ModelUsage(id="nvidia/nemotron-3-super-120b", pct=18, calls=288, color=CATEGORICAL[2]),
            ModelUsage(id="poolside/laguna-m.1:free", pct=12, calls=192, color=CATEGORICAL[3]),
            ModelUsage(id="google/gemma-4-31b-it:free", pct=8, calls=128, color=CATEGORICAL[4]),
            ModelUsage(id="liquid/lfm-2.5-1.2b-thinking:free", pct=6, calls=96, color=CATEGORICAL[5]),
        ],
        media_services=[
            MediaService(name="Speech-to-Text", provider="Whisper", calls=128, delta="+15%", accent="cyan", icon="Mic"),
            MediaService(name="Text-to-Speech", provider="Orpheus", calls=95, delta="+35%", accent="violet", icon="Volume2"),
            MediaService(name="Image Generation", provider="FLUX.1-schnell", calls=342, delta="+25%", accent="emerald", icon="Image"),
        ],
        achievements=[
            Achievement(title="100+ Tasks Completed", subtitle="Today", accent="cyan", icon="PartyPopper"),
            Achievement(title="98.6% Success Rate", subtitle="Excellent Performance", accent="emerald", icon="ShieldCheck"),
            Achievement(title="18 Agents Online", subtitle="All Systems Go", accent="blue", icon="Zap"),
            Achievement(title="Zero Critical Errors", subtitle="Last 24 Hours", accent="violet", icon="ServerCog"),
            Achievement(title="Cost Optimized", subtitle="90% Below Industry Avg", accent="amber", icon="Coins"),
        ],
    )
