"""Load and query the local synthetic subscriber dataset."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from migration_control_tower.config import SYNTHETIC_DATA_PATH
from migration_control_tower.data.models import ExpectedOutcome, SyntheticDataset, SyntheticSubscriberRecord
from migration_control_tower.domain.enums import MigrationTier, RulesOutcome
from migration_control_tower.domain.models import CanonicalMigrationContext


def load_synthetic_dataset(path: Path | None = None) -> SyntheticDataset:
    """Load and validate the synthetic dataset from disk."""
    data_path = path or SYNTHETIC_DATA_PATH
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return SyntheticDataset.model_validate(raw)


@lru_cache(maxsize=1)
def _cached_dataset() -> SyntheticDataset:
    return load_synthetic_dataset()


def list_subscriber_ids() -> list[str]:
    """Return all subscriber IDs in dataset order."""
    return [record.subscriber_id for record in _cached_dataset().subscribers]


def get_record(subscriber_id: str) -> SyntheticSubscriberRecord:
    """Return the full synthetic record for a subscriber."""
    for record in _cached_dataset().subscribers:
        if record.subscriber_id == subscriber_id:
            return record
    raise KeyError(f"subscriber not found in synthetic dataset: {subscriber_id}")


def get_context(subscriber_id: str) -> CanonicalMigrationContext:
    """Return canonical context for a subscriber."""
    return get_record(subscriber_id).context


def get_expected(subscriber_id: str) -> ExpectedOutcome:
    """Return expected test outcome metadata for a subscriber."""
    return get_record(subscriber_id).expected


def get_records_by_rules_outcome(outcome: RulesOutcome) -> list[SyntheticSubscriberRecord]:
    """Filter records by expected rules outcome."""
    return [
        record
        for record in _cached_dataset().subscribers
        if record.expected.rules_outcome == outcome
    ]


def get_records_by_final_tier(tier: MigrationTier) -> list[SyntheticSubscriberRecord]:
    """Filter records by expected final tier."""
    return [
        record
        for record in _cached_dataset().subscribers
        if record.expected.final_tier == tier
    ]


def clear_dataset_cache() -> None:
    """Clear cached dataset (useful in tests)."""
    _cached_dataset.cache_clear()
