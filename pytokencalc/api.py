"""Top-level ergonomic API: the two functions most users reach for first.

    from pytokencalc import count_tokens, estimate_cost

    tokens = count_tokens("Tell me a story", model="gpt-4o")
    cost = estimate_cost("gpt-4o", input_tokens=tokens)

``count_tokens`` is a thin wrapper around
``TokenCounterRegistry.count_tokens()`` that returns a plain int instead of
a ``TokenCountResult``, for the common case where you just want the number.
``estimate_cost`` is backed by the static pricing table in
``pytokencalc.pricing`` and returns a real dollar figure -- it is unrelated
to ``OKFTokenBaselines.estimate_cost()``, which predicts an *output token
count* from a historical input/output ratio, not a price.
"""

from typing import Optional

from .pricing import estimate_cost as _estimate_cost_dollars
from .tokenizers.registry import get_global_registry

# Default model used by count_tokens() when the caller doesn't specify one.
# gpt-4o/tiktoken is local-only (no API key, no network call), so this stays
# true to the "works offline" story for the default path.
DEFAULT_MODEL = "gpt-4o"


def count_tokens(
    text: str,
    model: str = DEFAULT_MODEL,
    provider: Optional[str] = None,
) -> int:
    """Count tokens in ``text`` for ``model``.

    Args:
        text: The text to tokenize.
        model: Model ID (e.g. "gpt-4o", "claude-3-5-sonnet", "llama-3-8b").
            Defaults to "gpt-4o" (counted locally via tiktoken, no network
            call, no API key required).
        provider: Optional explicit provider name (e.g. "openai",
            "anthropic"). If omitted, the provider is auto-detected from
            ``model``.

    Returns:
        The input token count as an int.

    Raises:
        ValueError: If no counter is available for the model/provider.
        RuntimeError: If the underlying counter fails (e.g. a network error
            for API-backed providers such as Anthropic/Google/Cohere).

    Note:
        Only the OpenAI/tiktoken, Azure OpenAI, and HuggingFace-backed
        counters run fully offline. Anthropic, Google, and Cohere counters
        call the provider's live API and require network access + an API
        key.
    """
    result = get_global_registry().count_tokens(model=model, text=text, provider=provider)
    return result.input_tokens


def estimate_cost(model: str, input_tokens: int, output_tokens: int = 0) -> float:
    """Estimate the USD cost of a request for ``model``.

    Uses the static, hand-maintained pricing table in ``pytokencalc.pricing``
    (see that module for sources and its last-updated date). This is a
    dollar-cost estimate, not a token-count prediction -- for the latter
    see ``OKFTokenBaselines.estimate_cost()``.

    Args:
        model: Model ID (e.g. "gpt-4o", "claude-3-opus").
        input_tokens: Number of input/prompt tokens.
        output_tokens: Number of output/completion tokens (default 0).

    Returns:
        Estimated cost in USD.

    Raises:
        ValueError: If the model isn't in the pricing table.
    """
    return _estimate_cost_dollars(model, input_tokens, output_tokens)
