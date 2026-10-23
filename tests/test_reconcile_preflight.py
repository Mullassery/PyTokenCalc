"""Tests for usage normalization, reconciliation, and preflight."""

import pytest

from pytokencalc.preflight import preflight
from pytokencalc.pricing import Usage
from pytokencalc.reconcile import parse_usage, reconcile


class _Result:
    def __init__(self, input_tokens=0, image_tokens=0):
        self.input_tokens = input_tokens
        self.image_tokens = image_tokens


class _FakeRegistry:
    def __init__(self, image_tokens_per_image=170):
        self.image_tokens_per_image = image_tokens_per_image
        self.calls = []

    def count_tokens(self, model, text, provider=None):
        self.calls.append((model, text, provider))
        return _Result(max(1, len(text.split())))

    def count_vision(self, text, model, num_images=1, provider=None, **kwargs):
        return _Result(0, self.image_tokens_per_image * num_images)


def test_parse_openai_usage():
    usage = parse_usage(
        {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "prompt_tokens_details": {"cached_tokens": 40},
                "completion_tokens_details": {"reasoning_tokens": 5},
            }
        },
        provider="openai",
    )
    assert usage.input_tokens == 100
    assert usage.output_tokens == 20
    assert usage.cached_input_tokens == 40
    assert usage.reasoning_tokens == 5


def test_parse_anthropic_usage_includes_cache_tokens():
    usage = parse_usage(
        {
            "usage": {
                "input_tokens": 100,
                "output_tokens": 30,
                "cache_read_input_tokens": 200,
                "cache_creation_input_tokens": 50,
            }
        }
    )
    assert usage.input_tokens == 350
    assert usage.output_tokens == 30
    assert usage.cached_input_tokens == 200
    assert usage.cache_write_tokens == 50


def test_parse_openrouter_usage_exposes_reported_cost():
    usage = parse_usage(
        {
            "usage": {
                "prompt_tokens": 1_000,
                "completion_tokens": 200,
                "prompt_tokens_details": {
                    "cached_tokens": 400,
                    "cache_write_tokens": 100,
                },
                "cost": 0.008,
            }
        },
        provider="openrouter",
    )
    assert usage.cached_input_tokens == 400
    assert usage.cache_write_tokens == 100
    assert usage.provider_reported_cost_usd == pytest.approx(0.008)


def test_parse_usage_rejects_missing_fields():
    with pytest.raises(ValueError, match="Could not find token usage fields"):
        parse_usage({"usage": {"elapsed": 1}})


def test_reconcile_with_expected_cost():
    result = reconcile(
        "gpt-4o",
        {"usage": {"prompt_tokens": 1_000, "completion_tokens": 500}},
        expected_cost_usd=0.001,
    )
    assert result.cost.total_usd == pytest.approx(0.0075)
    assert result.delta_usd == pytest.approx(0.0065)
    assert result.delta_percent == pytest.approx(650.0)


def test_reconcile_with_expected_usage():
    result = reconcile(
        "gpt-4o",
        {"usage": {"prompt_tokens": 1_000, "completion_tokens": 500}},
        expected_usage=Usage(input_tokens=500, output_tokens=100),
    )
    assert result.expected_cost_usd == pytest.approx(0.00225)
    assert result.delta_usd == pytest.approx(0.00525)


def test_reconcile_compares_provider_reported_cost():
    result = reconcile(
        "gpt-4o",
        {
            "usage": {
                "prompt_tokens": 1_000,
                "completion_tokens": 500,
                "cost": 0.008,
            }
        },
        provider="openrouter",
    )
    assert result.provider_reported_cost_usd == pytest.approx(0.008)
    assert result.provider_delta_usd == pytest.approx(-0.0005)


def test_preflight_counts_text_tools_and_context():
    registry = _FakeRegistry()
    result = preflight(
        [
            {"role": "system", "content": "be brief"},
            {"role": "user", "content": "hello world"},
        ],
        "gpt-4o",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "lookup",
                    "description": "look it up",
                    "parameters": {"type": "object"},
                },
            }
        ],
        max_output_tokens=100,
        registry=registry,
    )
    assert result.text_tokens == 4
    assert result.tool_tokens > 0
    assert result.message_overhead_tokens == 11
    assert result.input_tokens == (
        result.text_tokens
        + result.tool_tokens
        + result.image_tokens
        + result.message_overhead_tokens
    )
    assert result.context_length == 128_000
    assert result.fits is True
    assert result.estimated_cost_usd is not None


def test_preflight_reports_context_overflow():
    result = preflight(
        [{"role": "user", "content": "hello"}],
        "gpt-4o",
        max_output_tokens=128_000,
        registry=_FakeRegistry(),
    )
    assert result.fits is False
    assert result.context_remaining is not None


def test_preflight_counts_images_and_warns_when_unsupported():
    supported = preflight(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "describe"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/a.png"}},
                    {"type": "image_url", "image_url": {"url": "https://example.com/b.png"}},
                ],
            }
        ],
        "gpt-4o",
        registry=_FakeRegistry(image_tokens_per_image=170),
    )
    assert supported.image_tokens == 340
    assert supported.input_tokens >= 340

    unsupported = preflight(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "describe"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/a.png"}},
                ],
            }
        ],
        "gpt-4o",
        registry=_FakeRegistry(image_tokens_per_image=0),
    )
    assert any("unavailable" in warning for warning in unsupported.warnings)


def test_preflight_unknown_model_returns_warnings_not_crash():
    result = preflight(
        "hello",
        "totally-unknown-model",
        registry=_FakeRegistry(),
    )
    assert result.context_length is None
    assert result.fits is None
    assert result.estimated_cost_usd is None
    assert any("context window is unknown" in warning for warning in result.warnings)
    assert any("pricing unavailable" in warning for warning in result.warnings)
