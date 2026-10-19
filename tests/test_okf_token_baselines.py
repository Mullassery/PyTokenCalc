"""Tests for `pytokencalc/okf_token_baselines.py`.

Previously had no dedicated test file (ROADMAP_HONEST.md section 3). These
use a tmp_path baseline dir so they never touch the caller's cwd.
"""

import json

import pytest

import pytokencalc
from pytokencalc.okf_token_baselines import (
    BaselineEstimate,
    OKFTokenBaselines,
    TokenBaseline,
    estimate_from_baseline,
)


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


def test_estimate_from_baseline_returns_provenance_and_total(store):
    store.save_baseline(_baseline())

    estimate = estimate_from_baseline(
        "openai", "gpt-4o", "chat", 100, baseline_dir=store.baseline_dir
    )

    assert estimate == BaselineEstimate(
        provider="openai",
        model="gpt-4o",
        task_type="chat",
        input_tokens=100,
        predicted_output_tokens=50,
        total_tokens=150,
        samples=10,
        method="historical_ratio",
    )


def test_estimate_from_baseline_scales_with_input(store):
    store.save_baseline(_baseline())

    estimate = estimate_from_baseline(
        "openai", "gpt-4o", "chat", 200, baseline_dir=store.baseline_dir
    )

    assert estimate.predicted_output_tokens == 100
    assert estimate.total_tokens == 300


def test_estimate_from_baseline_missing_baseline_returns_none(store):
    estimate = estimate_from_baseline(
        "openai", "does-not-exist", "chat", 100, baseline_dir=store.baseline_dir
    )
    assert estimate is None


def test_estimate_from_baseline_zero_input_average_avoids_division(store):
    store.save_baseline(_baseline(avg_input_tokens=0, avg_output_tokens=0))

    estimate = estimate_from_baseline(
        "openai", "gpt-4o", "chat", 100, baseline_dir=store.baseline_dir
    )

    assert estimate.predicted_output_tokens == 0
    assert estimate.total_tokens == 100


@pytest.mark.parametrize("bad_value", [-1, -100])
def test_estimate_from_baseline_rejects_negative_input(store, bad_value):
    store.save_baseline(_baseline())

    with pytest.raises(ValueError, match="non-negative"):
        estimate_from_baseline(
            "openai", "gpt-4o", "chat", bad_value, baseline_dir=store.baseline_dir
        )


@pytest.mark.parametrize("bad_value", [1.5, "100", None, True])
def test_estimate_from_baseline_rejects_non_int_input(store, bad_value):
    store.save_baseline(_baseline())

    with pytest.raises(TypeError, match="input_tokens must be an int"):
        estimate_from_baseline(
            "openai", "gpt-4o", "chat", bad_value, baseline_dir=store.baseline_dir
        )


def test_estimate_from_baseline_malformed_file_raises(store):
    path = store.baseline_dir / "openai_gpt-4o_chat.json"
    path.write_text("{not valid json")

    with pytest.raises(json.JSONDecodeError):
        estimate_from_baseline(
            "openai", "gpt-4o", "chat", 100, baseline_dir=store.baseline_dir
        )


def test_estimate_from_baseline_does_not_create_default_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert estimate_from_baseline("openai", "gpt-4o", "chat", 100) is None
    assert not (tmp_path / "token_baselines").exists()


def test_estimate_from_baseline_is_exported_from_package():
    assert pytokencalc.estimate_from_baseline is estimate_from_baseline
    assert pytokencalc.BaselineEstimate is BaselineEstimate
    assert "estimate_from_baseline" in pytokencalc.__all__
    assert "BaselineEstimate" in pytokencalc.__all__
