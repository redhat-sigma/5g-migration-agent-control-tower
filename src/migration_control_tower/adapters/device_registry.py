"""DeviceRegistry placeholder adapter.

TODO: Load from synthetic dataset JSON.
"""

from typing import Any

from migration_control_tower.adapters.base import SourceAdapter


class DeviceRegistryAdapter(SourceAdapter):
    system_name = "DeviceRegistry"

    def fetch(self, subscriber_id: str) -> dict[str, Any]:
        raise NotImplementedError("TODO: implement synthetic DeviceRegistry fetch")
