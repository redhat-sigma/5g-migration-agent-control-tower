"""Streamlit demo UI for the 5G Migration Agent Control Tower."""

from __future__ import annotations

import streamlit as st

from ui_helpers import (
    RULES_OUTCOME_LABELS,
    agent_added_chips,
    chip_row_html,
    compact_step_card_html,
    context_groups,
    final_decision_outcome_line,
    focal_card_close,
    focal_card_open,
    group_card_html,
    inject_page_styles,
    kpi_card_html,
    micc_operational_line,
    micc_status_color,
    path_arrow_html,
    pipeline_flow_steps,
    pipeline_stage_summary,
    rules_matched_chips,
    rules_takeaway,
    status_badge_html,
    subscriber_option_label,
    tier_badge_html,
    top_summary_strip,
    MICC_STATUS_LABELS,
)
from migration_control_tower.data import get_expected, get_record, list_subscriber_ids
from migration_control_tower.pipeline import EligibilityPipeline

st.set_page_config(
    page_title="5G Migration Control Tower",
    page_icon="📡",
    layout="wide",
)

st.markdown(inject_page_styles(), unsafe_allow_html=True)

st.title("5G Migration Control Tower")
st.caption("Subscriber migration eligibility — rules, agent review, and execution in one view.")

subscriber_ids = list_subscriber_ids()
labels = {
    subscriber_id: subscriber_option_label(
        subscriber_id,
        get_expected(subscriber_id).scenario,
        get_expected(subscriber_id).rules_outcome.value,
    )
    for subscriber_id in subscriber_ids
}

selected_label = st.selectbox("Select subscriber", options=[labels[sid] for sid in subscriber_ids])
selected_id = next(sid for sid, label in labels.items() if label == selected_label)

result = EligibilityPipeline().run(selected_id)
expected = get_record(selected_id).expected
decision = result.decision
execution = result.execution

summary = top_summary_strip(result)
kpi_cols = st.columns(4)
for column, (label, value) in zip(
    kpi_cols,
    [
        ("Final tier", summary["final_tier"]),
        ("Recommended action", summary["recommended_action"]),
        ("MiCC status", summary["micc_status"]),
        ("Agent reviewed", summary["agent_reviewed"]),
    ],
):
    column.markdown(kpi_card_html(label, value), unsafe_allow_html=True)

path = pipeline_flow_steps(result)
path_cols = st.columns([2, 0.4, 2, 0.4, 2])
path_cols[0].markdown(compact_step_card_html(*path[0]), unsafe_allow_html=True)
path_cols[1].markdown(path_arrow_html(), unsafe_allow_html=True)
path_cols[2].markdown(compact_step_card_html(*path[1]), unsafe_allow_html=True)
path_cols[3].markdown(path_arrow_html(), unsafe_allow_html=True)
path_cols[4].markdown(compact_step_card_html(*path[2]), unsafe_allow_html=True)

st.divider()

st.markdown("#### Subscriber context")
context_cols = st.columns(3)
for column, (group_name, fields) in zip(context_cols, context_groups(result.context.model_dump()).items()):
    column.markdown(group_card_html(group_name, fields), unsafe_allow_html=True)

st.divider()

st.markdown("#### Rules assessment")
rules = result.rules_result
rules_color = "#175cd3" if rules.outcome.value == "ambiguous" else "#344054"
st.markdown(status_badge_html(RULES_OUTCOME_LABELS[rules.outcome], rules_color), unsafe_allow_html=True)
st.markdown(f'<div class="mct-takeaway">{rules_takeaway(result)}</div>', unsafe_allow_html=True)
st.markdown(chip_row_html(rules_matched_chips(result)), unsafe_allow_html=True)

st.divider()

st.markdown("#### Agent review")
if result.agent_required:
    agent = result.agent_result
    assert agent is not None
    added_reasons, risks = agent_added_chips(result)
    st.markdown(f'<div class="mct-takeaway">{agent.review_summary}</div>', unsafe_allow_html=True)
    if added_reasons:
        st.markdown('<div class="mct-field-label">Added reason codes</div>', unsafe_allow_html=True)
        st.markdown(chip_row_html(added_reasons, accent=True), unsafe_allow_html=True)
    if risks:
        st.markdown('<div class="mct-field-label">Risk flags</div>', unsafe_allow_html=True)
        st.markdown(chip_row_html(risks, warn=True), unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="mct-card"><div class="mct-step-status">Not required</div></div>',
        unsafe_allow_html=True,
    )

st.divider()

st.markdown("#### Final migration decision")
st.markdown(focal_card_open(), unsafe_allow_html=True)
st.markdown(tier_badge_html(decision.tier), unsafe_allow_html=True)
st.markdown(
    f'<div class="mct-outcome-line">{final_decision_outcome_line(result)}</div>',
    unsafe_allow_html=True,
)
st.markdown(f'<div class="mct-verdict">{decision.review_summary}</div>', unsafe_allow_html=True)
st.markdown(focal_card_close(), unsafe_allow_html=True)

st.divider()

st.markdown("#### Downstream execution")
micc_label = MICC_STATUS_LABELS.get(
    execution.status,
    execution.status.value.replace("_", " ").title(),
)
st.markdown(
    status_badge_html(micc_label, micc_status_color(execution.status)),
    unsafe_allow_html=True,
)
st.markdown(f'<div class="mct-outcome-line">{micc_operational_line(result)}</div>', unsafe_allow_html=True)

with st.expander("Technical execution details"):
    st.write("Queue ID", execution.queue_id or "—")
    st.write("Job ID", execution.job_id)
    st.write("Submitted at", execution.submitted_at)
    st.write(execution.message)

with st.expander("Scenario notes"):
    st.write(expected.notes)
    st.json(pipeline_stage_summary(result))
