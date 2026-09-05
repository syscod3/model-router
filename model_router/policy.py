"""The small, provider-neutral policy interface."""

from __future__ import annotations

from collections.abc import Mapping

from .candidates import resolve_candidate
from .types import CandidateHealth, RoutingDecision, RoutingSession, Tier


class RoutingPolicy:
    def __init__(self, tiers: Mapping[int, Tier]) -> None:
        self._tiers = dict(tiers)

    def select_tier(self, selected_tier: int, session: RoutingSession) -> int:
        if session.hard_model_pin is not None:
            return session.tier or selected_tier
        return session.tier if session.tier_pinned and session.tier else selected_tier

    def select_candidate(
        self,
        tier: int,
        session: RoutingSession,
        health: Mapping[str, CandidateHealth],
    ) -> RoutingDecision | None:
        if session.hard_model_pin is not None:
            return RoutingDecision(
                tier=tier,
                candidate=session.hard_model_pin,
                reason="hard model pin",
                source="manual",
            )
        return resolve_candidate(self._tiers[tier], session.attempted_candidates, health)
