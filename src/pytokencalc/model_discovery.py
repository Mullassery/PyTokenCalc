"""
Model Discovery and Lookup System

When users try to count tokens for an unknown model/provider,
PyTokenCalc discovers where that model can be found and suggests providers.

Supports dynamic lookup of:
- New models just released
- Providers we haven't explicitly coded
- Custom/proprietary models users are using
- Models across all major platforms

Architecture: Progressive discovery
1. Check built-in providers
2. Check custom registered providers
3. Attempt dynamic lookup via provider APIs
4. Suggest providers based on model naming patterns
5. Help users find/setup the right provider
"""

from typing import List, Dict, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class ModelDiscovery:
    """Discover models and providers dynamically

    Helps users find which provider supports a given model,
    even if that provider isn't explicitly coded in PyTokenCalc.
    """

    # Model naming patterns -> likely provider
    PROVIDER_PATTERNS = {
        r"^(gpt-|text-davinci|text-embedding)": "openai",
        r"^claude-": "anthropic",
        r"^gemini-": "google",
        r"^command": "cohere",
        r"^(llama|llama2|llama-2)": ["ollama", "huggingface", "runpod", "together-ai"],
        r"^mistral": ["ollama", "huggingface", "together-ai", "replicate"],
        r"^(openchat|openhermes|dolphin)": ["ollama", "huggingface", "replicate"],
        r"^(neural-chat|orca)": ["huggingface", "ollama", "together-ai"],
        r"^(phi|zephyr|aya)": ["huggingface", "ollama"],
        r"^meta-llama": "huggingface",
        r"^mistralai": "huggingface",
        r"^deepseek": ["ollama", "huggingface", "together-ai"],
        r"^qwen": ["huggingface", "ollama"],
        r"^falcon": ["huggingface", "ollama"],
        r"^nous-hermes": ["huggingface", "together-ai"],
        # Cloud providers
        r"^palm-|^bison": "google",
        r"^(replicate|r8)": "replicate",
        r"^together-": "together-ai",
        r"^hf-": "huggingface",
    }

    # Known model aliases
    MODEL_ALIASES = {
        "gpt4": "gpt-4",
        "gpt3": "gpt-3.5-turbo",
        "claude3": "claude-3-sonnet",
        "claude-opus": "claude-3-opus",
        "llama": "llama-2-7b",
        "mistral": "mistral-7b",
        "code-llama": "codellama",
    }

    @staticmethod
    def suggest_provider(model: str) -> Tuple[Optional[List[str]], str]:
        """Suggest provider(s) for a model based on naming pattern

        Returns:
            (providers_list, confidence_message)
            e.g., (["openai"], "Likely OpenAI based on model name")
        """
        model_lower = model.lower()

        # Check aliases first
        if model_lower in ModelDiscovery.MODEL_ALIASES:
            actual_model = ModelDiscovery.MODEL_ALIASES[model_lower]
            return ModelDiscovery.suggest_provider(actual_model)

        # Check patterns
        for pattern, providers in ModelDiscovery.PROVIDER_PATTERNS.items():
            if re.match(pattern, model_lower):
                providers_list = providers if isinstance(providers, list) else [providers]
                confidence = f"High confidence: '{model}' matches '{pattern}' pattern"
                return (providers_list, confidence)

        # Unknown model
        return (None, f"Unknown model '{model}'. Try: ModelDiscovery.lookup_model('{model}')")

    @staticmethod
    def lookup_model(model: str, registry=None) -> Dict[str, any]:
        """Lookup model across all providers

        Returns metadata about where model can be found:
        {
            "model": "llama-2-7b",
            "providers": ["ollama", "huggingface"],
            "suggestions": ["Try registering with Ollama", "Available on HuggingFace"],
            "status": "found" or "not_found"
        }
        """
        model_lower = model.lower()

        result = {
            "model": model,
            "providers": [],
            "suggestions": [],
            "status": "unknown",
            "aliases": [],
        }

        # Check aliases
        if model_lower in ModelDiscovery.MODEL_ALIASES:
            result["aliases"].append(ModelDiscovery.MODEL_ALIASES[model_lower])

        # Try provider pattern matching
        suggested, message = ModelDiscovery.suggest_provider(model)

        if suggested:
            result["providers"] = suggested
            result["suggestions"].append(message)
            result["status"] = "suggested"

            # Add setup instructions
            for provider in suggested:
                result["suggestions"].extend(
                    ModelDiscovery._get_setup_instructions(provider, model)
                )

        # Try to find in registered providers (if registry provided)
        if registry:
            found_in = ModelDiscovery._search_in_registry(model, registry)
            if found_in:
                result["providers"].extend(found_in)
                result["status"] = "found"

        if not result["providers"]:
            result["status"] = "not_found"
            result["suggestions"].append(
                f"Model '{model}' not recognized. "
                f"Check provider documentation or register as custom provider."
            )

        return result

    @staticmethod
    def _search_in_registry(model: str, registry) -> List[str]:
        """Search for model in all registered providers"""
        found_in = []

        try:
            for provider_name in registry.list_providers():
                counter = registry.get_counter(provider_name)
                if counter and model in counter.supported_models:
                    found_in.append(provider_name)
        except Exception as e:
            logger.debug(f"Error searching registry: {e}")

        return found_in

    @staticmethod
    def _get_setup_instructions(provider: str, model: str) -> List[str]:
        """Get instructions for using model with provider"""
        instructions_map = {
            "openai": [
                "OpenAI: Get API key from https://platform.openai.com/",
                "Set OPENAI_API_KEY environment variable",
            ],
            "anthropic": [
                "Anthropic: Get API key from https://console.anthropic.com/",
                "Set ANTHROPIC_API_KEY environment variable",
            ],
            "google": [
                "Google: Get API key from https://makersuite.google.com/app/apikey",
                "Set GOOGLE_API_KEY environment variable",
            ],
            "ollama": [
                "Ollama: Install from https://ollama.ai/",
                f"Run: ollama pull {model}",
                "Then: ollama serve",
            ],
            "huggingface": [
                "HuggingFace: Get token from https://huggingface.co/settings/tokens",
                "Set HF_TOKEN environment variable",
                f"Model automatically downloads on first use: {model}",
            ],
            "replicate": [
                "Replicate: Get API token from https://replicate.com/account/api-tokens",
                "Set REPLICATE_API_TOKEN environment variable",
            ],
            "together-ai": [
                "Together AI: Get API key from https://www.together.ai/",
                "Set TOGETHER_API_KEY environment variable",
            ],
            "runpod": [
                "RunPod: Deploy model to runpod.io/console/pods",
                "Get serverless endpoint ID",
                "Use CustomProviderCounter to register endpoint",
            ],
        }

        return instructions_map.get(provider, [f"Setup {provider} provider for {model}"])

    @staticmethod
    def discover_models_by_provider(provider: str) -> Dict[str, any]:
        """Discover available models for a provider

        Returns:
        {
            "provider": "ollama",
            "models": ["llama-2-7b", "mistral-7b", ...],
            "count": 42,
            "note": "Models available via 'ollama list'"
        }
        """
        discovery_methods = {
            "openai": {
                "provider": "openai",
                "method": "API",
                "endpoint": "https://api.openai.com/v1/models",
                "docs": "https://platform.openai.com/docs/models",
            },
            "anthropic": {
                "provider": "anthropic",
                "method": "Docs",
                "docs": "https://docs.anthropic.com/claude/reference/getting-started-with-the-api",
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            },
            "google": {
                "provider": "google",
                "method": "Docs",
                "docs": "https://ai.google.dev/available-models",
            },
            "ollama": {
                "provider": "ollama",
                "method": "CLI",
                "command": "ollama list",
                "docs": "https://ollama.ai/library",
            },
            "huggingface": {
                "provider": "huggingface",
                "method": "API/Web",
                "endpoint": "https://huggingface.co/api/models",
                "docs": "https://huggingface.co/models",
            },
            "replicate": {
                "provider": "replicate",
                "method": "Web",
                "docs": "https://replicate.com/explore",
            },
        }

        return discovery_methods.get(provider, {
            "provider": provider,
            "method": "Unknown",
            "note": "Check provider documentation for available models",
        })

    @staticmethod
    def get_discovery_report(model: str, registry=None) -> str:
        """Get human-readable discovery report

        Example output:
        ```
        Model Discovery Report: "llama-2-7b"
        =====================================

        Suggested Providers:
        - Ollama (local inference)
          $ ollama pull llama-2-7b
          $ ollama serve

        - RunPod (serverless GPU)
          https://www.runpod.io/
          Use CustomProviderCounter to register endpoint

        - HuggingFace (inference API)
          https://huggingface.co/meta-llama/Llama-2-7b-hf
          Requires HF_TOKEN environment variable

        Not Sure? Try this:
        1. Which provider do you prefer? (local, cloud, serverless)
        2. Check provider documentation
        3. Register with PyTokenCalc using CustomProviderCounter
        ```
        """
        lookup = ModelDiscovery.lookup_model(model, registry)

        report = f"\nModel Discovery Report: \"{model}\"\n"
        report += "=" * 50 + "\n\n"

        if lookup["status"] == "found":
            report += f"✓ FOUND in: {', '.join(lookup['providers'])}\n\n"

        if lookup["status"] == "suggested":
            report += f"? SUGGESTED: {', '.join(lookup['providers'])}\n\n"

        if lookup["providers"]:
            report += "Setup Instructions:\n"
            report += "-" * 50 + "\n"
            for provider in lookup["providers"]:
                report += f"\n{provider.upper()}:\n"
                for instruction in ModelDiscovery._get_setup_instructions(provider, model):
                    report += f"  • {instruction}\n"

        if lookup["status"] == "not_found":
            report += "? MODEL NOT FOUND\n\n"
            report += "Options:\n"
            report += "  1. Check spelling: {}\n".format(
                ", ".join(lookup["aliases"]) if lookup["aliases"] else "no aliases found"
            )
            report += "  2. Use a custom provider: register with CustomProviderCounter\n"
            report += "  3. Check provider documentation for available models\n"

        report += "\n" + "=" * 50 + "\n"
        return report
