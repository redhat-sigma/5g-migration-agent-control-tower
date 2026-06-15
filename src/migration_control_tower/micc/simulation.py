"""Deterministic MiCC stub execution simulation."""

from __future__ import annotations

from datetime import datetime, timezone

from migration_control_tower.domain.enums import (
    MiCCExecutionStatus,
    MigrationTier,
    RecommendedAction,
)
from migration_control_tower.domain.models import MiCCExecutionResult, MigrationDecision
from migration_control_tower.micc.queues import (
    AUTO_MIGRATE_QUEUE,
    BLOCKED_QUEUE,
    MANUAL_REVIEW_QUEUE,
    RETRY_QUEUE,
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _job_id(decision: MigrationDecision) -> str:
    return f"JOB-{decision.subscriber_id}"


def _queue_id(decision: MigrationDecision, queue_name: str) -> str:
    slug = queue_name.replace("-", "_").upper()
    return f"MICC-{decision.subscriber_id}-{slug}"


def simulate_micc_execution(decision: MigrationDecision) -> MiCCExecutionResult:
    """Simulate MiCC queue placement and execution based on the final decision only."""
    job_id = _job_id(decision)
    submitted_at = _timestamp()

    if decision.tier == MigrationTier.TIER_0 and decision.recommended_action == RecommendedAction.AUTO_MIGRATE:
        queue_name = AUTO_MIGRATE_QUEUE
        return MiCCExecutionResult(
            subscriber_id=decision.subscriber_id,
            decision_tier=decision.tier,
            recommended_action=decision.recommended_action,
            queue_name=queue_name,
            queue_id=_queue_id(decision, queue_name),
            job_id=job_id,
            status=MiCCExecutionStatus.EXECUTED_SUCCESS,
            message="Queued to auto-migrate queue and executed successfully (simulated).",
            submitted_at=submitted_at,
        )

    if decision.tier == MigrationTier.TIER_2 and decision.recommended_action == RecommendedAction.BLOCK:
        return MiCCExecutionResult(
            subscriber_id=decision.subscriber_id,
            decision_tier=decision.tier,
            recommended_action=decision.recommended_action,
            queue_name=BLOCKED_QUEUE,
            queue_id="",
            job_id=job_id,
            status=MiCCExecutionStatus.BLOCKED,
            message="Migration blocked by decision; no queue placement performed (simulated).",
            submitted_at=submitted_at,
        )

    if decision.tier == MigrationTier.TIER_2 and decision.recommended_action == RecommendedAction.RETRY_LATER:
        queue_name = RETRY_QUEUE
        return MiCCExecutionResult(
            subscriber_id=decision.subscriber_id,
            decision_tier=decision.tier,
            recommended_action=decision.recommended_action,
            queue_name=queue_name,
            queue_id=_queue_id(decision, queue_name),
            job_id=job_id,
            status=MiCCExecutionStatus.DEFERRED,
            message="Queued for retry but execution deferred pending remediation (simulated).",
            submitted_at=submitted_at,
        )

    if decision.tier == MigrationTier.TIER_1 and decision.recommended_action == RecommendedAction.ASSISTED_REVIEW:
        queue_name = MANUAL_REVIEW_QUEUE
        return MiCCExecutionResult(
            subscriber_id=decision.subscriber_id,
            decision_tier=decision.tier,
            recommended_action=decision.recommended_action,
            queue_name=queue_name,
            queue_id=_queue_id(decision, queue_name),
            job_id=job_id,
            status=MiCCExecutionStatus.QUEUED,
            message="Queued to manual review queue for assisted handling (simulated).",
            submitted_at=submitted_at,
        )

    if decision.unresolved:
        queue_name = MANUAL_REVIEW_QUEUE
        return MiCCExecutionResult(
            subscriber_id=decision.subscriber_id,
            decision_tier=decision.tier,
            recommended_action=decision.recommended_action,
            queue_name=queue_name,
            queue_id=_queue_id(decision, queue_name),
            job_id=job_id,
            status=MiCCExecutionStatus.QUEUED,
            message="Unresolved decision queued to manual review for agent follow-up (simulated).",
            submitted_at=submitted_at,
        )

    queue_name = MANUAL_REVIEW_QUEUE
    return MiCCExecutionResult(
        subscriber_id=decision.subscriber_id,
        decision_tier=decision.tier,
        recommended_action=decision.recommended_action,
        queue_name=queue_name,
        queue_id=_queue_id(decision, queue_name),
        job_id=job_id,
        status=MiCCExecutionStatus.QUEUED,
        message="Decision routed to manual review queue (simulated fallback).",
        submitted_at=submitted_at,
    )
