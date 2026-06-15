"""Heuristic eligibility review for ambiguous rules outcomes."""

from __future__ import annotations

from migration_control_tower.agent.heuristics import (
    AgentSignals,
    agent_reason_codes,
    assess_signals,
)
from migration_control_tower.domain.enums import MigrationTier, RecommendedAction, RulesOutcome
from migration_control_tower.domain.models import (
    AgentReviewResult,
    CanonicalMigrationContext,
    RulesResult,
)
from migration_control_tower.rules.definitions import RuleId


class AmbiguousReviewRequiredError(ValueError):
    """Raised when the agent is invoked for a non-ambiguous rules outcome."""


def _tier2_review(signals: AgentSignals, rules_result: RulesResult) -> AgentReviewResult | None:
    """Recommend Tier 2 when care risk outweighs green technical readiness."""
    escalation_present = RuleId.AMB_ESCALATION_OPEN.value in rules_result.matched_rules
    high_case_volume = RuleId.AMB_RECENT_CASE_ACTIVITY.value in rules_result.matched_rules

    if escalation_present and signals.technical_readiness_green:
        return AgentReviewResult(
            suggested_tier=MigrationTier.TIER_2,
            confidence_score=0.85,
            reason_codes=agent_reason_codes(rules_result, signals),
            risk_flags=signals.care_risk_flags + signals.technical_risk_flags,
            review_summary=(
                "Care escalation with otherwise green technical readiness warrants "
                "blocking migration until care resolution."
            ),
            recommended_action=RecommendedAction.BLOCK,
        )

    if high_case_volume and signals.technical_readiness_green and signals.care_risk_score >= 4:
        return AgentReviewResult(
            suggested_tier=MigrationTier.TIER_2,
            confidence_score=0.80,
            reason_codes=agent_reason_codes(rules_result, signals),
            risk_flags=signals.care_risk_flags + signals.technical_risk_flags,
            review_summary=(
                "Elevated care activity conflicts with green technical signals; "
                "migration should remain blocked pending care review."
            ),
            recommended_action=RecommendedAction.BLOCK,
        )

    return None


def _tier1_review(
    context: CanonicalMigrationContext,
    signals: AgentSignals,
    rules_result: RulesResult,
) -> AgentReviewResult | None:
    """Recommend Tier 1 for assisted handling of soft gaps or care friction."""
    matched = set(rules_result.matched_rules)

    if RuleId.AMB_OPEN_COMPLAINT.value in matched:
        return AgentReviewResult(
            suggested_tier=MigrationTier.TIER_1,
            confidence_score=0.68,
            reason_codes=agent_reason_codes(rules_result, signals),
            risk_flags=signals.care_risk_flags + signals.technical_risk_flags,
            review_summary=(
                "Technical readiness looks sound, but an open care complaint requires "
                "assisted review before migration."
            ),
            recommended_action=RecommendedAction.ASSISTED_REVIEW,
        )

    if RuleId.AMB_NETWORK_NOT_READY.value in matched:
        return AgentReviewResult(
            suggested_tier=MigrationTier.TIER_1,
            confidence_score=0.62,
            reason_codes=agent_reason_codes(rules_result, signals),
            risk_flags=signals.care_risk_flags + signals.technical_risk_flags,
            review_summary=(
                "Account and device signals are eligible, but network readiness is "
                "unconfirmed and needs assisted follow-up."
            ),
            recommended_action=RecommendedAction.ASSISTED_REVIEW,
        )

    if RuleId.AMB_PROVISIONING_INCOMPLETE.value in matched:
        return AgentReviewResult(
            suggested_tier=MigrationTier.TIER_1,
            confidence_score=0.60,
            reason_codes=agent_reason_codes(rules_result, signals),
            risk_flags=signals.care_risk_flags + signals.technical_risk_flags,
            review_summary=(
                "Provisioning is not fully validated despite other positive readiness "
                "signals; assisted review is recommended."
            ),
            recommended_action=RecommendedAction.ASSISTED_REVIEW,
        )

    if RuleId.AMB_SIM_SWAP_REQUIRED.value in matched:
        return AgentReviewResult(
            suggested_tier=MigrationTier.TIER_1,
            confidence_score=0.70,
            reason_codes=agent_reason_codes(rules_result, signals),
            risk_flags=signals.care_risk_flags + signals.technical_risk_flags,
            review_summary=(
                "Subscriber appears otherwise eligible but requires a SIM swap before "
                "migration can proceed safely."
            ),
            recommended_action=RecommendedAction.ASSISTED_REVIEW,
        )

    if signals.care_risk_score > 0:
        return AgentReviewResult(
            suggested_tier=MigrationTier.TIER_1,
            confidence_score=0.65,
            reason_codes=agent_reason_codes(rules_result, signals),
            risk_flags=signals.care_risk_flags + signals.technical_risk_flags,
            review_summary=(
                "Care signals introduce friction without a hard block; assisted review "
                "is appropriate."
            ),
            recommended_action=RecommendedAction.ASSISTED_REVIEW,
        )

    return None


def _tier0_review(signals: AgentSignals, rules_result: RulesResult) -> AgentReviewResult:
    """Recommend Tier 0 when ambiguity is minor and no care or technical gaps remain."""
    return AgentReviewResult(
        suggested_tier=MigrationTier.TIER_0,
        confidence_score=0.72,
        reason_codes=agent_reason_codes(rules_result, signals),
        risk_flags=signals.care_risk_flags + signals.technical_risk_flags,
        review_summary=(
            "No material care friction or technical gaps detected after review; "
            "subscriber can proceed with straight-through migration."
        ),
        recommended_action=RecommendedAction.AUTO_MIGRATE,
    )


def review_ambiguous_case(
    context: CanonicalMigrationContext,
    rules_result: RulesResult,
) -> AgentReviewResult:
    """Apply bounded heuristics to an ambiguous rules outcome."""
    if rules_result.outcome != RulesOutcome.AMBIGUOUS:
        raise AmbiguousReviewRequiredError(
            "Eligibility review agent only handles RulesOutcome.AMBIGUOUS cases."
        )

    signals = assess_signals(context, rules_result)

    tier2 = _tier2_review(signals, rules_result)
    if tier2 is not None:
        return tier2

    tier1 = _tier1_review(context, signals, rules_result)
    if tier1 is not None:
        return tier1

    if signals.care_risk_score == 0 and signals.technical_gap_score == 0:
        return _tier0_review(signals, rules_result)

    return AgentReviewResult(
        suggested_tier=MigrationTier.TIER_1,
        confidence_score=0.58,
        reason_codes=agent_reason_codes(rules_result, signals),
        risk_flags=signals.care_risk_flags + signals.technical_risk_flags,
        review_summary=(
            "Unresolved mixed signals remain after review; defaulting to assisted handling."
        ),
        recommended_action=RecommendedAction.ASSISTED_REVIEW,
    )
