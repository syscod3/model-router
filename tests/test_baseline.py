"""Regression boundary for the pre-refactor router behavior."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / "__init__.py"


@pytest.fixture()
def router():
    """Load a fresh plugin module so session state cannot leak between tests."""
    name = "model_router_baseline"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, PLUGIN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    setattr(module, "_manager_ref", None)
    yield module
    sys.modules.pop(name, None)


def test_obvious_ack_uses_tier_one_without_classifier(router):
    result = router.prepare_turn(
        session_id="ack-session",
        user_message="thanks",
        current_model="starter/model",
    )

    assert result["tier"] == 1
    assert result["model"] == router.TIERS[1]["model"]


def test_explicit_tier_request_wins_over_classifier(router):
    result = router.prepare_turn(
        session_id="explicit-tier-session",
        user_message="Please use T4 for this design.",
        current_model="starter/model",
    )

    assert result["tier"] == 4
    assert result["model"] == router.TIERS[4]["model"]


def test_legacy_model_config_remains_a_five_tier_contract(router):
    config = router._normalize_router_config(
        {"tiers": {3: {"label": "Custom T3", "model": "vendor/custom"}}}
    )

    assert set(config["tiers"]) == {1, 2, 3, 4, 5}
    assert config["tiers"][3]["model"] == "vendor/custom"
    assert config["tiers"][3]["label"] == "Custom T3"


def test_manual_pin_stops_routing_until_auto_unpins(router):
    router.pin_session("pinned-session", "manual/model")

    pinned = router.prepare_turn(
        session_id="pinned-session",
        user_message="use T4",
        current_model="manual/model",
    )
    router.unpin_session("pinned-session")
    resumed = router.prepare_turn(
        session_id="pinned-session",
        user_message="thanks",
        current_model="manual/model",
    )

    assert pinned["pinned"] is True
    assert pinned["model"] == "manual/model"
    assert resumed["pinned"] is False
    assert resumed["tier"] == 1


def test_two_consecutive_tool_errors_escalate_one_tier(router):
    agent = SimpleNamespace(model=router.TIERS[2]["model"], reasoning_config=None)
    cli = SimpleNamespace(agent=agent, _vprint=lambda _message: None)
    router._manager_ref = SimpleNamespace(_cli_ref=cli)
    router.bind_session_agent("tool-session", agent)
    router._last_tier["tool-session"] = 2
    router._base_tier["tool-session"] = 2

    router.on_post_tool_call(session_id="tool-session", result="Error: first failure")
    router.on_post_tool_call(session_id="tool-session", result="Error: second failure")

    assert router.get_last_tier("tool-session") == 3
    assert agent.model == router.TIERS[3]["model"]
