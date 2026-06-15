"""Pydantic domain models for migration eligibility decisioning."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from migration_control_tower.domain.enums import (
    MigrationTier,
    MiCCExecutionStatus,
    ReasonCodeSource,
    RecommendedAction,
    RulesOutcome,
)
from migration_control_tower.domain.reason_codes import ReasonCode


class BrandMetadata(BaseModel):
    """Brand carried as metadata. Policy overrides applied via BrandPolicyHook."""

    brand_id: str


class CanonicalMigrationContext(BaseModel):
    """Canonical subscriber view assembled from all source adapters."""

    subscriber_id: str
    brand: BrandMetadata
    contract_type: str
    account_status: str
    billing_ok: bool
    sim_status: str
    provisioning_state: str
    network_ready: bool
    prior_migration_state: str
    device_model: str
    is_5g_capable: bool
    requires_sim_swap: bool
    open_complaint: bool
    recent_case_count: int = Field(ge=0)
    escalation_flag: bool


class RulesResult(BaseModel):
    """Output of the deterministic rules engine."""

    outcome: RulesOutcome
    tier: MigrationTier | None = None
    reason_codes: list[ReasonCode] = Field(default_factory=list)
    matched_rules: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_tier_for_outcome(self) -> RulesResult:
        if self.outcome == RulesOutcome.AMBIGUOUS:
            if self.tier is not None:
                raise ValueError("tier must be None when rules outcome is AMBIGUOUS")
            return self
        expected = MigrationTier(self.outcome.value)
        if self.tier is not None and self.tier != expected:
            raise ValueError(
                f"tier must be {expected.value} when outcome is {self.outcome.value}"
            )
        if self.tier is None:
            self.tier = expected
        return self


class SourcedReasonCode(BaseModel):
    """Reason code with explicit rules vs agent provenance."""

    source: ReasonCodeSource
    code: ReasonCode

    @property
    def prefixed(self) -> str:
        """Human-readable provenance prefix, e.g. rules:BILLING_NOT_OK."""
        return f"{self.source.value}:{self.code.value}"


class AgentReviewResult(BaseModel):
    """Structured output from the eligibility review agent for ambiguous cases.

    The agent may recommend Tier 0, Tier 1, or Tier 2.
    """

    suggested_tier: MigrationTier
    confidence_score: float = Field(ge=0.0, le=1.0)
    reason_codes: list[ReasonCode] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    review_summary: str
    recommended_action: RecommendedAction


class MigrationDecision(BaseModel):
    """Final combined decision returned to callers and the MiCC stub."""

    subscriber_id: str
    tier: MigrationTier
    reason_codes: list[SourcedReasonCode] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_action: RecommendedAction
    review_summary: str
    rules_outcome: RulesOutcome
    agent_reviewed: bool = False
    risk_flags: list[str] = Field(default_factory=list)
    unresolved: bool = False

    def codes_for_source(self, source: ReasonCodeSource) -> list[ReasonCode]:
        """Return reason codes contributed by a specific stage."""
        return [entry.code for entry in self.reason_codes if entry.source == source]


class MiCCExecutionResult(BaseModel):
    """Simulated MiCC queue receipt and execution outcome."""

    subscriber_id: str
    decision_tier: MigrationTier
    recommended_action: RecommendedAction
    queue_name: str
    queue_id: str
    job_id: str
    status: MiCCExecutionStatus
    message: str
    submitted_at: str
