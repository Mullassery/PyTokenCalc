"""
Regression tests for TokenCounterRegistry resilience to a single
tokenizer's construction failure.

Bug (documented in ROADMAP_HONEST.md, section 2, and reproduced live during
the OSS-standardization audit pass -- root cause of 47/100 test failures):

`OpenAITokenCounter.__init__` (pytokencalc/tokenizers/openai_counter.py)
eagerly downloads tiktoken's `cl100k_base`/`o200k_base` encodings and raises
`RuntimeError` if that network call fails. `TokenCounterRegistry.
_register_default_counters` (pytokencalc/tokenizers/registry.py) used to
wrap each counter's construction in `except ImportError` only, so that
RuntimeError was never caught -- it propagated out of
`TokenCounterRegistry.__init__`, meaning the *entire* registry failed to
construct, taking down Anthropic/Google/Cohere/HuggingFace/Ollama counting
too, not just OpenAI/tiktoken.

The fix broadens each per-provider `except` clause to `Exception`, so the
registry registers what it can and skips/logs what it can't. These tests
simulate a failing constructor (via mocking, so they don't depend on actual
network conditions or which optional provider SDKs happen to be installed)
and assert the registry still constructs and still serves the other
providers.
"""

from unittest.mock import patch

import pytest

from pytokencalc.tokenizers.base import TokenCounter, TokenCountResult
from pytokencalc.tokenizers.cache import TokenCounterCache
from pytokencalc.tokenizers.registry import TokenCounterRegistry


class _FakeWorkingCounter(TokenCounter):
    """Minimal stand-in for a tokenizer whose construction succeeds."""

    @property
    def provider_name(self) -> str:
        return "fake"

    @property
    def supported_models(self):
        return ["fake-model"]

    def count(self, text: str, model: str) -> TokenCountResult:
        return TokenCountResult(
            input_tokens=len(text.split()),
            provider=self.provider_name,
            model=model,
            source="local",
        )

    def validate_model(self, model: str) -> bool:
        return model == "fake-model"


def test_registry_survives_one_counter_raising_runtime_error():
    """Simulates the exact reported bug: a provider's constructor raises
    RuntimeError (e.g. OpenAITokenCounter's tiktoken encoding download
    failing over the network) -- not an ImportError. The registry must
    still construct, must skip only that provider, and every other
    provider must still work normally."""
    with patch(
        "pytokencalc.tokenizers.registry.OpenAITokenCounter",
        side_effect=RuntimeError("Failed to load tiktoken encodings: simulated network hiccup"),
    ), patch(
        "pytokencalc.tokenizers.registry.AnthropicTokenCounter",
        return_value=_FakeWorkingCounter(),
    ):
        registry = TokenCounterRegistry()  # must not raise

    assert "openai" not in registry.counters
    assert "anthropic" in registry.counters

    # The unaffected provider is fully usable through the registry.
    result = registry.count_tokens("fake-model", "hello world", provider="anthropic")
    assert result.input_tokens == 2
    assert result.provider == "fake"


def test_registry_survives_arbitrary_exception_types():
    """Not just RuntimeError -- any exception raised by any single
    provider's constructor (OSError, ValueError, a bare Exception, etc.)
    must be isolated to that one provider and not affect the rest."""
    with patch(
        "pytokencalc.tokenizers.registry.CohereTokenCounter",
        side_effect=OSError("simulated DNS failure"),
    ), patch(
        "pytokencalc.tokenizers.registry.GoogleTokenCounter",
        return_value=_FakeWorkingCounter(),
    ):
        registry = TokenCounterRegistry()  # must not raise

    assert "cohere" not in registry.counters
    assert "google" in registry.counters

    result = registry.count_tokens("fake-model", "one two three", provider="google")
    assert result.input_tokens == 3


def test_registry_still_registers_unaffected_real_counters():
    """With the real OpenAI counter forced to fail, other real (non-mocked)
    built-in counters whose optional dependencies are installed must still
    end up registered -- confirming the isolation holds end-to-end, not
    just for mocked counters."""
    with patch(
        "pytokencalc.tokenizers.registry.OpenAITokenCounter",
        side_effect=RuntimeError("simulated tiktoken network failure"),
    ):
        registry = TokenCounterRegistry()

    assert "openai" not in registry.counters
    # At least one other counter category should be present: providers only
    # fail to register when their optional dependency truly isn't
    # installed, which is independent of the OpenAI failure simulated here.
    assert len(registry.counters) >= 1


def test_batch_defaults_to_strict_and_does_not_hide_errors():
    registry = TokenCounterRegistry(cache=TokenCounterCache())
    registry.counters = {"fake": _FakeWorkingCounter()}

    with pytest.raises(ValueError, match="Unknown provider"):
        registry.count_batch(
            [{"model": "fake-model", "text": "hello", "provider": "missing"}]
        )

    results = registry.count_batch(
        [{"model": "fake-model", "text": "hello", "provider": "missing"}],
        strict=False,
    )
    assert results[0].input_tokens == 0
    assert results[0].source == "error"


def test_cache_preserves_source_and_provider_metadata():
    cache = TokenCounterCache()
    registry = TokenCounterRegistry(cache=cache)
    registry.counters = {"fake": _FakeWorkingCounter()}

    first = registry.count_tokens("fake-model", "hello world", provider="fake")
    second = registry.count_tokens("fake-model", "hello world", provider="fake")

    assert first.cached is False
    assert second.cached is True
    assert second.input_tokens == first.input_tokens
    assert second.source == first.source == "local"
    assert second.provider == first.provider == "fake"
    assert second.latency_ms >= 0


def test_cache_is_scoped_by_provider():
    cache = TokenCounterCache()
    cache.set("same-model", "same text", 1, provider="provider-a")
    assert cache.get("same-model", "same text", provider="provider-a") == 1
    assert cache.get("same-model", "same text", provider="provider-b") is None


def test_new_openai_families_route_to_openai():
    registry = TokenCounterRegistry(cache=TokenCounterCache())
    sentinel = object()
    registry.get_counter = lambda provider: sentinel if provider == "openai" else None

    for model in (
        "gpt-5",
        "gpt-4.1",
        "o1-preview",
        "o3-mini",
        "openai/o3-mini",
        "openai/gpt-5",
    ):
        assert registry._auto_detect_counter(model) is sentinel
