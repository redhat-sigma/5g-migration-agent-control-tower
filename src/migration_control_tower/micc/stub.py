"""Stubbed MiCC execution layer.

Simulates queue receipt and execution outcomes only — no real execution engine.
MiCC is downstream only and does not influence eligibility decisioning.
"""

from migration_control_tower.domain.models import MiCCExecutionResult, MigrationDecision
from migration_control_tower.micc.simulation import simulate_micc_execution


class MiCCStub:
    """Simulate handing a migration decision to MiCC."""

    def submit(self, decision: MigrationDecision) -> MiCCExecutionResult:
        return simulate_micc_execution(decision)
