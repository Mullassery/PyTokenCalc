"""
Ollama token counter.
Provides token counting for models running in Ollama (local LLM inference engine).
Supports dynamic model discovery - any model in Ollama is automatically supported.
"""

from typing import List, Dict, Any
import time
import logging

from .base import TokenCounter, TokenCountResult

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class OllamaTokenCounter(TokenCounter):
    """Token counter for models running in Ollama

    Ollama provides local LLM inference with dynamic model support.
    Models in Ollama change continuously - new ones are pulled, old ones deleted.
    PyTokenCalc automatically adapts without code changes.

    Architecture for Ollama Integration:
    - Connects to local Ollama instance (default: localhost:11434)
    - Fetches model list from Ollama dynamically (not hardcoded)
    - Models added to Ollama work immediately (no deployment needed)
    - Models deleted from Ollama fail gracefully
    - No code changes when Ollama models change

    Dynamic Behavior:
    - supported_models: Queries Ollama API each time (always current)
    - validate_model: Permissive (accepts any model name)
    - count(): Ollama validates actual model availability at token count time
    - New models: ollama pull custom/model-name → immediately works
    - Deleted models: ollama rm model-name → error on next use (caught)

    Example Ollama models (these change):
    - llama2, llama2-13b, llama2-70b
    - mistral, mistral-7b
    - neural-chat, neural-chat-7b
    - dolphin-mixtral, mixtral
    - openchat, openhermes
    - phi, wizardlm
    - Any custom or newly released model
    """

    # Common Ollama models (for documentation, not restrictive)
    KNOWN_MODELS = {
        "llama2",
        "llama2-13b",
        "llama2-70b",
        "mistral",
        "mistral-7b",
        "neural-chat",
        "neural-chat-7b",
        "dolphin-mixtral",
        "mixtral",
        "openchat",
        "openhermes",
        "phi",
        "wizardlm",
    }

    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize Ollama token counter

        Args:
            base_url: Ollama API endpoint (default: localhost:11434)
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for Ollama token counting. "
                "Install: pip install requests"
            )

        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api"

        # Verify Ollama is running
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=2)
            if response.status_code != 200:
                raise RuntimeError(f"Ollama API error: {response.status_code}")
        except Exception as e:
            raise RuntimeError(
                f"Ollama not accessible at {self.base_url}. "
                f"Ensure Ollama is running: ollama serve. "
                f"Details: {e}"
            )

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def supported_models(self) -> List[str]:
        """Get list of available models in Ollama

        Dynamically fetches models from Ollama instance.
        New models added to Ollama are automatically available.
        """
        try:
            response = requests.get(
                f"{self.api_url}/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = [model["name"].split(":")[0] for model in data.get("models", [])]
                return list(set(models))  # Remove duplicates
            return list(self.KNOWN_MODELS)
        except Exception as e:
            logger.warning(f"Failed to fetch Ollama models: {e}")
            return list(self.KNOWN_MODELS)

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens using Ollama's tokenization API

        Dynamic discovery: accepts any model name.
        Ollama validates model existence and availability.

        API Interface Stability:
        - Input: Always accepts (model, text)
        - Output: Always returns TokenCountResult with same fields
        - Behavior: Same regardless of which Ollama models are installed
        - Token counts: Consistent format even as Ollama models change

        Ollama models may be added/removed anytime, but PyTokenCalc API remains stable.
        """
        start_time = time.time()

        if not self.validate_model(model):
            raise ValueError(
                f"Model '{model}' not recognized. "
                f"Available models: {self.supported_models}"
            )

        try:
            # Use Ollama's generate API with streaming disabled to count tokens
            # This is the most reliable way to get token count from Ollama
            response = requests.post(
                f"{self.api_url}/generate",
                json={
                    "model": model,
                    "prompt": text,
                    "stream": False,
                },
                timeout=30
            )

            if response.status_code != 200:
                raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")

            data = response.json()

            # Ollama returns eval_count (tokens generated) and prompt_eval_count (input tokens)
            # We want prompt_eval_count for the input text
            token_count = data.get("prompt_eval_count", 0)

            if token_count == 0:
                # Fallback: use character-based estimation if Ollama doesn't return count
                # Average ~4 characters per token
                token_count = len(text) // 4 + 1

        except Exception as e:
            raise RuntimeError(f"Failed to count tokens with Ollama for {model}: {e}")

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
        """Validate model pattern (permissive for dynamic discovery)

        Architecture: Accept ANY model name.
        Ollama will validate model existence when counting tokens.
        Reason: New models can be pulled into Ollama anytime.

        Validation happens during count() when we actually use the model.
        """
        # Permissive: accept any non-empty model name
        # Ollama API will reject if model doesn't exist
        return bool(model and len(model) > 0)

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tokenizer info"""
        info = super().get_tokenizer_info()
        info.update({
            "library": "ollama",
            "base_url": self.base_url,
            "architecture": "dynamic_model_discovery",
            "available_models": self.supported_models,
            "note": "New models pulled into Ollama are automatically supported",
        })
        return info
