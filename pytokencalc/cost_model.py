"""
Unified multi-provider cost model.
Abstraction layer for calculating costs across OpenAI, Bedrock, and Gemini.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid


class ProviderType(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    BEDROCK = "bedrock"
    GEMINI = "gemini"
    CLAUDE = "claude"  # Direct Anthropic API


@dataclass
class Cost:
    """Represents the cost of a single LLM API call"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    input_cost: float = 0.0  # dollars
    output_cost: float = 0.0  # dollars
    total_cost: float = 0.0  # dollars
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure total_cost is accurate"""
        self.total_cost = self.input_cost + self.output_cost


class Provider(ABC):
    """Abstract base class for LLM providers"""

    name: str

    @abstractmethod
    def detect_call(self, call_data: Dict[str, Any]) -> bool:
        """Check if this call is for this provider"""
        pass

    @abstractmethod
    def calculate_cost(
        self,
        call_data: Dict[str, Any],
        response_data: Dict[str, Any]
    ) -> Optional[Cost]:
        """Calculate cost for a single call"""
        pass

    @abstractmethod
    def validate_pricing(self) -> bool:
        """Validate pricing table is loaded correctly"""
        pass

    def _get_tokens_from_response(self, response_data: Dict) -> tuple:
        """Helper to extract input/output tokens from response"""
        # Override in subclasses
        return 0, 0


class OpenAIProvider(Provider):
    """OpenAI GPT-4/GPT-5 cost calculator"""

    name = "openai"

    # Mock pricing - replaces with API pricing in production
    PRICING = {
        'gpt-4': {'input': 0.030, 'output': 0.060},  # $/1K tokens
        'gpt-4-turbo': {'input': 0.010, 'output': 0.030},
        'gpt-4-vision': {'input': 0.030, 'output': 0.060, 'vision_premium': 0.25},
        'gpt-5': {'input': 0.050, 'output': 0.150},
        'gpt-5-turbo': {'input': 0.020, 'output': 0.060},
    }

    def detect_call(self, call_data: Dict[str, Any]) -> bool:
        """Detect if this is an OpenAI call"""
        model = call_data.get('model', '')
        return 'gpt' in model.lower()

    def calculate_cost(
        self,
        call_data: Dict[str, Any],
        response_data: Dict[str, Any]
    ) -> Optional[Cost]:
        """Calculate OpenAI cost"""
        model = call_data.get('model', 'gpt-4')

        # Normalize model name
        model = self._normalize_model_name(model)

        if model not in self.PRICING:
            raise ValueError(f"Unknown OpenAI model: {model}")

        # Extract tokens from response
        usage = response_data.get('usage', {})
        input_tokens = usage.get('prompt_tokens', 0)
        output_tokens = usage.get('completion_tokens', 0)

        # Get pricing
        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']

        # Handle vision premium
        vision_premium = 0.0
        if 'vision' in model or call_data.get('vision'):
            vision_premium = pricing.get('vision_premium', 0.25)
            input_cost *= (1 + vision_premium)

        return Cost(
            provider='openai',
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
            details={'vision_premium': vision_premium}
        )

    def validate_pricing(self) -> bool:
        """Validate pricing table"""
        return all(
            'input' in p and 'output' in p
            for p in self.PRICING.values()
        )

    @staticmethod
    def _normalize_model_name(model: str) -> str:
        """Normalize model names to pricing table keys"""
        model_lower = model.lower()

        if 'gpt-5' in model_lower:
            return 'gpt-5-turbo' if 'turbo' in model_lower else 'gpt-5'
        elif 'gpt-4' in model_lower:
            if 'vision' in model_lower:
                return 'gpt-4-vision'
            return 'gpt-4-turbo' if 'turbo' in model_lower else 'gpt-4'

        return model_lower


class BedrockProvider(Provider):
    """AWS Bedrock cost calculator (Claude, Llama, Mistral)"""

    name = "bedrock"

    # Mock pricing
    PRICING = {
        'anthropic.claude-3-opus': {'input': 0.015, 'output': 0.075},  # $/1K tokens
        'anthropic.claude-3-sonnet': {'input': 0.003, 'output': 0.015},
        'anthropic.claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
        'meta.llama2-70b-chat': {'input': 0.0008, 'output': 0.001},
        'meta.llama2-13b-chat': {'input': 0.00075, 'output': 0.001},
        'mistral.mistral-7b-instruct': {'input': 0.00015, 'output': 0.0004},
        'mistral.mistral-large': {'input': 0.008, 'output': 0.024},
    }

    # Provisioned throughput discount
    PROVISIONED_DISCOUNT = 0.1  # 10% off

    def detect_call(self, call_data: Dict[str, Any]) -> bool:
        """Detect if this is a Bedrock call"""
        model_id = call_data.get('modelId', '')
        return any(prefix in model_id for prefix in ['anthropic', 'meta.', 'mistral.'])

    def calculate_cost(
        self,
        call_data: Dict[str, Any],
        response_data: Dict[str, Any]
    ) -> Optional[Cost]:
        """Calculate Bedrock cost"""
        model_id = call_data.get('modelId', '')

        if model_id not in self.PRICING:
            raise ValueError(f"Unknown Bedrock model: {model_id}")

        # Extract tokens
        usage = response_data.get('usage', {})
        input_tokens = usage.get('inputTokens', 0)
        output_tokens = usage.get('outputTokens', 0)

        # Get pricing
        pricing = self.PRICING[model_id]
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']

        # Apply provisioned throughput discount if applicable
        discount = 0.0
        if call_data.get('provisioned_throughput_arn'):
            discount = self.PROVISIONED_DISCOUNT
            input_cost *= (1 - discount)
            output_cost *= (1 - discount)

        return Cost(
            provider='bedrock',
            model=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
            details={'provisioned_discount': discount}
        )

    def validate_pricing(self) -> bool:
        """Validate pricing table"""
        return all(
            'input' in p and 'output' in p
            for p in self.PRICING.values()
        )


class GeminiProvider(Provider):
    """Google Gemini cost calculator"""

    name = "gemini"

    # Mock pricing
    PRICING = {
        'gemini-pro': {'input': 0.000125, 'output': 0.000375},  # $/1K tokens
        'gemini-pro-vision': {'input': 0.000125, 'output': 0.000375},
        'gemini-1.5-pro': {'input': 0.0075, 'output': 0.03},
    }

    def detect_call(self, call_data: Dict[str, Any]) -> bool:
        """Detect if this is a Gemini call"""
        model = call_data.get('model', '')
        return 'gemini' in model.lower()

    def calculate_cost(
        self,
        call_data: Dict[str, Any],
        response_data: Dict[str, Any]
    ) -> Optional[Cost]:
        """Calculate Gemini cost"""
        model = call_data.get('model', 'gemini-pro')

        if model not in self.PRICING:
            raise ValueError(f"Unknown Gemini model: {model}")

        # Extract tokens
        usage = response_data.get('usage_metadata', {})
        input_tokens = usage.get('prompt_token_count', 0)
        output_tokens = usage.get('candidates_token_count', 0)

        # Get pricing
        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']

        return Cost(
            provider='gemini',
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
            details={}
        )

    def validate_pricing(self) -> bool:
        """Validate pricing table"""
        return all(
            'input' in p and 'output' in p
            for p in self.PRICING.values()
        )


class ProviderRegistry:
    """Registry of all supported providers"""

    def __init__(self):
        self.providers = {
            'openai': OpenAIProvider(),
            'bedrock': BedrockProvider(),
            'gemini': GeminiProvider(),
        }

    def detect_provider(self, call_data: Dict[str, Any]) -> Optional[Provider]:
        """Auto-detect provider from call data"""
        for provider in self.providers.values():
            if provider.detect_call(call_data):
                return provider
        return None

    def get_provider(self, name: str) -> Optional[Provider]:
        """Get provider by name"""
        return self.providers.get(name.lower())

    def list_providers(self) -> List[str]:
        """List all registered provider names"""
        return list(self.providers.keys())

    def register_provider(self, provider: Provider):
        """Register a new provider"""
        self.providers[provider.name] = provider


class CostTracker:
    """Main API for tracking costs across all providers"""

    def __init__(self):
        self.registry = ProviderRegistry()
        self.costs: List[Cost] = []

    def track_api_call(
        self,
        call_data: Dict[str, Any],
        response_data: Dict[str, Any]
    ) -> Optional[Cost]:
        """Track a single API call"""
        provider = self.registry.detect_provider(call_data)

        if not provider:
            # If we can't detect provider, return None
            return None

        cost = provider.calculate_cost(call_data, response_data)
        if cost:
            self.costs.append(cost)

        return cost

    def get_costs(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Cost]:
        """Get costs with optional filters"""
        results = self.costs

        if provider:
            results = [c for c in results if c.provider == provider]

        if model:
            results = [c for c in results if c.model == model]

        if start_time:
            results = [c for c in results if c.timestamp >= start_time]

        if end_time:
            results = [c for c in results if c.timestamp <= end_time]

        return results

    def get_total_cost(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> float:
        """Get total cost"""
        costs = self.get_costs(provider=provider, model=model)
        return sum(c.total_cost for c in costs)

    def cost_by_provider(self) -> Dict[str, float]:
        """Breakdown by provider"""
        breakdown = {}
        for cost in self.costs:
            breakdown[cost.provider] = breakdown.get(cost.provider, 0) + cost.total_cost
        return breakdown

    def cost_by_model(self) -> Dict[str, float]:
        """Breakdown by model"""
        breakdown = {}
        for cost in self.costs:
            breakdown[cost.model] = breakdown.get(cost.model, 0) + cost.total_cost
        return breakdown

    def clear(self):
        """Clear all tracked costs"""
        self.costs.clear()

    def export_costs(self) -> List[Dict[str, Any]]:
        """Export costs as dictionaries"""
        return [
            {
                'id': c.id,
                'timestamp': c.timestamp.isoformat(),
                'provider': c.provider,
                'model': c.model,
                'input_tokens': c.input_tokens,
                'output_tokens': c.output_tokens,
                'input_cost': c.input_cost,
                'output_cost': c.output_cost,
                'total_cost': c.total_cost,
                'details': c.details,
                'metadata': c.metadata,
            }
            for c in self.costs
        ]
