"""Tests for domain models, reason codes, and brand policy hook."""

import pytest
from pydantic import ValidationError

from migration_control_tower.domain import (
    AgentReviewResult,
    BrandMetadata,
    CanonicalMigrationContext,
    DEFAULT_BRAND_POLICY_HOOK,
    MiCCExecutionResult,
    MigrationDecision,
    MigrationTier,
    MiCCExecutionStatus,
    ReasonCode,
    ReasonCodeSource,
    RecommendedAction,
    RulesOutcome,
    RulesResult,
    SourcedReasonCode,
)


@pytest.fixture
def sample_context() -> CanonicalMigrationContext:
    return CanonicalMigrationContext(
        subscriber_id="SUB-10001",
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


def test_canonical_context_fields(sample_context: CanonicalMigrationContext) -> None:
    assert sample_context.subscriber_id == "SUB-10001"
    assert sample_context.brand.brand_id == "1und1"
    assert sample_context.recent_case_count == 0


def test_rules_result_tier_0_auto_fills_tier() -> None:
    result = RulesResult(
        outcome=RulesOutcome.TIER_0,
        reason_codes=[ReasonCode.AUTO_MIGRATE_READY],
        matched_rules=["tier_0_all_clear"],
    )
    assert result.tier == MigrationTier.TIER_0


def test_rules_result_tier_2_auto_fills_tier() -> None:
    result = RulesResult(
        outcome=RulesOutcome.TIER_2,
        reason_codes=[ReasonCode.BILLING_NOT_OK],
        matched_rules=["tier_2_billing_block"],
    )
    assert result.tier == MigrationTier.TIER_2


def test_rules_result_ambiguous_has_no_tier() -> None:
    result = RulesResult(
        outcome=RulesOutcome.AMBIGUOUS,
        reason_codes=[ReasonCode.MIXED_READINESS_SIGNALS],
        matched_rules=["ambiguous_mixed_signals"],
    )
    assert result.tier is None


def test_rules_result_ambiguous_rejects_tier() -> None:
    with pytest.raises(ValidationError):
        RulesResult(
            outcome=RulesOutcome.AMBIGUOUS,
            tier=MigrationTier.TIER_1,
            reason_codes=[ReasonCode.MIXED_READINESS_SIGNALS],
        )


def test_agent_review_can_suggest_any_tier() -> None:
    for tier in MigrationTier:
        result = AgentReviewResult(
            suggested_tier=tier,
            confidence_score=0.75,
            reason_codes=[ReasonCode.PARTIAL_MIGRATION_READINESS],
            risk_flags=["care_history"],
            review_summary=f"Agent suggests {tier.value}.",
            recommended_action=RecommendedAction.ASSISTED_REVIEW,
        )
        assert result.suggested_tier == tier


def test_migration_decision_from_rules_path(sample_context: CanonicalMigrationContext) -> None:
    decision = MigrationDecision(
        subscriber_id=sample_context.subscriber_id,
        tier=MigrationTier.TIER_0,
        reason_codes=[
            SourcedReasonCode(source=ReasonCodeSource.RULES, code=ReasonCode.ELIGIBILITY_CONFIRMED)
        ],
        confidence=1.0,
        recommended_action=RecommendedAction.AUTO_MIGRATE,
        review_summary="Straight-through eligibility confirmed by rules.",
        rules_outcome=RulesOutcome.TIER_0,
        agent_reviewed=False,
    )
    assert decision.agent_reviewed is False
    assert decision.tier == MigrationTier.TIER_0


def test_migration_decision_from_agent_path() -> None:
    decision = MigrationDecision(
        subscriber_id="SUB-10002",
        tier=MigrationTier.TIER_1,
        reason_codes=[
            SourcedReasonCode(source=ReasonCodeSource.RULES, code=ReasonCode.OPEN_COMPLAINT),
            SourcedReasonCode(
                source=ReasonCodeSource.AGENT, code=ReasonCode.PARTIAL_MIGRATION_READINESS
            ),
        ],
        confidence=0.68,
        recommended_action=RecommendedAction.ASSISTED_REVIEW,
        review_summary="Conflicting care and provisioning signals require assisted handling.",
        rules_outcome=RulesOutcome.AMBIGUOUS,
        agent_reviewed=True,
        risk_flags=["open_care_complaint"],
    )
    assert decision.agent_reviewed is True
    assert decision.rules_outcome == RulesOutcome.AMBIGUOUS
    assert decision.codes_for_source(ReasonCodeSource.AGENT) == [
        ReasonCode.PARTIAL_MIGRATION_READINESS
    ]


def test_sourced_reason_code_prefixed() -> None:
    sourced = SourcedReasonCode(source=ReasonCodeSource.RULES, code=ReasonCode.BILLING_NOT_OK)
    assert sourced.prefixed == "rules:BILLING_NOT_OK"


def test_micc_execution_result(sample_context: CanonicalMigrationContext) -> None:
    result = MiCCExecutionResult(
        subscriber_id=sample_context.subscriber_id,
        decision_tier=MigrationTier.TIER_0,
        recommended_action=RecommendedAction.AUTO_MIGRATE,
        queue_name="migration-auto-queue",
        queue_id="MICC-SUB-10001-MIGRATION_AUTO_QUEUE",
        job_id="JOB-SUB-10001",
        status=MiCCExecutionStatus.EXECUTED_SUCCESS,
        message="Decision accepted by MiCC stub queue.",
        submitted_at="2026-06-12T12:00:00+00:00",
    )
    assert result.status == MiCCExecutionStatus.EXECUTED_SUCCESS


def test_reason_codes_are_unique_strings() -> None:
    values = [code.value for code in ReasonCode]
    assert len(values) == len(set(values))


def test_brand_policy_hook_noop(sample_context: CanonicalMigrationContext) -> None:
    assert DEFAULT_BRAND_POLICY_HOOK.apply(sample_context) == sample_context
