"""Tests for the offline OpenRouter catalog importer."""

import json

import pytest

from pytokencalc import pricing
from pytokencalc.catalog import get_model_spec
from pytokencalc.openrouter import (
    import_openrouter_catalog,
    import_openrouter_catalog_file,
)


@pytest.fixture(autouse=True)
def restore_pricing_table():
    original = dict(pricing.PRICING_TABLE)
    yield
    pricing.PRICING_TABLE.clear()
    pricing.PRICING_TABLE.update(original)


PAYLOAD = {
    "fetched_at": "2026-10-24T00:00:00Z",
    "data": [
        {
            "id": "testvendor/test-model",
            "canonical_slug": "testvendor/test-model-2026-01-01",
            "name": "Test Model",
            "context_length": 128_000,
            "architecture": {
                "input_modalities": ["text", "image"],
                "output_modalities": ["text"],
                "tokenizer": "GPT",
            },
            "pricing": {
                "prompt": "0.000002",
                "completion": "0.00001",
                "request": "0.001",
                "input_cache_read": "0.0000005",
                "input_cache_write": "0.0000025",
            },
            "top_provider": {"max_completion_tokens": 4_096},
            "supported_parameters": ["tools", "temperature"],
            "expiration_date": "2027-01-01",
        },
        {
            "id": "testvendor/test-model:free",
            "name": "Test Model Free",
            "pricing": {"prompt": "0", "completion": "0"},
        },
        {
            "id": "testvendor/unpriced-model",
            "name": "Unpriced Model",
            "pricing": {"prompt": "-1", "completion": "-1"},
        },
    ],
}


def test_import_openrouter_catalog_converts_prices_and_metadata():
    result = import_openrouter_catalog(PAYLOAD)
    assert result.imported == 2
    assert result.pricing_imported == 1
    assert result.skipped_variants == 1
    assert any("in-memory only" in warning for warning in result.warnings)

    spec = get_model_spec("testvendor/test-model")
    assert spec is not None
    assert spec.context_length == 128_000
    assert spec.max_output_tokens == 4_096
    assert spec.input_modalities == ("text", "image")
    assert spec.capabilities == ("tools",)
    assert spec.aliases == ("testvendor/test-model-2026-01-01",)
    assert spec.source.startswith("openrouter:")
    assert spec.expiration_date == "2027-01-01"

    model_pricing = pricing.get_model_pricing("testvendor/test-model")
    assert model_pricing.input_per_million == 2.0
    assert model_pricing.output_per_million == 10.0
    assert model_pricing.cache_read_per_million == 0.5
    assert model_pricing.cache_write_per_million == 2.5
    assert model_pricing.request_fee_usd == 0.001


def test_variants_are_skipped_by_default():
    result = import_openrouter_catalog(PAYLOAD)
    assert result.skipped_variants == 1
    assert get_model_spec("testvendor/test-model:free") is None


def test_variants_can_be_included_explicitly():
    payload = {
        "data": [
            {
                "id": "testvendor/variant-model:free",
                "pricing": {"prompt": "0", "completion": "0"},
            }
        ]
    }
    result = import_openrouter_catalog(payload, include_variants=True)
    assert result.imported == 1
    assert result.skipped_variants == 0
    assert get_model_spec("testvendor/variant-model:free") is not None


def test_invalid_pricing_is_imported_without_price():
    result = import_openrouter_catalog(PAYLOAD)
    assert result.imported == 2
    assert pricing.get_model_pricing("testvendor/unpriced-model") is None
    assert any("unpriced-model" in warning for warning in result.warnings)


def test_import_from_file(tmp_path):
    path = tmp_path / "models.json"
    path.write_text(json.dumps(PAYLOAD), encoding="utf-8")
    result = import_openrouter_catalog_file(str(path))
    assert result.imported == 2
    assert str(path) in result.source
    assert result.to_dict()["pricing_imported"] == 1
