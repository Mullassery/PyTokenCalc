"""
Token counter registry with intelligent routing.
Routes to correct tokenizer based on model/provider.
"""

from typing import Optional, Dict, List, Any
import logging

from .base import TokenCounter, TokenCountResult
from .openai_counter import OpenAITokenCounter
from .huggingface_counter import HuggingFaceTokenCounter
from .anthropic_counter import AnthropicTokenCounter
from .google_counter import GoogleTokenCounter
from .cohere_counter import CohereTokenCounter
from .azure_openai_counter import AzureOpenAITokenCounter
from .opensource_counter import OpenSourceTokenCounter
from .ollama_counter import OllamaTokenCounter

logger = logging.getLogger(__name__)


class TokenCounterRegistry:
    """
    Registry of token counters for different providers.
    Intelligently routes to correct tokenizer based on model ID.
    """

    def __init__(self):
        self.counters: Dict[str, TokenCounter] = {}
        self._register_default_counters()

    def _register_default_counters(self):
        """Register built-in token counters"""
        # Try to register each counter; skip if dependency not available
        try:
            self.register("openai", OpenAITokenCounter())
            logger.info("Registered OpenAI token counter (tiktoken)")
        except ImportError as e:
            logger.warning(f"OpenAI counter unavailable: {e}")

        try:
            self.register("huggingface", HuggingFaceTokenCounter())
            logger.info("Registered HuggingFace token counter (transformers)")
        except ImportError as e:
            logger.warning(f"HuggingFace counter unavailable: {e}")

        try:
            self.register("anthropic", AnthropicTokenCounter())
            logger.info("Registered Anthropic token counter")
        except ImportError as e:
            logger.warning(f"Anthropic counter unavailable: {e}")

        try:
            self.register("google", GoogleTokenCounter())
            logger.info("Registered Google token counter")
        except ImportError as e:
            logger.warning(f"Google counter unavailable: {e}")

        try:
            self.register("cohere", CohereTokenCounter())
            logger.info("Registered Cohere token counter")
        except ImportError as e:
            logger.warning(f"Cohere counter unavailable: {e}")

        try:
            self.register("azure", AzureOpenAITokenCounter())
            logger.info("Registered Azure OpenAI token counter")
        except ImportError as e:
            logger.warning(f"Azure OpenAI counter unavailable: {e}")

        try:
            self.register("opensource", OpenSourceTokenCounter())
            logger.info("Registered open-source model token counter")
        except ImportError as e:
            logger.warning(f"Open-source counter unavailable: {e}")

        try:
            self.register("ollama", OllamaTokenCounter())
            logger.info("Registered Ollama token counter")
        except (ImportError, RuntimeError) as e:
            logger.warning(f"Ollama counter unavailable: {e}")

    def register(self, provider: str, counter: TokenCounter):
        """Register a new token counter"""
        self.counters[provider.lower()] = counter
        logger.info(f"Registered token counter: {provider}")

    def get_counter(self, provider: str) -> Optional[TokenCounter]:
        """Get counter by provider name"""
        return self.counters.get(provider.lower())

    def _auto_detect_counter(self, model: str) -> Optional[TokenCounter]:
        """Auto-detect which counter to use based on model ID"""
        model_lower = model.lower()

        # OpenAI models
        if any(x in model_lower for x in ["gpt-4", "gpt-3.5", "text-davinci", "text-embedding"]):
            return self.get_counter("openai")

        # Anthropic Claude models
        if "claude" in model_lower:
            return self.get_counter("anthropic")

        # Google Gemini models
        if "gemini" in model_lower:
            return self.get_counter("google")

        # Cohere models
        if "command" in model_lower:
            return self.get_counter("cohere")

        # Azure OpenAI models
        if "gpt-35" in model_lower or ("gpt-4" in model_lower and "azure" in model_lower):
            return self.get_counter("azure")

        # Ollama models (local inference)
        if "ollama" in model_lower or any(x in model_lower for x in
                                          ["llama2", "neural-chat", "dolphin", "openchat", "openhermes", "wizardlm"]):
            ollama_counter = self.get_counter("ollama")
            if ollama_counter:
                return ollama_counter

        # Open-source models: DeepSeek, Falcon, PALM, Llama, Mistral, etc.
        if any(x in model_lower for x in ["deepseek", "falcon", "text-bison", "code-bison",
                                            "llama", "mistral", "qwen", "mixtral"]):
            return self.get_counter("opensource")

        # Default to open-source counter
        return self.get_counter("opensource")

    def count_tokens(
        self,
        model: str,
        text: str,
        provider: Optional[str] = None,
    ) -> TokenCountResult:
        """
        Count tokens for text input.

        Args:
            model: Model ID (e.g., 'gpt-4o', 'claude-3-5-sonnet', 'llama-70b')
            text: Text to tokenize
            provider: Optional provider hint (e.g., 'openai', 'huggingface')

        Returns:
            TokenCountResult with token count and metadata

        Raises:
            ValueError: If model cannot be tokenized
            ImportError: If required tokenizer library not installed
        """
        # Resolve counter
        counter = None

        if provider:
            counter = self.get_counter(provider)
            if not counter:
                raise ValueError(f"Unknown provider: {provider}")
        else:
            counter = self._auto_detect_counter(model)

        if not counter:
            raise ValueError(
                f"No token counter available for model: {model}. "
                f"Available counters: {list(self.counters.keys())}"
            )

        # Count tokens
        try:
            result = counter.count(text, model)
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to count tokens for {model}: {e}")

    def count_batch(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[TokenCountResult]:
        """
        Count tokens for multiple requests.

        Each request: {"model": "...", "text": "...", "provider": "..."}
        """
        results = []

        for req in requests:
            model = req.get("model")
            text = req.get("text", "")
            provider = req.get("provider")

            try:
                result = self.count_tokens(model, text, provider)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to count tokens for {model}: {e}")
                results.append(
                    TokenCountResult(
                        input_tokens=0,
                        provider=provider or "unknown",
                        model=model or "unknown",
                        source="error",
                    )
                )

        return results

    def list_providers(self) -> List[str]:
        """List registered providers"""
        return list(self.counters.keys())

    def list_models(self, provider: Optional[str] = None) -> List[str]:
        """List supported models (all or for specific provider)"""
        if provider:
            counter = self.get_counter(provider)
            if counter:
                return counter.supported_models
            return []

        # All models from all counters
        models = []
        for counter in self.counters.values():
            models.extend(counter.supported_models)
        return models

    def validate_platform_consistency(self, results: List[TokenCountResult]) -> Dict[str, Any]:
        """Validate that results don't accidentally mix platforms

        Same model on different platforms (Ollama, GCP, Azure) may have
        different token counts. This validator warns when results might be
        accidentally mixed or aggregated.

        Returns:
            {
                "consistent": bool,
                "providers": [list of providers],
                "platforms": [list of platforms],
                "warnings": [list of warnings if mixing detected]
            }
        """
        if not results:
            return {
                "consistent": True,
                "providers": [],
                "platforms": [],
                "warnings": [],
            }

        providers = set(r.provider for r in results)
        models = set(r.model for r in results)
        platforms = set((r.provider, r.platform or r.provider) for r in results)

        warnings = []

        # Warn if same model appears on different platforms
        for model in models:
            model_results = [r for r in results if r.model == model]
            model_providers = set(r.provider for r in model_results)

            if len(model_providers) > 1:
                warnings.append(
                    f"Model '{model}' appears on multiple platforms: {model_providers}. "
                    f"Token counts may differ. Keep results separate and don't aggregate."
                )

        return {
            "consistent": len(warnings) == 0,
            "providers": sorted(list(providers)),
            "platforms": sorted(list(str(p) for p in platforms)),
            "warnings": warnings,
        }

    def get_info(self) -> Dict[str, Any]:
        """Get info about all registered counters"""
        return {
            "providers": {
                name: counter.get_tokenizer_info()
                for name, counter in self.counters.items()
            },
            "total_providers": len(self.counters),
        }


# Global registry instance
_global_registry: Optional[TokenCounterRegistry] = None


def get_global_registry() -> TokenCounterRegistry:
    """Get or create global token counter registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = TokenCounterRegistry()
    return _global_registry


def count_tokens(
    model: str,
    text: str,
    provider: Optional[str] = None,
) -> TokenCountResult:
    """Convenience function using global registry"""
    return get_global_registry().count_tokens(model, text, provider)
