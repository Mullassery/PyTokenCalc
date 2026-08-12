"""Static per-model pricing table for real dollar-cost estimation.

This is the pricing data behind the top-level ``pytokencalc.estimate_cost()``
function. Prices are USD **per 1,000,000 tokens**, split by input vs. output,
taken from each provider's publicly published pricing pages.

IMPORTANT: LLM provider pricing changes frequently and without notice. This
table is a static snapshot, not a live feed (PyTokenCalc deliberately does
not call out to the network to fetch pricing -- see PRICING_LAST_UPDATED
below). Treat these numbers as good-enough estimates for budgeting, not as
a source of truth for billing-critical decisions. Verify against the
provider's official pricing page before relying on this for anything that
touches real money:

    OpenAI:    https://openai.com/api/pricing/
    Anthropic: https://www.anthropic.com/pricing
    Google:    https://ai.google.dev/pricing

To update: edit PRICING_TABLE below and bump PRICING_LAST_UPDATED.
"""

from typing import Dict, NamedTuple, Optional

# Bump this whenever PRICING_TABLE is edited.
PRICING_LAST_UPDATED = "2025-06"


class ModelPricing(NamedTuple):
    """USD price per 1,000,000 tokens."""

    input_per_million: float
    output_per_million: float


# Keys are matched case-insensitively, first as an exact match, then as the
# longest registered prefix of the requested model string. This keeps the
# table usable for dated/versioned model IDs (e.g. "gpt-4o-2024-11-20")
# without needing an entry for every snapshot release.
PRICING_TABLE: Dict[str, ModelPricing] = {
    # --- OpenAI ---------------------------------------------------------
    "gpt-4o-mini": ModelPricing(0.15, 0.60),
    "gpt-4o": ModelPricing(2.50, 10.00),
    "gpt-4-turbo": ModelPricing(10.00, 30.00),
    "gpt-4-32k": ModelPricing(60.00, 120.00),
    "gpt-4": ModelPricing(30.00, 60.00),
    "gpt-3.5-turbo": ModelPricing(0.50, 1.50),
    "text-davinci-003": ModelPricing(20.00, 20.00),
    "text-davinci-002": ModelPricing(20.00, 20.00),

    # --- Azure OpenAI (mirrors OpenAI pricing; region-dependent in reality) --
    "gpt-35-turbo": ModelPricing(0.50, 1.50),

    # --- Anthropic Claude -------------------------------------------------
    "claude-3-opus": ModelPricing(15.00, 75.00),
    "claude-3-5-sonnet": ModelPricing(3.00, 15.00),
    "claude-3-sonnet": ModelPricing(3.00, 15.00),
    "claude-3-5-haiku": ModelPricing(0.80, 4.00),
    "claude-3-haiku": ModelPricing(0.25, 1.25),

    # --- Google Gemini ------------------------------------------------
    "gemini-1.5-pro": ModelPricing(1.25, 5.00),
    "gemini-1.5-flash": ModelPricing(0.075, 0.30),
    "gemini-2-flash": ModelPricing(0.10, 0.40),
    "gemini-pro": ModelPricing(0.50, 1.50),

    # --- Cohere ------------------------------------------------------
    "command-r-plus": ModelPricing(2.50, 10.00),
    "command-r": ModelPricing(0.15, 0.60),
    "command-light": ModelPricing(0.30, 0.60),
    "command": ModelPricing(1.00, 2.00),
}


def get_model_pricing(model: str) -> Optional[ModelPricing]:
    """Look up pricing for a model, tolerating dated/versioned suffixes.

    Returns None if no pricing entry matches.
    """
    if not model:
        return None

    model_lower = model.lower()

    if model_lower in PRICING_TABLE:
        return PRICING_TABLE[model_lower]

    # Longest-prefix match so e.g. "gpt-4o-2024-11-20" resolves to "gpt-4o"
    # and "gpt-4o-mini-2024-07-18" resolves to "gpt-4o-mini" (not "gpt-4o").
    candidates = [key for key in PRICING_TABLE if model_lower.startswith(key)]
    if not candidates:
        return None

    best_match = max(candidates, key=len)
    return PRICING_TABLE[best_match]


def estimate_cost(model: str, input_tokens: int, output_tokens: int = 0) -> float:
    """Estimate the USD cost of a request.

    Args:
        model: Model ID (e.g. "gpt-4o", "claude-3-5-sonnet").
        input_tokens: Number of input/prompt tokens.
        output_tokens: Number of output/completion tokens (default 0, i.e.
            input-only cost).

    Returns:
        Estimated cost in USD.

    Raises:
        ValueError: If there is no pricing data for the model.
    """
    pricing = get_model_pricing(model)
    if pricing is None:
        raise ValueError(
            f"No pricing data for model '{model}'. "
            f"Known models: {sorted(PRICING_TABLE)}. "
            f"Pricing table last updated: {PRICING_LAST_UPDATED}."
        )

    cost = (
        input_tokens * pricing.input_per_million
        + output_tokens * pricing.output_per_million
    ) / 1_000_000
    return cost
