"""
Token counter registry with intelligent routing.
Routes to correct tokenizer based on model/provider.
"""

import logging
from typing import Any, Dict, List, Optional

from .anthropic_counter import AnthropicTokenCounter
from .azure_openai_counter import AzureOpenAITokenCounter
from .base import TokenCounter, TokenCountResult
from .cache import TokenCounterCache, get_global_cache
from .cohere_counter import CohereTokenCounter
from .custom_provider_counter import get_custom_provider, list_custom_providers
from .google_counter import GoogleTokenCounter
from .huggingface_counter import HuggingFaceTokenCounter
from .ollama_counter import OllamaTokenCounter
from .openai_counter import OpenAITokenCounter
from .opensource_counter import OpenSourceTokenCounter

logger = logging.getLogger(__name__)


class TokenCounterRegistry:
    """
    Registry of token counters for different providers.
    Intelligently routes to correct tokenizer based on model ID.
    """

    def __init__(self, cache: Optional[TokenCounterCache] = None):
        self.counters: Dict[str, TokenCounter] = {}
        self.cache = cache if cache is not None else TokenCounterCache()
        self._register_default_counters()

    def _register_default_counters(self):
        """Register built-in token counters.

        Each counter is registered independently: a construction failure for
        one provider (missing optional dependency, or something like
        OpenAITokenCounter's eager tiktoken encoding download hitting a
        network hiccup and raising RuntimeError) must not prevent the other
        providers from being registered, and must not prevent
        TokenCounterRegistry.__init__ from completing. We therefore catch
        `Exception` broadly here (not just `ImportError`) around each
        individual registration -- the registry's job is to register what it
        can and log/skip what it can't, not to crash entirely because one
        provider's constructor blew up.
        """
        try:
            self.register("openai", OpenAITokenCounter())
            logger.info("Registered OpenAI token counter (tiktoken)")
        except Exception as e:
            logger.warning(f"OpenAI counter unavailable: {e}")

        try:
            self.register("huggingface", HuggingFaceTokenCounter())
            logger.info("Registered HuggingFace token counter (transformers)")
        except Exception as e:
            logger.warning(f"HuggingFace counter unavailable: {e}")

        try:
            self.register("anthropic", AnthropicTokenCounter())
            logger.info("Registered Anthropic token counter")
        except Exception as e:
            logger.warning(f"Anthropic counter unavailable: {e}")

        try:
            self.register("google", GoogleTokenCounter())
            logger.info("Registered Google token counter")
        except Exception as e:
            logger.warning(f"Google counter unavailable: {e}")

        try:
            self.register("cohere", CohereTokenCounter())
            logger.info("Registered Cohere token counter")
        except Exception as e:
            logger.warning(f"Cohere counter unavailable: {e}")

        try:
            self.register("azure", AzureOpenAITokenCounter())
            logger.info("Registered Azure OpenAI token counter")
        except Exception as e:
            logger.warning(f"Azure OpenAI counter unavailable: {e}")

        try:
            self.register("opensource", OpenSourceTokenCounter())
            logger.info("Registered open-source model token counter")
        except Exception as e:
            logger.warning(f"Open-source counter unavailable: {e}")

        try:
            self.register("ollama", OllamaTokenCounter())
            logger.info("Registered Ollama token counter")
        except Exception as e:
            logger.warning(f"Ollama counter unavailable: {e}")

    def register(self, provider: str, counter: TokenCounter):
        """Register a new token counter"""
        self.counters[provider.lower()] = counter
        logger.info(f"Registered token counter: {provider}")

    def get_counter(self, provider: str) -> Optional[TokenCounter]:
        """Get counter by provider name

        Checks built-in providers first, then custom providers.
        """
        # Check built-in providers
        counter = self.counters.get(provider.lower())
        if counter:
            return counter

        # Check custom providers
        custom = get_custom_provider(provider.lower())
        if custom:
            return custom

        return None

    def _auto_detect_counter(self, model: str) -> Optional[TokenCounter]:
        """Auto-detect which counter to use based on model ID"""
        model_lower = model.lower()
        # Also inspect the final segment so provider-prefixed IDs such as
        # "openai/o3-mini" route correctly.
        model_name = model_lower.rsplit("/", 1)[-1]

        # Azure OpenAI models (must be checked before the generic OpenAI
        # patterns below, otherwise an Azure gpt-4* deployment matches
        # "gpt-4" and never reaches the azure branch).
        if "gpt-35" in model_lower or (
            "azure" in model_lower
            and any(x in model_name for x in ("gpt-", "o1", "o3", "o4"))
        ):
            return self.get_counter("azure")

        # OpenAI models (include newer GPT families)
        openai_patterns = [
            "gpt-4",
            "gpt-3.5",
            "text-davinci",
            "text-embedding",
            "gpt-5",
            "gpt-4.1",
            "gpt-4.5",
        ]
        if any(x in model_name for x in openai_patterns) or model_name.startswith(
            ("o1", "o3", "o4")
        ):
            return self.get_counter("openai")

        # Anthropic Claude models
        if "claude" in model_name:
            counter = self.get_counter("anthropic")
            if counter:
                return counter

        # Google Gemini models
        if "gemini" in model_name:
            counter = self.get_counter("google")
            if counter:
                return counter

        # Cohere models
        if "command" in model_name:
            counter = self.get_counter("cohere")
            if counter:
                return counter

        # Ollama models (local inference)
        if "ollama" in model_name or any(x in model_name for x in
                                          ["llama2", "neural-chat", "dolphin", "openchat", "openhermes", "wizardlm"]):
            ollama_counter = self.get_counter("ollama")
            if ollama_counter:
                return ollama_counter

        # Open-source models: DeepSeek, Falcon, PALM, Llama, Mistral, etc.
        if any(x in model_name for x in ["deepseek", "falcon", "text-bison", "code-bison",
                                            "llama", "mistral", "qwen", "mixtral"]):
            counter = self.get_counter("opensource")
            if counter:
                return counter

        # Default to the open-source counter (matches historical behavior)
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

        # Count tokens (with caching)
        try:
            if self.cache is not None:
                cached = self.cache.get_result(
                    model, text, provider=counter.provider_name
                )
                if cached is not None:
                    return cached
            result = counter.count(text, model)
            try:
                if self.cache is not None and result.input_tokens >= 0:
                    result.cached = False
                    self.cache.set_result(
                        model, text, result, provider=counter.provider_name
                    )
            except Exception:
                pass
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to count tokens for {model}: {e}") from e

    def count_vision(
        self,
        model: str,
        text: str,
        num_images: int = 1,
        provider: Optional[str] = None,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> TokenCountResult:
        """
        Count tokens for text + vision (image) input.

        Args:
            model: Model ID (e.g., 'gpt-4o', 'gpt-4-vision')
            text: Text to tokenize
            num_images: Number of images included
            provider: Optional provider hint (e.g., 'openai')
            image_path: Optional local path to an image (provider-specific)
            image_url: Optional URL to an image (provider-specific)

        Returns:
            TokenCountResult with input/image token counts

        Raises:
            ValueError: If model cannot be tokenized
        """
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

        try:
            return counter.count_vision(
                text,
                model,
                image_path=image_path,
                image_url=image_url,
                num_images=num_images,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to count vision tokens for {model}: {e}") from e

    def count_batch(
        self,
        requests: List[Dict[str, Any]],
        strict: bool = True,
    ) -> List[TokenCountResult]:
        """
        Count tokens for multiple requests.

        Each request: {"model": "...", "text": "...", "provider": "..."}

        Set ``strict=False`` to return a zero-token error placeholder for
        failed requests instead of raising. The placeholder has
        ``source="error"`` so callers can detect it.
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
                if strict:
                    raise
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
        """List registered providers (built-in + custom)"""
        return list(self.counters.keys()) + list_custom_providers()

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

        providers = {r.provider for r in results}
        models = {r.model for r in results}
        platforms = {(r.provider, r.platform or r.provider) for r in results}

        warnings = []

        # Warn if same model appears on different platforms
        for model in models:
            model_results = [r for r in results if r.model == model]
            model_providers = {r.provider for r in model_results}

            if len(model_providers) > 1:
                warnings.append(
                    f"Model '{model}' appears on multiple platforms: {model_providers}. "
                    f"Token counts may differ. Keep results separate and don't aggregate."
                )

        return {
            "consistent": len(warnings) == 0,
            "providers": sorted(providers),
            "platforms": sorted(str(p) for p in platforms),
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
        _global_registry = TokenCounterRegistry(cache=get_global_cache())
    return _global_registry


def count_tokens(
    model: str,
    text: str,
    provider: Optional[str] = None,
) -> TokenCountResult:
    """Convenience function using global registry"""
    return get_global_registry().count_tokens(model, text, provider)
