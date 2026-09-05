from __future__ import annotations

from model_router.failures import FailureType, classify_failure
from model_router.health import HealthStore
from model_router.types import HealthState


def test_retry_after_429_is_shared_and_persisted(tmp_path):
    database = tmp_path / "state.db"
    store = HealthStore(database)

    failure = classify_failure(status_code=429, retry_after_seconds=120)
    store.record_failure("openai-codex:gpt-terra", failure, now=1_000)

    stored = HealthStore(database).get("openai-codex:gpt-terra", now=1_010)
    assert failure.type is FailureType.RATE_LIMIT
    assert stored.state is HealthState.COOLING_DOWN
    assert stored.cooldown_until == 1_120


def test_expired_cooldown_returns_candidate_to_healthy(tmp_path):
    store = HealthStore(tmp_path / "state.db")
    store.record_failure(
        "zai:glm-4.7", classify_failure(status_code=503), now=1_000
    )

    assert store.get("zai:glm-4.7", now=1_030).state is HealthState.COOLING_DOWN
    assert store.get("zai:glm-4.7", now=1_061).state is HealthState.HEALTHY
