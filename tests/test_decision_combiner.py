"""Tests for the decision combiner."""

import pytest

from migration_control_tower.agent import EligibilityReviewAgent
from migration_control_tower.data import get_context, get_expected, get_records_by_rules_outcome, list_subscriber_ids
from migration_control_tower.decision import DecisionCombiner, UnresolvedDecisionError
from migration_control_tower.domain import MigrationTier, ReasonCodeSource, RulesOutcome
from migration_control_tower.rules import RulesEngine


@pytest.fixture
def combiner() -> DecisionCombiner:
    return DecisionCombiner()


@pytest.fixture
def rules_engine() -> RulesEngine:
    return RulesEngine()


@pytest.fixture
def agent() -> EligibilityReviewAgent:
    return EligibilityReviewAgent()


def _combine_for_subscriber(
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
    agent: EligibilityReviewAgent,
    subscriber_id: str,
):
    context = get_context(subscriber_id)
    rules_result = rules_engine.evaluate(context)
    expected = get_expected(subscriber_id)

    agent_result = None
    if expected.agent_reviewed:
        agent_result = agent.review(context, rules_result)

    decision = combiner.combine(context, rules_result, agent_result)
    return decision, expected, rules_result


@pytest.mark.parametrize("subscriber_id", list_subscriber_ids())
def test_final_tier_matches_expected(
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
    agent: EligibilityReviewAgent,
    subscriber_id: str,
) -> None:
    decision, expected, _ = _combine_for_subscriber(
        combiner, rules_engine, agent, subscriber_id
    )
    assert decision.tier == expected.final_tier
    assert decision.unresolved is False


@pytest.mark.parametrize("subscriber_id", list_subscriber_ids())
def test_recommended_action_matches_expected(
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
    agent: EligibilityReviewAgent,
    subscriber_id: str,
) -> None:
    decision, expected, _ = _combine_for_subscriber(
        combiner, rules_engine, agent, subscriber_id
    )
    assert decision.recommended_action == expected.recommended_action


@pytest.mark.parametrize("subscriber_id", list_subscriber_ids())
def test_agent_reviewed_flag_matches_expected(
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
    agent: EligibilityReviewAgent,
    subscriber_id: str,
) -> None:
    decision, expected, _ = _combine_for_subscriber(
        combiner, rules_engine, agent, subscriber_id
    )
    assert decision.agent_reviewed is expected.agent_reviewed


@pytest.mark.parametrize(
    "subscriber_id",
    [record.subscriber_id for record in get_records_by_rules_outcome(RulesOutcome.TIER_0)],
)
def test_tier_0_straight_through_from_rules_only(
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
    subscriber_id: str,
) -> None:
    context = get_context(subscriber_id)
    rules_result = rules_engine.evaluate(context)
    decision = combiner.combine(context, rules_result)

    assert decision.tier == MigrationTier.TIER_0
    assert decision.agent_reviewed is False
    assert decision.confidence == 1.0
    assert all(entry.source == ReasonCodeSource.RULES for entry in decision.reason_codes)


@pytest.mark.parametrize(
    "subscriber_id",
    [record.subscriber_id for record in get_records_by_rules_outcome(RulesOutcome.TIER_2)],
)
def test_tier_2_straight_through_from_rules_only(
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
    subscriber_id: str,
) -> None:
    context = get_context(subscriber_id)
    rules_result = rules_engine.evaluate(context)
    decision = combiner.combine(context, rules_result)

    assert decision.tier == MigrationTier.TIER_2
    assert decision.agent_reviewed is False
    assert decision.confidence == 1.0


@pytest.mark.parametrize(
    "subscriber_id",
    [record.subscriber_id for record in get_records_by_rules_outcome(RulesOutcome.AMBIGUOUS)],
)
def test_ambiguous_with_agent_matches_suggested_and_final_tier(
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
    agent: EligibilityReviewAgent,
    subscriber_id: str,
) -> None:
    decision, expected, _ = _combine_for_subscriber(
        combiner, rules_engine, agent, subscriber_id
    )

    assert decision.agent_reviewed is True
    assert decision.tier == expected.agent_suggested_tier
    assert decision.tier == expected.final_tier
    assert decision.risk_flags
    assert any(entry.source == ReasonCodeSource.RULES for entry in decision.reason_codes)
    assert any(entry.source == ReasonCodeSource.AGENT for entry in decision.reason_codes)


@pytest.mark.parametrize("subscriber_id", list_subscriber_ids())
def test_rules_reason_codes_preserved_with_provenance(
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
    agent: EligibilityReviewAgent,
    subscriber_id: str,
) -> None:
    decision, expected, _ = _combine_for_subscriber(
        combiner, rules_engine, agent, subscriber_id
    )

    rules_codes = set(decision.codes_for_source(ReasonCodeSource.RULES))
    assert rules_codes == set(expected.reason_codes)


def test_ambiguous_without_agent_fails_fast(
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
) -> None:
    context = get_context("SUB-20001")
    rules_result = rules_engine.evaluate(context)

    assert rules_result.outcome == RulesOutcome.AMBIGUOUS

    with pytest.raises(UnresolvedDecisionError):
        combiner.combine(context, rules_result, allow_unresolved=False)


@pytest.mark.parametrize(
    "subscriber_id",
    [record.subscriber_id for record in get_records_by_rules_outcome(RulesOutcome.AMBIGUOUS)],
)
def test_ambiguous_without_agent_can_return_unresolved_decision(
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
    subscriber_id: str,
) -> None:
    context = get_context(subscriber_id)
    rules_result = rules_engine.evaluate(context)

    assert rules_result.outcome == RulesOutcome.AMBIGUOUS

    decision = combiner.combine(context, rules_result, allow_unresolved=True)

    assert decision.unresolved is True
    assert decision.agent_reviewed is False
    assert decision.confidence == 0.0
    assert decision.tier == MigrationTier.TIER_1
    assert decision.rules_outcome == RulesOutcome.AMBIGUOUS
    assert all(entry.source == ReasonCodeSource.RULES for entry in decision.reason_codes)
