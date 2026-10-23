"""Tests for endpoint-level pricing and OpenRouter endpoint imports."""

import json

from pytokencalc.catalog import get_model_spec
from pytokencalc.endpoints import compare_endpoints, endpoint_pricing
from pytokencalc.openrouter import import_openrouter_endpoints
from pytokencalc.pricing import ModelPricing, Usage

PAYLOAD = {
    "data": {
        "id": "testvendor/endpoint-model",
        "endpoints": [
            {
                "provider_name": "provider-a",
                "name": "Provider A",
                "context_length": 128_000,
                "max_completion_tokens": 4_096,
                "quantization": "fp8",
                "pricing": {
                    "prompt": "0.000001",
                    "completion": "0.000002",
                    "input_cache_read": "0.0000005",
                    "input_cache_write": "0.0000015",
                    "request": "0.001",
                },
                "uptime_last_30m": 99.5,
                "latency_last_30m": {"p50": 0.4},
                "throughput_last_30m": 120.0,
                "status": 0,
            },
            {
                "provider_name": "provider-b",
                "name": "Provider B",
                "pricing": {"prompt": "0.000002", "completion": "0.000004"},
                "uptime_last_30m": 98.0,
            },
            {
                "provider_name": "provider-c",
                "name": "Provider C",
                "pricing": {},
            },
        ],
    }
}


def test_import_endpoints_and_compare():
    result = import_openrouter_endpoints(PAYLOAD)
    assert result.model == "testvendor/endpoint-model"
    assert result.imported == 3
    assert result.skipped_invalid == 1

    spec = get_model_spec("testvendor/endpoint-model")
    assert spec is not None
    assert len(spec.endpoints) == 3
    first = spec.endpoints[0]
    assert first.provider == "provider-a"
    assert first.input_per_million == 1.0
    assert first.output_per_million == 2.0
    assert first.cache_read_per_million == 0.5
    assert first.cache_write_per_million == 1.5
    assert first.request_fee_usd == 0.001
    assert first.uptime_last_30m == 99.5
    assert first.latency_p50_seconds == 0.4
    assert first.throughput_tokens_per_second == 120.0
    assert first.quantizations == ("fp8",)

    comparisons = compare_endpoints(
        "testvendor/endpoint-model",
        Usage(input_tokens=1_000, output_tokens=500),
    )
    assert [item.endpoint.provider for item in comparisons] == [
        "provider-a",
        "provider-b",
        "provider-c",
    ]
    assert comparisons[0].cost.total_usd == 0.003
    assert comparisons[1].cost.total_usd == 0.004
    assert comparisons[2].cost is None
    assert comparisons[2].error


def test_compare_endpoints_filters_provider():
    import_openrouter_endpoints(PAYLOAD)
    comparisons = compare_endpoints(
        "testvendor/endpoint-model",
        Usage(input_tokens=1_000),
        provider="provider-b",
    )
    assert len(comparisons) == 1
    assert comparisons[0].endpoint.provider == "provider-b"


def test_endpoint_pricing_falls_back_to_model_price():
    from pytokencalc.catalog import ProviderEndpoint

    fallback = ModelPricing(1.0, 2.0)
    endpoint = ProviderEndpoint(provider="x")
    assert endpoint_pricing(endpoint, fallback) == fallback
    overridden = ProviderEndpoint(
        provider="x",
        input_per_million=0.5,
        output_per_million=1.0,
    )
    assert endpoint_pricing(overridden, fallback) == ModelPricing(0.5, 1.0)


def test_endpoints_serialize_in_catalog():
    import_openrouter_endpoints(PAYLOAD)
    spec = get_model_spec("testvendor/endpoint-model")
    payload = spec.to_dict()
    assert payload["endpoints"][0]["provider"] == "provider-a"
    assert payload["endpoints"][0]["pricing_per_million"]["input"] == 1.0
    assert json.dumps(payload)
