"""
Local inference engine token counter.
Supports multiple local LLM providers (LM Studio, LocalAI, GPT4All, Llama.cpp, etc).

Local providers change rapidly - new ones appear, old ones update APIs.
This counter uses a unified interface for common local inference patterns.
"""

from typing import List, Dict, Any, Optional
import time
import logging

from .base import TokenCounter, TokenCountResult

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class LocalInferenceTokenCounter(TokenCounter):
    """Token counter for local LLM inference engines

    Supports multiple local inference providers:
    - LM Studio: Default localhost:1234
    - LocalAI: Default localhost:8080
    - Llama.cpp: Default localhost:8000
    - GPT4All: Default localhost:4891
    - Text Generation WebUI: Default localhost:5000
    - Jan: Default localhost:1337
    - Vllm (local): Default localhost:8000
    - Any OpenAI-compatible local API

    Architecture for Local Inference:
    - Auto-detects available local providers
    - Unified interface across different engines
    - Dynamic model discovery (models vary by provider)
    - No hardcoded lists - adapts to installed providers

    Example Usage:
    ```python
    counter = LocalInferenceTokenCounter()
    result = counter.count("Hello world", "mistral-7b")
    # Automatically finds provider (LM Studio, LocalAI, etc)
    # Returns token count from available provider
    ```
    """

    # Local inference provider endpoints (auto-probed in order)
    DEFAULT_PROVIDERS = [
        # Format: (name, url_base, api_path)
        ("lm-studio", "http://localhost:1234", "/api/v1/completions"),
        ("localai", "http://localhost:8080", "/v1/completions"),
        ("llama-cpp", "http://localhost:8000", "/v1/completions"),
        ("gpt4all", "http://localhost:4891", "/v1/completions"),
        ("text-gen-webui", "http://localhost:5000", "/v1/completions"),
        ("jan", "http://localhost:1337", "/v1/completions"),
        ("vllm", "http://localhost:8000", "/v1/completions"),
    ]

    # Known local models (varies by what's installed)
    KNOWN_MODELS = {
        # LLaMA family
        "llama2", "llama2-7b", "llama2-13b", "llama2-70b",
        "llama-3-8b", "llama-3-70b",
        # Mistral family
        "mistral", "mistral-7b", "mistral-8x7b", "mixtral",
        # Other local favorites
        "neural-chat", "neural-chat-7b",
        "openchat", "openhermes",
        "dolphin-mixtral",
        "phi", "phi-2",
        "orca", "orca-mini",
        "nous-hermes",
        "zephyr",
        "model-identifier",  # Placeholder for user's model
    }

    def __init__(self, provider_urls: Optional[Dict[str, str]] = None):
        """Initialize local inference counter

        Args:
            provider_urls: Override default provider URLs
                          {provider_name: base_url}
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for local inference token counting. "
                "Install: pip install requests"
            )

        self.provider_urls = provider_urls or {}
        self.detected_provider = None
        self.detected_base_url = None

        # Try to detect available local provider
        self._detect_provider()

    def _detect_provider(self):
        """Auto-detect which local inference provider is available"""
        for provider_name, default_url, api_path in self.DEFAULT_PROVIDERS:
            custom_url = self.provider_urls.get(provider_name)
            base_url = custom_url or default_url

            try:
                # Try to reach provider's API
                response = requests.get(f"{base_url}/models", timeout=1)
                if response.status_code == 200:
                    self.detected_provider = provider_name
                    self.detected_base_url = base_url
                    logger.info(f"Detected local inference provider: {provider_name} at {base_url}")
                    return
            except Exception:
                continue  # Try next provider

        logger.warning("No local inference provider detected. Install LM Studio, LocalAI, or similar.")

    @property
    def provider_name(self) -> str:
        return "local-inference"

    @property
    def supported_models(self) -> List[str]:
        """Get list of available models in detected provider

        Dynamically fetches from provider's API if available.
        Falls back to known models list.
        """
        if not self.detected_provider or not self.detected_base_url:
            return list(self.KNOWN_MODELS)

        try:
            response = requests.get(
                f"{self.detected_base_url}/models",
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                # Different providers have different response formats
                if "data" in data:  # OpenAI-compatible format
                    models = [m.get("id", m.get("name")) for m in data["data"]]
                    return list(set(models))
                elif "models" in data:  # Some providers use this
                    models = data["models"]
                    if isinstance(models, list):
                        return models
            return list(self.KNOWN_MODELS)
        except Exception as e:
            logger.warning(f"Failed to fetch models from local provider: {e}")
            return list(self.KNOWN_MODELS)

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens using local inference provider

        Supports OpenAI-compatible API format (used by most local providers).
        """
        start_time = time.time()

        if not self.detected_provider or not self.detected_base_url:
            raise RuntimeError(
                "No local inference provider detected. "
                "Install and run one of: LM Studio, LocalAI, Ollama, Llama.cpp, GPT4All, etc.\n"
                "Or provide custom provider URL via provider_urls parameter."
            )

        if not self.validate_model(model):
            raise ValueError(
                f"Model '{model}' not recognized. "
                f"Available models: {self.supported_models}"
            )

        try:
            # Use OpenAI-compatible API format
            # Most local providers support /v1/completions endpoint
            response = requests.post(
                f"{self.detected_base_url}/v1/completions",
                json={
                    "model": model,
                    "prompt": text,
                    "max_tokens": 1,  # Minimal generation for token counting
                    "temperature": 0.7,
                },
                timeout=30
            )

            if response.status_code != 200:
                raise RuntimeError(f"Provider API error: {response.status_code} - {response.text}")

            data = response.json()

            # Extract token count from response
            # OpenAI-compatible format has usage.prompt_tokens
            if "usage" in data:
                token_count = data["usage"].get("prompt_tokens", 0)
            else:
                # Fallback: estimate from text
                token_count = len(text) // 4 + 1

            if token_count == 0:
                # Fallback estimation
                token_count = len(text) // 4 + 1

        except Exception as e:
            raise RuntimeError(f"Failed to count tokens with local provider for {model}: {e}")

        latency_ms = (time.time() - start_time) * 1000

        return TokenCountResult(
            input_tokens=token_count,
            cached=False,
            source="api",
            latency_ms=latency_ms,
            provider=self.provider_name,
            model=model,
            platform=self.detected_provider or "local-inference",
        )

    def validate_model(self, model: str) -> bool:
        """Validate model pattern (permissive for dynamic discovery)

        Architecture: Accept ANY model name.
        Local provider will validate model existence when counting tokens.
        Reason: Users can install any model in their local provider.

        Validation happens during count() when we actually use the model.
        """
        return bool(model and len(model) > 0)

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tokenizer info"""
        info = super().get_tokenizer_info()
        info.update({
            "library": "local-inference",
            "detected_provider": self.detected_provider,
            "base_url": self.detected_base_url,
            "architecture": "dynamic_model_discovery",
            "supported_providers": [name for name, _, _ in self.DEFAULT_PROVIDERS],
            "available_models": self.supported_models,
            "note": "Install local LLM provider and run it to enable token counting",
        })
        return info
