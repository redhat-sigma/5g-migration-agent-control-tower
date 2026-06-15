"""Customer360 placeholder adapter.

TODO: Load from synthetic dataset JSON.
"""

from typing import Any

from migration_control_tower.adapters.base import SourceAdapter


class Customer360Adapter(SourceAdapter):
    system_name = "Customer360"

    def fetch(self, subscriber_id: str) -> dict[str, Any]:
        raise NotImplementedError("TODO: implement synthetic Customer360 fetch")
