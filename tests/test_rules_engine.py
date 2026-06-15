"""Tests for the deterministic rules engine."""

import pytest

from migration_control_tower.data import get_context, get_expected, get_records_by_rules_outcome, list_subscriber_ids
from migration_control_tower.domain import MigrationTier, ReasonCode, RulesOutcome
from migration_control_tower.rules import RuleId, RulesEngine

# Primary ambiguous trigger per dataset record — each ambiguous case is distinct.
AMBIGUOUS_PRIMARY_RULE = {
    "SUB-20001": RuleId.AMB_OPEN_COMPLAINT,
    "SUB-20002": RuleId.AMB_NETWORK_NOT_READY,
    "SUB-20003": RuleId.AMB_SIM_SWAP_REQUIRED,
    "SUB-20004": RuleId.AMB_PROVISIONING_INCOMPLETE,
    "SUB-20005": RuleId.AMB_ESCALATION_OPEN,
}


@pytest.fixture
def engine() -> RulesEngine:
    return RulesEngine()


@pytest.mark.parametrize("subscriber_id", list_subscriber_ids())
def test_rules_outcome_matches_dataset(engine: RulesEngine, subscriber_id: str) -> None:
    context = get_context(subscriber_id)
    expected = get_expected(subscriber_id)
    result = engine.evaluate(context)

    assert result.outcome == expected.rules_outcome


@pytest.mark.parametrize("subscriber_id", list_subscriber_ids())
def test_rules_tier_matches_dataset(engine: RulesEngine, subscriber_id: str) -> None:
    context = get_context(subscriber_id)
    expected = get_expected(subscriber_id)
    result = engine.evaluate(context)

    if expected.rules_outcome == RulesOutcome.AMBIGUOUS:
        assert result.tier is None
    else:
        assert result.tier == MigrationTier(expected.rules_outcome.value)


@pytest.mark.parametrize("subscriber_id", list_subscriber_ids())
def test_rules_reason_codes_match_dataset(engine: RulesEngine, subscriber_id: str) -> None:
    context = get_context(subscriber_id)
    expected = get_expected(subscriber_id)
    result = engine.evaluate(context)

    assert set(result.reason_codes) == set(expected.reason_codes)


@pytest.mark.parametrize(
    "subscriber_id",
    [record.subscriber_id for record in get_records_by_rules_outcome(RulesOutcome.TIER_0)],
)
def test_tier_0_straight_through(engine: RulesEngine, subscriber_id: str) -> None:
    result = engine.evaluate(get_context(subscriber_id))

    assert result.outcome == RulesOutcome.TIER_0
    assert result.tier == MigrationTier.TIER_0
    assert RuleId.T0_STRAIGHT_THROUGH_ELIGIBLE.value in result.matched_rules
    assert ReasonCode.AUTO_MIGRATE_READY in result.reason_codes


@pytest.mark.parametrize(
    "subscriber_id",
    [record.subscriber_id for record in get_records_by_rules_outcome(RulesOutcome.TIER_2)],
)
def test_tier_2_hard_blocks(engine: RulesEngine, subscriber_id: str) -> None:
    result = engine.evaluate(get_context(subscriber_id))

    assert result.outcome == RulesOutcome.TIER_2
    assert result.tier == MigrationTier.TIER_2
    assert result.matched_rules
    assert all(rule.startswith("t2_") for rule in result.matched_rules)


@pytest.mark.parametrize(
    "subscriber_id,primary_rule",
    list(AMBIGUOUS_PRIMARY_RULE.items()),
    ids=list(AMBIGUOUS_PRIMARY_RULE.keys()),
)
def test_ambiguous_cases_have_distinct_primary_triggers(
    engine: RulesEngine,
    subscriber_id: str,
    primary_rule: RuleId,
) -> None:
    result = engine.evaluate(get_context(subscriber_id))

    assert result.outcome == RulesOutcome.AMBIGUOUS
    assert result.tier is None
    assert primary_rule.value in result.matched_rules


def test_ambiguous_primary_rules_are_unique() -> None:
    assert len(set(AMBIGUOUS_PRIMARY_RULE.values())) == len(AMBIGUOUS_PRIMARY_RULE)


@pytest.mark.parametrize(
    "subscriber_id",
    [record.subscriber_id for record in get_records_by_rules_outcome(RulesOutcome.AMBIGUOUS)],
)
def test_rules_outcome_separate_from_final_tier(engine: RulesEngine, subscriber_id: str) -> None:
    """Expected metadata is stage-aware: rules outcome vs agent/final tier."""
    expected = get_expected(subscriber_id)
    result = engine.evaluate(get_context(subscriber_id))

    assert result.outcome == RulesOutcome.AMBIGUOUS
    assert expected.rules_outcome == RulesOutcome.AMBIGUOUS
    # Final tier may differ once the agent reviews (e.g. SUB-20005 → tier_2).
    assert expected.final_tier in {MigrationTier.TIER_0, MigrationTier.TIER_1, MigrationTier.TIER_2}


def test_tier2_blocks_before_ambiguous_care_signals(engine: RulesEngine) -> None:
    """Suspended account is Tier 2 even when care signals would otherwise be ambiguous."""
    result = engine.evaluate(get_context("SUB-30003"))

    assert result.outcome == RulesOutcome.TIER_2
    assert RuleId.T2_ACCOUNT_SUSPENDED.value in result.matched_rules
    assert RuleId.AMB_OPEN_COMPLAINT.value not in result.matched_rules


def test_tier2_blocks_before_ambiguous_provisioning(engine: RulesEngine) -> None:
    """In-progress migration is Tier 2 even with other soft signals present."""
    result = engine.evaluate(get_context("SUB-30004"))

    assert result.outcome == RulesOutcome.TIER_2
    assert RuleId.T2_PRIOR_MIGRATION_IN_PROGRESS.value in result.matched_rules
