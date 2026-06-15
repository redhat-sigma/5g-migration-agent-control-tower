"""Deterministic rules engine for Tier 0 and Tier 2 classification.

Ambiguous cases are deferred to the eligibility review agent.
"""

from migration_control_tower.domain.models import CanonicalMigrationContext, RulesResult
from migration_control_tower.rules.evaluators import evaluate_rules


class RulesEngine:
    """Evaluate subscriber context against deterministic eligibility rules."""

    def evaluate(self, context: CanonicalMigrationContext) -> RulesResult:
        return evaluate_rules(context)
