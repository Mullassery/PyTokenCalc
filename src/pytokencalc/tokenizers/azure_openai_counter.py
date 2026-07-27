"""
Azure OpenAI token counter.
Provides token counting for Azure OpenAI models (GPT-4, GPT-3.5, etc).
Uses same tokenization as OpenAI via tiktoken.
"""

from typing import List, Dict, Any
import time

from .base import TokenCounter, TokenCountResult

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class AzureOpenAITokenCounter(TokenCounter):
    """Azure OpenAI token counter (same tokenization as OpenAI)"""

    MODEL_TO_ENCODING = {
        "gpt-4": "cl100k_base",
        "gpt-4-32k": "cl100k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-35-turbo": "cl100k_base",
        "gpt-35-turbo-16k": "cl100k_base",
    }

    def __init__(self):
        if not TIKTOKEN_AVAILABLE:
            raise ImportError(
                "tiktoken is required for Azure OpenAI token counting. "
                "Install: pip install tiktoken"
            )
        self.encodings = {}
        self._load_default_encodings()

    def _load_default_encodings(self):
        """Pre-load commonly used encodings"""
        try:
            self.encodings["cl100k_base"] = tiktoken.get_encoding("cl100k_base")
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
        return "azure"

    @property
    def supported_models(self) -> List[str]:
        return list(self.MODEL_TO_ENCODING.keys())

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens using tiktoken (same as OpenAI)"""
        if not self.validate_model(model):
            raise ValueError(f"Unknown Azure OpenAI model: {model}")

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
        return model.lower() in self.MODEL_TO_ENCODING

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tokenizer info"""
        info = super().get_tokenizer_info()
        info.update({
            "library": "tiktoken",
            "note": "Uses OpenAI's tiktoken (Azure OpenAI compatible)"
        })
        return info
