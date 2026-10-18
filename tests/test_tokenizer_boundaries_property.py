"""Property-based boundary tests for the local token-counting path.

RECHECK-016: the tokenizer was only covered by example-based tests, which
leaves off-by-one / boundary bugs (multi-byte code points, whitespace runs,
empty input, astral characters) easy to miss. These Hypothesis properties
assert the strongest available invariant -- that our public `count_tokens`
agrees *exactly* with the underlying `tiktoken` encoding for the same model
-- over generated inputs, plus the basic sanity bounds.

Skipped cleanly when the optional `hypothesis` / `tiktoken` extras are not
installed.
"""

from __future__ import annotations

import pytest

hypothesis = pytest.importorskip("hypothesis")
tiktoken = pytest.importorskip("tiktoken")

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from pytokencalc import count_tokens  # noqa: E402

# Bias generation toward the boundary-y inputs that historically break
# tokenizers: empty strings, pure whitespace, control characters, astral
# (non-BMP) code points, emoji, and long runs of the same character.
_boundary_text = st.one_of(
    st.text(max_size=0),
    st.text(alphabet=st.sampled_from([" ", "\t", "\n", "\r", "\v", "\f", "\u00a0"]), max_size=40),
    st.text(alphabet=st.characters(min_codepoint=0x10000, max_codepoint=0x10FFFF), max_size=20),
    st.text(alphabet=["a", " ", "\n", "\t", "\u00e9", "\U0001f600"], max_size=120),
    st.text(min_size=1, max_size=200).flatmap(
        lambda s: st.just(s * 3)
    ),
)


def _encoding_for(model: str):
    return tiktoken.encoding_for_model(model)


@given(_boundary_text)
@settings(max_examples=300, deadline=None)
def test_gpt4o_count_matches_tiktoken_exactly(text: str):
    expected = len(_encoding_for("gpt-4o").encode(text))
    assert count_tokens(text, model="gpt-4o") == expected


@given(_boundary_text)
@settings(max_examples=300, deadline=None)
def test_gpt4_count_matches_tiktoken_exactly(text: str):
    expected = len(_encoding_for("gpt-4").encode(text))
    assert count_tokens(text, model="gpt-4") == expected


@given(_boundary_text)
@settings(max_examples=200, deadline=None)
def test_count_invariants(text: str):
    n = count_tokens(text, model="gpt-4o")

    assert n >= 0
    if text == "":
        assert n == 0
    else:
        assert n >= 1

    # Byte-level BPE never emits more than one token per UTF-8 byte.
    assert n <= max(1, len(text.encode("utf-8")))

    # Deterministic across repeated calls (no hidden state leaking counts).
    assert count_tokens(text, model="gpt-4o") == n


@given(_boundary_text)
@settings(max_examples=150, deadline=None)
def test_single_token_counts_as_one(text: str):
    """Splitting `text` into its tokens and counting each decoded token must
    yield exactly one token per piece -- a direct check of the boundary
    handling around token seams."""
    enc = _encoding_for("gpt-4o")
    tokens = enc.encode(text)
    if len(tokens) > 40:  # keep the property cheap
        return
    total = sum(count_tokens(enc.decode([t]), model="gpt-4o") for t in tokens)
    assert total == len(tokens)
