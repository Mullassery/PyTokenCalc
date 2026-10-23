"""Reconcile local estimates with provider-reported usage.

OpenRouter exposes authoritative token/cost metadata in every response (and
via ``/generation``); OpenAI and Anthropic report authoritative usage too.
This module normalizes those shapes and compares them with PyTokenCalc's
pre-request estimate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .pricing import CostBreakdown, Usage, estimate_usage


@dataclass(frozen=True)
class Reconciliation:
    """Actual usage/cost for a response, versus an optional expected cost."""

    model: str
    usage: Usage
    cost: CostBreakdown
    provider: Optional[str] = None
    expected_cost_usd: Optional[float] = None
    delta_usd: Optional[float] = None
    delta_percent: Optional[float] = None
    provider_reported_cost_usd: Optional[float] = None
    provider_delta_usd: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage.to_dict(),
            "cost": self.cost.to_dict(),
            "expected_cost_usd": self.expected_cost_usd,
            "delta_usd": self.delta_usd,
            "delta_percent": self.delta_percent,
            "provider_reported_cost_usd": self.provider_reported_cost_usd,
            "provider_delta_usd": self.provider_delta_usd,
        }


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    for method in ("model_dump", "dict"):
        converter = getattr(value, method, None)
        if callable(converter):
            converted = converter()
            if isinstance(converted, Mapping):
                return converted
    raise TypeError("response/usage must be a mapping or expose model_dump()/dict()")


def _int_field(data: Mapping[str, Any], key: str, default: int = 0) -> int:
    value = data.get(key, default)
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{key} must be non-negative")
    return parsed


def _optional_float(value: Any, name: str) -> Optional[float]:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return parsed


def _unwrap_usage(payload: Any) -> Mapping[str, Any]:
    data = _as_mapping(payload)
    nested = data.get("usage")
    if nested is not None:
        try:
            return _as_mapping(nested)
        except TypeError:
            pass
    return data


def parse_usage(payload: Any, provider: Optional[str] = None) -> Usage:
    """Normalize OpenAI, Anthropic, OpenRouter, or generic usage metadata.

    ``payload`` may be a full response object (``{"usage": {...}}``) or the
    usage mapping itself. ``input_tokens`` is normalized to include cache
    reads/writes; those are also exposed as subsets.
    """
    usage = _unwrap_usage(payload)
    provider_lower = provider.lower() if provider else None

    has_prompt = "prompt_tokens" in usage or "completion_tokens" in usage
    has_anthropic_cache = (
        "cache_read_input_tokens" in usage or "cache_creation_input_tokens" in usage
    )
    is_anthropic = (
        provider_lower in {"anthropic", "claude"}
        or has_anthropic_cache
        or (
            provider_lower is None
            and not has_prompt
            and ("input_tokens" in usage or "output_tokens" in usage)
        )
    )

    if is_anthropic:
        raw_input = _int_field(usage, "input_tokens")
        cache_read = _int_field(usage, "cache_read_input_tokens")
        cache_write = _int_field(usage, "cache_creation_input_tokens")
        output = _int_field(usage, "output_tokens")
        reasoning = _int_field(usage, "thinking_tokens")
        reported_cost = _optional_float(
            usage.get("cost", usage.get("total_cost")), "cost"
        )
        return Usage(
            input_tokens=raw_input + cache_read + cache_write,
            output_tokens=output,
            cached_input_tokens=cache_read,
            cache_write_tokens=cache_write,
            reasoning_tokens=reasoning,
            provider_reported_cost_usd=reported_cost,
        )

    if has_prompt or provider_lower in {"openai", "openrouter", "azure"}:
        prompt = _int_field(usage, "prompt_tokens", _int_field(usage, "input_tokens"))
        output = _int_field(
            usage, "completion_tokens", _int_field(usage, "output_tokens")
        )
        prompt_details = usage.get("prompt_tokens_details")
        if not isinstance(prompt_details, Mapping):
            prompt_details = {}
        completion_details = usage.get("completion_tokens_details")
        if not isinstance(completion_details, Mapping):
            completion_details = {}

        cached = _int_field(prompt_details, "cached_tokens")
        cache_write = _int_field(prompt_details, "cache_write_tokens")
        if cache_write == 0:
            cache_write = _int_field(usage, "cache_write_tokens")
        reasoning = _int_field(completion_details, "reasoning_tokens")
        cost_value = usage.get("cost")
        if cost_value is None:
            cost_details = usage.get("cost_details")
            if isinstance(cost_details, Mapping):
                cost_value = cost_details.get("upstream_inference_cost")
        reported_cost = _optional_float(cost_value, "cost")

        return Usage(
            input_tokens=prompt,
            output_tokens=output,
            cached_input_tokens=cached,
            cache_write_tokens=cache_write,
            reasoning_tokens=reasoning,
            provider_reported_cost_usd=reported_cost,
        )

    if "input_tokens" in usage or "output_tokens" in usage:
        input_tokens = _int_field(usage, "input_tokens")
        cached = _int_field(usage, "cached_input_tokens")
        cache_write = _int_field(usage, "cache_write_tokens")
        return Usage(
            input_tokens=input_tokens,
            output_tokens=_int_field(usage, "output_tokens"),
            cached_input_tokens=cached,
            cache_write_tokens=cache_write,
            reasoning_tokens=_int_field(usage, "reasoning_tokens"),
            provider_reported_cost_usd=_optional_float(
                usage.get("cost", usage.get("total_cost")), "cost"
            ),
        )

    raise ValueError(
        "Could not find token usage fields (expected prompt_tokens/completion_tokens "
        "or input_tokens/output_tokens)"
    )


def reconcile(
    model: str,
    response: Any,
    *,
    provider: Optional[str] = None,
    expected_usage: Optional[Usage] = None,
    expected_cost_usd: Optional[float] = None,
) -> Reconciliation:
    """Reconcile provider usage/cost with an optional preflight estimate."""
    usage = parse_usage(response, provider)
    cost = estimate_usage(model, usage, provider)

    if expected_usage is not None:
        expected = estimate_usage(model, expected_usage, provider).total_usd
    else:
        expected = expected_cost_usd
    if expected is not None:
        if not math.isfinite(expected) or expected < 0:
            raise ValueError("expected_cost_usd must be finite and non-negative")
        delta = cost.total_usd - expected
        delta_percent = (delta / expected * 100.0) if expected else None
    else:
        delta = None
        delta_percent = None

    reported = usage.provider_reported_cost_usd
    provider_delta = (cost.total_usd - reported) if reported is not None else None

    return Reconciliation(
        model=model,
        provider=provider,
        usage=usage,
        cost=cost,
        expected_cost_usd=expected,
        delta_usd=delta,
        delta_percent=delta_percent,
        provider_reported_cost_usd=reported,
        provider_delta_usd=provider_delta,
    )
