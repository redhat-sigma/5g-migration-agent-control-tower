"""Assemble canonical subscriber migration context from source adapters."""

from migration_control_tower.adapters import (
    CareCaseHubAdapter,
    Customer360Adapter,
    DeviceRegistryAdapter,
    ProvisioningHubAdapter,
)
from migration_control_tower.data import get_context
from migration_control_tower.domain.brand_policy import BrandPolicyHook, DEFAULT_BRAND_POLICY_HOOK
from migration_control_tower.domain.models import CanonicalMigrationContext


class ContextAssembler:
    """Merge adapter outputs into a CanonicalMigrationContext."""

    def __init__(
        self,
        customer360: Customer360Adapter | None = None,
        provisioning_hub: ProvisioningHubAdapter | None = None,
        device_registry: DeviceRegistryAdapter | None = None,
        care_case_hub: CareCaseHubAdapter | None = None,
        brand_policy_hook: BrandPolicyHook | None = None,
    ) -> None:
        self.customer360 = customer360 or Customer360Adapter()
        self.provisioning_hub = provisioning_hub or ProvisioningHubAdapter()
        self.device_registry = device_registry or DeviceRegistryAdapter()
        self.care_case_hub = care_case_hub or CareCaseHubAdapter()
        self.brand_policy_hook = brand_policy_hook or DEFAULT_BRAND_POLICY_HOOK

    def assemble(self, subscriber_id: str) -> CanonicalMigrationContext:
        """Load canonical context from the local synthetic dataset and apply brand hook."""
        context = get_context(subscriber_id)
        return self.brand_policy_hook.apply(context)
