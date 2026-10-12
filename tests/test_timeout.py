"""Tests for the bounded thread-based timeout helper (`_timeout.py`).

Introduced to cap `AutoTokenizer.from_pretrained()` (no native timeout) so
`count_tokens()` can't hang for the full OS TCP connect timeout on an
uncached HuggingFace model ID. See ROADMAP_HONEST.md section 7 item (6).
"""

import time

import pytest

from pytokencalc.tokenizers._timeout import (
    DEFAULT_HF_LOAD_TIMEOUT,
    call_with_timeout,
    resolve_default_timeout,
)


def test_returns_result_when_fast():
    assert call_with_timeout(lambda a, b: a + b, 5, 2, 3) == 5


def test_forwards_kwargs():
    assert call_with_timeout(lambda *, x: x * 2, 5, x=21) == 42


def test_raises_timeouterror_when_slow():
    def slow():
        time.sleep(5)
        return "never"

    start = time.monotonic()
    with pytest.raises(TimeoutError):
        call_with_timeout(slow, 0.2)
    # Must actually return control promptly, not after the full sleep.
    assert time.monotonic() - start < 2.0


def test_propagates_original_exception():
    def boom():
        raise ValueError("inner failure")

    with pytest.raises(ValueError, match="inner failure"):
        call_with_timeout(boom, 5)


def test_non_positive_timeout_is_unbounded():
    # A timeout <= 0 means "no timeout"; should just run the function.
    assert call_with_timeout(lambda: "ok", 0) == "ok"
    assert call_with_timeout(lambda: "ok", -1) == "ok"


def test_default_timeout_constant_is_positive():
    assert DEFAULT_HF_LOAD_TIMEOUT > 0


def test_env_override(monkeypatch):
    monkeypatch.setenv("PYTOKENCALC_HF_TIMEOUT", "12.5")
    assert resolve_default_timeout() == 12.5


def test_env_override_invalid_falls_back(monkeypatch):
    monkeypatch.setenv("PYTOKENCALC_HF_TIMEOUT", "not-a-number")
    assert resolve_default_timeout() == DEFAULT_HF_LOAD_TIMEOUT


def test_env_override_nonpositive_falls_back(monkeypatch):
    monkeypatch.setenv("PYTOKENCALC_HF_TIMEOUT", "0")
    assert resolve_default_timeout() == DEFAULT_HF_LOAD_TIMEOUT
