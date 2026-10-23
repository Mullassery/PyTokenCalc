"""Endpoint-level cost comparison.

One model can be served by multiple providers/platforms at different prices.
OpenRouter exposes this through its model-endpoints API; PyTokenCalc models it
with :class:`~pytokencalc.catalog.ProviderEndpoint` and compares them locally.
This module never routes requests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .catalog import ModelSpec, ProviderEndpoint, get_model_spec
from .pricing import (
    CostBreakdown,
    ModelPricing,
    Usage,
    cost_from_pricing,
    get_model_pricing,
    resolve_model_pricing_key,
)


@dataclass(frozen=True)
class EndpointCostComparison:
    model: str
    endpoint: ProviderEndpoint
    cost: Optional[CostBreakdown] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "provider": self.endpoint.provider,
            "endpoint": self.endpoint.to_dict(),
            "cost_usd": self.cost.total_usd if self.cost is not None else None,
            "breakdown": self.cost.to_dict() if self.cost is not None else None,
            "error": self.error,
        }


def endpoint_pricing(
    endpoint: ProviderEndpoint,
    fallback: Optional[ModelPricing],
) -> Optional[ModelPricing]:
    """Return endpoint-specific pricing, or the model fallback."""
    if endpoint.input_per_million is not None and endpoint.output_per_million is not None:
        return ModelPricing(
            input_per_million=endpoint.input_per_million,
            output_per_million=endpoint.output_per_million,
            cache_read_per_million=endpoint.cache_read_per_million,
            cache_write_per_million=endpoint.cache_write_per_million,
            request_fee_usd=endpoint.request_fee_usd,
        )
    return fallback


def _comparison_endpoints(
    spec: ModelSpec, fallback: Optional[ModelPricing]
) -> List[ProviderEndpoint]:
    if spec.endpoints:
        return list(spec.endpoints)
    if fallback is None:
        return []
    return [
        ProviderEndpoint(
            provider=spec.provider,
            context_length=spec.context_length,
            max_output_tokens=spec.max_output_tokens,
            input_per_million=fallback.input_per_million,
            output_per_million=fallback.output_per_million,
            cache_read_per_million=fallback.cache_read_per_million,
            cache_write_per_million=fallback.cache_write_per_million,
            request_fee_usd=fallback.request_fee_usd,
            note="model-level pricing fallback",
        )
    ]


def compare_endpoints(
    model: str,
    usage: Usage,
    *,
    provider: Optional[str] = None,
) -> List[EndpointCostComparison]:
    """Compare endpoint prices for one model/usage, cheapest first.

    Endpoints without endpoint-specific pricing inherit the model's price.
    Unpriced endpoints are returned last with an ``error`` instead of aborting
    the comparison.
    """
    spec = get_model_spec(model)
    if spec is None:
        raise ValueError(f"Unknown model in catalog: {model}")

    fallback = get_model_pricing(model)
    resolved_model = resolve_model_pricing_key(model) or model
    comparisons: List[EndpointCostComparison] = []

    for endpoint in _comparison_endpoints(spec, fallback):
        if provider and endpoint.provider.lower() != provider.lower():
            continue
        pricing = endpoint_pricing(endpoint, fallback)
        if pricing is None:
            comparisons.append(
                EndpointCostComparison(
                    model=model,
                    endpoint=endpoint,
                    error="no pricing data for endpoint",
                )
            )
            continue
        comparisons.append(
            EndpointCostComparison(
                model=model,
                endpoint=endpoint,
                cost=cost_from_pricing(
                    model,
                    pricing,
                    usage,
                    resolved_model=resolved_model,
                ),
            )
        )

    comparisons.sort(
        key=lambda item: (
            item.cost is None,
            item.cost.total_usd if item.cost is not None else 0.0,
            -(item.endpoint.uptime_last_30m or 0.0),
        )
    )
    return comparisons
