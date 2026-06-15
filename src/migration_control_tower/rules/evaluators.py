"""Deterministic rule evaluation helpers.

Rules classify only obvious Tier 0 and Tier 2 cases. Any other signal returns
AMBIGUOUS so the eligibility agent can decide — rules never guess on gray zones.
"""

from __future__ import annotations

from migration_control_tower.domain.enums import RulesOutcome
from migration_control_tower.domain.models import CanonicalMigrationContext, RulesResult
from migration_control_tower.domain.reason_codes import ReasonCode
from migration_control_tower.rules.definitions import RuleId

_RECENT_CASE_AMBIGUITY_THRESHOLD = 3


def _dedupe_reason_codes(codes: list[ReasonCode]) -> list[ReasonCode]:
    return list(dict.fromkeys(codes))


def _build_result(
    outcome: RulesOutcome,
    matched_rules: list[RuleId],
    reason_codes: list[ReasonCode],
) -> RulesResult:
    return RulesResult(
        outcome=outcome,
        reason_codes=_dedupe_reason_codes(reason_codes),
        matched_rules=[rule.value for rule in matched_rules],
    )


def _evaluate_tier2(context: CanonicalMigrationContext) -> RulesResult | None:
    """Return a Tier 2 result when a hard block is present, else None."""
    matched_rules: list[RuleId] = []
    reason_codes: list[ReasonCode] = []

    if context.account_status == "suspended":
        matched_rules.append(RuleId.T2_ACCOUNT_SUSPENDED)
        reason_codes.append(ReasonCode.ACCOUNT_SUSPENDED)

    if context.account_status == "inactive":
        matched_rules.append(RuleId.T2_ACCOUNT_INACTIVE)
        reason_codes.append(ReasonCode.ACCOUNT_INACTIVE)

    if not context.billing_ok:
        matched_rules.append(RuleId.T2_BILLING_NOT_OK)
        reason_codes.append(ReasonCode.BILLING_NOT_OK)

    if context.prior_migration_state == "in_progress":
        matched_rules.append(RuleId.T2_PRIOR_MIGRATION_IN_PROGRESS)
        reason_codes.append(ReasonCode.PRIOR_MIGRATION_IN_PROGRESS)

    if context.prior_migration_state == "failed":
        matched_rules.append(RuleId.T2_PRIOR_MIGRATION_FAILED)
        reason_codes.append(ReasonCode.PRIOR_MIGRATION_FAILED)

    if context.sim_status != "active":
        matched_rules.append(RuleId.T2_SIM_NOT_ACTIVE)
        reason_codes.append(ReasonCode.SIM_NOT_ACTIVE)

    if not context.is_5g_capable:
        matched_rules.append(RuleId.T2_DEVICE_NOT_5G_CAPABLE)
        reason_codes.append(ReasonCode.DEVICE_NOT_5G_CAPABLE)

    if not matched_rules:
        return None

    return _build_result(RulesOutcome.TIER_2, matched_rules, reason_codes)


def _technical_readiness_green(context: CanonicalMigrationContext) -> bool:
    """Account, billing, SIM, and network signals that care rules weigh against."""
    return (
        context.account_status == "active"
        and context.billing_ok
        and context.sim_status == "active"
        and context.network_ready
        and context.provisioning_state == "complete"
    )


def _evaluate_ambiguous(context: CanonicalMigrationContext) -> RulesResult | None:
    """Return AMBIGUOUS when soft or conflicting signals are present, else None."""
    matched_rules: list[RuleId] = []
    reason_codes: list[ReasonCode] = []

    if context.open_complaint:
        matched_rules.append(RuleId.AMB_OPEN_COMPLAINT)
        reason_codes.append(ReasonCode.OPEN_COMPLAINT)

    if context.escalation_flag:
        matched_rules.append(RuleId.AMB_ESCALATION_OPEN)
        reason_codes.append(ReasonCode.ESCALATION_OPEN)

    if context.recent_case_count >= _RECENT_CASE_AMBIGUITY_THRESHOLD:
        matched_rules.append(RuleId.AMB_RECENT_CASE_ACTIVITY)
        reason_codes.append(ReasonCode.RECENT_CASE_ACTIVITY)

    if not context.network_ready:
        matched_rules.append(RuleId.AMB_NETWORK_NOT_READY)
        reason_codes.append(ReasonCode.NETWORK_NOT_READY)
        reason_codes.append(ReasonCode.MIXED_READINESS_SIGNALS)

    if context.provisioning_state != "complete":
        matched_rules.append(RuleId.AMB_PROVISIONING_INCOMPLETE)
        reason_codes.append(ReasonCode.PROVISIONING_INCOMPLETE)
        reason_codes.append(ReasonCode.MIXED_READINESS_SIGNALS)

    if context.requires_sim_swap:
        matched_rules.append(RuleId.AMB_SIM_SWAP_REQUIRED)
        reason_codes.append(ReasonCode.SIM_SWAP_REQUIRED)
        reason_codes.append(ReasonCode.PARTIAL_MIGRATION_READINESS)

    care_conflict = context.open_complaint or context.escalation_flag or (
        context.recent_case_count >= _RECENT_CASE_AMBIGUITY_THRESHOLD
        and _technical_readiness_green(context)
    )
    if care_conflict:
        reason_codes.append(ReasonCode.CONFLICTING_CARE_AND_PROVISIONING)

    if not matched_rules:
        return None

    return _build_result(RulesOutcome.AMBIGUOUS, matched_rules, reason_codes)


def _evaluate_tier0(context: CanonicalMigrationContext) -> RulesResult | None:
    """Return Tier 0 when every straight-through criterion is met, else None."""
    straight_through = (
        context.account_status == "active"
        and context.billing_ok
        and context.sim_status == "active"
        and context.provisioning_state == "complete"
        and context.network_ready
        and context.prior_migration_state == "none"
        and context.is_5g_capable
        and not context.requires_sim_swap
        and not context.open_complaint
        and not context.escalation_flag
        and context.recent_case_count < _RECENT_CASE_AMBIGUITY_THRESHOLD
    )

    if not straight_through:
        return None

    return _build_result(
        RulesOutcome.TIER_0,
        [RuleId.T0_STRAIGHT_THROUGH_ELIGIBLE],
        [ReasonCode.ELIGIBILITY_CONFIRMED, ReasonCode.AUTO_MIGRATE_READY],
    )


def evaluate_rules(context: CanonicalMigrationContext) -> RulesResult:
    """Run deterministic rules: Tier 2 blocks, then ambiguous, then Tier 0."""
    tier2 = _evaluate_tier2(context)
    if tier2 is not None:
        return tier2

    ambiguous = _evaluate_ambiguous(context)
    if ambiguous is not None:
        return ambiguous

    tier0 = _evaluate_tier0(context)
    if tier0 is not None:
        return tier0

    return _build_result(
        RulesOutcome.AMBIGUOUS,
        [RuleId.AMB_UNRESOLVED],
        [],
    )
