"""Tests for usage-aware cost estimation."""

import pytest

from pytokencalc import pricing
from pytokencalc.pricing import (
    CostBreakdown,
    ModelPricing,
    Usage,
    estimate_cost,
    estimate_usage,
)


def test_usage_validates_subsets():
    with pytest.raises(ValueError, match="cannot exceed"):
        Usage(input_tokens=10, cached_input_tokens=8, cache_write_tokens=3)
    with pytest.raises(ValueError, match="non-negative"):
        Usage(input_tokens=-1)


def test_estimate_usage_with_cache_and_request_fee(monkeypatch):
    monkeypatch.setitem(
        pricing.PRICING_TABLE,
        "gpt-4o",
        ModelPricing(
            input_per_million=2.5,
            output_per_million=10.0,
            cache_read_per_million=1.25,
            cache_write_per_million=3.0,
            request_fee_usd=0.01,
        ),
    )
    breakdown = estimate_usage(
        "gpt-4o",
        Usage(
            input_tokens=1_000,
            output_tokens=200,
            cached_input_tokens=400,
            cache_write_tokens=100,
            request_count=2,
        ),
    )

    assert isinstance(breakdown, CostBreakdown)
    assert breakdown.input_cost_usd == pytest.approx(0.00125)
    assert breakdown.cache_read_cost_usd == pytest.approx(0.0005)
    assert breakdown.cache_write_cost_usd == pytest.approx(0.0003)
    assert breakdown.output_cost_usd == pytest.approx(0.002)
    assert breakdown.request_cost_usd == pytest.approx(0.02)
    assert breakdown.cache_savings_usd == pytest.approx(0.0005)
    assert breakdown.total_usd == pytest.approx(0.02405)


def test_cache_tokens_fall_back_to_input_rate(monkeypatch):
    monkeypatch.setitem(
        pricing.PRICING_TABLE,
        "gpt-4o",
        ModelPricing(2.5, 10.0),
    )
    breakdown = estimate_usage(
        "gpt-4o",
        Usage(input_tokens=1_000, cached_input_tokens=400),
    )
    assert breakdown.cache_read_rate_per_million == 2.5
    assert breakdown.cache_savings_usd == 0.0
    assert breakdown.total_usd == pytest.approx(0.0025)


def test_legacy_estimate_cost_still_works():
    assert estimate_cost("gpt-4o", 1_000_000, 1_000_000) == pytest.approx(12.50)


def test_cost_breakdown_serializes():
    breakdown = estimate_usage("gpt-4o", Usage(input_tokens=100))
    payload = breakdown.to_dict()
    assert payload["resolved_model"] == "gpt-4o"
    assert payload["usage"]["input_tokens"] == 100
    assert payload["costs_usd"]["total"] == pytest.approx(0.00025)


def test_pricing_override_accepts_cache_fields(tmp_path):
    original_table = dict(pricing.PRICING_TABLE)
    original_updated = pricing.PRICING_LAST_UPDATED
    original_source = pricing.PRICING_SOURCE
    try:
        path = tmp_path / "pricing.json"
        path.write_text(
            '{"last_updated": "2026-10-19", "models": {'
            ' "cached-model": {"input_per_million": 2.0,'
            ' "output_per_million": 4.0, "cache_read_per_million": 0.5,'
            ' "cache_write_per_million": 2.5, "request_fee_usd": 0.001}}}',
            encoding="utf-8",
        )
        pricing.load_pricing_override(str(path))
        model = pricing.get_model_pricing("cached-model")
        assert model.cache_read_per_million == 0.5
        assert model.cache_write_per_million == 2.5
        assert model.request_fee_usd == 0.001
    finally:
        pricing.PRICING_TABLE = original_table
        pricing.PRICING_LAST_UPDATED = original_updated
        pricing.PRICING_SOURCE = original_source
