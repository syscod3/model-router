from __future__ import annotations

import importlib.util
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from model_router.health import HealthStore


def _router():
    name = "model_router_route_observability_test"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / "__init__.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_route_observability_reports_and_resets_health_without_resetting_budget(tmp_path):
    router = _router()
    router._apply_router_config(router._normalize_router_config({
        "payg": {"daily_budget_usd": 0.05},
        "tiers": {2: {"candidates": [
            {"provider": "free", "model": "primary"},
            {"provider": "openrouter", "model": "overflow", "paid": True, "estimated_cost_usd": 0.03},
        ]}},
    }))
    store = HealthStore(tmp_path / "state.db")
    router._health_store = store
    router._last_tier["route"] = 2
    store.record_failure(
        "free:primary", router.classify_failure(status_code=429), now=time.time()
    )
    assert store.reserve_budget_usd("2026-09-05", daily_limit_usd=0.05, amount_usd=0.03)

    health = router.get_route_health("route")
    assert health[0]["state"] == "cooling_down"
    assert health[1]["paid"] is True
    assert router.reset_route_health("route") == 2
    assert store.get("free:primary", now=time.time()).state.value == "healthy"
    assert store.remaining_budget_usd("2026-09-05", daily_limit_usd=0.05) == pytest.approx(0.02)


def test_route_status_reports_pin_tier_and_budget(tmp_path):
    router = _router()
    router._apply_router_config(router._normalize_router_config({"payg": {"daily_budget_usd": 0.05}}))
    router._health_store = HealthStore(tmp_path / "state.db")
    router._last_tier["route"] = 2
    router.pin_session("route", "manual/model")
    day = datetime.now(timezone.utc).date().isoformat()
    assert router._health_store.reserve_budget_usd(day, daily_limit_usd=0.05, amount_usd=0.03)

    status = router.get_route_status("route")

    assert status["tier"] == 2
    assert status["pinned"] is True
    assert status["remaining_budget_usd"] == pytest.approx(0.02)