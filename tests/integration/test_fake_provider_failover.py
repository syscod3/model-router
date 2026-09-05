"""Opt-in integration boundary: uses a fake provider and never opens a network connection."""

from __future__ import annotations

import importlib.util
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from model_router.health import HealthStore


pytestmark = pytest.mark.skipif(
    os.environ.get("MODEL_ROUTER_INTEGRATION") != "1",
    reason="set MODEL_ROUTER_INTEGRATION=1 to run fake-provider integration tests",
)


class FakeProviderAgent:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.reasoning_config = None

    def switch_model(self, model, provider, api_key="", base_url="", api_mode="", capabilities=None):
        self.calls.append((provider, model))
        self.model = model


def _router():
    name = "model_router_fake_provider_integration"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[2] / "__init__.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_fake_provider_429_fails_over_without_network(tmp_path):
    router = _router()
    router._apply_router_config(router._normalize_router_config({
        "tiers": {2: {"candidates": [
            {"provider": "fake-primary", "model": "primary"},
            {"provider": "fake-fallback", "model": "fallback"},
        ]}},
    }))
    router._health_store = HealthStore(tmp_path / "state.db")
    router._last_tier["integration"] = 2
    agent = FakeProviderAgent()
    router.bind_session_agent("integration", agent)

    router.on_api_request_error(
        session_id="integration", provider="fake-primary", model="primary", status_code=429
    )

    assert agent.calls == [("fake-fallback", "fallback")]


def test_fake_provider_exhaustion_uses_fixed_payg_overflow_within_budget(tmp_path):
    router = _router()
    router._apply_router_config(router._normalize_router_config({
        "payg": {"daily_budget_usd": 0.05},
        "tiers": {2: {"candidates": [
            {"provider": "fake-primary", "model": "primary"},
            {"provider": "fake-fallback", "model": "fallback"},
            {
                "provider": "openrouter",
                "model": "fixed-overflow",
                "paid": True,
                "estimated_cost_usd": 0.03,
            },
        ]}},
    }))
    store = HealthStore(tmp_path / "state.db")
    router._health_store = store
    router._last_tier["integration"] = 2
    agent = FakeProviderAgent()
    router.bind_session_agent("integration", agent)

    router.on_api_request_error(
        session_id="integration", provider="fake-primary", model="primary", status_code=429
    )
    router.on_api_request_error(
        session_id="integration", provider="fake-fallback", model="fallback", status_code=429
    )

    assert agent.calls == [
        ("fake-fallback", "fallback"),
        ("openrouter", "fixed-overflow"),
    ]
    assert store.remaining_budget_usd(
        datetime.now(timezone.utc).date().isoformat(), daily_limit_usd=0.05
    ) == pytest.approx(0.02)
