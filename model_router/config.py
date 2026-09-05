"""Configuration normalization for the policy core."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .types import Candidate, Tier


def normalize_tiers(raw_tiers: Mapping[Any, Any]) -> dict[int, Tier]:
    """Accept legacy ``model`` tiers and normalize them to candidate pools."""
    tiers: dict[int, Tier] = {}
    for number in range(1, 6):
        raw = raw_tiers.get(number, raw_tiers.get(str(number), {}))
        if not isinstance(raw, Mapping):
            raise ValueError(f"tiers.{number} must be a mapping")
        raw_candidates = raw.get("candidates")
        if raw_candidates is None:
            legacy_model = str(raw.get("model") or "")
            provider, separator, model = legacy_model.partition("/")
            if not separator or not provider or not model:
                raise ValueError(
                    f"tiers.{number}.model must use provider/model for compatibility"
                )
            raw_candidates = [
                {
                    "id": f"tier-{number}-primary",
                    "provider": provider,
                    "model": model,
                }
            ]
        if not isinstance(raw_candidates, list) or not raw_candidates:
            raise ValueError(f"tiers.{number}.candidates must be a non-empty list")
        candidates = tuple(
            Candidate(
                id=str(item.get("id") or f"tier-{number}-{index}"),
                provider=str(item.get("provider") or ""),
                model=str(item.get("model") or ""),
                reasoning=item.get("reasoning", raw.get("reasoning")),
                base_url=item.get("base_url"),
                priority=index,
                paid=bool(item.get("paid", False)),
                disabled=bool(item.get("disabled", False)),
            )
            for index, item in enumerate(raw_candidates)
            if isinstance(item, Mapping)
        )
        if len(candidates) != len(raw_candidates) or any(
            not candidate.provider or not candidate.model for candidate in candidates
        ):
            raise ValueError(f"tiers.{number}.candidates need provider and model")
        tiers[number] = Tier(
            number=number,
            label=str(raw.get("label") or f"T{number}"),
            reasoning=raw.get("reasoning"),
            candidates=candidates,
        )
    return tiers
