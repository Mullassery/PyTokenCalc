"""
Token counter registry with intelligent routing.
Routes to correct tokenizer based on model/provider.
"""

from typing import Optional, Dict, List, Any
import logging

from .base import TokenCounter, TokenCountResult
from .openai_counter import OpenAITokenCounter
from .huggingface_counter import HuggingFaceTokenCounter

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
        if any(x in model_lower for x in ["gpt-4", "gpt-3.5", "text-davinci"]):
            return self.get_counter("openai")

        # Llama models
        if any(x in model_lower for x in ["llama", "llama2", "llama3"]):
            return self.get_counter("huggingface")

        # Mistral models
        if "mistral" in model_lower:
            return self.get_counter("huggingface")

        # Qwen models
        if "qwen" in model_lower:
            return self.get_counter("huggingface")

        # Mixtral models
        if "mixtral" in model_lower:
            return self.get_counter("huggingface")

        # Default to HuggingFace (most permissive)
        return self.get_counter("huggingface")

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
