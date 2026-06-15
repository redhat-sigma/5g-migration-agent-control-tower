"""Pure formatting helpers for the Streamlit demo (no Streamlit dependency)."""

from __future__ import annotations

from migration_control_tower.domain.enums import (
    MigrationTier,
    MiCCExecutionStatus,
    ReasonCodeSource,
    RecommendedAction,
    RulesOutcome,
)
from migration_control_tower.pipeline.result import PipelineRunResult

TIER_LABELS = {
    MigrationTier.TIER_0: "Straight-through",
    MigrationTier.TIER_1: "Assisted handling",
    MigrationTier.TIER_2: "Blocked",
}

TIER_SHORT = {
    MigrationTier.TIER_0: "Tier 0",
    MigrationTier.TIER_1: "Tier 1",
    MigrationTier.TIER_2: "Tier 2",
}

TIER_BADGE_COLORS = {
    MigrationTier.TIER_0: "#1b7f4e",
    MigrationTier.TIER_1: "#b86e00",
    MigrationTier.TIER_2: "#b42318",
}

RULES_OUTCOME_LABELS = {
    RulesOutcome.TIER_0: "Definitive eligibility",
    RulesOutcome.TIER_2: "Hard block identified",
    RulesOutcome.AMBIGUOUS: "Needs agent review",
}

ACTION_LABELS = {
    RecommendedAction.AUTO_MIGRATE: "Auto migrate",
    RecommendedAction.ASSISTED_REVIEW: "Assisted review",
    RecommendedAction.BLOCK: "Block migration",
    RecommendedAction.RETRY_LATER: "Retry later",
}

MICC_STATUS_LABELS = {
    MiCCExecutionStatus.EXECUTED_SUCCESS: "Executed successfully",
    MiCCExecutionStatus.QUEUED: "Queued",
    MiCCExecutionStatus.DEFERRED: "Deferred",
    MiCCExecutionStatus.BLOCKED: "Blocked",
    MiCCExecutionStatus.FAILED: "Failed",
    MiCCExecutionStatus.IN_PROGRESS: "In progress",
    MiCCExecutionStatus.COMPLETED: "Completed",
}

MICC_STATUS_COLORS = {
    MiCCExecutionStatus.EXECUTED_SUCCESS: "#1b7f4e",
    MiCCExecutionStatus.QUEUED: "#175cd3",
    MiCCExecutionStatus.DEFERRED: "#b86e00",
    MiCCExecutionStatus.BLOCKED: "#b42318",
    MiCCExecutionStatus.FAILED: "#b42318",
}

CONTEXT_GROUPS = {
    "Account": [
        ("Subscriber", "subscriber_id"),
        ("Brand", "brand.brand_id"),
        ("Contract", "contract_type"),
        ("Account status", "account_status"),
        ("Billing", "billing_ok"),
    ],
    "Technical / device": [
        ("SIM", "sim_status"),
        ("Provisioning", "provisioning_state"),
        ("Network", "network_ready"),
        ("Prior migration", "prior_migration_state"),
        ("Device", "device_model"),
        ("5G capable", "is_5g_capable"),
        ("SIM swap", "requires_sim_swap"),
    ],
    "Care / history": [
        ("Open complaint", "open_complaint"),
        ("Recent cases", "recent_case_count"),
        ("Escalation", "escalation_flag"),
    ],
}

RULE_LABELS = {
    "t0_straight_through_eligible": "Straight-through eligible",
    "t2_account_suspended": "Account suspended",
    "t2_account_inactive": "Account inactive",
    "t2_billing_not_ok": "Billing issue",
    "t2_prior_migration_in_progress": "Migration in progress",
    "t2_prior_migration_failed": "Prior migration failed",
    "t2_sim_not_active": "SIM not active",
    "t2_device_not_5g_capable": "Device not 5G capable",
    "amb_open_complaint": "Open complaint",
    "amb_escalation_open": "Escalation open",
    "amb_recent_case_activity": "Recent case activity",
    "amb_network_not_ready": "Network not ready",
    "amb_provisioning_incomplete": "Provisioning incomplete",
    "amb_sim_swap_required": "SIM swap required",
    "amb_unresolved": "Unresolved signals",
}

REASON_LABELS = {
    "ELIGIBILITY_CONFIRMED": "Eligibility confirmed",
    "AUTO_MIGRATE_READY": "Ready for auto migration",
    "BILLING_NOT_OK": "Billing issue",
    "ACCOUNT_SUSPENDED": "Account suspended",
    "SIM_NOT_ACTIVE": "SIM not active",
    "DEVICE_NOT_5G_CAPABLE": "Device not 5G capable",
    "PRIOR_MIGRATION_FAILED": "Prior migration failed",
    "PRIOR_MIGRATION_IN_PROGRESS": "Migration in progress",
    "OPEN_COMPLAINT": "Open complaint",
    "NETWORK_NOT_READY": "Network not ready",
    "PROVISIONING_INCOMPLETE": "Provisioning incomplete",
    "SIM_SWAP_REQUIRED": "SIM swap required",
    "ESCALATION_OPEN": "Escalation open",
    "RECENT_CASE_ACTIVITY": "Recent case activity",
    "MIXED_READINESS_SIGNALS": "Mixed readiness signals",
    "CONFLICTING_CARE_AND_PROVISIONING": "Care vs provisioning conflict",
    "PARTIAL_MIGRATION_READINESS": "Partial readiness",
}

RISK_LABELS = {
    "open_care_complaint": "Open care complaint",
    "care_escalation_active": "Care escalation active",
    "elevated_case_volume": "Elevated case volume",
    "network_readiness_unconfirmed": "Network readiness unconfirmed",
    "provisioning_pending_validation": "Provisioning pending validation",
    "sim_swap_pending": "SIM swap pending",
    "care_technical_conflict": "Care vs technical conflict",
}


PAGE_STYLES = """
<style>
.mct-card {
  border: 1px solid #e4e7ec;
  border-radius: 10px;
  padding: 14px 16px;
  background: #ffffff;
  margin-bottom: 10px;
}
.mct-kpi {
  border: 1px solid #e4e7ec;
  border-radius: 10px;
  padding: 12px 14px;
  background: #f9fafb;
}
.mct-kpi-label {
  color: #667085;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 4px;
}
.mct-kpi-value {
  color: #101828;
  font-size: 1.05rem;
  font-weight: 700;
}
.mct-step {
  border: 1px solid #e4e7ec;
  border-left: 4px solid #98a2b3;
  border-radius: 10px;
  padding: 10px 12px;
  background: #fcfcfd;
  min-height: 58px;
  text-align: center;
}
.mct-step-active {
  border-left-color: #175cd3;
  background: #f5f8ff;
}
.mct-step-arrow {
  color: #98a2b3;
  font-size: 1.2rem;
  font-weight: 700;
  text-align: center;
  padding-top: 18px;
}
.mct-step-title {
  font-weight: 700;
  color: #101828;
  margin-bottom: 4px;
  font-size: 0.88rem;
}
.mct-step-status {
  color: #475467;
  font-size: 0.84rem;
  font-weight: 600;
}
.mct-focal {
  border: 1px solid #d0d5dd;
  border-radius: 12px;
  padding: 16px 18px;
  background: #f9fafb;
}
.mct-verdict {
  color: #101828;
  font-size: 1.02rem;
  font-weight: 600;
  line-height: 1.45;
  margin-top: 10px;
}
.mct-outcome-line {
  color: #475467;
  font-size: 0.92rem;
  font-weight: 600;
  margin: 8px 0 0 0;
}
.mct-group-title {
  color: #344054;
  font-size: 0.92rem;
  font-weight: 700;
  margin-bottom: 8px;
}
.mct-field-label {
  color: #667085;
  font-size: 0.76rem;
  font-weight: 600;
}
.mct-field-value {
  color: #101828;
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 8px;
}
.mct-chip-row { margin-top: 6px; margin-bottom: 4px; }
.mct-chip {
  display: inline-block;
  background: #eef2f6;
  color: #344054;
  border: 1px solid #e4e7ec;
  border-radius: 999px;
  padding: 3px 10px;
  margin: 0 6px 6px 0;
  font-size: 0.8rem;
  font-weight: 600;
}
.mct-chip-accent {
  background: #eff8ff;
  color: #175cd3;
  border-color: #b2ddff;
}
.mct-chip-warn {
  background: #fff6ed;
  color: #b54708;
  border-color: #f9dbaf;
}
.mct-muted {
  color: #667085;
  font-size: 0.9rem;
}
.mct-takeaway {
  color: #101828;
  font-size: 1rem;
  font-weight: 600;
  margin: 8px 0 6px 0;
}
</style>
"""


def inject_page_styles() -> str:
    return PAGE_STYLES


def micc_status_color(status: MiCCExecutionStatus) -> str:
    return MICC_STATUS_COLORS.get(status, "#475467")


def humanize_token(value: str, mapping: dict[str, str]) -> str:
    return mapping.get(value, value.replace("_", " ").strip().title())


def humanize_bool(value: object) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def humanize_context_field(field_path: str, raw_value: object) -> str:
    if isinstance(raw_value, bool):
        if field_path == "billing_ok":
            return "In good standing" if raw_value else "Issue outstanding"
        if field_path == "network_ready":
            return "Ready" if raw_value else "Not confirmed"
        if field_path == "is_5g_capable":
            return "Supported" if raw_value else "Not supported"
        if field_path == "requires_sim_swap":
            return "Required" if raw_value else "Not required"
        if field_path == "open_complaint":
            return "Open" if raw_value else "None"
        if field_path == "escalation_flag":
            return "Active" if raw_value else "None"
        return humanize_bool(raw_value)
    if field_path == "account_status":
        return str(raw_value).replace("_", " ").title()
    if field_path == "prior_migration_state":
        mapping = {
            "none": "None",
            "in_progress": "In progress",
            "failed": "Failed",
        }
        return mapping.get(str(raw_value), str(raw_value).replace("_", " ").title())
    if field_path == "provisioning_state":
        return str(raw_value).replace("_", " ").title()
    return str(raw_value)


def tier_badge_html(tier: MigrationTier) -> str:
    color = TIER_BADGE_COLORS[tier]
    label = f"{TIER_SHORT[tier]} — {TIER_LABELS[tier]}"
    return (
        f'<span style="background:{color};color:white;padding:4px 10px;'
        f'border-radius:999px;font-weight:600;">{label}</span>'
    )


def status_badge_html(label: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:white;padding:4px 10px;'
        f'border-radius:999px;font-weight:600;">{label}</span>'
    )


def chip_row_html(items: list[str], accent: bool = False, warn: bool = False) -> str:
    if not items or items == ["—"]:
        return '<div class="mct-muted">None</div>'
    css = "mct-chip-accent" if accent else "mct-chip-warn" if warn else "mct-chip"
    chips = "".join(f'<span class="mct-chip {css}">{item}</span>' for item in items)
    return f'<div class="mct-chip-row">{chips}</div>'


def kpi_card_html(label: str, value: str) -> str:
    return (
        f'<div class="mct-kpi"><div class="mct-kpi-label">{label}</div>'
        f'<div class="mct-kpi-value">{value}</div></div>'
    )


def compact_step_card_html(title: str, status: str, active: bool = False) -> str:
    css = "mct-step mct-step-active" if active else "mct-step"
    return (
        f'<div class="{css}"><div class="mct-step-title">{title}</div>'
        f'<div class="mct-step-status">{status}</div></div>'
    )


def path_arrow_html() -> str:
    return '<div class="mct-step-arrow">→</div>'


def group_card_html(title: str, fields: list[tuple[str, str]]) -> str:
    rows = "".join(
        f'<div class="mct-field-label">{label}</div><div class="mct-field-value">{value}</div>'
        for label, value in fields
    )
    return f'<div class="mct-card"><div class="mct-group-title">{title}</div>{rows}</div>'


def focal_card_open() -> str:
    return '<div class="mct-focal">'


def focal_card_close() -> str:
    return "</div>"


def subscriber_option_label(subscriber_id: str, scenario: str, rules_outcome: str) -> str:
    scenario_label = scenario.replace("_", " ")
    outcome_label = rules_outcome.replace("_", " ")
    return f"{subscriber_id} · {scenario_label} ({outcome_label})"


def _context_raw_value(context_data: dict, field_path: str) -> object:
    if "." in field_path:
        parent, child = field_path.split(".", 1)
        return context_data[parent][child]
    return context_data[field_path]


def context_groups(context_data: dict) -> dict[str, list[tuple[str, str]]]:
    return {
        group: [
            (label, humanize_context_field(path, _context_raw_value(context_data, path)))
            for label, path in fields
        ]
        for group, fields in CONTEXT_GROUPS.items()
    }


def top_summary_strip(result: PipelineRunResult) -> dict[str, str]:
    return {
        "final_tier": f"{TIER_SHORT[result.decision.tier]} — {TIER_LABELS[result.decision.tier]}",
        "recommended_action": ACTION_LABELS[result.decision.recommended_action],
        "micc_status": MICC_STATUS_LABELS.get(
            result.execution.status,
            result.execution.status.value.replace("_", " ").title(),
        ),
        "agent_reviewed": "Yes" if result.decision.agent_reviewed else "No",
    }


def pipeline_flow_steps(result: PipelineRunResult) -> list[tuple[str, str, bool]]:
    """Compact visual path: step title, short status, active flag."""
    if result.agent_required:
        agent = result.agent_result
        assert agent is not None
        return [
            ("Rules", "Deferred", True),
            ("Agent", TIER_SHORT[agent.suggested_tier], True),
            ("Decision", TIER_SHORT[result.decision.tier], True),
        ]
    rules_tier = result.rules_result.tier
    rules_status = TIER_SHORT[rules_tier] if rules_tier is not None else "Definitive"
    return [
        ("Rules", rules_status, True),
        ("Agent", "Skipped", False),
        ("Decision", TIER_SHORT[result.decision.tier], True),
    ]


def rules_takeaway(result: PipelineRunResult) -> str:
    rules = result.rules_result
    if rules.outcome == RulesOutcome.TIER_0:
        return "All deterministic checks passed — straight-through eligible."
    if rules.outcome == RulesOutcome.TIER_2:
        matched, _ = rules_detail_chips(result)
        driver = matched[0] if matched else "hard block"
        return f"Blocked by rules: {driver.lower()}."
    matched, _ = rules_detail_chips(result)
    driver = matched[0] if matched else "conflicting signals"
    return f"Deferred — {driver.lower()} requires agent review."


def rules_matched_chips(result: PipelineRunResult) -> list[str]:
    matched, _ = rules_detail_chips(result)
    return matched


def agent_added_chips(result: PipelineRunResult) -> tuple[list[str], list[str]]:
    """Return agent-only signals: risk flags and reason codes not already rules-matched labels."""
    if result.agent_result is None:
        return [], []
    rules_matched = set(rules_matched_chips(result))
    agent = result.agent_result
    added_reasons = [
        label
        for label in (humanize_token(code.value, REASON_LABELS) for code in agent.reason_codes)
        if label not in rules_matched
    ]
    risks = [humanize_token(flag, RISK_LABELS) for flag in agent.risk_flags]
    return added_reasons, risks


def final_decision_outcome_line(result: PipelineRunResult) -> str:
    decision = result.decision
    return (
        f"{ACTION_LABELS[decision.recommended_action]} · "
        f"{decision.confidence:.0%} confidence"
    )


def micc_operational_line(result: PipelineRunResult) -> str:
    execution = result.execution
    queue = execution.queue_name.replace("-", " ")
    status = MICC_STATUS_LABELS.get(
        execution.status,
        execution.status.value.replace("_", " ").title(),
    )
    return f"{status} · {queue}"


def rules_detail_chips(result: PipelineRunResult) -> tuple[list[str], list[str]]:
    rules = result.rules_result
    matched = [
        humanize_token(rule, RULE_LABELS) for rule in (rules.matched_rules or [])
    ]
    reasons = [
        humanize_token(code.value, REASON_LABELS) for code in rules.reason_codes
    ]
    return matched, reasons


def agent_takeaway(result: PipelineRunResult) -> str:
    if not result.agent_required or result.agent_result is None:
        return "Not required — rules produced a definitive outcome."
    agent = result.agent_result
    return f"Recommends {TIER_SHORT[agent.suggested_tier].lower()} with {agent.confidence_score:.0%} confidence."


def agent_detail_chips(result: PipelineRunResult) -> tuple[list[str], list[str]]:
    if result.agent_result is None:
        return [], []
    agent = result.agent_result
    reasons = [humanize_token(code.value, REASON_LABELS) for code in agent.reason_codes]
    risks = [humanize_token(flag, RISK_LABELS) for flag in agent.risk_flags]
    return reasons, risks


def grouped_decision_rationale(result: PipelineRunResult) -> dict[str, dict[str, str | list[str]]]:
    decision = result.decision
    rules_codes = [
        humanize_token(code.value, REASON_LABELS)
        for code in decision.codes_for_source(ReasonCodeSource.RULES)
    ]
    agent_codes = [
        humanize_token(code.value, REASON_LABELS)
        for code in decision.codes_for_source(ReasonCodeSource.AGENT)
    ]

    rules_detail = {
        "summary": rules_takeaway(result),
        "reason_codes": rules_codes or ["—"],
    }
    if result.agent_result is not None:
        agent_detail = {
            "summary": agent_takeaway(result),
            "reason_codes": agent_codes or ["—"],
            "risk_flags": [
                humanize_token(flag, RISK_LABELS) for flag in result.agent_result.risk_flags
            ]
            or ["—"],
        }
    else:
        agent_detail = {
            "summary": "Not required for definitive rules outcome.",
            "reason_codes": ["—"],
            "risk_flags": ["—"],
        }

    return {"rules": rules_detail, "agent": agent_detail}


def pipeline_stage_summary(result: PipelineRunResult) -> dict[str, str]:
    strip = top_summary_strip(result)
    return {
        "subscriber_id": result.subscriber_id,
        "rules_outcome": result.rules_result.outcome.value,
        "agent_required": str(result.agent_required),
        "final_tier": result.decision.tier.value,
        "recommended_action": result.decision.recommended_action.value,
        "micc_status": result.execution.status.value,
        "queue_name": result.execution.queue_name,
        "agent_reviewed": strip["agent_reviewed"],
    }
