"""
HuggingFace Transformers token counter.
Supports 1000+ models: Llama, Mistral, Qwen, etc.
"""

from typing import List, Dict, Any, Optional
import time

from .base import TokenCounter, TokenCountResult

try:
    from transformers import AutoTokenizer
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


class HuggingFaceTokenCounter(TokenCounter):
    """HuggingFace transformers token counter for open-source models"""

    # Common model aliases
    MODEL_ALIASES = {
        "llama-7b": "meta-llama/Llama-2-7b",
        "llama-13b": "meta-llama/Llama-2-13b",
        "llama-70b": "meta-llama/Llama-2-70b",
        "llama2-7b": "meta-llama/Llama-2-7b",
        "llama3-8b": "meta-llama/Meta-Llama-3-8B",
        "llama3-70b": "meta-llama/Meta-Llama-3-70B",
        "mistral-7b": "mistralai/Mistral-7B-v0.1",
        "mistral-small": "mistralai/Mistral-7B-Instruct-v0.1",
        "mistral-large": "mistralai/Mixtral-8x7B",
        "mixtral-8x7b": "mistralai/Mixtral-8x7B",
        "qwen-7b": "Qwen/Qwen-7B",
        "qwen-14b": "Qwen/Qwen-14B",
        "qwen-72b": "Qwen/Qwen-72B",
    }

    def __init__(self):
        if not HF_AVAILABLE:
            raise ImportError(
                "transformers is required for HuggingFace token counting. "
                "Install: pip install transformers torch sentencepiece"
            )

        self.tokenizers = {}  # Cache loaded tokenizers

    def _resolve_model_id(self, model: str) -> str:
        """Resolve model alias to HuggingFace model ID"""
        model_lower = model.lower()

        # Check aliases
        if model_lower in self.MODEL_ALIASES:
            return self.MODEL_ALIASES[model_lower]

        # Assume it's already a HF model ID
        return model

    def _get_tokenizer(self, model: str):
        """Get or load tokenizer for model"""
        model_id = self._resolve_model_id(model)

        if model_id not in self.tokenizers:
            try:
                self.tokenizers[model_id] = AutoTokenizer.from_pretrained(model_id)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load tokenizer for {model_id}: {e}. "
                    f"Make sure the model ID is valid on HuggingFace Hub."
                )

        return self.tokenizers[model_id]

    @property
    def provider_name(self) -> str:
        return "huggingface"

    @property
    def supported_models(self) -> List[str]:
        return [
            "llama-*",
            "mistral-*",
            "qwen-*",
            "mixtral-*",
            # HuggingFace org/model IDs
            "meta-llama/*",
            "mistralai/*",
            "Qwen/*",
        ]

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens for HuggingFace model"""
        if not self.validate_model(model):
            raise ValueError(f"Unknown HuggingFace model: {model}")

        start_time = time.time()

        tokenizer = self._get_tokenizer(model)
        tokens = tokenizer.encode(text)
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
        """Check if model can be loaded"""
        try:
            model_id = self._resolve_model_id(model)
            # Try to load (cached if already loaded)
            self._get_tokenizer(model)
            return True
        except Exception:
            return False

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tokenizer info"""
        info = super().get_tokenizer_info()
        info.update({
            "library": "transformers",
            "aliases": self.MODEL_ALIASES,
            "cached_tokenizers": list(self.tokenizers.keys()),
        })
        return info

    def count_batch(self, requests: List[Dict[str, Any]]) -> List[TokenCountResult]:
        """Batch token counting"""
        # HF tokenizer can handle batching
        results = []

        for req in requests:
            text = req.get("text", "")
            model = req.get("model", "")

            try:
                result = self.count(text, model)
                results.append(result)
            except Exception as e:
                # Return error result
                results.append(
                    TokenCountResult(
                        input_tokens=0,
                        provider=self.provider_name,
                        model=model,
                        source="error",
                    )
                )

        return results
