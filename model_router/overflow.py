"""Fixed-price PAYG overflow selection and daily budget accounting."""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite

from .types import CandidateHealth, HealthState, RoutingDecision, Tier

PAYG_OVERFLOW_PROVIDERS = frozenset({"openrouter", "deepinfra"})


def resolve_overflow(
    tier: Tier,
    attempted_candidates: set[str],
    health: Mapping[str, CandidateHealth],
    *,
    remaining_budget_usd: float,
) -> RoutingDecision | None:
    """Select the first healthy fixed-cost PAYG candidate within budget."""
    for candidate in tier.candidates:
        candidate_health = health.get(candidate.health_key)
        if (
            not candidate.paid
            or candidate.provider not in PAYG_OVERFLOW_PROVIDERS
            or candidate.estimated_cost_usd is None
            or not isfinite(candidate.estimated_cost_usd)
            or candidate.estimated_cost_usd < 0
            or candidate.estimated_cost_usd > remaining_budget_usd
            or candidate.id in attempted_candidates
            or candidate.disabled
            or (
                candidate_health
                and candidate_health.state
                in {HealthState.COOLING_DOWN, HealthState.UNAVAILABLE, HealthState.DISABLED}
            )
        ):
            continue
        return RoutingDecision(
            tier=tier.number,
            candidate=candidate,
            reason="first budget-approved fixed-price overflow candidate",
            source="overflow",
        )
    return None