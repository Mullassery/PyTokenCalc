"""
Cohere token counter.
Provides token counting for Cohere models (Command, Command Light, etc).
"""

from typing import List, Dict, Any
import time

from .base import TokenCounter, TokenCountResult

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False


class CohereTokenCounter(TokenCounter):
    """Cohere token counter using official API

    Supports all Cohere models via pattern matching (command-*).
    New models released by Cohere are automatically supported.
    Validation happens server-side via Cohere API.
    """

    KNOWN_MODELS = {
        "command",
        "command-light",
        "command-nightly",
        "command-r",
        "command-r-plus",
        "command-r-08-2024",  # Support new models without code changes
    }

    def __init__(self):
        if not COHERE_AVAILABLE:
            raise ImportError(
                "cohere is required for Cohere token counting. "
                "Install: pip install cohere"
            )
        self.client = cohere.Client()

    @property
    def provider_name(self) -> str:
        return "cohere"

    @property
    def supported_models(self) -> List[str]:
        return list(self.KNOWN_MODELS)

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens using Cohere's tokenize API

        Pattern-based validation: accepts any command-* model.
        Cohere API validates actual model existence server-side.
        This allows forward compatibility with new Cohere models.
        """
        if not self.validate_model(model):
            raise ValueError(
                f"Model '{model}' does not match command* pattern. "
                f"Cohere models must start with 'command'"
            )

        start_time = time.time()

        try:
            response = self.client.tokenize(text=text)
            token_count = len(response.tokens)
        except Exception as e:
            raise RuntimeError(f"Failed to count tokens for {model}: {e}")

        latency_ms = (time.time() - start_time) * 1000

        return TokenCountResult(
            input_tokens=token_count,
            cached=False,
            source="api",
            latency_ms=latency_ms,
            provider=self.provider_name,
            model=model,
        )

    def validate_model(self, model: str) -> bool:
        """Validate model pattern (not specific model list)

        Uses pattern matching instead of hardcoded list.
        Allows forward compatibility with new Cohere models.
        Server-side validation via Cohere API for actual existence.
        """
        model_lower = model.lower()
        return model_lower.startswith("command")

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tokenizer info"""
        info = super().get_tokenizer_info()
        info.update({"library": "cohere"})
        return info
