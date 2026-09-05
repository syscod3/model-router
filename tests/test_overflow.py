import pytest

from model_router.health import HealthStore
from model_router.overflow import resolve_overflow
from model_router.types import Candidate, CandidateHealth, HealthState, Tier


def test_overflow_uses_only_fixed_cost_paid_candidate_within_budget():
    tier = Tier(
        number=2,
        label="Default",
        reasoning=None,
        candidates=(
            Candidate(id="free", provider="local", model="free"),
            Candidate(
                id="payg", provider="openrouter", model="fixed", paid=True,
                estimated_cost_usd=0.03,
            ),
            Candidate(
                id="unsupported-paid", provider="other", model="fixed", paid=True,
                estimated_cost_usd=0.01,
            ),
            Candidate(id="unknown-cost", provider="openrouter", model="unknown", paid=True),
        ),
    )

    decision = resolve_overflow(tier, {"free"}, {}, remaining_budget_usd=0.03)

    assert decision is not None
    assert decision.candidate.id == "payg"
    assert decision.source == "overflow"


def test_overflow_skips_paid_candidates_from_unsupported_providers():
    tier = Tier(
        number=2,
        label="Default",
        reasoning=None,
        candidates=(
            Candidate(id="other", provider="other", model="fixed", paid=True, estimated_cost_usd=0.01),
        ),
    )

    assert resolve_overflow(tier, set(), {}, remaining_budget_usd=1.0) is None


def test_overflow_skips_unhealthy_or_over_budget_candidate():
    tier = Tier(
        number=2,
        label="Default",
        reasoning=None,
        candidates=(
            Candidate(id="payg", provider="openrouter", model="fixed", paid=True, estimated_cost_usd=0.03),
        ),
    )

    assert resolve_overflow(tier, set(), {}, remaining_budget_usd=0.02) is None
    assert resolve_overflow(
        tier,
        set(),
        {"openrouter:fixed": CandidateHealth(state=HealthState.COOLING_DOWN)},
        remaining_budget_usd=1.0,
    ) is None


@pytest.mark.parametrize("cost", [float("nan"), float("inf"), float("-inf")])
def test_overflow_skips_non_finite_costs(cost):
    tier = Tier(
        number=2,
        label="Default",
        reasoning=None,
        candidates=(
            Candidate(id="payg", provider="openrouter", model="fixed", paid=True, estimated_cost_usd=cost),
        ),
    )

    assert resolve_overflow(tier, set(), {}, remaining_budget_usd=1.0) is None


@pytest.mark.parametrize("remaining_budget_usd", [float("nan"), float("inf"), float("-inf")])
def test_overflow_skips_non_finite_remaining_budget(remaining_budget_usd):
    tier = Tier(
        number=2,
        label="Default",
        reasoning=None,
        candidates=(
            Candidate(id="payg", provider="openrouter", model="fixed", paid=True, estimated_cost_usd=0.03),
        ),
    )

    assert resolve_overflow(tier, set(), {}, remaining_budget_usd=remaining_budget_usd) is None


def test_daily_budget_reservation_is_shared_and_cannot_exceed_cap(tmp_path):
    store = HealthStore(tmp_path / "state.db")

    assert store.reserve_budget_usd("2026-09-05", daily_limit_usd=0.05, amount_usd=0.03)
    assert not store.reserve_budget_usd("2026-09-05", daily_limit_usd=0.05, amount_usd=0.03)
    assert store.remaining_budget_usd("2026-09-05", daily_limit_usd=0.05) == pytest.approx(0.02)
    assert HealthStore(tmp_path / "state.db").reserve_budget_usd(
        "2026-09-06", daily_limit_usd=0.05, amount_usd=0.05
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_daily_budget_rejects_non_finite_limits_and_reservations(tmp_path, value):
    store = HealthStore(tmp_path / "state.db")

    assert not store.reserve_budget_usd("2026-09-05", daily_limit_usd=0.05, amount_usd=value)
    assert not store.reserve_budget_usd("2026-09-05", daily_limit_usd=value, amount_usd=0.01)
    assert store.remaining_budget_usd("2026-09-05", daily_limit_usd=value) == 0.0
