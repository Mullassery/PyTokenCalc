"""
Provider-specific cost models for PyTokenCalc v0.6.

Different LLMs count and bill tokens differently:
- Claude: simple input/output token rates
- GPT-4o: split full + mini token counts
- Gemini: character-based billing (not tokens)
- Groq: speed-tiered pricing
- DeepSeek: batch-aware pricing
- Open-source APIs: quantization-dependent token counts
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum


class ModelFamily(Enum):
    """LLM model families"""
    CLAUDE = "claude"
    GPT = "gpt"
    GEMINI = "gemini"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    LLAMA = "llama"
    MISTRAL = "mistral"
    COHERE = "cohere"
    QWEN = "qwen"
    GLM = "glm"


@dataclass
class UsageData:
    """Provider-agnostic usage data structure with provider-specific fields"""
    provider: str
    model: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Standard tokens (all providers)
    input_tokens: int = 0
    output_tokens: int = 0

    # Provider-specific: GPT-4o (full + mini tokens)
    input_mini_tokens: Optional[int] = None
    output_mini_tokens: Optional[int] = None

    # Provider-specific: Gemini (character-based)
    input_characters: Optional[int] = None
    output_characters: Optional[int] = None

    # Provider-specific: Groq (speed-tiered)
    speed_tier: Optional[str] = None  # "standard", "fast", "fastest"

    # Provider-specific: DeepSeek (batch context)
    batch_size: Optional[int] = None
    is_batched: bool = False

    # Provider-specific: Open-source APIs (quantization)
    quantization_level: Optional[str] = None  # "int8", "int4", "fp8", "bf16"
    model_variant: Optional[str] = None  # "Llama 2 vs 3 vs 3.1"

    # Metadata
    task_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CostModel(ABC):
    """Abstract base class for provider-specific cost models"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name (e.g., 'anthropic', 'openai', 'google')"""
        pass

    @abstractmethod
    def calculate(self, usage: UsageData) -> float:
        """Calculate cost in USD based on provider-specific usage data"""
        pass

    @abstractmethod
    def validate(self, usage: UsageData) -> bool:
        """Validate that usage data has all required fields"""
        pass

    def get_pricing_info(self, model: str) -> Dict[str, Any]:
        """Get pricing details for a model"""
        raise NotImplementedError


class ClaudeTokenModel(CostModel):
    """Claude token-based cost model (simple input/output rates)"""

    PRICING = {
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
    }

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def calculate(self, usage: UsageData) -> float:
        """Calculate Claude cost from input/output tokens"""
        if not self.validate(usage):
            raise ValueError(f"Invalid usage data for Claude: {usage}")

        pricing = self.PRICING.get(usage.model)
        if not pricing:
            raise ValueError(f"Unknown Claude model: {usage.model}")

        input_cost = (usage.input_tokens * pricing["input"]) / 1_000_000
        output_cost = (usage.output_tokens * pricing["output"]) / 1_000_000
        return input_cost + output_cost

    def validate(self, usage: UsageData) -> bool:
        """Claude requires input and output tokens"""
        return (
            usage.provider == self.provider_name
            and usage.input_tokens >= 0
            and usage.output_tokens >= 0
            and usage.model in self.PRICING
        )


class GPT4oTokenModel(CostModel):
    """GPT-4o dual-token cost model (full + mini tokens)"""

    PRICING = {
        "gpt-4o": {
            "input_full": 2.50,
            "input_mini": 0.625,
            "output_full": 10.00,
            "output_mini": 2.50,
        },
        "gpt-4o-mini": {
            "input_full": 0.15,
            "input_mini": 0.0375,
            "output_full": 0.60,
            "output_mini": 0.15,
        },
        "gpt-4-turbo": {
            "input": 10.00,
            "output": 30.00,
        },
    }

    @property
    def provider_name(self) -> str:
        return "openai"

    def calculate(self, usage: UsageData) -> float:
        """Calculate GPT-4o cost with mini token support"""
        if not self.validate(usage):
            raise ValueError(f"Invalid usage data for GPT-4o: {usage}")

        pricing = self.PRICING.get(usage.model)
        if not pricing:
            raise ValueError(f"Unknown GPT model: {usage.model}")

        # GPT-4o uses full + mini tokens
        if "input_full" in pricing:
            input_cost = (
                (usage.input_tokens * pricing["input_full"]) +
                ((usage.input_mini_tokens or 0) * pricing["input_mini"])
            ) / 1_000_000

            output_cost = (
                (usage.output_tokens * pricing["output_full"]) +
                ((usage.output_mini_tokens or 0) * pricing["output_mini"])
            ) / 1_000_000
        else:
            # Fallback to standard pricing
            input_cost = (usage.input_tokens * pricing["input"]) / 1_000_000
            output_cost = (usage.output_tokens * pricing["output"]) / 1_000_000

        return input_cost + output_cost

    def validate(self, usage: UsageData) -> bool:
        """GPT-4o requires tokens, mini tokens optional"""
        return (
            usage.provider == self.provider_name
            and usage.input_tokens >= 0
            and usage.output_tokens >= 0
            and usage.model in self.PRICING
        )


class GeminiCharacterModel(CostModel):
    """Gemini character-based cost model (not token-based)"""

    PRICING = {
        "gemini-2-flash": {
            "input": 0.000000375,  # $3.75 per billion characters
            "output": 0.0000015,   # $1.50 per billion characters
        },
        "gemini-1-5-pro": {
            "input": 0.0075,
            "output": 0.03,
        },
    }

    @property
    def provider_name(self) -> str:
        return "google"

    def calculate(self, usage: UsageData) -> float:
        """Calculate Gemini cost from character counts"""
        if not self.validate(usage):
            raise ValueError(f"Invalid usage data for Gemini: {usage}")

        pricing = self.PRICING.get(usage.model)
        if not pricing:
            raise ValueError(f"Unknown Gemini model: {usage.model}")

        # Gemini charges per character, not per token
        input_cost = ((usage.input_characters or 0) * pricing["input"])
        output_cost = ((usage.output_characters or 0) * pricing["output"])
        return input_cost + output_cost

    def validate(self, usage: UsageData) -> bool:
        """Gemini requires character counts"""
        return (
            usage.provider == self.provider_name
            and (usage.input_characters is not None or usage.input_tokens > 0)
            and (usage.output_characters is not None or usage.output_tokens > 0)
            and usage.model in self.PRICING
        )


class GroqSpeedTieredModel(CostModel):
    """Groq speed-tiered cost model (pricing varies by speed tier)"""

    BASE_PRICING = {
        "llama-70b": {
            "input": 0.59,
            "output": 0.79,
        },
        "mixtral-8x7b": {
            "input": 0.24,
            "output": 0.24,
        },
    }

    SPEED_TIERS = {
        "standard": 1.0,      # Base rate
        "fast": 2.0,          # 2x cost
        "fastest": 3.0,       # 3x cost
    }

    @property
    def provider_name(self) -> str:
        return "groq"

    def calculate(self, usage: UsageData) -> float:
        """Calculate Groq cost with speed tier multiplier"""
        if not self.validate(usage):
            raise ValueError(f"Invalid usage data for Groq: {usage}")

        base_pricing = self.BASE_PRICING.get(usage.model)
        if not base_pricing:
            raise ValueError(f"Unknown Groq model: {usage.model}")

        # Apply speed tier multiplier
        speed_multiplier = self.SPEED_TIERS.get(usage.speed_tier or "standard", 1.0)

        input_cost = (usage.input_tokens * base_pricing["input"] * speed_multiplier) / 1_000_000
        output_cost = (usage.output_tokens * base_pricing["output"] * speed_multiplier) / 1_000_000
        return input_cost + output_cost

    def validate(self, usage: UsageData) -> bool:
        """Groq requires tokens and optional speed tier"""
        return (
            usage.provider == self.provider_name
            and usage.input_tokens >= 0
            and usage.output_tokens >= 0
            and usage.model in self.BASE_PRICING
            and (usage.speed_tier is None or usage.speed_tier in self.SPEED_TIERS)
        )


class DeepInfraTokenModel(CostModel):
    """DeepInfra open-source API token model (per 1M tokens)"""

    PRICING = {
        "llama-70b": {"input": 0.23, "output": 0.23},
        "llama-8b": {"input": 0.07, "output": 0.07},
        "mixtral-8x7b": {"input": 0.24, "output": 0.24},
        "deepseek-v3": {"input": 0.014, "output": 0.014},
        "qwen-32b": {"input": 0.08, "output": 0.08},
    }

    @property
    def provider_name(self) -> str:
        return "deepinfra"

    def calculate(self, usage: UsageData) -> float:
        """Calculate DeepInfra cost from token counts"""
        if not self.validate(usage):
            raise ValueError(f"Invalid usage data for DeepInfra: {usage}")

        pricing = self.PRICING.get(usage.model)
        if not pricing:
            raise ValueError(f"Unknown DeepInfra model: {usage.model}")

        input_cost = (usage.input_tokens * pricing["input"]) / 1_000_000
        output_cost = (usage.output_tokens * pricing["output"]) / 1_000_000
        return input_cost + output_cost

    def validate(self, usage: UsageData) -> bool:
        """DeepInfra requires input/output tokens"""
        return (
            usage.provider == self.provider_name
            and usage.input_tokens >= 0
            and usage.output_tokens >= 0
            and usage.model in self.PRICING
        )


class TogetherAITokenModel(CostModel):
    """Together.ai open-source API token model"""

    PRICING = {
        "llama-70b": {"input": 0.88, "output": 1.10},
        "llama-8b": {"input": 0.08, "output": 0.10},
        "mixtral-8x7b": {"input": 0.30, "output": 0.30},
    }

    @property
    def provider_name(self) -> str:
        return "together"

    def calculate(self, usage: UsageData) -> float:
        """Calculate Together.ai cost"""
        if not self.validate(usage):
            raise ValueError(f"Invalid usage data for Together.ai: {usage}")

        pricing = self.PRICING.get(usage.model)
        if not pricing:
            raise ValueError(f"Unknown Together.ai model: {usage.model}")

        input_cost = (usage.input_tokens * pricing["input"]) / 1_000_000
        output_cost = (usage.output_tokens * pricing["output"]) / 1_000_000
        return input_cost + output_cost

    def validate(self, usage: UsageData) -> bool:
        """Together.ai requires input/output tokens"""
        return (
            usage.provider == self.provider_name
            and usage.input_tokens >= 0
            and usage.output_tokens >= 0
            and usage.model in self.PRICING
        )


class CostModelRegistry:
    """Registry of all supported cost models"""

    def __init__(self):
        self.models = {
            "anthropic": ClaudeTokenModel(),
            "openai": GPT4oTokenModel(),
            "google": GeminiCharacterModel(),
            "groq": GroqSpeedTieredModel(),
            "deepinfra": DeepInfraTokenModel(),
            "together": TogetherAITokenModel(),
        }

    def get_model(self, provider: str) -> Optional[CostModel]:
        """Get cost model for provider"""
        return self.models.get(provider.lower())

    def register_model(self, provider: str, model: CostModel):
        """Register a new cost model"""
        self.models[provider.lower()] = model

    def list_providers(self) -> list:
        """List all registered providers"""
        return list(self.models.keys())

    def calculate_cost(self, usage: UsageData) -> float:
        """Calculate cost using appropriate provider model"""
        model = self.get_model(usage.provider)
        if not model:
            raise ValueError(f"No cost model for provider: {usage.provider}")

        return model.calculate(usage)
