from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from model_router.candidates import resolve_candidate
from model_router.config import normalize_tiers
from model_router.types import Candidate, CandidateHealth, HealthState, Tier


@pytest.fixture
def router():
    name = "model_router_root_config_test"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / "__init__.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_resolver_uses_first_eligible_same_tier_candidate():
    tier = Tier(
        number=3,
        label="Heavy Execution",
        reasoning="medium",
        candidates=(
            Candidate(id="terra", provider="openai-codex", model="gpt-terra"),
            Candidate(id="glm47", provider="zai", model="glm-4.7"),
        ),
    )

    decision = resolve_candidate(tier, attempted_candidates=set(), health={})

    assert decision.candidate.id == "terra"
    assert decision.source == "primary"


def test_resolver_skips_attempted_and_unavailable_same_tier_candidates():
    tier = Tier(
        number=3,
        label="Heavy Execution",
        reasoning="medium",
        candidates=(
            Candidate(id="terra", provider="openai-codex", model="gpt-terra"),
            Candidate(id="glm47", provider="zai", model="glm-4.7"),
            Candidate(id="local-qwen", provider="lmstudio", model="qwen-local"),
        ),
    )
    health = {
        "zai:glm-4.7": CandidateHealth(state=HealthState.UNAVAILABLE),
    }

    decision = resolve_candidate(tier, attempted_candidates={"terra"}, health=health)

    assert decision.candidate.id == "local-qwen"
    assert decision.source == "same-tier-fallback"


def test_legacy_model_config_becomes_a_single_candidate_pool():
    raw_tiers = {
        tier: {"model": f"provider-{tier}/model-{tier}"}
        for tier in range(1, 6)
    }

    tiers = normalize_tiers(raw_tiers)

    assert tiers[3].candidates == (
        Candidate(id="tier-3-primary", provider="provider-3", model="model-3"),
    )


def test_root_config_uses_first_candidate_as_legacy_primary(router):
    config = router._normalize_router_config({
        "tiers": {3: {"candidates": [
            {"id": "terra", "provider": "openai-codex", "model": "gpt-terra"},
            {"id": "glm", "provider": "zai", "model": "glm-4.7"},
        ]}},
    })

    assert config["tiers"][3]["model"] == "gpt-terra"
    assert len(config["tiers"][3]["candidates"]) == 2
