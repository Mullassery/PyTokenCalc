"""
PyTokenCalc v0.7: Multi-Provider LLM Token Counting & Cost Calculator

Unified token counting and cost calculation across 20+ cloud providers and 10+ open-source APIs.
The token counting core for OpenAnchor cost optimization middleware.

v0.6+ Multi-Provider Token Models:
- Provider-specific token counting (Claude simple, GPT-4o dual, Gemini character-based, etc.)
- Local tokenizers (tiktoken, HF transformers) - 60% of models
- Cloud APIs with aggressive caching (Anthropic, Google)
- Vision/multimodal support (images, PDFs)

v0.5 Core Features (Backwards Compatible):
- CostCalculator: Calculate cost for any provider/model/tokens
- CostDatabase: Track operations and aggregate costs
- PricingManager: Provider pricing + daily updates
- Budget Enforcement: Hard limits to prevent cost overruns

v0.7+ New Features:
- TokenCounterRegistry: Unified token counting interface
- Intelligent routing: auto-detect tokenizer per model
- In-memory caching: reduce API calls 70-80%
- Vision tokens: images, PDFs, multimodal

Core Team:
- PyTokenCalc: Token counting & cost calculation
- OpenAnchor: Cost optimization middleware
- PrismNote: OSS data science notebook

Repository: https://github.com/Mullassery/PyTokenCalc
"""

__version__ = "0.7.0"
__author__ = "Georgi Mammen Mullassery"

# Core cost calculation classes (v0.5 and v0.6)
from .cost_calculator import CostCalculator, CostCalculatorV6
from .cost_model import Cost, ProviderType
from .cost_models import (
    UsageData,
    CostModel,
    CostModelRegistry,
    ClaudeTokenModel,
    GPT4oTokenModel,
    GeminiCharacterModel,
    GroqSpeedTieredModel,
    DeepInfraTokenModel,
    TogetherAITokenModel,
)
from .pricing_manager import PricingManager
from .database import DatabaseManager
from .persistence import CostDatabase

# Tokenizers (v0.7+: Multi-provider token counting)
try:
    from .tokenizers import (
        TokenCounter,
        TokenCountResult,
        TokenCounterRegistry,
        TokenCounterCache,
    )
    TOKENIZERS_AVAILABLE = True
except ImportError:
    TOKENIZERS_AVAILABLE = False

# Safety feature: Hard budget enforcement
from ._budget_enforcement import (
    BudgetEnforcer,
    BudgetLimit,
    BudgetStatus,
    BudgetPeriod,
    EnforcementAction,
    BudgetExceededError,
    get_global_enforcer,
    set_budget_limit,
)

__all__ = [
    # Core v0.5 (backwards compatible)
    "CostCalculator",
    "Cost",
    "ProviderType",
    "PricingManager",
    "DatabaseManager",
    "CostDatabase",
    # v0.6+ multi-provider cost models
    "CostCalculatorV6",
    "UsageData",
    "CostModel",
    "CostModelRegistry",
    "ClaudeTokenModel",
    "GPT4oTokenModel",
    "GeminiCharacterModel",
    "GroqSpeedTieredModel",
    "DeepInfraTokenModel",
    "TogetherAITokenModel",
    # v0.7+ token counting (if available)
    "TokenCounter",
    "TokenCountResult",
    "TokenCounterRegistry",
    "TokenCounterCache",
    # Budget enforcement (safety feature)
    "BudgetEnforcer",
    "BudgetLimit",
    "BudgetStatus",
    "BudgetPeriod",
    "EnforcementAction",
    "BudgetExceededError",
    "get_global_enforcer",
    "set_budget_limit",
]
