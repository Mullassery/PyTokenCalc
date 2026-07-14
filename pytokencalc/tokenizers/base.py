"""
Abstract base class for token counters.
Each provider (OpenAI, Llama, Anthropic, etc.) has its own implementation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class TokenCountResult:
    """Result from token counting operation"""
    input_tokens: int
    output_tokens: int = 0
    image_tokens: int = 0
    system_tokens: int = 0
    tool_tokens: int = 0

    # Metadata
    cached: bool = False  # True if from cache
    source: str = "local"  # "local", "api", "formula"
    latency_ms: float = 0.0
    provider: str = ""
    model: str = ""

    @property
    def total_tokens(self) -> int:
        """Total tokens (all types)"""
        return (
            self.input_tokens +
            self.output_tokens +
            self.image_tokens +
            self.system_tokens +
            self.tool_tokens
        )


class TokenCounter(ABC):
    """Abstract base class for provider-specific token counters"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name (e.g., 'openai', 'anthropic', 'huggingface')"""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """List of supported models (patterns: 'gpt-4*', 'claude-*', 'llama-*')"""
        pass

    @abstractmethod
    def count(self, text: str, model: str) -> TokenCountResult:
        """
        Count tokens for text input.

        Args:
            text: Input text to tokenize
            model: Model ID (e.g., 'gpt-4o', 'claude-3-5-sonnet', 'llama-70b')

        Returns:
            TokenCountResult with input token count
        """
        pass

    def count_vision(
        self,
        text: str,
        model: str,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        num_images: int = 1
    ) -> TokenCountResult:
        """
        Count tokens for text + vision input.

        Override if provider supports vision tokenization.
        Default: return text tokens (no vision support).
        """
        return self.count(text, model)

    def count_system_prompt(self, system_prompt: str, model: str) -> int:
        """Count tokens in system prompt (optimization for repeated prompts)"""
        return self.count(system_prompt, model).input_tokens

    def count_tools(self, tools: List[Dict[str, Any]], model: str) -> int:
        """Count tokens in tool definitions"""
        # Convert tools to string representation
        tools_str = str(tools)  # Simple approach; can be refined
        return self.count(tools_str, model).input_tokens

    def count_batch(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[TokenCountResult]:
        """
        Count tokens for multiple requests (enables batch optimization).

        Each request: {"text": "...", "model": "...", "type": "text|vision"}
        """
        return [
            self.count(req["text"], req["model"])
            for req in requests
        ]

    @abstractmethod
    def validate_model(self, model: str) -> bool:
        """Check if this counter supports the model"""
        pass

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return info about this tokenizer (version, vocabulary size, etc.)"""
        return {
            "provider": self.provider_name,
            "supported_models": self.supported_models,
        }
