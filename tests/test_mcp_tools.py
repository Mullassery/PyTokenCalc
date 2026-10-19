"""Tests for the real PyTokenCalc MCP tool surface.

The previous `_mcp_tools.py` handlers returned hardcoded fabricated values
(`len(text) // 4`, fixed `0.01`/`0.03` rates, `total_tokens: 125000`, ...)
regardless of input. These tests pin the real behavior: token counts come from
an injected/tokenizer registry, and costs come from the real pricing table.

A fake registry is injected so the arithmetic and wiring are verified without
network access or optional tokenizer dependencies. One integration test
exercises the real tiktoken-backed OpenAI counter when available.
"""

import asyncio
import json

import pytest

from pytokencalc._mcp_connector import TokenCalculator
from pytokencalc._mcp_tools import PyTokenCalcMCPHandler, PyTokenCalcMCPTools
from pytokencalc.pricing import PRICING_TABLE, estimate_cost
from pytokencalc.tokenizers import TokenCountResult


class _FakeRegistry:
    """Counts whitespace-separated words so arithmetic is deterministic."""

    def __init__(self, fail_models=()):
        self.fail_models = set(fail_models)
        self.calls = []

    def count_tokens(self, model, text, provider=None):
        self.calls.append((model, text, provider))
        if model in self.fail_models:
            raise ValueError(f"no tokenizer for {model}")
        return TokenCountResult(
            input_tokens=len(text.split()),
            provider="fake",
            model=model,
            source="fake",
        )


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture()
def handler():
    return PyTokenCalcMCPHandler(registry=_FakeRegistry())


def test_get_tools_is_twelve_and_honest():
    tools = PyTokenCalcMCPTools.get_tools()
    assert len(tools) == 12
    joined = " ".join(t["description"] for t in tools.values()).lower()
    assert "hardcoded" not in joined
    assert "in memory" in tools["track_budget"]["description"].lower()
    assert "provider" in tools["count_tokens"]["inputSchema"]["properties"]


def test_count_tokens_uses_registry(handler):
    result = _run(handler.count_tokens("hello world", "gpt-4o"))
    assert result["input_tokens"] == 2
    assert result["total_tokens"] == 2
    assert result["model"] == "gpt-4o"
    assert result["provider"] == "fake"


def test_count_tokens_error_is_reported_not_faked():
    handler = PyTokenCalcMCPHandler(registry=_FakeRegistry(fail_models={"nope"}))
    result = _run(handler.count_tokens("hello", "nope"))
    assert result["status"] == "error"
    assert "no tokenizer" in result["message"]


def test_estimate_cost_matches_real_pricing_table(handler):
    result = _run(handler.estimate_cost(1000, 1000, "gpt-4o"))
    expected = estimate_cost("gpt-4o", 1000, 1000)
    assert result["estimated_cost_usd"] == pytest.approx(expected)
    assert result["input_cost_usd"] == pytest.approx(0.0025)
    assert result["output_cost_usd"] == pytest.approx(0.01)
    assert result["pricing_per_million"] == {"input": 2.50, "output": 10.00}


def test_estimate_cost_unknown_model_is_error(handler):
    result = _run(handler.estimate_cost(10, 10, "definitely-not-a-model"))
    assert result["status"] == "error"
    assert "gpt-4o" in result["known_models"]


def test_estimate_total_cost_matches_estimate_cost(handler):
    total = _run(handler.estimate_total_cost(500, 500, "gpt-4o-mini"))
    single = _run(handler.estimate_cost(500, 500, "gpt-4o-mini"))
    assert total["estimated_cost_usd"] == pytest.approx(single["estimated_cost_usd"])


def test_get_model_pricing_prefix_resolution(handler):
    result = _run(handler.get_model_pricing("gpt-4o-2024-11-20"))
    assert result["resolved_model"] == "gpt-4o"
    assert result["input_per_million_usd"] == 2.50


def test_compare_model_costs_picks_real_cheapest(handler):
    result = _run(handler.compare_model_costs("a b c d", ["gpt-4o", "gpt-4o-mini"]))
    assert result["cheapest_model"] == "gpt-4o-mini"
    assert result["priced_models"] == 2
    costs = [c["estimated_cost_usd"] for c in result["comparisons"]]
    assert costs == sorted(costs)


def test_compare_model_costs_reports_unpriced_model(handler):
    result = _run(handler.compare_model_costs("a b", ["gpt-4o", "mystery-model"]))
    unpriced = next(c for c in result["comparisons"] if c["model"] == "mystery-model")
    assert unpriced["error"] == "no pricing data"


def test_batch_count_tokens(handler):
    result = _run(handler.batch_count_tokens(["a b", "c d e"], "gpt-4o"))
    assert result["total_tokens"] == 5
    assert result["counted_texts"] == 2
    assert result["avg_tokens_per_text"] == pytest.approx(2.5)
    assert [r["tokens"] for r in result["results"]] == [2, 3]


def test_batch_count_tokens_partial_failure():
    handler = PyTokenCalcMCPHandler(registry=_FakeRegistry(fail_models={"bad"}))
    result = _run(handler.batch_count_tokens(["x"], "bad"))
    assert result["counted_texts"] == 0
    assert result["total_tokens"] == 0
    assert "error" in result["results"][0]


def test_get_token_breakdown_real_fields(handler):
    result = _run(handler.get_token_breakdown("one two three", "gpt-4o"))
    assert result["total_tokens"] == 3
    assert result["breakdown"]["input_tokens"] == 3
    assert result["breakdown"]["system_tokens"] == 0
    assert result["text_stats"] == {"characters": 13, "words": 3, "lines": 1}


def test_export_pricing_report_all_formats(handler):
    for fmt in ("json", "csv", "markdown"):
        result = _run(handler.export_pricing_report(format=fmt, include_models=["gpt-4o"]))
        assert result["format"] == fmt
        assert "gpt-4o" in result["content"]
        assert result["size_bytes"] > 0
    json_report = _run(handler.export_pricing_report(format="json"))
    parsed = json.loads(json_report["content"])
    assert parsed["models"]
    assert len(json_report["models_included"]) == len(PRICING_TABLE)


def test_export_pricing_report_unsupported_format(handler):
    result = _run(handler.export_pricing_report(format="xml"))
    assert result["status"] == "error"
    assert "json" in result["supported_formats"]


def test_track_budget_in_memory_arithmetic(handler):
    result = _run(handler.track_budget("b1", cost_used=2.5, limit_cost=10.0))
    assert result["cost_used_usd"] == pytest.approx(2.5)
    assert result["remaining_cost_usd"] == pytest.approx(7.5)
    assert result["used_percent"] == pytest.approx(25.0)
    assert result["alert_triggered"] is False

    _run(handler.set_budget_alert("b1", 20.0))
    result = _run(handler.track_budget("b1", cost_used=0.5))
    assert result["cost_used_usd"] == pytest.approx(3.0)
    assert result["used_percent"] == pytest.approx(30.0)
    assert result["alert_triggered"] is True


def test_track_budget_tokens_and_none_without_limit(handler):
    result = _run(handler.track_budget("b2", tokens_used=1000))
    assert result["limit_tokens"] is None
    assert result["remaining_tokens"] is None
    assert result["used_percent"] is None

    result = _run(handler.track_budget("b2", tokens_used=500, limit_tokens=2000))
    assert result["tokens_used"] == 1500
    assert result["remaining_tokens"] == 500
    assert result["used_percent"] == pytest.approx(75.0)


def test_analyze_token_usage_aggregates_recorded_usage(handler):
    _run(handler.count_tokens("a b c", "gpt-4o"))
    _run(handler.count_tokens("d e", "gpt-4o"))
    result = _run(handler.analyze_token_usage("last_24h", "model"))
    assert result["total_input_tokens"] == 5
    assert result["records"] == 2
    assert result["usage_by_group"] == {"gpt-4o": 5}

    bad = _run(handler.analyze_token_usage("last_century"))
    assert bad["status"] == "error"


def test_analyze_token_usage_group_by_user_has_no_data_source(handler):
    _run(handler.count_tokens("a b", "gpt-4o"))
    result = _run(handler.analyze_token_usage("last_24h", "user"))
    assert result["usage_by_group"] == {"unknown": 2}


def test_optimize_prompt_measures_reduction_not_target(handler):
    prompt = "line one   \n\n\n\nline two   \n"
    result = _run(handler.optimize_prompt(prompt, "gpt-4o", target_reduction_percent=20))
    assert result["model"] == "gpt-4o"
    assert result["optimized_prompt"] == "line one\n\nline two"
    assert result["target_reduction_percent"] == 20
    assert result["actual_reduction_percent"] == pytest.approx(0.0)
    assert result["target_met"] is False
    assert any("Target not reached" in tip for tip in result["optimization_tips"])


def test_optimize_prompt_error_when_count_fails():
    handler = PyTokenCalcMCPHandler(registry=_FakeRegistry(fail_models={"bad"}))
    result = _run(handler.optimize_prompt("hi", "bad"))
    assert result["status"] == "error"


def test_token_calculator_facade():
    calc = TokenCalculator(registry=_FakeRegistry())
    assert len(calc.get_tools()) == 12
    handler = calc.get_handler()
    assert _run(handler.count_tokens("a b", "gpt-4o"))["input_tokens"] == 2
    if __import__("importlib").util.find_spec("fastmcp") is None:
        from pytokencalc.mcp_server import MCPUnavailable

        with pytest.raises(MCPUnavailable):
            calc.start_mcp_connector()
    else:
        server = calc.start_mcp_connector()
        assert server is not None
    assert calc.stop_mcp_connector() is None


def test_global_registry_is_used_when_none_injected():
    handler = PyTokenCalcMCPHandler()
    registry = handler._get_registry()
    assert hasattr(registry, "count_tokens")


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("tiktoken") is None,
    reason="tiktoken not installed",
)
def test_real_openai_counter_integration():
    from pytokencalc.tokenizers import get_global_registry

    registry = get_global_registry()
    if registry.get_counter("openai") is None:
        pytest.skip("OpenAI/tiktoken counter unavailable in this environment")
    handler = PyTokenCalcMCPHandler(registry=registry)
    result = _run(handler.count_tokens("Hello, world!", "gpt-4o"))
    assert result["input_tokens"] > 0
    assert result["source"] in ("local", "api", "formula")
