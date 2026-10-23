"""Static per-model pricing table for real dollar-cost estimation.

This is the pricing data behind the top-level ``pytokencalc.estimate_cost()``
function. Prices are USD **per 1,000,000 tokens**, split by input vs. output,
with optional cache-read/cache-write and per-request fees, taken from each
provider's publicly published pricing pages.

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

import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional

# Bump this whenever PRICING_TABLE is edited.
#
# Spot-checked 2026-09: the entries below (gpt-4o at $2.50/$10.00 per
# million, claude-3-5-sonnet at $3.00/$15.00 per million, etc.) still match
# each provider's published rates for these specific model IDs as of this
# check -- OpenAI and Anthropic have kept the older model families at their
# original prices even as newer defaults launched. What this table does NOT
# have is entries for the current-generation model families that have
# shipped since 2025-06 (e.g. newer GPT-4.1/GPT-5-era and Claude 4-era
# models) -- adding those is real data-entry + verification work, out of
# scope for this quick-fix pass. Treat "last updated" as "existing rows
# verified accurate," not "table is complete."
PRICING_LAST_UPDATED = "2026-09"
PRICING_SOURCE = "builtin"
PRICING_MAX_AGE_DAYS = 90


class ModelPricing(NamedTuple):
    """USD price per 1,000,000 tokens.

    ``cache_read_per_million`` and ``cache_write_per_million`` are optional.
    When absent, cache tokens are billed at the normal input rate. The old
    two-argument form remains valid, so existing tables/overrides keep working.
    """

    input_per_million: float
    output_per_million: float
    cache_read_per_million: Optional[float] = None
    cache_write_per_million: Optional[float] = None
    request_fee_usd: float = 0.0


@dataclass(frozen=True)
class Usage:
    """Token usage for one or more requests.

    ``input_tokens`` is the total prompt-token count, including cached and
    cache-write tokens. ``cached_input_tokens`` and ``cache_write_tokens`` are
    subsets of it. ``reasoning_tokens`` is informational and normally included
    in ``output_tokens``; it is not billed twice.
    """

    input_tokens: int
    output_tokens: int = 0
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0
    request_count: int = 1
    provider_reported_cost_usd: Optional[float] = None

    def __post_init__(self) -> None:
        for name in (
            "input_tokens",
            "output_tokens",
            "cached_input_tokens",
            "cache_write_tokens",
            "reasoning_tokens",
            "request_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.cached_input_tokens + self.cache_write_tokens > self.input_tokens:
            raise ValueError(
                "cached_input_tokens + cache_write_tokens cannot exceed input_tokens"
            )
        if self.provider_reported_cost_usd is not None and (
            not math.isfinite(self.provider_reported_cost_usd)
            or self.provider_reported_cost_usd < 0
        ):
            raise ValueError(
                "provider_reported_cost_usd must be finite and non-negative"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "request_count": self.request_count,
            "provider_reported_cost_usd": self.provider_reported_cost_usd,
        }


def _per_token_cost(tokens: int, rate_per_million: float) -> Decimal:
    return (Decimal(tokens) * Decimal(str(rate_per_million))) / Decimal(1_000_000)


@dataclass(frozen=True)
class CostBreakdown:
    """Line-item USD cost for a :class:`Usage`."""

    model: str
    resolved_model: str
    usage: Usage
    input_rate_per_million: float
    output_rate_per_million: float
    cache_read_rate_per_million: float
    cache_write_rate_per_million: float
    request_fee_usd: float
    input_cost_usd: float
    cache_read_cost_usd: float
    cache_write_cost_usd: float
    output_cost_usd: float
    request_cost_usd: float
    cache_savings_usd: float

    @property
    def total_usd(self) -> float:
        return (
            self.input_cost_usd
            + self.cache_read_cost_usd
            + self.cache_write_cost_usd
            + self.output_cost_usd
            + self.request_cost_usd
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "resolved_model": self.resolved_model,
            "usage": self.usage.to_dict(),
            "rates_per_million": {
                "input": self.input_rate_per_million,
                "output": self.output_rate_per_million,
                "cache_read": self.cache_read_rate_per_million,
                "cache_write": self.cache_write_rate_per_million,
                "request_fee_usd": self.request_fee_usd,
            },
            "costs_usd": {
                "input": self.input_cost_usd,
                "cache_read": self.cache_read_cost_usd,
                "cache_write": self.cache_write_cost_usd,
                "output": self.output_cost_usd,
                "request": self.request_cost_usd,
                "total": self.total_usd,
                "cache_savings": self.cache_savings_usd,
            },
        }


def cost_from_pricing(
    model: str,
    pricing: ModelPricing,
    usage: Usage,
    *,
    resolved_model: Optional[str] = None,
) -> CostBreakdown:
    """Build a line-item cost breakdown from an explicit pricing record."""
    resolved_model = resolved_model or model
    cache_read_rate = (
        pricing.cache_read_per_million
        if pricing.cache_read_per_million is not None
        else pricing.input_per_million
    )
    cache_write_rate = (
        pricing.cache_write_per_million
        if pricing.cache_write_per_million is not None
        else pricing.input_per_million
    )

    uncached_input = (
        usage.input_tokens
        - usage.cached_input_tokens
        - usage.cache_write_tokens
    )
    input_cost = _per_token_cost(uncached_input, pricing.input_per_million)
    cache_read_cost = _per_token_cost(usage.cached_input_tokens, cache_read_rate)
    cache_write_cost = _per_token_cost(usage.cache_write_tokens, cache_write_rate)
    output_cost = _per_token_cost(usage.output_tokens, pricing.output_per_million)
    request_cost = Decimal(str(pricing.request_fee_usd)) * Decimal(usage.request_count)
    cache_savings = (
        _per_token_cost(usage.cached_input_tokens, pricing.input_per_million)
        - cache_read_cost
    )

    return CostBreakdown(
        model=model,
        resolved_model=resolved_model,
        usage=usage,
        input_rate_per_million=pricing.input_per_million,
        output_rate_per_million=pricing.output_per_million,
        cache_read_rate_per_million=cache_read_rate,
        cache_write_rate_per_million=cache_write_rate,
        request_fee_usd=pricing.request_fee_usd,
        input_cost_usd=float(input_cost),
        cache_read_cost_usd=float(cache_read_cost),
        cache_write_cost_usd=float(cache_write_cost),
        output_cost_usd=float(output_cost),
        request_cost_usd=float(request_cost),
        cache_savings_usd=float(cache_savings),
    )


def estimate_usage(
    model: str,
    usage: Usage,
    provider: Optional[str] = None,
) -> CostBreakdown:
    """Return a line-item cost estimate for *usage*.

    ``provider`` is accepted for API symmetry with reconciliation/preflight;
    provider-specific prices can be supplied through pricing overrides today.
    """
    del provider  # reserved for model-level pricing
    pricing = get_model_pricing(model)
    if pricing is None:
        raise ValueError(
            f"No pricing data for model '{model}'. "
            f"Known models: {sorted(PRICING_TABLE)}. "
            f"Pricing table last updated: {PRICING_LAST_UPDATED}."
        )
    return cost_from_pricing(
        model,
        pricing,
        usage,
        resolved_model=resolve_model_pricing_key(model) or model,
    )


# Keys are matched case-insensitively, first as an exact match, then against
# a known snapshot/version suffix (e.g. "gpt-4o-2024-11-20" -> "gpt-4o").
# Genuinely different variants (e.g. "gpt-4.1" or "gpt-4o-audio-preview")
# intentionally do not inherit a base model's price.
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

# Snapshot of the built-in table so overrides can merge safely.
_BUILTIN_PRICING_TABLE = dict(PRICING_TABLE)

# Only snapshot/version suffixes may inherit a base model's price. This
# deliberately rejects genuinely different variants such as "gpt-4.1"
# (a different model from "gpt-4"), "gpt-4o-audio-preview", or
# "gemini-1.5-flash-8b".
_VERSION_SUFFIX_RE = re.compile(
    r"-(?:\d{4}-\d{2}-\d{2}|\d{8}|\d{4}-preview|\d{2}-\d{4}|"
    r"\d{4}|\d{3}|latest|preview|v\d+(?:\.\d+)*)$"
)


def _model_id_variants(model: str) -> list[str]:
    """Yield normalized IDs to try, including a provider-prefixed variant."""
    model_lower = model.strip().lower()
    variants = [model_lower]
    if "/" in model_lower:
        suffix = model_lower.rsplit("/", 1)[1]
        if suffix and suffix not in variants:
            variants.append(suffix)
    return variants


def resolve_model_pricing_key(model: str) -> Optional[str]:
    """Return the PRICING_TABLE key for *model*, or None if no safe match.

    Exact IDs win. A model may inherit a base ID's price only when the
    remainder is a known snapshot/version suffix (e.g.
    "gpt-4o-2024-11-20" -> "gpt-4o"). Provider prefixes such as
    "openai/gpt-4o" are also accepted.
    """
    if not model:
        return None

    table = PRICING_TABLE
    for candidate in _model_id_variants(model):
        if candidate in table:
            return candidate

        # Longest base key first, so gpt-4o-mini wins over gpt-4o.
        for key in sorted(table, key=len, reverse=True):
            if not candidate.startswith(key):
                continue
            suffix = candidate[len(key):]
            if _VERSION_SUFFIX_RE.fullmatch(suffix):
                return key

    return None


def get_model_pricing(model: str) -> Optional[ModelPricing]:
    """Look up pricing for a model, tolerating dated/versioned suffixes.

    Returns None if no pricing entry matches safely.
    """
    key = resolve_model_pricing_key(model)
    return PRICING_TABLE[key] if key is not None else None


@dataclass(frozen=True)
class ModelCostComparison:
    """Cost for one model, or an error when it has no usable pricing."""

    model: str
    cost: Optional[CostBreakdown] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "cost_usd": self.cost.total_usd if self.cost is not None else None,
            "breakdown": self.cost.to_dict() if self.cost is not None else None,
            "error": self.error,
        }


def compare_models(
    models: list[str],
    usage: Usage,
) -> list[ModelCostComparison]:
    """Compare one :class:`Usage` across models, cheapest first."""
    comparisons: list[ModelCostComparison] = []
    for model in models:
        try:
            comparisons.append(
                ModelCostComparison(model=model, cost=estimate_usage(model, usage))
            )
        except ValueError as exc:
            comparisons.append(ModelCostComparison(model=model, error=str(exc)))
    comparisons.sort(
        key=lambda item: (
            item.cost is None,
            item.cost.total_usd if item.cost is not None else 0.0,
        )
    )
    return comparisons


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
        ValueError: If there is no pricing data for the model, or if token
            counts are negative.
    """
    usage = Usage(input_tokens=input_tokens, output_tokens=output_tokens)
    return estimate_usage(model, usage).total_usd


def pricing_status(now: Optional[date] = None) -> Dict[str, Any]:
    """Report the pricing snapshot's age and whether it should be refreshed.

    ``PRICING_LAST_UPDATED`` is usually a ``YYYY-MM`` marker, but may also be
    ``YYYY-MM-DD``. Age is measured from the first day of that month (or the
    actual date if fully specified). This is a warning signal, not a hard failure:
    old prices are still usable for estimates, but should be verified.
    """
    today = now or date.today()
    updated = None
    try:
        if len(PRICING_LAST_UPDATED) == 10:  # YYYY-MM-DD
            updated = datetime.strptime(PRICING_LAST_UPDATED, "%Y-%m-%d").date()
        elif len(PRICING_LAST_UPDATED) == 7:  # YYYY-MM
            updated = datetime.strptime(
                PRICING_LAST_UPDATED, "%Y-%m"
            ).date().replace(day=1)
        else:
            # Try to parse as date
            updated = datetime.strptime(PRICING_LAST_UPDATED[:10], "%Y-%m-%d").date()
    except Exception:
        updated = None
    age_days = None if updated is None else (today - updated).days
    return {
        "last_updated": PRICING_LAST_UPDATED,
        "source": PRICING_SOURCE,
        "models": len(PRICING_TABLE),
        "age_days": age_days,
        "max_age_days": PRICING_MAX_AGE_DAYS,
        "stale": True if age_days is None else age_days > PRICING_MAX_AGE_DAYS,
        "error": (
            None
            if updated is not None
            else f"Unparseable PRICING_LAST_UPDATED: {PRICING_LAST_UPDATED!r}"
        ),
    }


def load_pricing_override(
    path: str,
    replace: bool = False,
    merge: Optional[bool] = None,
) -> Dict[str, Any]:
    """Load pricing from a JSON file.

    By default this **merges** the override with built-in pricing, so adding
    a private or newly released model does not erase all existing entries.
    Pass ``replace=True`` to replace the table entirely.

    Expected shape::

        {"last_updated": "2026-10-19",
         "models": {"gpt-5": {"input_per_million": 1.25,
                               "output_per_million": 10.0,
                               "cache_read_per_million": 0.125,
                               "cache_write_per_million": 1.25,
                               "request_fee_usd": 0.0}}}

    The override is process-wide (the same table used by ``estimate_cost``)
    and intentionally explicit: there is no network fetch. Returns the same
    status dict as :func:`pricing_status`.
    """
    global PRICING_TABLE, PRICING_LAST_UPDATED, PRICING_SOURCE

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("pricing file must be a JSON object")
    last_updated = data.get("last_updated")
    models = data.get("models")
    if not isinstance(last_updated, str) or not last_updated:
        raise ValueError("pricing file requires a non-empty 'last_updated'")
    if not isinstance(models, dict) or not models:
        raise ValueError("pricing file requires a non-empty 'models' object")

    parsed: Dict[str, ModelPricing] = {}
    for model, raw in models.items():
        if not isinstance(model, str) or not model:
            raise ValueError("pricing model keys must be non-empty strings")
        if not isinstance(raw, dict):
            raise ValueError(f"pricing for {model!r} must be an object")
        try:
            input_price = float(raw["input_per_million"])
            output_price = float(raw["output_per_million"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"pricing for {model!r} requires numeric input_per_million and output_per_million"
            ) from exc
        if (
            not math.isfinite(input_price)
            or not math.isfinite(output_price)
            or input_price < 0
            or output_price < 0
        ):
            raise ValueError(f"pricing for {model!r} must be finite and non-negative")

        optional: Dict[str, Optional[float]] = {}
        for field_name in ("cache_read_per_million", "cache_write_per_million"):
            field_value = raw.get(field_name)
            if field_value is None:
                optional[field_name] = None
                continue
            try:
                parsed_value = float(field_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"pricing for {model!r} has a non-numeric {field_name}"
                ) from exc
            if not math.isfinite(parsed_value) or parsed_value < 0:
                raise ValueError(
                    f"pricing for {model!r} requires a finite, non-negative {field_name}"
                )
            optional[field_name] = parsed_value

        try:
            request_fee = float(raw.get("request_fee_usd", 0.0))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"pricing for {model!r} has a non-numeric request_fee_usd"
            ) from exc
        if not math.isfinite(request_fee) or request_fee < 0:
            raise ValueError(
                f"pricing for {model!r} requires a finite, non-negative request_fee_usd"
            )

        parsed[model.lower()] = ModelPricing(
            input_price,
            output_price,
            optional["cache_read_per_million"],
            optional["cache_write_per_million"],
            request_fee,
        )

    should_merge = (not replace) if merge is None else merge
    if should_merge:
        base = dict(_BUILTIN_PRICING_TABLE)
        base.update(parsed)
        PRICING_TABLE = base
    else:
        PRICING_TABLE = parsed
    PRICING_LAST_UPDATED = last_updated
    PRICING_SOURCE = path
    return pricing_status()
