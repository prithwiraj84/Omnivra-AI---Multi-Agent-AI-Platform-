"""Typed registry of every Omnivra agent (dashboard source of truth).

The frontend agent grid, the CEO orchestrator's delegation table, and the
/api/agents route all read from :data:`AGENT_REGISTRY`. Each entry pins the
department, the provider name (must exist in providers.registry.PROVIDER_NAMES),
and the exact model string.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Department(str, Enum):
    EXECUTIVE = "Executive"
    ARCHITECTURE = "Architecture"
    DESIGN = "Design"
    ENGINEERING = "Engineering"
    QUALITY_SECURITY = "Quality & Security"
    MARKETING = "Marketing"
    DOCUMENTATION = "Documentation"
    RECOVERY = "Recovery"
    SYSTEM_OPS = "System Ops"
    MEDIA = "Media"


class AgentStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


class AgentKind(str, Enum):
    TEXT = "text"        # chat / reasoning agent
    MEDIA = "media"      # STT / TTS / image
    SYSTEM = "system"    # internal system-ops utility


class AgentSpec(BaseModel):
    """Immutable definition of one agent."""

    id: str = Field(..., description="Stable kebab-case identifier")
    name: str
    department: Department
    provider: str = Field(..., description="Provider key in ProviderRegistry")
    model: str = Field(..., description="Exact model string sent to the provider")
    kind: AgentKind = AgentKind.TEXT
    responsibilities: list[str] = Field(default_factory=list)
    status: AgentStatus = AgentStatus.ONLINE


# --- The roster ------------------------------------------------------------
AGENT_REGISTRY: dict[str, AgentSpec] = {
    a.id: a
    for a in [
        # Executive
        AgentSpec(id="ceo-manager", name="CEO / Manager", department=Department.EXECUTIVE,
                  provider="google_ai", model="gemini-2.5-flash",
                  responsibilities=["planning", "orchestration", "delegation", "approvals"]),
        # Architecture
        AgentSpec(id="solution-architect", name="Solution Architect", department=Department.ARCHITECTURE,
                  provider="openrouter", model="openai/gpt-oss-120b:free",
                  responsibilities=["system design", "file manifest"]),
        # Design
        AgentSpec(id="uiux-designer", name="UI/UX Designer", department=Department.DESIGN,
                  provider="google_ai", model="gemini-2.5-flash",
                  responsibilities=["wireframes", "design system", "component specs"]),
        # Engineering
        AgentSpec(id="database-engineer", name="Database Engineer", department=Department.ENGINEERING,
                  provider="openrouter", model="nvidia/nemotron-3-super-120b-a12b:free",
                  responsibilities=["schema design", "migrations", "pgvector"]),
        AgentSpec(id="frontend-engineer", name="Frontend Engineer", department=Department.ENGINEERING,
                  provider="openrouter", model="poolside/laguna-m.1:free",
                  responsibilities=["React components", "state", "styling"]),
        AgentSpec(id="backend-engineer", name="Backend Engineer", department=Department.ENGINEERING,
                  provider="openrouter", model="z-ai/glm-4.5-air:free",
                  responsibilities=["FastAPI services", "business logic"]),
        AgentSpec(id="api-engineer", name="API Engineer", department=Department.ENGINEERING,
                  provider="openrouter", model="z-ai/glm-4.5-air:free",
                  responsibilities=["endpoint design", "contracts", "integration"]),
        # Quality & Security
        AgentSpec(id="qa-engineer", name="QA Engineer", department=Department.QUALITY_SECURITY,
                  provider="groq", model="llama-3.3-70b-versatile",
                  responsibilities=["test plans", "test code", "validation"]),
        AgentSpec(id="secops-engineer", name="SecOps Engineer", department=Department.QUALITY_SECURITY,
                  provider="openrouter", model="openai/gpt-oss-120b:free",
                  responsibilities=["threat modeling", "audits", "hardening"]),
        # Marketing
        AgentSpec(id="seo-researcher", name="SEO Researcher", department=Department.MARKETING,
                  provider="groq", model="groq/compound",
                  responsibilities=["keyword research", "SERP analysis"]),
        AgentSpec(id="social-strategist", name="Social Strategist", department=Department.MARKETING,
                  provider="openrouter", model="deepseek/deepseek-v4-flash:free",
                  responsibilities=["content strategy", "campaigns"]),
        AgentSpec(id="reel-automation", name="Reel Automation", department=Department.MARKETING,
                  provider="groq", model="llama-3.1-8b-instant",
                  responsibilities=["short-form scripting", "reel automation"]),
        # Documentation
        AgentSpec(id="documentation-agent", name="Documentation Agent", department=Department.DOCUMENTATION,
                  provider="openrouter", model="google/gemma-4-31b-it:free",
                  responsibilities=["docs", "READMEs", "guides"]),
        AgentSpec(id="presentation-designer", name="Presentation Designer", department=Department.DOCUMENTATION,
                  provider="openrouter", model="google/gemma-4-31b-it:free",
                  responsibilities=["slide decks", "presentation export"]),
        # Recovery
        AgentSpec(id="recovery-agent", name="Recovery Agent", department=Department.RECOVERY,
                  provider="openrouter", model="nvidia/nemotron-3-super-120b-a12b:free",
                  responsibilities=["checkpoint recovery", "resume"]),
        # System Ops (all liquid/lfm-2.5-1.2b-thinking:free)
        AgentSpec(id="task-classifier", name="Task Classifier", department=Department.SYSTEM_OPS,
                  provider="openrouter", model="liquid/lfm-2.5-1.2b-thinking:free",
                  kind=AgentKind.SYSTEM, responsibilities=["classify incoming tasks"]),
        AgentSpec(id="workflow-router", name="Workflow Router", department=Department.SYSTEM_OPS,
                  provider="openrouter", model="liquid/lfm-2.5-1.2b-thinking:free",
                  kind=AgentKind.SYSTEM, responsibilities=["route to department/agent"]),
        AgentSpec(id="memory-retrieval", name="Memory Retrieval", department=Department.SYSTEM_OPS,
                  provider="openrouter", model="liquid/lfm-2.5-1.2b-thinking:free",
                  kind=AgentKind.SYSTEM, responsibilities=["semantic recall via pgvector"]),
        AgentSpec(id="notification-agent", name="Notification Agent", department=Department.SYSTEM_OPS,
                  provider="openrouter", model="liquid/lfm-2.5-1.2b-thinking:free",
                  kind=AgentKind.SYSTEM, responsibilities=["notify users / channels"]),
        AgentSpec(id="log-analyzer", name="Log Analyzer", department=Department.SYSTEM_OPS,
                  provider="openrouter", model="liquid/lfm-2.5-1.2b-thinking:free",
                  kind=AgentKind.SYSTEM, responsibilities=["analyze logs / anomalies"]),
        # Media
        AgentSpec(id="speech-to-text", name="Speech-to-Text", department=Department.MEDIA,
                  provider="groq", model="whisper-large-v3-turbo",
                  kind=AgentKind.MEDIA, responsibilities=["transcription"]),
        AgentSpec(id="text-to-speech", name="Text-to-Speech", department=Department.MEDIA,
                  provider="groq", model="canopylabs/orpheus-v1-english",
                  kind=AgentKind.MEDIA, responsibilities=["voice synthesis"]),
        AgentSpec(id="image-generation", name="Image Generation", department=Department.MEDIA,
                  provider="huggingface", model="black-forest-labs/FLUX.1-dev",
                  kind=AgentKind.MEDIA, responsibilities=["image generation"]),
    ]
}


def get_agent(agent_id: str) -> AgentSpec:
    """Look up an agent by id, raising KeyError if unknown."""
    return AGENT_REGISTRY[agent_id]


def list_agents() -> list[AgentSpec]:
    """All agents in registration order (for the dashboard grid)."""
    return list(AGENT_REGISTRY.values())


def agents_by_department() -> dict[str, list[AgentSpec]]:
    """Group agents by department (sidebar DEPARTMENTS + grouped grid)."""
    grouped: dict[str, list[AgentSpec]] = {}
    for spec in AGENT_REGISTRY.values():
        grouped.setdefault(spec.department.value, []).append(spec)
    return grouped
