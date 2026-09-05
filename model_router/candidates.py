"""Deterministic candidate selection within one capability tier."""

from __future__ import annotations

from collections.abc import Mapping

from .types import CandidateHealth, HealthState, RoutingDecision, Tier


def resolve_candidate(
    tier: Tier,
    attempted_candidates: set[str],
    health: Mapping[str, CandidateHealth],
) -> RoutingDecision | None:
    """Return the first eligible normal candidate, never another tier."""
    for candidate in tier.candidates:
        candidate_health = health.get(candidate.health_key)
        if candidate.id in attempted_candidates or candidate.disabled:
            continue
        if candidate_health and candidate_health.state in {
            HealthState.COOLING_DOWN,
            HealthState.UNAVAILABLE,
            HealthState.DISABLED,
        }:
            continue
        return RoutingDecision(
            tier=tier.number,
            candidate=candidate,
            reason="first eligible same-tier candidate",
            source="primary" if not attempted_candidates else "same-tier-fallback",
        )
    return None
