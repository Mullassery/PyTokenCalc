"""Tests for `pytokencalc/okf_token_baselines.py`.

Previously had no dedicated test file (ROADMAP_HONEST.md section 3). These
use a tmp_path baseline dir so they never touch the caller's cwd.
"""

import pytest

from pytokencalc.okf_token_baselines import OKFTokenBaselines, TokenBaseline


def _baseline(**overrides):
    data = {
        "provider": "openai",
        "model": "gpt-4o",
        "task_type": "chat",
        "avg_input_tokens": 100,
        "avg_output_tokens": 50,
        "samples": 10,
        "percentile_95_input": 200,
        "percentile_95_output": 120,
    }
    data.update(overrides)
    return TokenBaseline(**data)


@pytest.fixture
def store(tmp_path):
    return OKFTokenBaselines(baseline_dir=tmp_path)


def test_save_then_get_round_trips(store):
    baseline = _baseline()
    store.save_baseline(baseline)

    loaded = store.get_baseline("openai", "gpt-4o", "chat")
    assert loaded == baseline


def test_get_missing_baseline_returns_none(store):
    assert store.get_baseline("openai", "does-not-exist", "chat") is None


def test_estimate_cost_predicts_total_tokens(store):
    # ratio = 50/100 = 0.5 -> predicted output = 100 * 0.5 = 50 -> total 150
    store.save_baseline(_baseline())
    assert store.estimate_cost("openai", "gpt-4o", "chat", input_tokens=100) == 150


def test_estimate_cost_missing_baseline_returns_none(store):
    assert store.estimate_cost("openai", "nope", "chat", 100) is None


def test_estimate_cost_zero_input_guard(store):
    # A zero historical input average must not raise ZeroDivisionError.
    store.save_baseline(_baseline(avg_input_tokens=0, avg_output_tokens=0))
    assert store.estimate_cost("openai", "gpt-4o", "chat", input_tokens=100) == 100


def test_compare_models(store):
    store.save_baseline(_baseline(model="gpt-4o", avg_input_tokens=100, avg_output_tokens=50))
    store.save_baseline(
        _baseline(model="gpt-4o-mini", avg_input_tokens=40, avg_output_tokens=10)
    )

    result = store.compare_models("openai", "chat")

    assert set(result) == {"gpt-4o", "gpt-4o-mini"}
    assert result["gpt-4o"] == {
        "avg_total_tokens": 150,
        "input_tokens": 100,
        "output_tokens": 50,
    }
    assert result["gpt-4o-mini"]["avg_total_tokens"] == 50


def test_compare_models_empty_when_none_saved(store):
    assert store.compare_models("anthropic", "chat") == {}
