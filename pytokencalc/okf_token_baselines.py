"""OKF Token Baselines for PyTokenCalc.

Provider benchmarks, model efficiency comparisons, and cost predictors
for token counting across LLM providers.
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Union


@dataclass
class TokenBaseline:
    """Token estimate baseline for provider-model-task."""

    provider: str  # openai, anthropic, google, etc.
    model: str
    task_type: str  # chat, completion, embedding, vision
    avg_input_tokens: int
    avg_output_tokens: int
    samples: int
    percentile_95_input: int
    percentile_95_output: int


@dataclass(frozen=True)
class BaselineEstimate:
    """Result of a historical-baseline (ratio-based) token estimate.

    This is **not** a tokenizer count. It extrapolates expected output from
    the historical output/input ratio observed for a provider-model-task
    combination, then adds it to the caller-supplied input count.
    """

    provider: str
    model: str
    task_type: str
    input_tokens: int
    predicted_output_tokens: int
    total_tokens: int
    samples: int
    method: str = "historical_ratio"
    # Historical 95th-percentile output tokens stored with the baseline.
    p95_output_tokens: int = 0
    # The same p95 scaled by input_tokens / avg_input_tokens, matching how
    # predicted_output_tokens is extrapolated. Both are estimates.
    predicted_p95_output_tokens: int = 0


class OKFTokenBaselines:
    """Manage token baseline library."""

    def __init__(self, baseline_dir: Path = None):
        self.baseline_dir = baseline_dir or Path.cwd() / "token_baselines"

    def save_baseline(self, baseline: TokenBaseline) -> None:
        """Save token baseline."""
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{baseline.provider}_{baseline.model}_{baseline.task_type}.json"
        with open(self.baseline_dir / filename, "w") as f:
            json.dump(
                {
                    "provider": baseline.provider,
                    "model": baseline.model,
                    "task_type": baseline.task_type,
                    "avg_input_tokens": baseline.avg_input_tokens,
                    "avg_output_tokens": baseline.avg_output_tokens,
                    "samples": baseline.samples,
                    "percentile_95_input": baseline.percentile_95_input,
                    "percentile_95_output": baseline.percentile_95_output,
                },
                f,
                indent=2,
            )

    def get_baseline(self, provider: str, model: str, task_type: str) -> Optional[TokenBaseline]:
        """Retrieve token baseline."""
        filename = f"{provider}_{model}_{task_type}.json"
        filepath = self.baseline_dir / filename

        if not filepath.exists():
            return None

        with open(filepath) as f:
            data = json.load(f)
            return TokenBaseline(**data)

    def list_baselines(
        self,
        provider: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> List[TokenBaseline]:
        """List stored baselines, optionally filtered by provider/task."""
        if not self.baseline_dir.exists():
            return []

        baselines = []
        for filepath in sorted(self.baseline_dir.glob("*.json")):
            with open(filepath) as f:
                data = json.load(f)
            # Ignore unrelated JSON files (e.g. a samples file saved in the
            # same directory); genuine baseline JSON is always an object.
            if not isinstance(data, dict):
                continue
            baseline = TokenBaseline(**data)
            if provider is not None and baseline.provider != provider:
                continue
            if task_type is not None and baseline.task_type != task_type:
                continue
            baselines.append(baseline)

        return baselines

    def compare_models(self, provider: str, task_type: str) -> Dict[str, Dict]:
        """Compare token efficiency across models.

        Includes the stored 95th-percentile counts so callers can budget for
        tail latency, not just the average. ``p95_total_tokens`` is the sum of
        the stored input/output p95 values.
        """
        results = {}

        for f in self.baseline_dir.glob(f"{provider}_*_{task_type}.json"):
            with open(f) as fp:
                data = json.load(fp)
                model = data["model"]
                total_avg = data["avg_input_tokens"] + data["avg_output_tokens"]
                p95_input = data.get("percentile_95_input", 0)
                p95_output = data.get("percentile_95_output", 0)
                results[model] = {
                    "avg_total_tokens": total_avg,
                    "input_tokens": data["avg_input_tokens"],
                    "output_tokens": data["avg_output_tokens"],
                    "samples": data.get("samples", 0),
                    "p95_input_tokens": p95_input,
                    "p95_output_tokens": p95_output,
                    "p95_total_tokens": p95_input + p95_output,
                }

        return results

    def estimate_cost(
        self, provider: str, model: str, task_type: str, input_tokens: int
    ) -> Optional[float]:
        """Predict total *token count* (input + expected output) from a
        historical baseline ratio.

        NOTE: Despite the name, this does NOT return a dollar amount. It's a
        token-count predictor for capacity planning ("given N input tokens,
        how many total tokens will this provider/model/task typically use,
        based on past samples?"). For a real USD cost estimate, use the
        top-level ``pytokencalc.estimate_cost(model, input_tokens,
        output_tokens)``, which is backed by a per-model pricing table.
        """
        baseline = self.get_baseline(provider, model, task_type)
        if not baseline:
            return None

        # Guard against a zero/negative historical input average, which would
        # make the output/input ratio undefined (ZeroDivisionError).
        return input_tokens + _predict_output_tokens(baseline, input_tokens)


def _predict_output_tokens(baseline: TokenBaseline, input_tokens: int) -> int:
    """Predict output tokens from the baseline's historical ratio."""
    if baseline.avg_input_tokens <= 0:
        return 0
    return int(input_tokens * baseline.avg_output_tokens / baseline.avg_input_tokens)


def _percentile_95(values: List[int]) -> int:
    """Nearest-rank 95th percentile (value at ceil(0.95 * n))."""
    ordered = sorted(values)
    index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return ordered[min(index, len(ordered) - 1)]


def _non_empty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _sample_int(value: object, field: str, index: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"sample {index}: {field} must be an integer")
    if value < 0:
        raise ValueError(f"sample {index}: {field} must be non-negative")
    return value


def build_baseline_from_samples(
    provider: str,
    model: str,
    task_type: str,
    samples: Iterable[Mapping],
    *,
    input_counter: Optional[Callable[[str], object]] = None,
) -> TokenBaseline:
    """Build a :class:`TokenBaseline` from real ``(prompt, output_tokens)`` samples.

    Each sample is a mapping containing ``output_tokens`` and either:

    * ``prompt`` -- tokenized with ``input_counter`` when one is supplied
      (the CLI passes the exact tokenizer registry for the target model), or
    * ``input_tokens`` -- a caller-supplied real prompt token count.

    Samples are never generated or padded. An empty sample list, a malformed
    sample, or a missing ``prompt``/``input_tokens`` raises ``ValueError``.

    The 95th percentile uses the nearest-rank method, so small sample sets
    report their maximum (there is no interpolation).
    """
    provider = _non_empty_string(provider, "provider")
    model = _non_empty_string(model, "model")
    task_type = _non_empty_string(task_type, "task_type")

    input_counts: List[int] = []
    output_counts: List[int] = []

    for index, sample in enumerate(samples):
        if not isinstance(sample, Mapping):
            raise ValueError(f"sample {index}: must be an object")

        if "output_tokens" not in sample:
            raise ValueError(f"sample {index}: missing output_tokens")
        output_tokens = _sample_int(sample["output_tokens"], "output_tokens", index)

        if "prompt" in sample and input_counter is not None:
            prompt = sample["prompt"]
            if not isinstance(prompt, str):
                raise ValueError(f"sample {index}: prompt must be a string")
            counted = input_counter(prompt)
            if hasattr(counted, "input_tokens"):
                counted = counted.input_tokens
            input_tokens = _sample_int(counted, "input_tokens", index)
        elif "input_tokens" in sample:
            input_tokens = _sample_int(sample["input_tokens"], "input_tokens", index)
        elif "prompt" in sample:
            raise ValueError(
                f"sample {index}: prompt requires a tokenizer; supply input_tokens instead"
            )
        else:
            raise ValueError(f"sample {index}: missing prompt or input_tokens")

        input_counts.append(input_tokens)
        output_counts.append(output_tokens)

    if not input_counts:
        raise ValueError("at least one sample is required")

    return TokenBaseline(
        provider=provider,
        model=model,
        task_type=task_type,
        avg_input_tokens=int(round(sum(input_counts) / len(input_counts))),
        avg_output_tokens=int(round(sum(output_counts) / len(output_counts))),
        samples=len(input_counts),
        percentile_95_input=_percentile_95(input_counts),
        percentile_95_output=_percentile_95(output_counts),
    )


def estimate_from_baseline(
    provider: str,
    model: str,
    task_type: str,
    input_tokens: int,
    *,
    baseline_dir: Optional[Union[str, Path]] = None,
) -> Optional[BaselineEstimate]:
    """Estimate total tokens from a stored historical baseline.

    .. warning::

        This is a **baseline estimate, not an exact token count**. It is
        based on previously saved samples for the given
        ``provider``/``model``/``task_type`` (see
        :class:`OKFTokenBaselines`): it scales the stored average
        output/input ratio by ``input_tokens``. It does not run a
        tokenizer, so it can be wrong for new prompts, prompt styles, or
        models lacking enough samples. Use :func:`pytokencalc.count_tokens`
        when you need an exact tokenizer count, and
        :func:`pytokencalc.estimate_cost` for USD pricing.

    Args:
        provider: Provider name used when the baseline was saved, e.g.
            ``"openai"``.
        model: Model ID used when the baseline was saved, e.g. ``"gpt-4o"``.
        task_type: Task category used when the baseline was saved, e.g.
            ``"chat"``, ``"completion"``, ``"embedding"``, or ``"vision"``.
        input_tokens: Prompt/input token count to extrapolate from.
        baseline_dir: Directory containing ``<provider>_<model>_<task>.json``
            baseline files. Defaults to ``./token_baselines``.

    Returns:
        A :class:`BaselineEstimate` with the predicted output and total
        token counts, the stored historical ``p95_output_tokens``, and a
        ratio-scaled ``predicted_p95_output_tokens`` for tail planning, or
        ``None`` if no baseline exists for that provider/model/task
        combination. The p95 values are estimates, not guarantees.

    Raises:
        TypeError: If ``input_tokens`` is not an ``int``, or the matching
            baseline file is missing required fields.
        ValueError: If ``input_tokens`` is negative.
        json.JSONDecodeError: If the matching baseline file is not valid JSON.
    """
    if isinstance(input_tokens, bool) or not isinstance(input_tokens, int):
        raise TypeError(f"input_tokens must be an int, got {type(input_tokens).__name__}")
    if input_tokens < 0:
        raise ValueError("input_tokens must be non-negative")

    store = OKFTokenBaselines(baseline_dir=Path(baseline_dir) if baseline_dir is not None else None)
    baseline = store.get_baseline(provider, model, task_type)
    if baseline is None:
        return None

    predicted_output = _predict_output_tokens(baseline, input_tokens)
    if baseline.avg_input_tokens > 0:
        predicted_p95_output = int(
            input_tokens * baseline.percentile_95_output / baseline.avg_input_tokens
        )
    else:
        predicted_p95_output = 0

    return BaselineEstimate(
        provider=baseline.provider,
        model=baseline.model,
        task_type=baseline.task_type,
        input_tokens=input_tokens,
        predicted_output_tokens=predicted_output,
        total_tokens=input_tokens + predicted_output,
        samples=baseline.samples,
        p95_output_tokens=baseline.percentile_95_output,
        predicted_p95_output_tokens=predicted_p95_output,
    )
