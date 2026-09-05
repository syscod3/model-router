"""Pure policy types; no Hermes imports belong here."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class HealthState(str, Enum):
    HEALTHY = "healthy"
    COOLING_DOWN = "cooling_down"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


@dataclass(frozen=True)
class Candidate:
    id: str
    provider: str
    model: str
    reasoning: str | None = None
    base_url: str | None = None
    priority: int = 0
    paid: bool = False
    estimated_cost_usd: float | None = None
    disabled: bool = False

    @property
    def health_key(self) -> str:
        return f"{self.provider}:{self.model}"


@dataclass(frozen=True)
class Tier:
    number: int
    label: str
    reasoning: str | None
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True)
class CandidateHealth:
    state: HealthState = HealthState.HEALTHY
    failure_type: str | None = None
    failure_count: int = 0
    cooldown_until: float | None = None


@dataclass(frozen=True)
class RoutingDecision:
    tier: int
    candidate: Candidate
    reason: str
    source: Literal[
        "primary", "same-tier-fallback", "overflow", "capability-escalation", "manual"
    ]


@dataclass
class RoutingSession:
    tier: int | None = None
    tier_pinned: bool = False
    hard_model_pin: Candidate | None = None
    attempted_candidates: set[str] = field(default_factory=set)
