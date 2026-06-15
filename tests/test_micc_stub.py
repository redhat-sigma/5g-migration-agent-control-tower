"""Tests for the MiCC stub."""

import pytest

from migration_control_tower.data import get_context, get_expected
from migration_control_tower.decision import DecisionCombiner
from migration_control_tower.domain import MiCCExecutionStatus, MigrationTier, RecommendedAction, RulesOutcome
from migration_control_tower.micc import (
    AUTO_MIGRATE_QUEUE,
    BLOCKED_QUEUE,
    MANUAL_REVIEW_QUEUE,
    MiCCStub,
    RETRY_QUEUE,
    simulate_micc_execution,
)
from migration_control_tower.rules import RulesEngine


@pytest.fixture
def stub() -> MiCCStub:
    return MiCCStub()


@pytest.fixture
def combiner() -> DecisionCombiner:
    return DecisionCombiner()


@pytest.fixture
def rules_engine() -> RulesEngine:
    return RulesEngine()


def _decision_for(subscriber_id: str, combiner: DecisionCombiner, rules_engine: RulesEngine):
    from migration_control_tower.agent import EligibilityReviewAgent

    context = get_context(subscriber_id)
    rules_result = rules_engine.evaluate(context)
    expected = get_expected(subscriber_id)

    agent_result = None
    if expected.agent_reviewed:
        agent_result = EligibilityReviewAgent().review(context, rules_result)

    return combiner.combine(context, rules_result, agent_result)


def test_tier_0_auto_migrate_executed_success(
    stub: MiCCStub,
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
) -> None:
    decision = _decision_for("SUB-10001", combiner, rules_engine)
    result = stub.submit(decision)

    assert decision.tier == MigrationTier.TIER_0
    assert decision.recommended_action == RecommendedAction.AUTO_MIGRATE
    assert result.status == MiCCExecutionStatus.EXECUTED_SUCCESS
    assert result.queue_name == AUTO_MIGRATE_QUEUE
    assert result.queue_id.startswith("MICC-SUB-10001-")
    assert result.job_id == "JOB-SUB-10001"


def test_tier_1_assisted_review_queued_to_manual_queue(
    stub: MiCCStub,
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
) -> None:
    decision = _decision_for("SUB-20001", combiner, rules_engine)
    result = stub.submit(decision)

    assert decision.tier == MigrationTier.TIER_1
    assert decision.recommended_action == RecommendedAction.ASSISTED_REVIEW
    assert result.status == MiCCExecutionStatus.QUEUED
    assert result.queue_name == MANUAL_REVIEW_QUEUE
    assert "MANUAL_REVIEW" in result.queue_id


def test_tier_2_block_not_queued(
    stub: MiCCStub,
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
) -> None:
    decision = _decision_for("SUB-30001", combiner, rules_engine)
    result = stub.submit(decision)

    assert decision.tier == MigrationTier.TIER_2
    assert decision.recommended_action == RecommendedAction.BLOCK
    assert result.status == MiCCExecutionStatus.BLOCKED
    assert result.queue_name == BLOCKED_QUEUE
    assert result.queue_id == ""


def test_tier_2_retry_later_deferred(
    stub: MiCCStub,
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
) -> None:
    decision = _decision_for("SUB-30002", combiner, rules_engine)
    result = stub.submit(decision)

    assert decision.tier == MigrationTier.TIER_2
    assert decision.recommended_action == RecommendedAction.RETRY_LATER
    assert result.status == MiCCExecutionStatus.DEFERRED
    assert result.queue_name == RETRY_QUEUE
    assert result.queue_id.startswith("MICC-SUB-30002-")


def test_micc_does_not_change_decision(
    stub: MiCCStub,
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
) -> None:
    decision = _decision_for("SUB-10002", combiner, rules_engine)
    before = decision.model_dump()
    stub.submit(decision)
    assert decision.model_dump() == before


@pytest.mark.parametrize(
    "subscriber_id,expected_status,expected_queue",
    [
        ("SUB-10001", MiCCExecutionStatus.EXECUTED_SUCCESS, AUTO_MIGRATE_QUEUE),
        ("SUB-20003", MiCCExecutionStatus.QUEUED, MANUAL_REVIEW_QUEUE),
        ("SUB-30004", MiCCExecutionStatus.DEFERRED, RETRY_QUEUE),
    ],
)
def test_simulate_micc_execution_deterministic_ids(
    subscriber_id: str,
    expected_status: MiCCExecutionStatus,
    expected_queue: str,
    combiner: DecisionCombiner,
    rules_engine: RulesEngine,
) -> None:
    decision = _decision_for(subscriber_id, combiner, rules_engine)
    first = simulate_micc_execution(decision)
    second = simulate_micc_execution(decision)

    assert first.status == expected_status
    assert first.queue_name == expected_queue
    assert first.queue_id == second.queue_id
    assert first.job_id == second.job_id
