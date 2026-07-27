"""
Anthropic Claude token counter.
Provides token counting for Claude 3 models (Opus, Sonnet, Haiku, 3.5-Sonnet).
"""

from typing import List, Dict, Any
import time

from .base import TokenCounter, TokenCountResult

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicTokenCounter(TokenCounter):
    """Anthropic Claude token counter using official API

    Supports all Claude models via pattern matching (claude-*).
    New models released by Anthropic are automatically supported.
    Validation happens server-side via Anthropic API.
    """

    # Known models as of 2026-07-17 (for documentation)
    KNOWN_MODELS = {
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "claude-3.5-sonnet",
        "claude-4-fable",  # Support new models without code changes
    }

    def __init__(self):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic is required for Claude token counting. "
                "Install: pip install anthropic"
            )
        self.client = Anthropic()

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def supported_models(self) -> List[str]:
        # Return known models, but pattern matching allows any claude-*
        return list(self.KNOWN_MODELS)

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens using Anthropic's token counting API

        Pattern-based validation: accepts any claude-* model.
        Anthropic API validates actual model existence server-side.
        This allows forward compatibility with new Claude models
        without requiring code updates.
        """
        if not self.validate_model(model):
            raise ValueError(
                f"Model '{model}' does not match claude-* pattern. "
                f"Anthropic models must start with 'claude-'"
            )

        start_time = time.time()

        try:
            response = self.client.messages.count_tokens(
                model=model,
                messages=[{"role": "user", "content": text}]
            )
            token_count = response.input_tokens
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
        Allows forward compatibility with new Claude models.
        Server-side validation via Anthropic API for actual existence.
        """
        model_lower = model.lower()
        # Pattern: any claude-* model is accepted
        # Anthropic API will reject if model doesn't actually exist
        return model_lower.startswith("claude-")

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tokenizer info"""
        info = super().get_tokenizer_info()
        info.update({"library": "anthropic"})
        return info
