"""Tests for the headline API: `pytokencalc/api.py` + `pytokencalc/pricing.py`.

These two modules back `count_tokens()` / `estimate_cost()` -- the functions
the README leads with -- and previously had no dedicated test file (see
ROADMAP_HONEST.md section 3). The pricing tests are pure (no network, no
optional deps); the API tests use a fake registry so they are deterministic,
plus one tiktoken-gated integration test against the real registry.
"""

import pytest

from pytokencalc import api
from pytokencalc.pricing import (
    PRICING_LAST_UPDATED,
    PRICING_TABLE,
    ModelPricing,
    estimate_cost,
    get_model_pricing,
)


class TestPricingTable:
    def test_last_updated_is_a_nonempty_marker(self):
        assert isinstance(PRICING_LAST_UPDATED, str)
        assert PRICING_LAST_UPDATED.strip()

    def test_table_is_nonempty_and_well_formed(self):
        assert PRICING_TABLE, "pricing table should not be empty"
        for key, value in PRICING_TABLE.items():
            assert isinstance(key, str) and key == key.lower()
            assert isinstance(value, ModelPricing)
            assert value.input_per_million > 0
            assert value.output_per_million > 0

    def test_keys_are_lowercase(self):
        # get_model_pricing lowercases the input, so table keys must be lower.
        assert all(key == key.lower() for key in PRICING_TABLE)


class TestGetModelPricing:
    def test_exact_match(self):
        assert get_model_pricing("gpt-4o") == ModelPricing(2.50, 10.00)

    def test_case_insensitive(self):
        assert get_model_pricing("GPT-4O") == get_model_pricing("gpt-4o")

    def test_dated_suffix_resolves_to_base_model(self):
        assert get_model_pricing("gpt-4o-2024-11-20") == ModelPricing(2.50, 10.00)

    def test_longest_prefix_wins(self):
        # "gpt-4o-mini-..." must resolve to gpt-4o-mini, not gpt-4o.
        assert get_model_pricing("gpt-4o-mini-2024-07-18") == ModelPricing(0.15, 0.60)

    def test_unknown_model_returns_none(self):
        assert get_model_pricing("totally-made-up-model") is None

    def test_empty_or_missing_returns_none(self):
        assert get_model_pricing("") is None
        assert get_model_pricing(None) is None


class TestEstimateCostDollars:
    def test_input_only_cost(self):
        # 1,000,000 input tokens on gpt-4o == $2.50 exactly.
        assert estimate_cost("gpt-4o", input_tokens=1_000_000) == pytest.approx(2.50)

    def test_input_and_output_cost(self):
        # 1M in ($2.50) + 1M out ($10.00) == $12.50.
        assert estimate_cost("gpt-4o", 1_000_000, 1_000_000) == pytest.approx(12.50)

    def test_zero_tokens_is_zero(self):
        assert estimate_cost("gpt-4o", 0, 0) == 0.0

    def test_dated_model_is_counted(self):
        assert estimate_cost("gpt-4o-2024-11-20", 1_000_000) == pytest.approx(2.50)

    def test_unknown_model_raises_valueerror(self):
        with pytest.raises(ValueError) as excinfo:
            estimate_cost("no-such-model", 100)
        msg = str(excinfo.value)
        assert "no-such-model" in msg
        assert PRICING_LAST_UPDATED in msg


class TestTopLevelApi:
    def test_default_model_is_gpt_4o(self):
        assert api.DEFAULT_MODEL == "gpt-4o"

    def test_api_estimate_cost_matches_pricing(self):
        assert api.estimate_cost("gpt-4o", 1_000_000, 500_000) == pytest.approx(
            estimate_cost("gpt-4o", 1_000_000, 500_000)
        )

    def test_api_estimate_cost_returns_float(self):
        assert isinstance(api.estimate_cost("gpt-4o", 10), float)

    def test_count_tokens_delegates_and_returns_int(self, monkeypatch):
        from pytokencalc.tokenizers.base import TokenCountResult

        calls = {}

        class _FakeRegistry:
            def count_tokens(self, model, text, provider=None):
                calls["model"] = model
                calls["text"] = text
                calls["provider"] = provider
                return TokenCountResult(
                    input_tokens=42, model=model, provider=provider or "fake"
                )

        monkeypatch.setattr(api, "get_global_registry", lambda: _FakeRegistry())

        result = api.count_tokens("hello world", model="gpt-4o", provider="openai")

        assert result == 42
        assert isinstance(result, int)
        assert calls == {"model": "gpt-4o", "text": "hello world", "provider": "openai"}

    def test_count_tokens_uses_default_model_when_omitted(self, monkeypatch):
        from pytokencalc.tokenizers.base import TokenCountResult

        seen = {}

        class _FakeRegistry:
            def count_tokens(self, model, text, provider=None):
                seen["model"] = model
                return TokenCountResult(input_tokens=1, model=model)

        monkeypatch.setattr(api, "get_global_registry", lambda: _FakeRegistry())

        api.count_tokens("x")

        assert seen["model"] == api.DEFAULT_MODEL


class TestRealRegistryIntegration:
    """End-to-end against the real registry -- requires tiktoken."""

    def test_count_tokens_real_gpt4o(self):
        try:
            import tiktoken  # noqa: F401
        except ImportError:
            pytest.skip("tiktoken not installed")

        from pytokencalc.tokenizers.registry import get_global_registry

        text = "Tell me a story about a robot"
        count = api.count_tokens(text, model="gpt-4o")

        assert isinstance(count, int)
        assert count > 0
        # Must agree with the registry it delegates to.
        assert count == get_global_registry().count_tokens("gpt-4o", text).input_tokens


class TestPricingStatusAndOverride:
    def test_status_reports_age_and_staleness(self):
        from datetime import date

        from pytokencalc.pricing import pricing_status

        status = pricing_status(now=date(2026, 10, 19))
        assert status["last_updated"] == PRICING_LAST_UPDATED
        assert status["models"] == len(PRICING_TABLE)
        assert status["stale"] is False

    def test_override_replaces_table_and_source(self, tmp_path):
        from pytokencalc import pricing

        original_table = dict(pricing.PRICING_TABLE)
        original_updated = pricing.PRICING_LAST_UPDATED
        original_source = pricing.PRICING_SOURCE
        try:
            path = tmp_path / "pricing.json"
            path.write_text(
                '{"last_updated": "2026-10-19",'
                ' "models": {"gpt-5": {"input_per_million": 1.25,'
                ' "output_per_million": 10.0}}}',
                encoding="utf-8",
            )
            status = pricing.load_pricing_override(str(path))
            assert status["source"] == str(path)
            assert pricing.get_model_pricing("gpt-5") == ModelPricing(1.25, 10.0)
            assert pricing.estimate_cost("gpt-5", 1_000_000, 1_000_000) == pytest.approx(11.25)
        finally:
            pricing.PRICING_TABLE = original_table
            pricing.PRICING_LAST_UPDATED = original_updated
            pricing.PRICING_SOURCE = original_source

    def test_override_rejects_missing_models(self, tmp_path):
        from pytokencalc import pricing

        path = tmp_path / "bad.json"
        path.write_text('{"last_updated": "2026-10-19"}', encoding="utf-8")
        with pytest.raises(ValueError, match="models"):
            pricing.load_pricing_override(str(path))
