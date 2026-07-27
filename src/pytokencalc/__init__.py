"""
PyTokenCalc v0.9: Universal Token Counting for ANY LLM

One library. One API. Every LLM provider. Custom models. BYOM support.

Features:
- 8 cloud providers (OpenAI, Anthropic, Google, Cohere, Azure, etc.)
- 7 local inference engines (Ollama, LM Studio, LocalAI, Llama.cpp, etc.)
- Custom provider registration (bring your own provider)
- BYOM: Bring your own model (fine-tuned, proprietary, custom)
- Model discovery (automatic provider suggestion)
- Platform-aware token counting (handles variations across platforms)
- Temporal variation tracking (session-based monitoring)
- Forward-compatible (new models work without code updates)
- 99%+ accuracy verified against official counters
- Intelligent caching: 70-80% fewer API calls

Supported Providers:
- Cloud APIs: OpenAI GPT, Anthropic Claude, Google Gemini, Cohere Command, Azure OpenAI
- Cloud Services: RunPod, Together AI, Replicate, HuggingFace Inference, Llama Labs
- Local Inference: Ollama, LM Studio, LocalAI, Llama.cpp, GPT4All, Text Generation WebUI, Jan
- Custom: Any provider with an API endpoint, any model, any framework

Token Counting + Workflow Automation:
- Count tokens for any LLM (cloud, local, custom, BYOM)
- Intelligent routing (local when fast, API when accurate)
- Aggressive caching (70-80% fewer API calls)
- CLI + REST API for workflow automation (n8n, Power Automate, Temporal, Airflow)
- No external services or persistence required
- No configuration needed

Repository: https://github.com/Mullassery/PyTokenCalc
Documentation: https://github.com/Mullassery/PyTokenCalc/blob/main/README.md
Custom Providers: https://github.com/Mullassery/PyTokenCalc/blob/main/CUSTOM_PROVIDERS.md
"""

__version__ = "0.9.0"
__author__ = "Georgi Mammen Mullassery"

# Token counting (v0.7+: Multi-provider token counter)
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

__all__ = [
    # Token counting interface
    "TokenCounter",
    "TokenCountResult",
    "TokenCounterRegistry",
    "TokenCounterCache",
]
