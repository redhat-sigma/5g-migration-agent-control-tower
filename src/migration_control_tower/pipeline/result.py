"""Result envelope for a full pipeline run."""

from __future__ import annotations

from pydantic import BaseModel, Field

from migration_control_tower.domain.models import (
    AgentReviewResult,
    CanonicalMigrationContext,
    MiCCExecutionResult,
    MigrationDecision,
    RulesResult,
)


class PipelineRunResult(BaseModel):
    """All pipeline stages produced for one subscriber evaluation."""

    subscriber_id: str
    context: CanonicalMigrationContext
    rules_result: RulesResult
    agent_result: AgentReviewResult | None = None
    decision: MigrationDecision
    execution: MiCCExecutionResult

    @property
    def agent_required(self) -> bool:
        return self.rules_result.outcome.value == "ambiguous"
