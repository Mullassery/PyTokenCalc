"""
PyTokenCalc v1.5.0: Universal Token Counting for ANY LLM

One library. One API. Every LLM provider. Custom models. BYOM support.

Features:
- 8 cloud providers (OpenAI, Anthropic, Google, Cohere, Azure, etc.)
- 7 local inference engines (Ollama, LM Studio, LocalAI, Llama.cpp, etc.)
- Custom provider registration (bring your own provider)
- BYOM: Bring your own model (fine-tuned, proprietary, custom)
- Model discovery (automatic provider suggestion)
- Platform-aware token counting (handles variations across platforms)
- Temporal variation tracking (session-based monitoring)
- Best-effort forward compatibility for new model IDs
- Deterministic local tokenizers; provider-API counters where required
- In-memory caching for repeated counts
- Model catalog with context windows, modalities, and aliases
- Usage-aware cost breakdowns (cache reads/writes + request fees)
- Provider usage reconciliation for OpenAI, Anthropic, and OpenRouter
- Chat/tool preflight for context fit and cost before sending
- StatGuardian quality validation (v1.0.0+)

Supported Providers:
- Cloud APIs: OpenAI GPT, Anthropic Claude, Google Gemini, Cohere Command, Azure OpenAI
- Cloud Services: RunPod, Together AI, Replicate, HuggingFace Inference, Llama Labs
- Local Inference: Ollama, LM Studio, LocalAI, Llama.cpp, GPT4All, Text Generation WebUI, Jan
- Custom: Any provider with an API endpoint, any model, any framework

Token Counting + Workflow Automation:
- Count tokens for any LLM (cloud, local, custom, BYOM)
- Intelligent routing (local when fast, API when accurate)
- In-memory caching for repeated counts
- CLI + REST API for workflow automation (n8n, Power Automate, Temporal, Airflow)
- No external services or persistence required
- No configuration needed

Repository: https://github.com/Mullassery/PyTokenCalc
Documentation: https://github.com/Mullassery/PyTokenCalc/blob/main/README.md
Custom Providers: https://github.com/Mullassery/PyTokenCalc/blob/main/CUSTOM_PROVIDERS.md
"""

from ._version import __version__

__author__ = "Georgi Mammen Mullassery"

# Top-level ergonomic API (v1.1.0+): count_tokens() -> int, estimate_cost() -> USD
from .api import count_tokens, estimate_cost
from .benchmark import ParitySampleResult, ParitySummary, benchmark_counts
from .catalog import (
    ModelSpec,
    ProviderEndpoint,
    get_model_spec,
    list_models,
    register_model_spec,
)
from .endpoints import (
    EndpointCostComparison,
    compare_endpoints,
    endpoint_pricing,
)
from .ledger import DEFAULT_LEDGER_PATH, UsageLedger
from .openrouter import (
    OpenRouterEndpointImportResult,
    OpenRouterImportResult,
    import_openrouter_catalog,
    import_openrouter_catalog_file,
    import_openrouter_endpoints,
    import_openrouter_endpoints_file,
)
from .preflight import PreflightResult, preflight
from .pricing import (
    PRICING_LAST_UPDATED,
    PRICING_TABLE,
    CostBreakdown,
    ModelCostComparison,
    ModelPricing,
    Usage,
    compare_models,
    estimate_usage,
    get_model_pricing,
    load_pricing_override,
    pricing_status,
)
from .reconcile import Reconciliation, parse_usage, reconcile

# Token counting (v0.7+: Multi-provider token counter)
try:
    from .tokenizers import (
        TokenCounter,
        TokenCounterCache,
        TokenCounterRegistry,
        TokenCountResult,
        get_global_registry,
    )
    TOKENIZERS_AVAILABLE = True
except ImportError:
    TOKENIZERS_AVAILABLE = False
    TokenCounter = None
    TokenCountResult = None
    TokenCounterRegistry = None
    TokenCounterCache = None
    get_global_registry = None

# Model discovery
# MCP 2.0 Support (v1.0.3+)
from pytokencalc._mcp_connector import TokenCalculator

from .cli import CLIInterface

# Exceptions
from .exceptions import (
    APIError,
    CacheError,
    ModelNotSupportedError,
    PyTokenCalcError,
    TokenCountError,
    ValidationError,
)
from .model_discovery import ModelDiscovery

# OKF integration (token baselines, optimization)
from .okf_token_baselines import (
    BaselineEstimate,
    OKFTokenBaselines,
    TokenBaseline,
    build_baseline_from_samples,
    estimate_from_baseline,
)
from .quick_cli import QuickCLI

# Server and CLI
from .server import PyTokenCalcServer

# StatGuardian integration (quality validation, cost prediction, etc.)
from .statguardian_integration import (
    CostPredictionContract,
    ModelEfficiencyContract,
    ProviderReliabilityContract,
    StatGuardianTokenCounter,
    TokenCountContract,
    TokenCountValidation,
)

__all__ = [
    # Package version
    "__version__",
    # Top-level ergonomic API
    "count_tokens",
    "estimate_cost",
    "get_model_pricing",
    "ModelPricing",
    "PRICING_TABLE",
    "PRICING_LAST_UPDATED",
    "load_pricing_override",
    "pricing_status",
    "Usage",
    "CostBreakdown",
    "ModelCostComparison",
    "compare_models",
    "estimate_usage",
    "ModelSpec",
    "ProviderEndpoint",
    "get_model_spec",
    "list_models",
    "register_model_spec",
    "ParitySampleResult",
    "ParitySummary",
    "benchmark_counts",
    "EndpointCostComparison",
    "compare_endpoints",
    "endpoint_pricing",
    "Reconciliation",
    "parse_usage",
    "reconcile",
    "PreflightResult",
    "preflight",
    "OpenRouterImportResult",
    "OpenRouterEndpointImportResult",
    "import_openrouter_catalog",
    "import_openrouter_catalog_file",
    "import_openrouter_endpoints",
    "import_openrouter_endpoints_file",
    "UsageLedger",
    "DEFAULT_LEDGER_PATH",
    # Token counting interface
    "TokenCounter",
    "TokenCountResult",
    "TokenCounterRegistry",
    "TokenCounterCache",
    "get_global_registry",
    # Model discovery
    "ModelDiscovery",
    # Exceptions
    "PyTokenCalcError",
    "ValidationError",
    "TokenCountError",
    "ModelNotSupportedError",
    "APIError",
    "CacheError",
    # StatGuardian integration
    "TokenCountValidation",
    "TokenCountContract",
    "ModelEfficiencyContract",
    "CostPredictionContract",
    "ProviderReliabilityContract",
    "StatGuardianTokenCounter",
    # OKF integration
    "TokenBaseline",
    "OKFTokenBaselines",
    "BaselineEstimate",
    "build_baseline_from_samples",
    "estimate_from_baseline",
    # Server and CLI
    "PyTokenCalcServer",
    "CLIInterface",
    "QuickCLI",
    # MCP
    "TokenCalculator",
]
