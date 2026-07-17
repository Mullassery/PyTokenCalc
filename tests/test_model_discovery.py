"""
Tests for model discovery and lookup system.
"""

import pytest
from pytokencalc.model_discovery import ModelDiscovery


class TestModelPatternMatching:
    """Test model-to-provider pattern matching"""

    def test_openai_model_patterns(self):
        """Recognize OpenAI models by pattern"""
        providers, message = ModelDiscovery.suggest_provider("gpt-4o")
        assert "openai" in providers

        providers, message = ModelDiscovery.suggest_provider("gpt-3.5-turbo")
        assert "openai" in providers

    def test_anthropic_model_patterns(self):
        """Recognize Anthropic Claude models"""
        providers, message = ModelDiscovery.suggest_provider("claude-3-opus")
        assert "anthropic" in providers

        providers, message = ModelDiscovery.suggest_provider("claude-4-fable")
        assert "anthropic" in providers

    def test_google_model_patterns(self):
        """Recognize Google Gemini models"""
        providers, message = ModelDiscovery.suggest_provider("gemini-pro")
        assert "google" in providers

    def test_cohere_model_patterns(self):
        """Recognize Cohere Command models"""
        providers, message = ModelDiscovery.suggest_provider("command-r")
        assert "cohere" in providers

    def test_llama_model_patterns(self):
        """Recognize Llama models - multiple providers"""
        providers, message = ModelDiscovery.suggest_provider("llama-2-7b")
        assert len(providers) > 1, "Llama should work on multiple providers"
        assert "ollama" in providers

    def test_mistral_model_patterns(self):
        """Recognize Mistral models"""
        providers, message = ModelDiscovery.suggest_provider("mistral-7b")
        assert "ollama" in providers or "huggingface" in providers

    def test_unknown_model(self):
        """Unknown models return None"""
        providers, message = ModelDiscovery.suggest_provider("unknown-xyz-model")
        assert providers is None


class TestModelAliases:
    """Test model name aliasing"""

    def test_alias_resolution(self):
        """Common aliases should resolve"""
        providers, message = ModelDiscovery.suggest_provider("gpt4")
        assert providers is not None, "gpt4 alias should resolve to gpt-4"

        providers, message = ModelDiscovery.suggest_provider("claude3")
        assert "anthropic" in providers

    def test_alias_in_lookup(self):
        """Lookup should include aliases"""
        result = ModelDiscovery.lookup_model("gpt4")
        assert "gpt-4" in result["aliases"]


class TestModelLookup:
    """Test full model lookup functionality"""

    def test_lookup_known_model(self):
        """Lookup should find known models"""
        result = ModelDiscovery.lookup_model("gpt-4o")

        assert result["model"] == "gpt-4o"
        assert result["status"] in ["found", "suggested"]
        assert "openai" in result["providers"]

    def test_lookup_unknown_model(self):
        """Lookup should handle unknown models gracefully"""
        result = ModelDiscovery.lookup_model("unknown-model-xyz")

        assert result["model"] == "unknown-model-xyz"
        assert result["status"] == "not_found"
        assert len(result["suggestions"]) > 0

    def test_lookup_includes_setup_instructions(self):
        """Lookup should include setup instructions"""
        result = ModelDiscovery.lookup_model("llama-2-7b")

        assert result["status"] in ["found", "suggested"]
        assert len(result["suggestions"]) > 0
        # Should have instructions like "ollama pull"
        instructions_text = " ".join(result["suggestions"])
        assert "ollama" in instructions_text.lower()

    def test_lookup_returns_multiple_providers(self):
        """Lookup can return multiple providers for same model"""
        result = ModelDiscovery.lookup_model("llama-2-7b")

        # Llama works on multiple platforms
        assert len(result["providers"]) > 1


class TestProviderDiscovery:
    """Test provider model discovery"""

    def test_discover_openai_models(self):
        """Can discover OpenAI models"""
        discovery = ModelDiscovery.discover_models_by_provider("openai")

        assert discovery["provider"] == "openai"
        assert "method" in discovery

    def test_discover_ollama_models(self):
        """Can discover Ollama models"""
        discovery = ModelDiscovery.discover_models_by_provider("ollama")

        assert discovery["provider"] == "ollama"
        assert "ollama" in discovery.get("command", "").lower()

    def test_discover_unknown_provider(self):
        """Unknown providers return generic info"""
        discovery = ModelDiscovery.discover_models_by_provider("unknown-provider")

        assert "note" in discovery or "method" in discovery


class TestDiscoveryReport:
    """Test human-readable discovery reports"""

    def test_report_known_model(self):
        """Report for known model should be helpful"""
        report = ModelDiscovery.get_discovery_report("gpt-4o")

        assert "gpt-4o" in report
        assert "openai" in report.lower() or "OPENAI" in report
        assert ("FOUND" in report or "SUGGESTED" in report)

    def test_report_unknown_model(self):
        """Report for unknown model should suggest alternatives"""
        report = ModelDiscovery.get_discovery_report("completely-unknown-model-xyz")

        assert "completely-unknown-model-xyz" in report
        assert "NOT FOUND" in report
        # Should suggest alternatives
        assert "Options" in report or "Check" in report

    def test_report_formatting(self):
        """Report should be well-formatted"""
        report = ModelDiscovery.get_discovery_report("llama-2-7b")

        # Should have clear sections
        assert "Model Discovery Report" in report
        assert "=" in report  # Header separator
        assert "-" in report  # Section separator

    def test_report_includes_instructions(self):
        """Report should include setup instructions"""
        report = ModelDiscovery.get_discovery_report("llama-2-7b")

        # For Ollama, should mention how to setup
        assert ("ollama" in report.lower() or "custom" in report.lower())


class TestDiscoveryIntegration:
    """Test discovery with registry"""

    def test_lookup_with_registry(self):
        """Lookup can check registry for registered providers"""
        from pytokencalc.tokenizers import TokenCounterRegistry

        registry = TokenCounterRegistry()
        result = ModelDiscovery.lookup_model("gpt-4o", registry)

        # Should find in OpenAI counter
        assert "openai" in result["providers"]

    def test_discovery_catches_typos(self):
        """Discovery should suggest corrections for common typos"""
        # "gpt4" might be typo for "gpt-4"
        result = ModelDiscovery.lookup_model("gpt4")

        # Should either resolve or suggest
        assert result["status"] in ["found", "suggested", "unknown"]

    def test_multi_provider_model_handling(self):
        """Models available on multiple providers should be clear"""
        result = ModelDiscovery.lookup_model("llama-2-7b")

        # Should list all providers
        providers = result["providers"]
        assert len(providers) > 0

        # Report should clarify multiple options
        report = ModelDiscovery.get_discovery_report("llama-2-7b", registry=None)
        # Should show setup for multiple providers
        assert report.count("://") > 0 or report.count("$") > 0
