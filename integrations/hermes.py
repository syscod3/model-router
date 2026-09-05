"""Hermes-only live-agent routing compatibility adapter.

The policy core never imports this module. Replace this adapter when Hermes
ships a native per-turn route override.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HermesRouteTarget:
    provider: str
    model: str
    base_url: str = ""
    api_mode: str = ""
    api_key: str = ""
    reasoning: str | None = None
    capabilities: dict[str, Any] | None = None


def apply_route(agent: Any, target: HermesRouteTarget) -> None:
    """Apply a complete route to a live Hermes agent without restarting it."""
    switch_model = getattr(agent, "switch_model", None)
    if not callable(switch_model):
        raise RuntimeError("Hermes agent does not support switch_model")

    switch_model(
        target.model,
        target.provider,
        target.api_key,
        target.base_url,
        target.api_mode,
        target.capabilities,
    )
    agent.reasoning_config = (
        {"effort": target.reasoning} if target.reasoning else None
    )
