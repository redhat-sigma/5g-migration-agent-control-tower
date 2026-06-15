"""Tests for the end-to-end pipeline."""

import pytest

from migration_control_tower.data import get_expected, list_subscriber_ids
from migration_control_tower.domain import MiCCExecutionStatus, RulesOutcome
from migration_control_tower.micc import AUTO_MIGRATE_QUEUE, BLOCKED_QUEUE, MANUAL_REVIEW_QUEUE, RETRY_QUEUE
from migration_control_tower.pipeline import EligibilityPipeline, PipelineRunResult


@pytest.fixture
def pipeline() -> EligibilityPipeline:
    return EligibilityPipeline()


@pytest.mark.parametrize("subscriber_id", list_subscriber_ids())
def test_pipeline_matches_expected_decision(pipeline: EligibilityPipeline, subscriber_id: str) -> None:
    expected = get_expected(subscriber_id)
    result = pipeline.run(subscriber_id)

    assert isinstance(result, PipelineRunResult)
    assert result.decision.subscriber_id == subscriber_id
    assert result.decision.tier == expected.final_tier
    assert result.decision.recommended_action == expected.recommended_action
    assert result.decision.agent_reviewed == expected.agent_reviewed
    assert result.decision.rules_outcome == expected.rules_outcome
    assert result.decision.unresolved is False
    assert result.execution.subscriber_id == subscriber_id
    assert result.execution.decision_tier == result.decision.tier
    assert result.agent_required == (expected.rules_outcome == RulesOutcome.AMBIGUOUS)
    if expected.agent_reviewed:
        assert result.agent_result is not None
    else:
        assert result.agent_result is None


def test_pipeline_tier_0_end_to_end(pipeline: EligibilityPipeline) -> None:
    result = pipeline.run("SUB-10001")

    assert result.decision.rules_outcome == RulesOutcome.TIER_0
    assert result.execution.status == MiCCExecutionStatus.EXECUTED_SUCCESS
    assert result.execution.queue_name == AUTO_MIGRATE_QUEUE


def test_pipeline_tier_1_end_to_end(pipeline: EligibilityPipeline) -> None:
    result = pipeline.run("SUB-20002")

    assert result.decision.rules_outcome == RulesOutcome.AMBIGUOUS
    assert result.decision.agent_reviewed is True
    assert result.execution.status == MiCCExecutionStatus.QUEUED
    assert result.execution.queue_name == MANUAL_REVIEW_QUEUE


def test_pipeline_tier_2_block_end_to_end(pipeline: EligibilityPipeline) -> None:
    result = pipeline.run("SUB-30003")

    assert result.decision.rules_outcome == RulesOutcome.TIER_2
    assert result.execution.status == MiCCExecutionStatus.BLOCKED
    assert result.execution.queue_name == BLOCKED_QUEUE


def test_pipeline_tier_2_retry_later_end_to_end(pipeline: EligibilityPipeline) -> None:
    result = pipeline.run("SUB-30004")

    assert result.decision.rules_outcome == RulesOutcome.TIER_2
    assert result.execution.status == MiCCExecutionStatus.DEFERRED
    assert result.execution.queue_name == RETRY_QUEUE
