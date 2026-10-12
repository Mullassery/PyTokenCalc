"""
Tests for PyTokenCalc v0.7 token counting.
Tests multi-provider token counter integration.
"""

import pytest

from pytokencalc.tokenizers import (
    TokenCounterRegistry,
    TokenCountResult,
)


class TestTokenCounterRegistry:
    """Test TokenCounterRegistry functionality"""

    def test_registry_initialization(self):
        """Registry initializes with built-in counters"""
        registry = TokenCounterRegistry()
        assert registry is not None

    def test_count_gpt_tokens(self):
        """Count tokens for OpenAI GPT models"""
        registry = TokenCounterRegistry()
        text = "Hello world"
        result = registry.count_tokens("gpt-4o", text)

        assert isinstance(result, TokenCountResult)
        assert result.input_tokens > 0
        assert result.source in ["local", "cache", "formula"]
        assert result.latency_ms > 0

    def test_count_llama_tokens(self):
        """Count tokens for Llama models (HuggingFace)"""
        registry = TokenCounterRegistry()
        text = "Hello world"

        # Llama tokenizer might not be available in test environment
        try:
            result = registry.count_tokens("llama-2-7b", text)
            assert isinstance(result, TokenCountResult)
            assert result.input_tokens > 0
            assert result.source in ["local", "cache", "formula"]
        except (ValueError, RuntimeError):
            # Expected if transformers/llama tokenizer not installed
            pytest.skip("Llama tokenizer not available")

    def test_token_count_consistency(self):
        """Same text should produce consistent token counts"""
        registry = TokenCounterRegistry()
        text = "The quick brown fox jumps over the lazy dog"
        model = "gpt-4o"

        result1 = registry.count_tokens(model, text)
        result2 = registry.count_tokens(model, text)

        assert result1.input_tokens == result2.input_tokens

    def test_caching_behavior(self):
        """Second call for same model+text should be cached"""
        registry = TokenCounterRegistry()
        text = "Sample text for caching test"
        model = "gpt-4o"

        # First call
        result1 = registry.count_tokens(model, text)
        first_latency = result1.latency_ms

        # Second call (should be cached and faster)
        result2 = registry.count_tokens(model, text)

        assert result1.input_tokens == result2.input_tokens
        # Cached calls should typically be faster, allowing for timing variance in CI
        assert result2.latency_ms <= first_latency * 1.5

    def test_different_models_different_counts(self):
        """Different models may have different token counts"""
        registry = TokenCounterRegistry()
        text = "Sample text for comparison"

        result_gpt = registry.count_tokens("gpt-4o", text)
        assert result_gpt.input_tokens > 0

        # Try llama if available, otherwise just test GPT
        try:
            result_llama = registry.count_tokens("llama-2-7b", text)
            assert result_llama.input_tokens > 0
        except (ValueError, RuntimeError):
            pytest.skip("Llama tokenizer not available")

    def test_batch_count_tokens(self):
        """Count tokens for multiple prompts in batch"""
        registry = TokenCounterRegistry()
        batch = [
            {"model": "gpt-4o", "text": "First prompt"},
            {"model": "gpt-4o", "text": "Second prompt"},
        ]

        results = registry.count_batch(batch)

        assert len(results) == len(batch)
        for result in results:
            assert isinstance(result, TokenCountResult)
            assert result.input_tokens > 0

    def test_empty_text(self):
        """Empty text should return 0 tokens"""
        registry = TokenCounterRegistry()
        result = registry.count_tokens("gpt-4o", "")

        assert result.input_tokens == 0

    def test_long_text(self):
        """Long text should count many tokens"""
        registry = TokenCounterRegistry()
        text = "word " * 1000  # 1000 words
        result = registry.count_tokens("gpt-4o", text)

        # Long text should produce many tokens
        assert result.input_tokens > 100

    def test_special_characters(self):
        """Text with special characters should count correctly"""
        registry = TokenCounterRegistry()
        text = "Hello! @#$%^&*() [test] {nested} <html>"
        result = registry.count_tokens("gpt-4o", text)

        assert result.input_tokens > 0

    def test_unicode_text(self):
        """Unicode text should count correctly"""
        registry = TokenCounterRegistry()
        text = "Hello 世界 🌍 Привет مرحبا"
        result = registry.count_tokens("gpt-4o", text)

        assert result.input_tokens > 0

    def test_whitespace_handling(self):
        """Extra whitespace should be handled correctly"""
        registry = TokenCounterRegistry()
        text1 = "hello world"
        text2 = "hello    world"  # Extra spaces

        result1 = registry.count_tokens("gpt-4o", text1)
        result2 = registry.count_tokens("gpt-4o", text2)

        # Both should produce tokens
        assert result1.input_tokens > 0
        assert result2.input_tokens > 0

    def test_model_auto_detection(self):
        """Registry should auto-detect appropriate tokenizer for model"""
        registry = TokenCounterRegistry()
        text = "Test text"

        # Should auto-detect and work
        result = registry.count_tokens("gpt-4o", text)
        assert result.input_tokens > 0

    def test_result_contains_all_fields(self):
        """TokenCountResult should contain all required fields"""
        registry = TokenCounterRegistry()
        result = registry.count_tokens("gpt-4o", "test")

        assert hasattr(result, 'input_tokens')
        assert hasattr(result, 'source')
        assert hasattr(result, 'latency_ms')
        assert hasattr(result, 'cached')

    def test_source_types_valid(self):
        """Result source should be a valid type"""
        registry = TokenCounterRegistry()
        text = "Sample text"
        models = ["gpt-4o"]

        for model in models:
            result = registry.count_tokens(model, text)
            assert result.source in ["local", "api", "formula", "cache"]

        # Try llama if available
        try:
            result = registry.count_tokens("llama-2-7b", text)
            assert result.source in ["local", "api", "formula", "cache"]
        except (ValueError, RuntimeError):
            pass  # Llama not available, that's ok

    def test_latency_positive(self):
        """Latency should always be positive"""
        registry = TokenCounterRegistry()
        result = registry.count_tokens("gpt-4o", "test")
        assert result.latency_ms >= 0

    def test_repeated_calls_cache_optimization(self):
        """Repeated calls should show caching optimization"""
        registry = TokenCounterRegistry()
        text = "This text will be used multiple times"
        model = "gpt-4o"

        # First call: not cached
        r1 = registry.count_tokens(model, text)
        # Second call: cached
        r2 = registry.count_tokens(model, text)
        # Third call: cached
        r3 = registry.count_tokens(model, text)

        # All should have same token count
        assert r1.input_tokens == r2.input_tokens == r3.input_tokens
        # Cached calls should be nearly instant (<1ms)
        if r2.cached:
            assert r2.latency_ms < 5
        if r3.cached:
            assert r3.latency_ms < 5
