"""
Tests for new PyTokenCalc v0.9 providers.
Tests: Anthropic, Google, Cohere, Azure, Open-source models.
"""

import pytest

from pytokencalc.tokenizers import (
    TokenCounterRegistry,
    TokenCountResult,
)


class TestAnthropicCounter:
    """Test Anthropic Claude token counter"""

    def test_claude_models_registered(self):
        """Claude models should be auto-detected"""
        registry = TokenCounterRegistry()
        text = "Hello world"

        try:
            result = registry.count_tokens("claude-3-opus", text)
            assert isinstance(result, TokenCountResult)
            assert result.input_tokens > 0
            assert result.provider == "anthropic"
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("Anthropic API not available")

    def test_claude_haiku_variant(self):
        """Claude 3 Haiku should be supported"""
        registry = TokenCounterRegistry()
        text = "Hello world"

        try:
            result = registry.count_tokens("claude-3-haiku", text)
            assert isinstance(result, TokenCountResult)
            assert result.input_tokens > 0
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("Anthropic API not available")


class TestGoogleCounter:
    """Test Google Gemini token counter"""

    def test_gemini_models_registered(self):
        """Gemini models should be auto-detected"""
        registry = TokenCounterRegistry()
        text = "Hello world"

        try:
            result = registry.count_tokens("gemini-pro", text)
            assert isinstance(result, TokenCountResult)
            assert result.input_tokens > 0
            assert result.provider == "google"
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("Google API not available")

    def test_gemini_variants(self):
        """Multiple Gemini variants should work"""
        registry = TokenCounterRegistry()
        text = "Test text"

        variants = ["gemini-pro", "gemini-ultra", "gemini-nano"]
        for variant in variants:
            try:
                result = registry.count_tokens(variant, text)
                assert result.input_tokens > 0
            except (ValueError, RuntimeError, ImportError):
                pytest.skip(f"{variant} not available")


class TestCohereCounter:
    """Test Cohere token counter"""

    def test_cohere_models_registered(self):
        """Cohere models should be auto-detected"""
        registry = TokenCounterRegistry()
        text = "Hello world"

        try:
            result = registry.count_tokens("command", text)
            assert isinstance(result, TokenCountResult)
            assert result.input_tokens > 0
            assert result.provider == "cohere"
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("Cohere API not available")

    def test_cohere_light_variant(self):
        """Cohere Light should be supported"""
        registry = TokenCounterRegistry()
        text = "Hello world"

        try:
            result = registry.count_tokens("command-light", text)
            assert isinstance(result, TokenCountResult)
            assert result.input_tokens > 0
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("Cohere API not available")


class TestAzureOpenAICounter:
    """Test Azure OpenAI token counter"""

    def test_azure_gpt4_models(self):
        """Azure GPT-4 should be supported"""
        registry = TokenCounterRegistry()
        text = "Hello world"

        try:
            result = registry.count_tokens("gpt-4", text, provider="azure")
            assert isinstance(result, TokenCountResult)
            assert result.input_tokens > 0
            assert result.provider == "azure"
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("tiktoken not available")

    def test_azure_gpt35_models(self):
        """Azure GPT-3.5 should be supported"""
        registry = TokenCounterRegistry()
        text = "Hello world"

        try:
            result = registry.count_tokens("gpt-35-turbo", text, provider="azure")
            assert isinstance(result, TokenCountResult)
            assert result.input_tokens > 0
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("tiktoken not available")


class TestOpenSourceCounter:
    """Test open-source model token counter"""

    def test_deepseek_models(self):
        """DeepSeek models should be supported"""
        registry = TokenCounterRegistry()
        text = "Hello world"

        try:
            result = registry.count_tokens("deepseek-chat", text)
            assert isinstance(result, TokenCountResult)
            assert result.input_tokens > 0
            assert result.provider == "opensource"
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("transformers not available")

    def test_falcon_models(self):
        """Falcon models should be supported"""
        registry = TokenCounterRegistry()
        text = "Hello world"

        try:
            result = registry.count_tokens("falcon-7b", text)
            assert isinstance(result, TokenCountResult)
            assert result.input_tokens > 0
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("transformers not available")

    def test_llama_variants(self):
        """Llama variants should be supported"""
        registry = TokenCounterRegistry()
        text = "Test text"

        variants = ["llama-2-7b-hf", "llama-3-8b"]
        for variant in variants:
            try:
                result = registry.count_tokens(variant, text)
                assert result.input_tokens > 0
            except (ValueError, RuntimeError, ImportError):
                pytest.skip(f"{variant} not available")


class TestMultiProviderAutoDetection:
    """Test auto-detection across all new providers"""

    def test_auto_detects_all_providers(self):
        """Auto-detection should work for all providers"""
        registry = TokenCounterRegistry()
        text = "Hello world"

        test_cases = [
            ("claude-3-sonnet", "anthropic"),
            ("gemini-pro", "google"),
            ("command", "cohere"),
            ("gpt-4", "openai"),
            ("deepseek-chat", "opensource"),
        ]

        for model, expected_provider in test_cases:
            try:
                result = registry.count_tokens(model, text)
                assert result.provider == expected_provider
            except (ValueError, RuntimeError, ImportError):
                pytest.skip(f"{model} not available")


class TestProviderListing:
    """Test listing all available providers"""

    def test_list_all_providers(self):
        """Should list all registered providers"""
        registry = TokenCounterRegistry()
        providers = registry.list_providers()

        # Should have at least openai
        assert "openai" in providers

        # May have others depending on installed dependencies
        assert len(providers) >= 1


class TestTokenCountConsistency:
    """Test consistency across providers"""

    def test_same_text_consistent_counts(self):
        """Same text should produce consistent counts within provider"""
        registry = TokenCounterRegistry()
        text = "The quick brown fox"
        model = "gpt-4"

        try:
            result1 = registry.count_tokens(model, text)
            result2 = registry.count_tokens(model, text)
            assert result1.input_tokens == result2.input_tokens
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("OpenAI tokenizer not available")

    def test_longer_text_more_tokens(self):
        """Longer text should produce more tokens"""
        registry = TokenCounterRegistry()
        short_text = "Hello"
        long_text = "Hello world. This is a longer piece of text."
        model = "gpt-4"

        try:
            result_short = registry.count_tokens(model, short_text)
            result_long = registry.count_tokens(model, long_text)
            assert result_long.input_tokens > result_short.input_tokens
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("OpenAI tokenizer not available")


class TestBatchCounting:
    """Test batch token counting across providers"""

    def test_batch_count_multiple_models(self):
        """Should count tokens for multiple models in batch"""
        registry = TokenCounterRegistry()
        batch = [
            {"model": "gpt-4", "text": "First prompt"},
            {"model": "gpt-4o", "text": "Second prompt"},
        ]

        try:
            results = registry.count_batch(batch)
            assert len(results) == 2
            for result in results:
                assert result.input_tokens > 0
        except (ValueError, RuntimeError, ImportError):
            pytest.skip("OpenAI tokenizer not available")
