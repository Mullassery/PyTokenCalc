"""
Google Gemini token counter.
Provides token counting for Gemini models (Pro, Ultra, Nano).
"""

from typing import List, Dict, Any
import time

from .base import TokenCounter, TokenCountResult

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class GoogleTokenCounter(TokenCounter):
    """Google Gemini token counter using official API

    Supports all Gemini models via pattern matching (gemini-*).
    New models released by Google are automatically supported.
    Validation happens server-side via Google API.
    """

    KNOWN_MODELS = {
        "gemini-pro",
        "gemini-pro-vision",
        "gemini-ultra",
        "gemini-nano",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-2-flash",  # Support new models without code changes
    }

    def __init__(self):
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "google-generativeai is required for Gemini token counting. "
                "Install: pip install google-generativeai"
            )

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def supported_models(self) -> List[str]:
        return list(self.KNOWN_MODELS)

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens using Google's token counting API

        Pattern-based validation: accepts any gemini-* model.
        Google API validates actual model existence server-side.
        This allows forward compatibility with new Gemini models.
        """
        if not self.validate_model(model):
            raise ValueError(
                f"Model '{model}' does not match gemini-* pattern. "
                f"Gemini models must start with 'gemini-'"
            )

        start_time = time.time()

        try:
            model_obj = genai.GenerativeModel(model)
            response = model_obj.count_tokens(text)
            token_count = response.total_tokens
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
        Allows forward compatibility with new Gemini models.
        Server-side validation via Google API for actual existence.
        """
        model_lower = model.lower()
        return model_lower.startswith("gemini-")

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tokenizer info"""
        info = super().get_tokenizer_info()
        info.update({"library": "google-generativeai"})
        return info
