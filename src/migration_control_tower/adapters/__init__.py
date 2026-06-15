"""Input adapters for placeholder source systems."""

from migration_control_tower.adapters.base import SourceAdapter
from migration_control_tower.adapters.care_case_hub import CareCaseHubAdapter
from migration_control_tower.adapters.customer360 import Customer360Adapter
from migration_control_tower.adapters.device_registry import DeviceRegistryAdapter
from migration_control_tower.adapters.provisioning_hub import ProvisioningHubAdapter

__all__ = [
    "CareCaseHubAdapter",
    "Customer360Adapter",
    "DeviceRegistryAdapter",
    "ProvisioningHubAdapter",
    "SourceAdapter",
]
