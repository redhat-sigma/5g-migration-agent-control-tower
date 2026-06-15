"""Heuristic signals and scoring for the eligibility review agent.

The agent reasons about care vs technical readiness using rules output and
context fields. It does not re-run rules engine logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from migration_control_tower.domain.models import CanonicalMigrationContext, RulesResult
from migration_control_tower.domain.reason_codes import ReasonCode
from migration_control_tower.rules.definitions import RuleId

_RECENT_CASE_HIGH_RISK_THRESHOLD = 3


@dataclass(frozen=True)
class AgentSignals:
    """Care and technical signal summary for heuristic review."""

    care_risk_score: int
    technical_gap_score: int
    technical_readiness_green: bool
    care_risk_flags: list[str]
    technical_risk_flags: list[str]


def _technical_readiness_green(context: CanonicalMigrationContext) -> bool:
    return (
        context.account_status == "active"
        and context.billing_ok
        and context.sim_status == "active"
        and context.network_ready
        and context.provisioning_state == "complete"
        and context.is_5g_capable
        and context.prior_migration_state == "none"
    )


def assess_signals(context: CanonicalMigrationContext, rules_result: RulesResult) -> AgentSignals:
    """Summarize care vs technical posture from context and matched ambiguous rules."""
    matched = set(rules_result.matched_rules)
    care_risk_score = 0
    technical_gap_score = 0
    care_risk_flags: list[str] = []
    technical_risk_flags: list[str] = []

    if RuleId.AMB_OPEN_COMPLAINT.value in matched or context.open_complaint:
        care_risk_score += 2
        care_risk_flags.append("open_care_complaint")

    if RuleId.AMB_ESCALATION_OPEN.value in matched or context.escalation_flag:
        care_risk_score += 3
        care_risk_flags.append("care_escalation_active")

    if (
        RuleId.AMB_RECENT_CASE_ACTIVITY.value in matched
        or context.recent_case_count >= _RECENT_CASE_HIGH_RISK_THRESHOLD
    ):
        care_risk_score += 2
        care_risk_flags.append("elevated_case_volume")

    if RuleId.AMB_NETWORK_NOT_READY.value in matched or not context.network_ready:
        technical_gap_score += 2
        technical_risk_flags.append("network_readiness_unconfirmed")

    if (
        RuleId.AMB_PROVISIONING_INCOMPLETE.value in matched
        or context.provisioning_state != "complete"
    ):
        technical_gap_score += 2
        technical_risk_flags.append("provisioning_pending_validation")

    if RuleId.AMB_SIM_SWAP_REQUIRED.value in matched or context.requires_sim_swap:
        technical_gap_score += 1
        technical_risk_flags.append("sim_swap_pending")

    technical_green = _technical_readiness_green(context)
    if care_risk_score > 0 and technical_green:
        care_risk_flags.append("care_technical_conflict")

    return AgentSignals(
        care_risk_score=care_risk_score,
        technical_gap_score=technical_gap_score,
        technical_readiness_green=technical_green,
        care_risk_flags=_dedupe(care_risk_flags),
        technical_risk_flags=_dedupe(technical_risk_flags),
    )


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def agent_reason_codes(rules_result: RulesResult, signals: AgentSignals) -> list[ReasonCode]:
    """Carry forward relevant rules reason codes for the agent review."""
    codes = list(rules_result.reason_codes)

    if "care_technical_conflict" in signals.care_risk_flags:
        codes.append(ReasonCode.CONFLICTING_CARE_AND_PROVISIONING)

    if signals.technical_gap_score > 0 and signals.care_risk_score == 0:
        if ReasonCode.MIXED_READINESS_SIGNALS not in codes:
            codes.append(ReasonCode.MIXED_READINESS_SIGNALS)

    if signals.technical_gap_score > 0 and ReasonCode.PARTIAL_MIGRATION_READINESS not in codes:
        if any(
            flag in signals.technical_risk_flags
            for flag in ("sim_swap_pending", "provisioning_pending_validation")
        ):
            codes.append(ReasonCode.PARTIAL_MIGRATION_READINESS)

    return list(dict.fromkeys(codes))
