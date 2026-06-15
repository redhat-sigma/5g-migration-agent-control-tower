"""Shared pytest fixtures."""

import pytest

from migration_control_tower.data import clear_dataset_cache
from migration_control_tower.domain import CanonicalMigrationContext


@pytest.fixture(autouse=True)
def _reset_dataset_cache() -> None:
    clear_dataset_cache()


@pytest.fixture
def sample_subscriber_id() -> str:
    return "SUB-10001"


@pytest.fixture
def sample_context() -> CanonicalMigrationContext:
    from migration_control_tower.data import get_context

    return get_context("SUB-10001")
