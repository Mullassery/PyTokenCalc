"""Import OpenRouter's public model catalog snapshot.

No network request is made here. Download the catalog yourself, then pass the
JSON file (or parsed payload) to :func:`import_openrouter_catalog_file` /
:func:`import_openrouter_catalog`. This keeps imports reproducible and avoids
silent runtime price changes.

OpenRouter prices are USD per token; they are converted to the per-million
rates PyTokenCalc uses internally.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, List, Mapping, Optional, Tuple

from .catalog import (
    ModelSpec,
    ProviderEndpoint,
    get_model_spec,
    register_model_spec,
)
from .pricing import PRICING_TABLE, ModelPricing

_OPENROUTER_CAPABILITIES = ("tools", "reasoning", "structured_outputs")


@dataclass(frozen=True)
class OpenRouterImportResult:
    imported: int
    pricing_imported: int
    skipped_variants: int
    skipped_invalid: int
    warnings: Tuple[str, ...]
    source: str

    def to_dict(self) -> dict:
        return {
            "imported": self.imported,
            "pricing_imported": self.pricing_imported,
            "skipped_variants": self.skipped_variants,
            "skipped_invalid": self.skipped_invalid,
            "warnings": list(self.warnings),
            "source": self.source,
        }


def _models_from_payload(payload: Any) -> Tuple[List[Mapping[str, Any]], Optional[str]]:
    if isinstance(payload, Mapping):
        models = payload.get("data", payload.get("models"))
        fetched_at = payload.get("fetched_at") or payload.get("updated_at")
        if isinstance(models, (list, tuple)):
            return [model for model in models if isinstance(model, Mapping)], fetched_at
        raise ValueError('OpenRouter payload must contain a "data" or "models" array')
    if isinstance(payload, list):
        return [model for model in payload if isinstance(model, Mapping)], None
    raise ValueError("OpenRouter payload must be a JSON object or array")


def _per_million(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite() or parsed < 0:
        return None
    return float(parsed * Decimal(1_000_000))


def _request_fee(value: Any) -> Optional[float]:
    if value is None or value == "":
        return 0.0
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite() or parsed < 0:
        return None
    return float(parsed)


def _pricing_from_openrouter(raw: Mapping[str, Any]) -> Tuple[Optional[ModelPricing], List[str]]:
    warnings: List[str] = []
    input_price = _per_million(raw.get("prompt"))
    output_price = _per_million(raw.get("completion"))
    if input_price is None or output_price is None:
        return None, ["missing or invalid prompt/completion pricing"]

    cache_read = _per_million(raw.get("input_cache_read"))
    cache_write = _per_million(raw.get("input_cache_write"))
    request_fee = _request_fee(raw.get("request"))
    if request_fee is None:
        warnings.append("invalid request fee; using 0")
        request_fee = 0.0

    return (
        ModelPricing(
            input_per_million=input_price,
            output_per_million=output_price,
            cache_read_per_million=cache_read,
            cache_write_per_million=cache_write,
            request_fee_usd=request_fee,
        ),
        warnings,
    )


def _spec_from_openrouter(
    raw: Mapping[str, Any],
    *,
    source: str,
) -> Tuple[Optional[ModelSpec], Optional[ModelPricing], List[str]]:
    model_id = raw.get("id") or raw.get("canonical_slug")
    if not isinstance(model_id, str) or not model_id.strip():
        return None, None, ["model has no id"]

    model_id = model_id.strip()
    architecture = raw.get("architecture")
    if not isinstance(architecture, Mapping):
        architecture = {}
    top_provider = raw.get("top_provider")
    if not isinstance(top_provider, Mapping):
        top_provider = {}
    pricing_raw = raw.get("pricing")
    if not isinstance(pricing_raw, Mapping):
        pricing_raw = {}

    provider = (
        raw.get("provider")
        or (model_id.split("/", 1)[0] if "/" in model_id else "openrouter")
    )
    if not isinstance(provider, str) or not provider:
        provider = "openrouter"

    input_modalities = architecture.get("input_modalities") or ("text",)
    output_modalities = architecture.get("output_modalities") or ("text",)
    if not isinstance(input_modalities, (list, tuple)):
        input_modalities = ("text",)
    if not isinstance(output_modalities, (list, tuple)):
        output_modalities = ("text",)

    supported = raw.get("supported_parameters") or ()
    if not isinstance(supported, (list, tuple)):
        supported = ()
    capabilities = tuple(
        capability for capability in _OPENROUTER_CAPABILITIES if capability in supported
    )

    canonical_slug = raw.get("canonical_slug")
    aliases: List[str] = []
    if isinstance(canonical_slug, str) and canonical_slug and canonical_slug != model_id:
        aliases.append(canonical_slug)

    context_length = raw.get("context_length")
    if not isinstance(context_length, int):
        context_length = top_provider.get("context_length")
    if not isinstance(context_length, int) or context_length < 0:
        context_length = None

    max_output = top_provider.get(
        "max_completion_tokens", top_provider.get("max_output_tokens")
    )
    if not isinstance(max_output, int) or max_output < 0:
        max_output = None

    pricing, pricing_warnings = _pricing_from_openrouter(pricing_raw)
    if pricing is None:
        pricing_warnings = [f"{model_id}: {warning}" for warning in pricing_warnings]

    endpoint = ProviderEndpoint(
        provider=provider,
        context_length=context_length,
        max_output_tokens=max_output,
        note="OpenRouter top_provider",
    )
    spec = ModelSpec(
        id=model_id,
        name=raw.get("name") if isinstance(raw.get("name"), str) else model_id,
        provider=provider,
        aliases=tuple(aliases),
        tokenizer=(
            architecture.get("tokenizer")
            if isinstance(architecture.get("tokenizer"), str)
            else None
        ),
        context_length=context_length,
        max_output_tokens=max_output,
        input_modalities=tuple(str(item) for item in input_modalities),
        output_modalities=tuple(str(item) for item in output_modalities),
        capabilities=capabilities,
        endpoints=(endpoint,),
        expiration_date=(
            raw.get("expiration_date")
            if isinstance(raw.get("expiration_date"), str)
            else None
        ),
        source=source,
    )
    return spec, pricing, pricing_warnings


def import_openrouter_catalog(
    payload: Any,
    *,
    source: str = "snapshot",
    include_variants: bool = False,
) -> OpenRouterImportResult:
    """Register models/prices from an OpenRouter models payload.

    Variant IDs containing ``:`` (e.g. ``:free``/``:nitro``) are skipped by
    default because they are routing/pricing variants, not separate models.
    """
    models, fetched_at = _models_from_payload(payload)
    imported = 0
    pricing_imported = 0
    skipped_variants = 0
    skipped_invalid = 0
    warnings: List[str] = []

    for raw in models:
        model_id = raw.get("id")
        if isinstance(model_id, str) and ":" in model_id and not include_variants:
            skipped_variants += 1
            continue
        spec_source = f"openrouter:{source}"
        if fetched_at:
            spec_source = f"{spec_source}@{fetched_at}"
        spec, pricing, spec_warnings = _spec_from_openrouter(
            raw, source=spec_source
        )
        warnings.extend(spec_warnings)
        if spec is None:
            skipped_invalid += 1
            continue

        register_model_spec(spec, overwrite=True)
        imported += 1
        if pricing is not None:
            PRICING_TABLE[spec.id.lower()] = pricing
            pricing_imported += 1

    if imported and pricing_imported == 0:
        warnings.append("catalog imported without pricing data")
    warnings.append(
        "imported prices are in-memory only; persist them with a pricing override if needed"
    )

    return OpenRouterImportResult(
        imported=imported,
        pricing_imported=pricing_imported,
        skipped_variants=skipped_variants,
        skipped_invalid=skipped_invalid,
        warnings=tuple(dict.fromkeys(warnings)),
        source=source,
    )


def import_openrouter_catalog_file(
    path: str,
    *,
    include_variants: bool = False,
) -> OpenRouterImportResult:
    """Load and import an OpenRouter models JSON snapshot from disk."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return import_openrouter_catalog(
        payload,
        source=str(path),
        include_variants=include_variants,
    )


@dataclass(frozen=True)
class OpenRouterEndpointImportResult:
    model: str
    imported: int
    skipped_invalid: int
    warnings: Tuple[str, ...]
    source: str

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "imported": self.imported,
            "skipped_invalid": self.skipped_invalid,
            "warnings": list(self.warnings),
            "source": self.source,
        }


def _finite_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _quantizations(value: Any) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if item is not None)
    return ()


def _endpoints_from_payload(
    payload: Any,
) -> Tuple[Optional[str], List[Mapping[str, Any]], Optional[str]]:
    if isinstance(payload, Mapping):
        data = payload.get("data", payload)
        fetched_at = payload.get("fetched_at") or payload.get("updated_at")
        if isinstance(data, Mapping):
            model_id = data.get("id") or data.get("model_id") or data.get("model")
            endpoints = data.get("endpoints", data.get("data"))
            if isinstance(endpoints, (list, tuple)):
                return (
                    str(model_id) if model_id is not None else None,
                    [item for item in endpoints if isinstance(item, Mapping)],
                    fetched_at,
                )
            raise ValueError('OpenRouter endpoint payload must contain an "endpoints" array')
        if isinstance(data, (list, tuple)):
            return (
                None,
                [item for item in data if isinstance(item, Mapping)],
                fetched_at,
            )
    if isinstance(payload, (list, tuple)):
        return None, [item for item in payload if isinstance(item, Mapping)], None
    raise ValueError("OpenRouter endpoint payload must be an object or array")


def import_openrouter_endpoints(
    payload: Any,
    *,
    model_id: Optional[str] = None,
    source: str = "snapshot",
) -> OpenRouterEndpointImportResult:
    """Import a downloaded OpenRouter model-endpoints snapshot.

    Endpoint pricing is converted to per-million rates; latency/uptime/
    throughput are stored as provider-reported metadata only. No routing is
    performed by PyTokenCalc.
    """
    payload_model, endpoint_mappings, fetched_at = _endpoints_from_payload(payload)
    resolved_model = model_id or payload_model
    if not resolved_model:
        raise ValueError("model_id is required when the payload has no model id")

    warnings: List[str] = []
    endpoints: List[ProviderEndpoint] = []
    skipped = 0
    for raw in endpoint_mappings:
        provider = raw.get("provider_name") or raw.get("provider") or "unknown"
        pricing_raw = raw.get("pricing")
        if not isinstance(pricing_raw, Mapping):
            pricing_raw = {}
        pricing, pricing_warnings = _pricing_from_openrouter(pricing_raw)
        warnings.extend(
            f"{resolved_model}/{provider}: {warning}" for warning in pricing_warnings
        )
        if pricing is None:
            skipped += 1

        latency_data = raw.get("latency_last_30m")
        latency_p50 = None
        if isinstance(latency_data, Mapping):
            latency_p50 = _finite_float(latency_data.get("p50"))

        context_length = raw.get("context_length")
        if not isinstance(context_length, int) or context_length < 0:
            context_length = None
        max_output = raw.get(
            "max_completion_tokens", raw.get("max_output_tokens")
        )
        if not isinstance(max_output, int) or max_output < 0:
            max_output = None

        endpoints.append(
            ProviderEndpoint(
                provider=str(provider),
                context_length=context_length,
                max_output_tokens=max_output,
                quantizations=_quantizations(raw.get("quantization")),
                input_per_million=(
                    pricing.input_per_million if pricing is not None else None
                ),
                output_per_million=(
                    pricing.output_per_million if pricing is not None else None
                ),
                cache_read_per_million=(
                    pricing.cache_read_per_million if pricing is not None else None
                ),
                cache_write_per_million=(
                    pricing.cache_write_per_million if pricing is not None else None
                ),
                request_fee_usd=(
                    pricing.request_fee_usd if pricing is not None else 0.0
                ),
                uptime_last_30m=_finite_float(raw.get("uptime_last_30m")),
                latency_p50_seconds=latency_p50,
                throughput_tokens_per_second=_finite_float(
                    raw.get("throughput_last_30m")
                ),
                status=(
                    str(raw.get("status"))
                    if raw.get("status") is not None
                    else None
                ),
                note=(
                    raw.get("name")
                    if isinstance(raw.get("name"), str)
                    else "OpenRouter endpoint"
                ),
            )
        )

    spec = get_model_spec(resolved_model)
    spec_source = f"openrouter:{source}"
    if fetched_at:
        spec_source = f"{spec_source}@{fetched_at}"
    if spec is None:
        provider = (
            resolved_model.split("/", 1)[0]
            if "/" in resolved_model
            else "openrouter"
        )
        spec = ModelSpec(
            id=resolved_model,
            name=resolved_model,
            provider=provider,
            endpoints=tuple(endpoints),
            source=spec_source,
        )
        warnings.append("model was not in the catalog; created a minimal spec")
    else:
        spec = replace(spec, endpoints=tuple(endpoints), source=spec_source)

    register_model_spec(spec, overwrite=True)
    return OpenRouterEndpointImportResult(
        model=resolved_model,
        imported=len(endpoints),
        skipped_invalid=skipped,
        warnings=tuple(dict.fromkeys(warnings)),
        source=source,
    )


def import_openrouter_endpoints_file(
    path: str,
    *,
    model_id: Optional[str] = None,
) -> OpenRouterEndpointImportResult:
    """Load and import an OpenRouter endpoints JSON snapshot from disk."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return import_openrouter_endpoints(
        payload,
        model_id=model_id,
        source=str(path),
    )
