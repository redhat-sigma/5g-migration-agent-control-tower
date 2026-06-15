"""Domain enums for migration eligibility decisioning."""

from enum import Enum


class MigrationTier(str, Enum):
    """Final subscriber migration tier."""

    TIER_0 = "tier_0"  # straight-through
    TIER_1 = "tier_1"  # assisted-handling
    TIER_2 = "tier_2"  # blocked / exception


class RulesOutcome(str, Enum):
    """Result of deterministic rules evaluation.

    TIER_0 and TIER_2 are definitive rule classifications.
    AMBIGUOUS means rules could not classify the case; the eligibility agent
    must review it and may recommend Tier 0, Tier 1, or Tier 2.
    """

    TIER_0 = "tier_0"
    TIER_2 = "tier_2"
    AMBIGUOUS = "ambiguous"


class RecommendedAction(str, Enum):
    """Suggested downstream handling action."""

    AUTO_MIGRATE = "auto_migrate"
    ASSISTED_REVIEW = "assisted_review"
    BLOCK = "block"
    RETRY_LATER = "retry_later"


class ReasonCodeSource(str, Enum):
    """Provenance for reason codes attached to a migration decision."""

    RULES = "rules"
    AGENT = "agent"


class MiCCExecutionStatus(str, Enum):
    """Simulated MiCC queue/execution status."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    EXECUTED_SUCCESS = "executed_success"
