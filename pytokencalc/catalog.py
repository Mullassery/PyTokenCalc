"""Built-in model catalog.

This is the OpenRouter-inspired metadata layer PyTokenCalc's pricing table
lacked: canonical model IDs, aliases, tokenizer family, context window,
output limit, and input/output modalities. Pricing stays in
:mod:`pytokencalc.pricing`; this module only describes the models.

The catalog is intentionally a reviewed snapshot, not a live feed. Custom
models can be added at runtime with :func:`register_model_spec`, or pricing
can be supplied through :func:`pytokencalc.pricing.load_pricing_override`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .pricing import get_model_pricing, resolve_model_pricing_key


@dataclass(frozen=True)
class ProviderEndpoint:
    """A provider/platform serving a model, possibly at a different price."""

    provider: str
    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    quantizations: Tuple[str, ...] = ()
    input_per_million: Optional[float] = None
    output_per_million: Optional[float] = None
    cache_read_per_million: Optional[float] = None
    cache_write_per_million: Optional[float] = None
    request_fee_usd: float = 0.0
    uptime_last_30m: Optional[float] = None
    latency_p50_seconds: Optional[float] = None
    throughput_tokens_per_second: Optional[float] = None
    status: Optional[str] = None
    note: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "provider": self.provider,
            "context_length": self.context_length,
            "max_output_tokens": self.max_output_tokens,
            "quantizations": list(self.quantizations),
            "pricing_per_million": (
                {
                    "input": self.input_per_million,
                    "output": self.output_per_million,
                    "cache_read": self.cache_read_per_million,
                    "cache_write": self.cache_write_per_million,
                    "request_fee_usd": self.request_fee_usd,
                }
                if self.input_per_million is not None
                and self.output_per_million is not None
                else None
            ),
            "uptime_last_30m": self.uptime_last_30m,
            "latency_p50_seconds": self.latency_p50_seconds,
            "throughput_tokens_per_second": self.throughput_tokens_per_second,
            "status": self.status,
            "note": self.note,
        }


@dataclass(frozen=True)
class ModelSpec:
    """Normalized metadata for one model."""

    id: str
    name: str
    provider: str
    aliases: Tuple[str, ...] = ()
    tokenizer: Optional[str] = None
    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    input_modalities: Tuple[str, ...] = ("text",)
    output_modalities: Tuple[str, ...] = ("text",)
    capabilities: Tuple[str, ...] = ()
    endpoints: Tuple[ProviderEndpoint, ...] = ()
    expiration_date: Optional[str] = None
    source: str = "builtin"

    @property
    def pricing(self):
        """Return the model's :class:`~pytokencalc.pricing.ModelPricing`."""
        return get_model_pricing(self.id)

    @property
    def supports_vision(self) -> bool:
        return "image" in self.input_modalities

    def to_dict(self) -> Dict[str, object]:
        pricing = self.pricing
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "aliases": list(self.aliases),
            "tokenizer": self.tokenizer,
            "context_length": self.context_length,
            "max_output_tokens": self.max_output_tokens,
            "input_modalities": list(self.input_modalities),
            "output_modalities": list(self.output_modalities),
            "capabilities": list(self.capabilities),
            "expiration_date": self.expiration_date,
            "pricing_per_million": (
                {
                    "input": pricing.input_per_million,
                    "output": pricing.output_per_million,
                    "cache_read": pricing.cache_read_per_million,
                    "cache_write": pricing.cache_write_per_million,
                    "request_fee_usd": pricing.request_fee_usd,
                }
                if pricing is not None
                else None
            ),
            "endpoints": [endpoint.to_dict() for endpoint in self.endpoints],
            "source": self.source,
        }


_SPECS: Tuple[ModelSpec, ...] = (
    # --- OpenAI ---------------------------------------------------------
    ModelSpec(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        aliases=("gpt-4o-latest",),
        tokenizer="o200k_base",
        context_length=128_000,
        max_output_tokens=16_384,
        input_modalities=("text", "image"),
    ),
    ModelSpec(
        id="gpt-4o-mini",
        name="GPT-4o mini",
        provider="openai",
        aliases=("gpt-4o-mini-latest",),
        tokenizer="o200k_base",
        context_length=128_000,
        max_output_tokens=16_384,
        input_modalities=("text", "image"),
    ),
    ModelSpec(
        id="gpt-4-turbo",
        name="GPT-4 Turbo",
        provider="openai",
        tokenizer="cl100k_base",
        context_length=128_000,
        max_output_tokens=4_096,
        input_modalities=("text", "image"),
    ),
    ModelSpec(
        id="gpt-4-32k",
        name="GPT-4 32K",
        provider="openai",
        tokenizer="cl100k_base",
        context_length=32_768,
    ),
    ModelSpec(
        id="gpt-4",
        name="GPT-4",
        provider="openai",
        tokenizer="cl100k_base",
        context_length=8_192,
    ),
    ModelSpec(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        provider="openai",
        tokenizer="cl100k_base",
        context_length=16_385,
        max_output_tokens=4_096,
    ),
    ModelSpec(
        id="text-davinci-003",
        name="text-davinci-003",
        provider="openai",
        tokenizer="p50k_base",
        context_length=4_097,
    ),
    ModelSpec(
        id="text-davinci-002",
        name="text-davinci-002",
        provider="openai",
        tokenizer="p50k_base",
        context_length=4_097,
    ),
    # --- Azure OpenAI ---------------------------------------------------
    ModelSpec(
        id="gpt-35-turbo",
        name="GPT-3.5 Turbo (Azure)",
        provider="azure",
        aliases=("gpt-35-turbo-16k",),
        tokenizer="cl100k_base",
        context_length=16_385,
        max_output_tokens=4_096,
    ),
    # --- Anthropic ------------------------------------------------------
    ModelSpec(
        id="claude-3-opus",
        name="Claude 3 Opus",
        provider="anthropic",
        aliases=("claude-3-opus-latest",),
        tokenizer="anthropic",
        context_length=200_000,
        max_output_tokens=4_096,
        input_modalities=("text", "image"),
    ),
    ModelSpec(
        id="claude-3-5-sonnet",
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        aliases=("claude-3-5-sonnet-latest",),
        tokenizer="anthropic",
        context_length=200_000,
        max_output_tokens=8_192,
        input_modalities=("text", "image"),
    ),
    ModelSpec(
        id="claude-3-sonnet",
        name="Claude 3 Sonnet",
        provider="anthropic",
        tokenizer="anthropic",
        context_length=200_000,
        max_output_tokens=4_096,
        input_modalities=("text", "image"),
    ),
    ModelSpec(
        id="claude-3-5-haiku",
        name="Claude 3.5 Haiku",
        provider="anthropic",
        aliases=("claude-3-5-haiku-latest",),
        tokenizer="anthropic",
        context_length=200_000,
        max_output_tokens=8_192,
        input_modalities=("text", "image"),
    ),
    ModelSpec(
        id="claude-3-haiku",
        name="Claude 3 Haiku",
        provider="anthropic",
        tokenizer="anthropic",
        context_length=200_000,
        max_output_tokens=4_096,
        input_modalities=("text", "image"),
    ),
    # --- Google Gemini --------------------------------------------------
    ModelSpec(
        id="gemini-1.5-pro",
        name="Gemini 1.5 Pro",
        provider="google",
        aliases=("gemini-1.5-pro-latest",),
        tokenizer="gemini",
        context_length=2_097_152,
        max_output_tokens=8_192,
        input_modalities=("text", "image", "audio", "video"),
    ),
    ModelSpec(
        id="gemini-1.5-flash",
        name="Gemini 1.5 Flash",
        provider="google",
        aliases=("gemini-1.5-flash-latest",),
        tokenizer="gemini",
        context_length=1_048_576,
        max_output_tokens=8_192,
        input_modalities=("text", "image", "audio", "video"),
    ),
    ModelSpec(
        id="gemini-2-flash",
        name="Gemini 2 Flash",
        provider="google",
        tokenizer="gemini",
        context_length=1_048_576,
        max_output_tokens=8_192,
        input_modalities=("text", "image", "audio", "video"),
    ),
    ModelSpec(
        id="gemini-pro",
        name="Gemini Pro",
        provider="google",
        tokenizer="gemini",
        context_length=32_760,
        max_output_tokens=2_048,
    ),
    # --- Cohere ---------------------------------------------------------
    ModelSpec(
        id="command-r-plus",
        name="Command R+",
        provider="cohere",
        tokenizer="cohere",
        context_length=128_000,
        max_output_tokens=4_096,
    ),
    ModelSpec(
        id="command-r",
        name="Command R",
        provider="cohere",
        tokenizer="cohere",
        context_length=128_000,
        max_output_tokens=4_096,
    ),
    ModelSpec(
        id="command-light",
        name="Command Light",
        provider="cohere",
        tokenizer="cohere",
        context_length=4_096,
        max_output_tokens=4_096,
    ),
    ModelSpec(
        id="command",
        name="Command",
        provider="cohere",
        tokenizer="cohere",
        context_length=4_096,
        max_output_tokens=4_096,
    ),
)

_CATALOG: Dict[str, ModelSpec] = {spec.id: spec for spec in _SPECS}


def register_model_spec(spec: ModelSpec, *, overwrite: bool = False) -> None:
    """Add or replace a model in the process-wide catalog."""
    key = spec.id.strip().lower()
    if not key:
        raise ValueError("ModelSpec.id must be a non-empty string")
    if key in _CATALOG and not overwrite:
        raise ValueError(f"Model spec already registered: {spec.id}")
    _CATALOG[key] = spec


def get_model_spec(model: str) -> Optional[ModelSpec]:
    """Return the catalog entry for *model*, or None if unknown."""
    if not model:
        return None

    normalized = model.strip().lower()
    pricing_key = resolve_model_pricing_key(model)
    if pricing_key is not None and pricing_key in _CATALOG:
        return _CATALOG[pricing_key]

    if normalized in _CATALOG:
        return _CATALOG[normalized]

    for spec in _CATALOG.values():
        if normalized == spec.id.lower() or normalized in {
            alias.lower() for alias in spec.aliases
        }:
            return spec

    if "/" in normalized:
        tail = normalized.rsplit("/", 1)[1]
        if tail in _CATALOG:
            return _CATALOG[tail]

    return None


def list_models(provider: Optional[str] = None) -> List[ModelSpec]:
    """Return catalog entries, optionally filtered by provider."""
    specs = sorted(_CATALOG.values(), key=lambda spec: spec.id)
    if provider:
        provider_lower = provider.lower()
        specs = [spec for spec in specs if spec.provider.lower() == provider_lower]
    return specs
