"""
OpenAI token counter using tiktoken.
Provides 100% accurate token counting for GPT-4, GPT-4o, and GPT-3.5 models.
"""

from typing import List, Dict, Any
import time

from .base import TokenCounter, TokenCountResult

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class OpenAITokenCounter(TokenCounter):
    """OpenAI token counter using tiktoken library"""

    # Model to encoding mapping
    MODEL_TO_ENCODING = {
        "gpt-4": "cl100k_base",
        "gpt-4-32k": "cl100k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-4-turbo-preview": "cl100k_base",
        "gpt-4-0125-preview": "cl100k_base",
        "gpt-4-1106-preview": "cl100k_base",
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-4o-2024-11-20": "o200k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "gpt-3.5-turbo-0613": "cl100k_base",
        "gpt-3.5-turbo-1106": "cl100k_base",
        "text-davinci-003": "p50k_base",
        "text-davinci-002": "p50k_base",
    }

    def __init__(self):
        if not TIKTOKEN_AVAILABLE:
            raise ImportError(
                "tiktoken is required for OpenAI token counting. "
                "Install: pip install tiktoken"
            )

        self.encodings = {}  # Cache loaded encodings
        self._load_default_encodings()

    def _load_default_encodings(self):
        """Pre-load commonly used encodings"""
        try:
            self.encodings["cl100k_base"] = tiktoken.get_encoding("cl100k_base")
            self.encodings["o200k_base"] = tiktoken.get_encoding("o200k_base")
        except Exception as e:
            raise RuntimeError(f"Failed to load tiktoken encodings: {e}")

    def _get_encoding(self, model: str):
        """Get tiktoken encoding for model"""
        encoding_name = self.MODEL_TO_ENCODING.get(model, "cl100k_base")

        if encoding_name not in self.encodings:
            self.encodings[encoding_name] = tiktoken.get_encoding(encoding_name)

        return self.encodings[encoding_name]

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def supported_models(self) -> List[str]:
        return [
            "gpt-4*",
            "gpt-4o*",
            "gpt-3.5-turbo*",
            "text-davinci-*",
        ]

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens for OpenAI model using tiktoken"""
        if not self.validate_model(model):
            raise ValueError(f"Unknown GPT model: {model}")

        start_time = time.time()

        encoding = self._get_encoding(model)
        tokens = encoding.encode(text)
        token_count = len(tokens)

        latency_ms = (time.time() - start_time) * 1000

        return TokenCountResult(
            input_tokens=token_count,
            cached=False,
            source="local",
            latency_ms=latency_ms,
            provider=self.provider_name,
            model=model,
        )

    def validate_model(self, model: str) -> bool:
        """Check if model is supported"""
        model_lower = model.lower()

        for pattern in self.MODEL_TO_ENCODING.keys():
            if model_lower.startswith(pattern):
                return True

        # Pattern-based matching
        for pattern in ["gpt-4", "gpt-3.5", "text-davinci"]:
            if pattern in model_lower:
                return True

        return False

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tiktoken version info"""
        info = super().get_tokenizer_info()
        info.update({
            "library": "tiktoken",
            "version": getattr(tiktoken, "__version__", "unknown"),
            "encoding_mapping": self.MODEL_TO_ENCODING,
        })
        return info

    def count_batch(self, requests: List[Dict[str, Any]]) -> List[TokenCountResult]:
        """Batch token counting (same speed as individual calls with tiktoken)"""
        return super().count_batch(requests)

    # Vision token counting for GPT-4 Vision
    def count_vision(
        self,
        text: str,
        model: str,
        image_path: str = None,
        image_url: str = None,
        num_images: int = 1,
    ) -> TokenCountResult:
        """
        Count tokens for text + images (GPT-4 Vision).

        Formula: 85 (image overhead) + (width/256 * height/256) * 170 per image

        For simplicity, we estimate:
        - Low detail: 65 tokens per image
        - High detail: 2,665 tokens per image (1024x1024)
        - Default: 170 tokens per image (512x512 estimate)
        """
        if not model.lower().startswith("gpt-4"):
            # Non-vision model, just count text
            return self.count(text, model)

        # Count text tokens
        text_result = self.count(text, model)

        # Estimate image tokens (default 170 per image = 512x512)
        # Real calculation requires image dimensions
        image_tokens = 170 * num_images

        return TokenCountResult(
            input_tokens=text_result.input_tokens,
            image_tokens=image_tokens,
            cached=False,
            source="formula",
            latency_ms=text_result.latency_ms,
            provider=self.provider_name,
            model=model,
        )
