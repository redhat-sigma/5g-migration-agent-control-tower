"""Tests for the synthetic subscriber dataset."""

import pytest
from pydantic import ValidationError

from migration_control_tower.data import (
    ExpectedOutcome,
    SyntheticDataset,
    clear_dataset_cache,
    get_context,
    get_expected,
    get_record,
    get_records_by_final_tier,
    get_records_by_rules_outcome,
    list_subscriber_ids,
    load_synthetic_dataset,
)
from migration_control_tower.domain import MigrationTier, RulesOutcome


@pytest.fixture(autouse=True)
def _reset_dataset_cache() -> None:
    clear_dataset_cache()


def test_dataset_loads_and_validates() -> None:
    dataset = load_synthetic_dataset()
    assert dataset.version == "1"
    assert len(dataset.subscribers) == 12


def test_all_contexts_are_valid_canonical_models() -> None:
    for subscriber_id in list_subscriber_ids():
        context = get_context(subscriber_id)
        assert context.subscriber_id == subscriber_id
        assert context.brand.brand_id


def test_expected_metadata_separate_from_context() -> None:
    record = get_record("SUB-20001")
    assert "expected" not in record.context.model_dump()
    assert isinstance(record.expected, ExpectedOutcome)
    assert record.expected.rules_outcome == RulesOutcome.AMBIGUOUS


def test_coverage_tier_0_cases() -> None:
    records = get_records_by_rules_outcome(RulesOutcome.TIER_0)
    assert len(records) == 3
    assert {record.subscriber_id for record in records} == {
        "SUB-10001",
        "SUB-10002",
        "SUB-10003",
    }


def test_coverage_ambiguous_cases() -> None:
    records = get_records_by_rules_outcome(RulesOutcome.AMBIGUOUS)
    assert len(records) == 5
    assert all(record.expected.agent_reviewed for record in records)
    assert all(record.expected.agent_suggested_tier is not None for record in records)


def test_coverage_tier_2_cases() -> None:
    records = get_records_by_rules_outcome(RulesOutcome.TIER_2)
    assert len(records) == 4
    assert all(not record.expected.agent_reviewed for record in records)


def test_ambiguous_cases_do_not_assume_tier_1() -> None:
    ambiguous = get_records_by_rules_outcome(RulesOutcome.AMBIGUOUS)
    suggested_tiers = {record.expected.agent_suggested_tier for record in ambiguous}
    assert MigrationTier.TIER_1 in suggested_tiers
    assert MigrationTier.TIER_2 in suggested_tiers


def test_conflicting_signal_edge_case() -> None:
    expected = get_expected("SUB-20005")
    context = get_context("SUB-20005")
    assert context.escalation_flag is True
    assert context.network_ready is True
    assert context.billing_ok is True
    assert expected.rules_outcome == RulesOutcome.AMBIGUOUS
    assert expected.agent_suggested_tier == MigrationTier.TIER_2


def test_brand_present_as_metadata_only() -> None:
    brand_ids = {get_context(subscriber_id).brand.brand_id for subscriber_id in list_subscriber_ids()}
    assert brand_ids == {"1und1", "drillisch", "webde"}


def test_get_record_missing_subscriber_raises() -> None:
    with pytest.raises(KeyError, match="SUB-99999"):
        get_record("SUB-99999")


def test_dataset_rejects_duplicate_subscriber_ids(tmp_path) -> None:
    invalid = {
        "version": "1",
        "subscribers": [
            {
                "subscriber_id": "SUB-DUP",
                "context": {
                    "subscriber_id": "SUB-DUP",
                    "brand": {"brand_id": "1und1"},
                    "contract_type": "postpaid",
                    "account_status": "active",
                    "billing_ok": True,
                    "sim_status": "active",
                    "provisioning_state": "complete",
                    "network_ready": True,
                    "prior_migration_state": "none",
                    "device_model": "iPhone 14",
                    "is_5g_capable": True,
                    "requires_sim_swap": False,
                    "open_complaint": False,
                    "recent_case_count": 0,
                    "escalation_flag": False,
                },
                "expected": {
                    "scenario": "dup_a",
                    "rules_outcome": "tier_0",
                    "final_tier": "tier_0",
                    "reason_codes": ["ELIGIBILITY_CONFIRMED"],
                    "recommended_action": "auto_migrate",
                },
            },
            {
                "subscriber_id": "SUB-DUP",
                "context": {
                    "subscriber_id": "SUB-DUP",
                    "brand": {"brand_id": "1und1"},
                    "contract_type": "postpaid",
                    "account_status": "active",
                    "billing_ok": True,
                    "sim_status": "active",
                    "provisioning_state": "complete",
                    "network_ready": True,
                    "prior_migration_state": "none",
                    "device_model": "iPhone 14",
                    "is_5g_capable": True,
                    "requires_sim_swap": False,
                    "open_complaint": False,
                    "recent_case_count": 0,
                    "escalation_flag": False,
                },
                "expected": {
                    "scenario": "dup_b",
                    "rules_outcome": "tier_0",
                    "final_tier": "tier_0",
                    "reason_codes": ["ELIGIBILITY_CONFIRMED"],
                    "recommended_action": "auto_migrate",
                },
            },
        ],
    }
    path = tmp_path / "subscribers.json"
    path.write_text(__import__("json").dumps(invalid), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_synthetic_dataset(path)


def test_filter_by_final_tier() -> None:
    tier_1 = get_records_by_final_tier(MigrationTier.TIER_1)
    assert len(tier_1) == 4
    assert all(record.expected.final_tier == MigrationTier.TIER_1 for record in tier_1)
