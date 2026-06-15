"""ProvisioningHub placeholder adapter.

TODO: Load from synthetic dataset JSON.
"""

from typing import Any

from migration_control_tower.adapters.base import SourceAdapter


class ProvisioningHubAdapter(SourceAdapter):
    system_name = "ProvisioningHub"

    def fetch(self, subscriber_id: str) -> dict[str, Any]:
        raise NotImplementedError("TODO: implement synthetic ProvisioningHub fetch")
