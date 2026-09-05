from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from model_router.health import HealthStore


class FakeAgent:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.reasoning_config = None

    def switch_model(self, model, provider, api_key="", base_url="", api_mode="", capabilities=None):
        self.calls.append((model, provider, api_key, base_url, api_mode, capabilities))
        self.model = model


def _router():
    name = "model_router_payg_test"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / "__init__.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_api_failure_uses_paid_overflow_only_after_free_candidates_and_within_budget(tmp_path):
    router = _router()
    router._apply_router_config(router._normalize_router_config({
        "payg": {"daily_budget_usd": 0.05},
        "tiers": {2: {"candidates": [
            {"provider": "free", "model": "primary"},
            {
                "provider": "unsupported", "model": "not-payg", "paid": True,
                "estimated_cost_usd": 0.01,
            },
            {
                "provider": "openrouter", "model": "fixed-overflow", "paid": True,
                "estimated_cost_usd": 0.03,
            },
        ]}},
    }))
    router._health_store = HealthStore(tmp_path / "state.db")
    agent = FakeAgent()
    router.bind_session_agent("payg", agent)
    router._last_tier["payg"] = 2

    router.on_api_request_error(
        session_id="payg", provider="free", model="primary", status_code=429
    )
    router.on_api_request_error(
        session_id="payg", provider="free", model="primary", status_code=429
    )

    assert [call[:2] for call in agent.calls] == [("fixed-overflow", "openrouter")]


def test_api_failure_does_not_use_non_finite_payg_budget_or_cost(tmp_path):
    router = _router()
    router._apply_router_config(router._normalize_router_config({
        "payg": {"daily_budget_usd": float("inf")},
        "tiers": {2: {"candidates": [
            {"provider": "free", "model": "primary"},
            {
                "provider": "openrouter", "model": "unbounded", "paid": True,
                "estimated_cost_usd": float("nan"),
            },
        ]}},
    }))
    router._health_store = HealthStore(tmp_path / "state.db")
    agent = FakeAgent()
    router.bind_session_agent("payg", agent)
    router._last_tier["payg"] = 2

    router.on_api_request_error(
        session_id="payg", provider="free", model="primary", status_code=429
    )

    assert agent.calls == []


def test_api_failure_skips_disabled_payg_overflow_candidate(tmp_path):
    router = _router()
    router._apply_router_config(router._normalize_router_config({
        "payg": {"daily_budget_usd": 0.05},
        "tiers": {2: {"candidates": [
            {"provider": "free", "model": "primary"},
            {
                "provider": "openrouter", "model": "disabled-overflow", "paid": True,
                "estimated_cost_usd": 0.03, "disabled": True,
            },
        ]}},
    }))
    store = HealthStore(tmp_path / "state.db")
    router._health_store = store
    agent = FakeAgent()
    router.bind_session_agent("disabled-payg", agent)
    router._last_tier["disabled-payg"] = 2

    router.on_api_request_error(
        session_id="disabled-payg", provider="free", model="primary", status_code=429
    )

    assert agent.calls == []
    assert store.remaining_budget_usd("2026-09-05", daily_limit_usd=0.05) == 0.05
