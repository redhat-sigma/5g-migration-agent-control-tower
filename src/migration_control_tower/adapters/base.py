"""Base adapter interface for placeholder source systems."""

from abc import ABC, abstractmethod
from typing import Any


class SourceAdapter(ABC):
    """Read subscriber signals from a single placeholder source system."""

    system_name: str

    @abstractmethod
    def fetch(self, subscriber_id: str) -> dict[str, Any]:
        """Return raw records for a subscriber from this source."""
        ...
