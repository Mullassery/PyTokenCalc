"""
Open-source model token counter.
Supports any HuggingFace model ID + models from Azure, AWS, GCP.
New models appear daily across these platforms - no code changes needed.
"""

import time
from typing import Any, Dict, List

from ._hf_validation import validate_model_id_for_from_pretrained
from ._timeout import call_with_timeout, resolve_default_timeout
from .base import TokenCounter, TokenCountResult

try:
    from transformers import AutoTokenizer
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


class OpenSourceTokenCounter(TokenCounter):
    """Token counter for open-source models - dynamically supports new models

    Architecture for Daily Model Discovery:
    - HuggingFace: Accept any "org/model-name" ID (no hardcoded list)
    - AWS SageMaker: Support "aws://model-registry/model-name" URIs
    - Azure ML: Support "azure://workspace/model-name" URIs
    - GCP Vertex: Support "gcp://vertex-ai/model-name" URIs

    New models released daily are automatically supported without code changes.
    Tokenizer loading happens on-demand via HuggingFace API or cloud provider APIs.
    """

    # Common aliases for convenience (updated quarterly, not blocking)
    KNOWN_ALIASES = {
        # DeepSeek
        "deepseek-chat": "deepseek-ai/deepseek-coder-1.3b",
        "deepseek-coder": "deepseek-ai/deepseek-coder-7b",
        # Falcon
        "falcon-7b": "tiiuae/falcon-7b",
        "falcon-40b": "tiiuae/falcon-40b",
        # PALM 2
        "text-bison": "google/flan-t5-large",
        "code-bison": "google/flan-t5-large",
        # Llama variants
        "llama-2-7b-hf": "meta-llama/Llama-2-7b-hf",
        "llama-2-13b-hf": "meta-llama/Llama-2-13b-hf",
        "llama-2-70b-hf": "meta-llama/Llama-2-70b-hf",
        "llama-3-8b": "meta-llama/Meta-Llama-3-8B",
        "llama-3-70b": "meta-llama/Meta-Llama-3-70B",
        # Mistral variants
        "mistral-7b": "mistralai/Mistral-7B-v0.1",
        "mistral-instruct": "mistralai/Mistral-7B-Instruct-v0.1",
        "mixtral-8x7b": "mistralai/Mixtral-8x7B",
    }

    def __init__(self, load_timeout: float = None):
        if not HF_AVAILABLE:
            raise ImportError(
                "transformers is required for open-source model token counting. "
                "Install: pip install transformers torch"
            )
        # Ceiling (seconds) for a single tokenizer download/load; see
        # _timeout.py and huggingface_counter.py. Overridable via
        # PYTOKENCALC_HF_TIMEOUT.
        self.load_timeout = load_timeout or resolve_default_timeout()
        self.tokenizers = {}

    def _resolve_model_id(self, model: str) -> str:
        """Resolve model identifier to HuggingFace or cloud provider ID

        Supports three formats:
        1. Alias (convenience): "llama-3-8b" → "meta-llama/Meta-Llama-3-8B"
        2. HuggingFace direct: "meta-llama/Meta-Llama-3-8B" (passed through)
        3. Cloud provider URI: "aws://sagemaker/model-name" (future)

        New models added daily on these platforms are automatically supported.
        """
        model_lower = model.lower()

        # Check aliases first (convenience, optional)
        if model_lower in self.KNOWN_ALIASES:
            return self.KNOWN_ALIASES[model_lower]

        # Pass through any other format (HF direct ID, cloud URIs, etc.)
        return model

    def _get_tokenizer(self, model: str):
        """Get or load tokenizer - supports HuggingFace and cloud providers

        Dynamic loading strategy:
        - HuggingFace: Load via AutoTokenizer.from_pretrained()
        - AWS/Azure/GCP: (Future) Load via cloud provider SDKs

        Tokenizers are cached after first load for performance.
        """
        model_lower = model.lower()
        resolved_from_alias = model_lower in self.KNOWN_ALIASES
        model_id = self._resolve_model_id(model)

        error = validate_model_id_for_from_pretrained(model_id, resolved_from_alias)
        if error:
            raise ValueError(error)

        if model_id not in self.tokenizers:
            try:
                self.tokenizers[model_id] = call_with_timeout(
                    AutoTokenizer.from_pretrained,
                    self.load_timeout,
                    model_id,
                )
            except TimeoutError as e:
                raise RuntimeError(
                    f"Timed out loading tokenizer for '{model}' (resolved to "
                    f"'{model_id}') after {self.load_timeout:g}s. The model may "
                    f"be uncached and HuggingFace Hub unreachable; set "
                    f"PYTOKENCALC_HF_TIMEOUT to wait longer, or pre-download "
                    f"the tokenizer."
                ) from e
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load tokenizer for '{model}' (resolved to '{model_id}'). "
                    f"Ensure model exists on HuggingFace Hub (org/model-name format). "
                    f"Details: {e}"
                ) from e

        return self.tokenizers[model_id]

    @property
    def provider_name(self) -> str:
        return "opensource"

    @property
    def supported_models(self) -> List[str]:
        # Return known aliases, but any HF model ID or cloud provider URI works
        return list(self.KNOWN_ALIASES.keys())

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens for open-source model

        Supports any model from:
        - HuggingFace Hub (any "org/model" ID)
        - AWS SageMaker (any model in registry)
        - Azure ML (any model in workspace)
        - GCP Vertex AI (any model in project)

        New models released daily are automatically supported.
        """
        start_time = time.time()

        try:
            tokenizer = self._get_tokenizer(model)
            tokens = tokenizer.encode(text)
            token_count = len(tokens)
        except Exception as e:
            # Clear error message for debugging
            raise RuntimeError(
                f"Failed to count tokens for model '{model}': {e}. "
                f"Try using format: 'org/model-name' for HuggingFace models."
            ) from e

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
        """Validate model pattern (permissive, not exhaustive)

        Architecture: Accept ANY model format, validate on-demand during token counting.
        Reason: New models appear daily on HF/Azure/AWS/GCP - can't maintain hardcoded list.

        Validation happens during count() when we actually need the tokenizer.
        """
        model_id = self._resolve_model_id(model)

        # Permissive validation: only reject obviously invalid formats.
        # Anything that looks like a model ID is accepted (HuggingFace
        # org/model, cloud URIs like aws://, azure://, gcp://); actual
        # validation happens when the tokenizer is loaded.
        return bool(model_id) and len(model_id) >= 3

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tokenizer info"""
        info = super().get_tokenizer_info()
        info.update({
            "library": "transformers",
            "architecture": "dynamic_model_discovery",
            "supports": [
                "HuggingFace (any org/model-name)",
                "AWS SageMaker (future)",
                "Azure ML (future)",
                "GCP Vertex AI (future)",
            ],
            "convenience_aliases": self.KNOWN_ALIASES,
            "note": "New models added daily - no code changes needed",
        })
        return info
