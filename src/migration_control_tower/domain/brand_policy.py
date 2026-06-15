"""Placeholder hook for future brand-specific policy overrides.

v1 does not implement brand-specific logic. The hook exists so callers can
inject overrides later without changing the pipeline interface.
"""

from __future__ import annotations

from typing import Protocol

from migration_control_tower.domain.models import CanonicalMigrationContext


class BrandPolicyHook(Protocol):
    """Apply brand-specific policy adjustments to a canonical context."""

    def apply(self, context: CanonicalMigrationContext) -> CanonicalMigrationContext:
        """Return the context after any brand-specific overrides."""
        ...


class NoOpBrandPolicyHook:
    """Default v1 hook — passes context through unchanged."""

    def apply(self, context: CanonicalMigrationContext) -> CanonicalMigrationContext:
        return context


DEFAULT_BRAND_POLICY_HOOK = NoOpBrandPolicyHook()
