"""Tests for the offline parity benchmark."""


import pytest

from pytokencalc.benchmark import benchmark_counts, load_samples


class _Result:
    def __init__(self, tokens):
        self.input_tokens = tokens


class _Registry:
    def count_tokens(self, model, text, provider=None):
        return _Result(len(text.split()))


def test_benchmark_counts_summary():
    summary = benchmark_counts(
        [
            {"model": "gpt-4o", "prompt": "a b", "usage": {"prompt_tokens": 2}},
            {"model": "gpt-4o", "prompt": "a b c", "usage": {"prompt_tokens": 4}},
        ],
        registry=_Registry(),
    )
    assert summary.count == 2
    assert summary.exact_matches == 1
    assert summary.exact_match_rate == 0.5
    assert summary.mean_absolute_error == 0.5
    assert summary.mean_absolute_percent_error == pytest.approx(12.5)
    assert summary.max_absolute_error == 1
    assert summary.p95_absolute_error == 1
    payload = summary.to_dict()
    assert payload["results"][0]["exact"] is True


def test_benchmark_supports_nested_response_and_default_model():
    summary = benchmark_counts(
        [
            {
                "prompt": "a b c",
                "response": {"usage": {"prompt_tokens": 3}},
            }
        ],
        model="gpt-4o",
        registry=_Registry(),
    )
    assert summary.count == 1
    assert summary.exact_matches == 1


def test_benchmark_requires_prompt_and_model():
    with pytest.raises(ValueError, match="no model"):
        benchmark_counts([{"prompt": "x", "usage": {"prompt_tokens": 1}}], registry=_Registry())
    with pytest.raises(ValueError, match="prompt/text"):
        benchmark_counts(
            [{"model": "gpt-4o", "usage": {"prompt_tokens": 1}}],
            registry=_Registry(),
        )


def test_load_samples_jsonl(tmp_path):
    path = tmp_path / "samples.jsonl"
    path.write_text(
        '\n{"model": "gpt-4o", "prompt": "x"}\n\n',
        encoding="utf-8",
    )
    samples = load_samples(str(path))
    assert len(samples) == 1
    assert samples[0]["model"] == "gpt-4o"


def test_load_samples_reports_bad_json(tmp_path):
    path = tmp_path / "samples.jsonl"
    path.write_text("not-json\n", encoding="utf-8")
    with pytest.raises(ValueError, match=":1: invalid JSON"):
        load_samples(str(path))
