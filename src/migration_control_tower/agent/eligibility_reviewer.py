"""Single eligibility review agent for ambiguous rules outcomes only."""

from migration_control_tower.agent.review_logic import AmbiguousReviewRequiredError, review_ambiguous_case
from migration_control_tower.domain.models import AgentReviewResult, CanonicalMigrationContext, RulesResult


class EligibilityReviewAgent:
    """Review ambiguous subscriber cases after rules evaluation."""

    def review(
        self,
        context: CanonicalMigrationContext,
        rules_result: RulesResult,
    ) -> AgentReviewResult:
        return review_ambiguous_case(context, rules_result)
