"""Combine rules output and optional agent review into a final decision."""

from migration_control_tower.decision.logic import UnresolvedDecisionError, combine_decision
from migration_control_tower.domain.models import (
    AgentReviewResult,
    CanonicalMigrationContext,
    MigrationDecision,
    RulesResult,
)


class DecisionCombiner:
    """Produce final tier assignment and recommended action."""

    def combine(
        self,
        context: CanonicalMigrationContext,
        rules_result: RulesResult,
        agent_result: AgentReviewResult | None = None,
        *,
        allow_unresolved: bool = False,
    ) -> MigrationDecision:
        return combine_decision(
            context,
            rules_result,
            agent_result,
            allow_unresolved=allow_unresolved,
        )
