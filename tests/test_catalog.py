"""Tests for the built-in model catalog."""

from pytokencalc.catalog import (
    ModelSpec,
    get_model_spec,
    list_models,
    register_model_spec,
)


def test_known_model_has_context_and_pricing():
    spec = get_model_spec("gpt-4o")
    assert spec is not None
    assert spec.id == "gpt-4o"
    assert spec.provider == "openai"
    assert spec.context_length == 128_000
    assert spec.max_output_tokens == 16_384
    assert spec.supports_vision
    assert spec.pricing is not None
    assert spec.pricing.input_per_million == 2.50


def test_provider_prefixed_and_dated_ids_resolve():
    assert get_model_spec("openai/gpt-4o") == get_model_spec("gpt-4o")
    assert get_model_spec("gpt-4o-2024-11-20") == get_model_spec("gpt-4o")
    assert get_model_spec("openrouter/openai/gpt-4o") == get_model_spec("gpt-4o")


def test_alias_resolves():
    assert get_model_spec("gpt-4o-latest") == get_model_spec("gpt-4o")
    assert get_model_spec("claude-3-5-sonnet-latest") == get_model_spec(
        "claude-3-5-sonnet"
    )


def test_unknown_model_returns_none():
    assert get_model_spec("totally-unknown-model") is None


def test_list_models_filtered_by_provider():
    specs = list_models("openai")
    assert specs
    assert all(spec.provider == "openai" for spec in specs)
    assert list_models("nope") == []


def test_register_custom_spec():
    spec = ModelSpec(
        id="custom/private-model",
        name="Private Model",
        provider="custom",
        aliases=("private-model",),
        context_length=32_000,
        max_output_tokens=2_000,
        source="test",
    )
    register_model_spec(spec)
    assert get_model_spec("custom/private-model") == spec
    assert get_model_spec("private-model") == spec
    assert spec.to_dict()["pricing_per_million"] is None
