"""Pydantic models for synthetic dataset records and expected test outcomes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from migration_control_tower.domain.enums import MigrationTier, RecommendedAction, RulesOutcome
from migration_control_tower.domain.models import CanonicalMigrationContext
from migration_control_tower.domain.reason_codes import ReasonCode


class ExpectedOutcome(BaseModel):
    """Test metadata kept separate from the canonical migration context."""

    scenario: str
    rules_outcome: RulesOutcome
    final_tier: MigrationTier
    agent_reviewed: bool = False
    agent_suggested_tier: MigrationTier | None = None
    reason_codes: list[ReasonCode] = Field(default_factory=list)
    recommended_action: RecommendedAction
    notes: str = ""


class SyntheticSubscriberRecord(BaseModel):
    """One synthetic subscriber with canonical context and expected test outcome."""

    subscriber_id: str
    context: CanonicalMigrationContext
    expected: ExpectedOutcome

    def model_post_init(self, __context: object) -> None:
        if self.subscriber_id != self.context.subscriber_id:
            raise ValueError(
                f"subscriber_id mismatch: record={self.subscriber_id}, "
                f"context={self.context.subscriber_id}"
            )


class SyntheticDataset(BaseModel):
    """Top-level synthetic dataset envelope."""

    version: str = "1"
    subscribers: list[SyntheticSubscriberRecord]

    def model_post_init(self, __context: object) -> None:
        ids = [record.subscriber_id for record in self.subscribers]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate subscriber_id values in synthetic dataset")
