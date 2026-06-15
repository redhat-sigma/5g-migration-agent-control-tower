"""CareCaseHub placeholder adapter.

TODO: Load from synthetic dataset JSON.
"""

from typing import Any

from migration_control_tower.adapters.base import SourceAdapter


class CareCaseHubAdapter(SourceAdapter):
    system_name = "CareCaseHub"

    def fetch(self, subscriber_id: str) -> dict[str, Any]:
        raise NotImplementedError("TODO: implement synthetic CareCaseHub fetch")
