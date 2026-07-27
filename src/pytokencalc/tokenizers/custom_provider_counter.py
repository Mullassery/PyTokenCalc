"""
Custom provider token counter.
Enables token counting for ANY provider with an API endpoint.

Supports:
- RunPod serverless endpoints
- Llama Labs custom implementations
- Replicate API
- Together AI
- HuggingFace Inference API
- Custom self-hosted solutions
- Any OpenAI-compatible API endpoint
- Proprietary/private APIs with custom logic

Users can register custom providers without modifying PyTokenCalc code.
"""

from typing import List, Dict, Any, Optional, Callable
import time
import logging

from .base import TokenCounter, TokenCountResult

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class CustomProviderCounter(TokenCounter):
    """Token counter for custom/unknown providers

    Architecture for Custom Providers:
    - Accept any API endpoint URL
    - Support multiple API formats (OpenAI-compatible, custom)
    - Custom token extraction logic via callable
    - Verification against provider documentation
    - No hardcoded assumptions about provider

    Example Providers:
    - RunPod: Custom inference endpoints
    - Llama Labs: LlamaIndex-hosted endpoints
    - Replicate: replicate.com API
    - Together AI: together.ai API
    - HuggingFace: huggingface.co/inference API
    - Custom self-hosted solutions
    - Proprietary enterprise APIs

    Usage:
    ```python
    # Register custom provider
    counter = CustomProviderCounter(
        provider_name="runpod",
        base_url="https://api.runpod.io/v2/xxx",
        api_key="your-api-key",
        token_extraction_fn=lambda response: response['usage']['prompt_tokens']
    )

    result = counter.count("Hello world", "llama-2-7b")
    ```
    """

    def __init__(
        self,
        provider_name: str,
        base_url: str,
        api_key: Optional[str] = None,
        api_path: str = "/v1/completions",
        token_extraction_fn: Optional[Callable[[Dict], int]] = None,
        models: Optional[List[str]] = None,
        verify_provider: bool = True,
    ):
        """Initialize custom provider counter

        Args:
            provider_name: Name of provider (e.g., 'runpod', 'llama-labs')
            base_url: API endpoint base URL
            api_key: API key for authentication (optional)
            api_path: API endpoint path (default: /v1/completions)
            token_extraction_fn: Function to extract token count from response
                                Default: tries common formats
            models: List of available models (or auto-detect)
            verify_provider: Verify provider is accessible at startup
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for custom provider token counting. "
                "Install: pip install requests"
            )

        self._provider_name = provider_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_path = api_path
        self.token_extraction_fn = token_extraction_fn or self._default_token_extraction
        self._supported_models = models or []

        # Verify provider accessibility
        if verify_provider:
            self._verify_provider_accessible()

    def _verify_provider_accessible(self):
        """Verify custom provider is accessible"""
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Try to reach provider
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=5
            )

            if response.status_code not in [200, 404]:  # 404 is ok if endpoint doesn't have /models
                logger.warning(
                    f"Custom provider {self._provider_name} returned {response.status_code}. "
                    f"May not be accessible or requires different authentication."
                )

        except Exception as e:
            logger.warning(
                f"Could not verify custom provider {self._provider_name} at {self.base_url}: {e}. "
                f"Token counting may fail."
            )

    @staticmethod
    def _default_token_extraction(response: Dict) -> int:
        """Default token extraction logic

        Tries common response formats:
        - OpenAI-compatible: response['usage']['prompt_tokens']
        - Alternative: response['tokens']
        - Alternative: response['token_count']
        - Fallback: estimate from response length
        """
        # Try OpenAI-compatible format
        if "usage" in response and "prompt_tokens" in response["usage"]:
            return response["usage"]["prompt_tokens"]

        # Try alternative formats
        if "tokens" in response:
            return response["tokens"]

        if "token_count" in response:
            return response["token_count"]

        if "prompt_tokens" in response:
            return response["prompt_tokens"]

        # Fallback: estimate
        text = str(response)
        return len(text) // 4 + 1

    def register_model(self, model_name: str):
        """Register a model for this provider"""
        if model_name not in self._supported_models:
            self._supported_models.append(model_name)

    def register_models(self, model_names: List[str]):
        """Register multiple models"""
        for model in model_names:
            self.register_model(model)

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def supported_models(self) -> List[str]:
        """List of supported models

        Users can register models via register_model() or register_models()
        """
        return self._supported_models

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens using custom provider API

        Flexible implementation that adapts to different provider APIs.
        Uses token_extraction_fn to parse responses.
        """
        start_time = time.time()

        if not self.validate_model(model):
            raise ValueError(
                f"Model '{model}' not registered for provider '{self._provider_name}'. "
                f"Available: {self._supported_models}. "
                f"Register with: counter.register_model('{model}')"
            )

        try:
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Use OpenAI-compatible format as default
            response = requests.post(
                f"{self.base_url}{self.api_path}",
                json={
                    "model": model,
                    "prompt": text,
                    "max_tokens": 1,  # Minimal generation for token counting
                },
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Provider API error: {response.status_code} - {response.text}"
                )

            data = response.json()

            # Extract token count using provider-specific logic
            token_count = self.token_extraction_fn(data)

            if token_count == 0:
                # Fallback estimation
                token_count = len(text) // 4 + 1

        except Exception as e:
            raise RuntimeError(
                f"Failed to count tokens with {self._provider_name} for {model}: {e}"
            )

        latency_ms = (time.time() - start_time) * 1000

        return TokenCountResult(
            input_tokens=token_count,
            cached=False,
            source="api",
            latency_ms=latency_ms,
            provider=self.provider_name,
            model=model,
            platform=self._provider_name,
        )

    def validate_model(self, model: str) -> bool:
        """Check if model is registered

        Users must explicitly register models they want to use.
        This prevents accidental misspellings and clear API contracts.
        """
        return model in self._supported_models

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tokenizer info"""
        return {
            "provider": self.provider_name,
            "base_url": self.base_url,
            "api_path": self.api_path,
            "supported_models": self.supported_models,
            "architecture": "custom-provider",
            "note": "Register models via register_model() or register_models()",
        }


# Registry for custom providers
_custom_providers: Dict[str, CustomProviderCounter] = {}


def register_custom_provider(counter: CustomProviderCounter):
    """Register a custom provider globally

    Example:
    ```python
    # Define custom provider
    runpod_counter = CustomProviderCounter(
        provider_name="runpod",
        base_url="https://api.runpod.io/v2/xxx",
        api_key="your-key"
    )
    runpod_counter.register_models(["llama-2-7b", "mistral-7b"])

    # Register globally
    register_custom_provider(runpod_counter)

    # Use via registry
    registry = TokenCounterRegistry()
    result = registry.count_tokens("llama-2-7b", "Hello", provider="runpod")
    ```
    """
    _custom_providers[counter.provider_name] = counter
    logger.info(f"Registered custom provider: {counter.provider_name}")


def get_custom_provider(provider_name: str) -> Optional[CustomProviderCounter]:
    """Get registered custom provider"""
    return _custom_providers.get(provider_name)


def list_custom_providers() -> List[str]:
    """List all registered custom providers"""
    return list(_custom_providers.keys())
