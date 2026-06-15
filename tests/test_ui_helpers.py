"""Smoke tests for UI helper formatting and pipeline data used by the Streamlit app."""

from pathlib import Path

import pytest

from app.ui_helpers import (
    agent_added_chips,
    context_groups,
    final_decision_outcome_line,
    grouped_decision_rationale,
    humanize_context_field,
    humanize_token,
    pipeline_flow_steps,
    pipeline_stage_summary,
    rules_detail_chips,
    subscriber_option_label,
    tier_badge_html,
    top_summary_strip,
    RULE_LABELS,
    REASON_LABELS,
)
from migration_control_tower.data import get_expected, list_subscriber_ids
from migration_control_tower.pipeline import EligibilityPipeline


def test_main_entrypoint_exists() -> None:
    main_path = Path(__file__).resolve().parents[1] / "app" / "main.py"
    assert main_path.exists()
    content = main_path.read_text(encoding="utf-8")
    assert "EligibilityPipeline" in content
    assert "st.selectbox" in content
    assert "compact_step_card_html" in content
    assert "Technical execution details" in content


@pytest.mark.parametrize("subscriber_id", list_subscriber_ids())
def test_pipeline_stage_summary_for_ui(subscriber_id: str) -> None:
    result = EligibilityPipeline().run(subscriber_id)
    expected = get_expected(subscriber_id)
    summary = pipeline_stage_summary(result)

    assert summary["subscriber_id"] == subscriber_id
    assert summary["final_tier"] == expected.final_tier.value
    assert summary["recommended_action"] == expected.recommended_action.value
    assert summary["micc_status"]
    assert summary["queue_name"]


def test_subscriber_option_label_includes_scenario() -> None:
    expected = get_expected("SUB-20001")
    label = subscriber_option_label("SUB-20001", expected.scenario, expected.rules_outcome.value)
    assert "SUB-20001" in label
    assert "open complaint" in label


def test_tier_badge_html_renders_all_tiers() -> None:
    from migration_control_tower.domain import MigrationTier

    for tier in MigrationTier:
        html = tier_badge_html(tier)
        assert "Tier" in html


def test_top_summary_strip_keys() -> None:
    result = EligibilityPipeline().run("SUB-20001")
    summary = top_summary_strip(result)
    assert set(summary) == {"final_tier", "recommended_action", "micc_status", "agent_reviewed"}
    assert summary["agent_reviewed"] == "Yes"


def test_ambiguous_flow_has_three_deferred_steps() -> None:
    result = EligibilityPipeline().run("SUB-20001")
    steps = pipeline_flow_steps(result)
    assert len(steps) == 3
    assert steps[0][1] == "Deferred"
    assert steps[1][0] == "Agent"


def test_agent_added_chips_focus_on_agent_contribution() -> None:
    result = EligibilityPipeline().run("SUB-20001")
    added_reasons, risks = agent_added_chips(result)
    assert risks


def test_final_decision_outcome_line() -> None:
    result = EligibilityPipeline().run("SUB-10001")
    line = final_decision_outcome_line(result)
    assert "confidence" in line.lower()
    assert "Auto migrate" in line


def test_humanize_context_values() -> None:
    assert humanize_context_field("billing_ok", True) == "In good standing"
    assert humanize_context_field("network_ready", False) == "Not confirmed"
    assert humanize_context_field("requires_sim_swap", False) == "Not required"


def test_rules_detail_chips_are_human_readable() -> None:
    result = EligibilityPipeline().run("SUB-10001")
    matched, reasons = rules_detail_chips(result)
    assert matched == ["Straight-through eligible"]
    assert "Ready for auto migration" in reasons


def test_humanize_rule_and_reason_tokens() -> None:
    assert humanize_token("t0_straight_through_eligible", RULE_LABELS) == "Straight-through eligible"
    assert humanize_token("BILLING_NOT_OK", REASON_LABELS) == "Billing issue"


def test_grouped_decision_rationale_splits_sources() -> None:
    result = EligibilityPipeline().run("SUB-20001")
    rationale = grouped_decision_rationale(result)
    assert rationale["rules"]["reason_codes"]
    assert rationale["agent"]["summary"]


def test_context_groups_use_human_labels() -> None:
    result = EligibilityPipeline().run("SUB-10001")
    groups = context_groups(result.context.model_dump())
    billing = next(value for label, value in groups["Account"] if label == "Billing")
    assert billing == "In good standing"
