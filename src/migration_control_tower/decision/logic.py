"""Decision combination helpers."""

from __future__ import annotations

from migration_control_tower.domain.enums import (
    MigrationTier,
    ReasonCodeSource,
    RecommendedAction,
    RulesOutcome,
)
from migration_control_tower.domain.models import (
    AgentReviewResult,
    CanonicalMigrationContext,
    MigrationDecision,
    RulesResult,
    SourcedReasonCode,
)
from migration_control_tower.domain.reason_codes import ReasonCode


class UnresolvedDecisionError(ValueError):
    """Raised when an ambiguous rules outcome has no agent review."""


_RETRY_LATER_CODES = {
    ReasonCode.PRIOR_MIGRATION_FAILED,
    ReasonCode.PRIOR_MIGRATION_IN_PROGRESS,
}


def _dedupe_sourced_reason_codes(codes: list[SourcedReasonCode]) -> list[SourcedReasonCode]:
    seen: set[tuple[str, str]] = set()
    deduped: list[SourcedReasonCode] = []
    for entry in codes:
        key = (entry.source.value, entry.code.value)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def _sourced_from_rules(reason_codes: list[ReasonCode]) -> list[SourcedReasonCode]:
    return [
        SourcedReasonCode(source=ReasonCodeSource.RULES, code=code) for code in reason_codes
    ]


def _sourced_from_agent(reason_codes: list[ReasonCode]) -> list[SourcedReasonCode]:
    return [
        SourcedReasonCode(source=ReasonCodeSource.AGENT, code=code) for code in reason_codes
    ]


def _recommended_action_for_definitive(
    tier: MigrationTier,
    reason_codes: list[ReasonCode],
) -> RecommendedAction:
    if tier == MigrationTier.TIER_0:
        return RecommendedAction.AUTO_MIGRATE
    if any(code in _RETRY_LATER_CODES for code in reason_codes):
        return RecommendedAction.RETRY_LATER
    return RecommendedAction.BLOCK


def _review_summary_for_definitive(rules_result: RulesResult) -> str:
    if rules_result.outcome == RulesOutcome.TIER_0:
        return "Straight-through eligibility confirmed by deterministic rules."
    if ReasonCode.PRIOR_MIGRATION_IN_PROGRESS in rules_result.reason_codes:
        return "Migration is already in progress; duplicate execution must be prevented."
    if ReasonCode.PRIOR_MIGRATION_FAILED in rules_result.reason_codes:
        return "Previous migration attempt failed; remediation required before retry."
    if ReasonCode.BILLING_NOT_OK in rules_result.reason_codes:
        return "Billing issue blocks migration until account standing is resolved."
    return "Hard eligibility block identified by deterministic rules."


def _unresolved_decision(
    context: CanonicalMigrationContext,
    rules_result: RulesResult,
) -> MigrationDecision:
    """Return a clearly marked unresolved decision when agent review is missing."""
    return MigrationDecision(
        subscriber_id=context.subscriber_id,
        tier=MigrationTier.TIER_1,
        reason_codes=_sourced_from_rules(rules_result.reason_codes),
        confidence=0.0,
        recommended_action=RecommendedAction.ASSISTED_REVIEW,
        review_summary=(
            "Ambiguous rules outcome requires eligibility agent review before "
            "a final migration decision can be issued."
        ),
        rules_outcome=RulesOutcome.AMBIGUOUS,
        agent_reviewed=False,
        risk_flags=[],
        unresolved=True,
    )


def combine_decision(
    context: CanonicalMigrationContext,
    rules_result: RulesResult,
    agent_result: AgentReviewResult | None = None,
    *,
    allow_unresolved: bool = False,
) -> MigrationDecision:
    """Combine rules and optional agent outputs into a final migration decision."""
    if rules_result.outcome in {RulesOutcome.TIER_0, RulesOutcome.TIER_2}:
        assert rules_result.tier is not None
        return MigrationDecision(
            subscriber_id=context.subscriber_id,
            tier=rules_result.tier,
            reason_codes=_sourced_from_rules(rules_result.reason_codes),
            confidence=1.0,
            recommended_action=_recommended_action_for_definitive(
                rules_result.tier,
                rules_result.reason_codes,
            ),
            review_summary=_review_summary_for_definitive(rules_result),
            rules_outcome=rules_result.outcome,
            agent_reviewed=False,
            risk_flags=[],
            unresolved=False,
        )

    if rules_result.outcome == RulesOutcome.AMBIGUOUS:
        if agent_result is None:
            if allow_unresolved:
                return _unresolved_decision(context, rules_result)
            raise UnresolvedDecisionError(
                "Ambiguous rules outcome requires agent review before combining a decision."
            )

        return MigrationDecision(
            subscriber_id=context.subscriber_id,
            tier=agent_result.suggested_tier,
            reason_codes=_dedupe_sourced_reason_codes(
                _sourced_from_rules(rules_result.reason_codes)
                + _sourced_from_agent(agent_result.reason_codes)
            ),
            confidence=agent_result.confidence_score,
            recommended_action=agent_result.recommended_action,
            review_summary=agent_result.review_summary,
            rules_outcome=RulesOutcome.AMBIGUOUS,
            agent_reviewed=True,
            risk_flags=list(agent_result.risk_flags),
            unresolved=False,
        )

    raise ValueError(f"Unsupported rules outcome: {rules_result.outcome}")
