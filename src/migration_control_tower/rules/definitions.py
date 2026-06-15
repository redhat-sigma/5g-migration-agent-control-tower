"""Centralized rule identifiers for the deterministic rules engine."""

from enum import Enum


class RuleId(str, Enum):
    """Stable rule IDs recorded in RulesResult.matched_rules."""

    # Tier 2 — hard blocks
    T2_ACCOUNT_SUSPENDED = "t2_account_suspended"
    T2_ACCOUNT_INACTIVE = "t2_account_inactive"
    T2_BILLING_NOT_OK = "t2_billing_not_ok"
    T2_PRIOR_MIGRATION_IN_PROGRESS = "t2_prior_migration_in_progress"
    T2_PRIOR_MIGRATION_FAILED = "t2_prior_migration_failed"
    T2_SIM_NOT_ACTIVE = "t2_sim_not_active"
    T2_DEVICE_NOT_5G_CAPABLE = "t2_device_not_5g_capable"

    # Ambiguous — defer to eligibility agent
    AMB_OPEN_COMPLAINT = "amb_open_complaint"
    AMB_ESCALATION_OPEN = "amb_escalation_open"
    AMB_RECENT_CASE_ACTIVITY = "amb_recent_case_activity"
    AMB_NETWORK_NOT_READY = "amb_network_not_ready"
    AMB_PROVISIONING_INCOMPLETE = "amb_provisioning_incomplete"
    AMB_SIM_SWAP_REQUIRED = "amb_sim_swap_required"
    AMB_UNRESOLVED = "amb_unresolved"

    # Tier 0 — straight-through
    T0_STRAIGHT_THROUGH_ELIGIBLE = "t0_straight_through_eligible"
