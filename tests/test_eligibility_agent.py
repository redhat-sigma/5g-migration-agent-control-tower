"""Tests for the eligibility review agent."""

import pytest

from migration_control_tower.agent import AmbiguousReviewRequiredError, EligibilityReviewAgent
from migration_control_tower.data import get_context, get_expected, get_records_by_rules_outcome
from migration_control_tower.domain import (
    BrandMetadata,
    CanonicalMigrationContext,
    MigrationTier,
    ReasonCode,
    RecommendedAction,
    RulesOutcome,
    RulesResult,
)
from migration_control_tower.rules import RuleId, RulesEngine

AMBIGUOUS_IDS = [
    record.subscriber_id for record in get_records_by_rules_outcome(RulesOutcome.AMBIGUOUS)
]

# Expected confidence bands per scenario (heuristic, not exact floats).
CONFIDENCE_BANDS = {
    "ambiguous_open_complaint_vs_ready_network": (0.65, 0.75),
    "ambiguous_network_not_ready": (0.58, 0.68),
    "ambiguous_sim_swap_required": (0.65, 0.75),
    "ambiguous_provisioning_pending_validation": (0.55, 0.65),
    "ambiguous_escalation_with_green_technical_signals": (0.80, 0.90),
}

ACTION_BY_TIER = {
    MigrationTier.TIER_0: RecommendedAction.AUTO_MIGRATE,
    MigrationTier.TIER_1: RecommendedAction.ASSISTED_REVIEW,
    MigrationTier.TIER_2: RecommendedAction.BLOCK,
}


@pytest.fixture
def agent() -> EligibilityReviewAgent:
    return EligibilityReviewAgent()


@pytest.fixture
def rules_engine() -> RulesEngine:
    return RulesEngine()


@pytest.mark.parametrize("subscriber_id", AMBIGUOUS_IDS)
def test_agent_suggested_tier_matches_dataset(
    agent: EligibilityReviewAgent,
    rules_engine: RulesEngine,
    subscriber_id: str,
) -> None:
    context = get_context(subscriber_id)
    rules_result = rules_engine.evaluate(context)
    expected = get_expected(subscriber_id)

    review = agent.review(context, rules_result)

    assert review.suggested_tier == expected.agent_suggested_tier


@pytest.mark.parametrize("subscriber_id", AMBIGUOUS_IDS)
def test_confidence_and_action_consistent_with_scenario(
    agent: EligibilityReviewAgent,
    rules_engine: RulesEngine,
    subscriber_id: str,
) -> None:
    context = get_context(subscriber_id)
    rules_result = rules_engine.evaluate(context)
    expected = get_expected(subscriber_id)
    review = agent.review(context, rules_result)

    low, high = CONFIDENCE_BANDS[expected.scenario]
    assert low <= review.confidence_score <= high
    assert review.recommended_action == ACTION_BY_TIER[review.suggested_tier]
    assert review.recommended_action == expected.recommended_action


@pytest.mark.parametrize("subscriber_id", AMBIGUOUS_IDS)
def test_agent_review_includes_risk_flags_and_summary(
    agent: EligibilityReviewAgent,
    rules_engine: RulesEngine,
    subscriber_id: str,
) -> None:
    context = get_context(subscriber_id)
    rules_result = rules_engine.evaluate(context)
    review = agent.review(context, rules_result)

    assert review.review_summary
    assert review.risk_flags
    assert review.reason_codes


def test_agent_only_runs_for_ambiguous_rules_outcomes(
    agent: EligibilityReviewAgent,
    rules_engine: RulesEngine,
) -> None:
    for outcome in (RulesOutcome.TIER_0, RulesOutcome.TIER_2):
        for record in get_records_by_rules_outcome(outcome):
            context = record.context
            rules_result = rules_engine.evaluate(context)

            assert rules_result.outcome == outcome
            with pytest.raises(AmbiguousReviewRequiredError):
                agent.review(context, rules_result)


def test_agent_rejects_non_ambiguous_rules_result_directly(agent: EligibilityReviewAgent) -> None:
    context = get_context("SUB-10001")
    rules_result = RulesResult(
        outcome=RulesOutcome.TIER_0,
        reason_codes=[ReasonCode.AUTO_MIGRATE_READY],
        matched_rules=[RuleId.T0_STRAIGHT_THROUGH_ELIGIBLE.value],
    )

    with pytest.raises(AmbiguousReviewRequiredError):
        agent.review(context, rules_result)


def test_agent_can_recommend_tier_0_for_minor_unresolved_ambiguity(
    agent: EligibilityReviewAgent,
) -> None:
    """Tier 0 is reachable when care and technical gap scores are both zero."""
    context = CanonicalMigrationContext(
        subscriber_id="SUB-AGENT-T0",
        brand=BrandMetadata(brand_id="1und1"),
        contract_type="postpaid",
        account_status="active",
        billing_ok=True,
        sim_status="active",
        provisioning_state="complete",
        network_ready=True,
        prior_migration_state="none",
        device_model="iPhone 14",
        is_5g_capable=True,
        requires_sim_swap=False,
        open_complaint=False,
        recent_case_count=0,
        escalation_flag=False,
    )
    rules_result = RulesResult(
        outcome=RulesOutcome.AMBIGUOUS,
        reason_codes=[],
        matched_rules=[RuleId.AMB_UNRESOLVED.value],
    )

    review = agent.review(context, rules_result)

    assert review.suggested_tier == MigrationTier.TIER_0
    assert review.recommended_action == RecommendedAction.AUTO_MIGRATE
    assert review.confidence_score >= 0.70


def test_escalation_scenario_flags_care_technical_conflict(
    agent: EligibilityReviewAgent,
    rules_engine: RulesEngine,
) -> None:
    context = get_context("SUB-20005")
    rules_result = rules_engine.evaluate(context)
    review = agent.review(context, rules_result)

    assert review.suggested_tier == MigrationTier.TIER_2
    assert "care_escalation_active" in review.risk_flags
    assert "care_technical_conflict" in review.risk_flags
    assert ReasonCode.CONFLICTING_CARE_AND_PROVISIONING in review.reason_codes
