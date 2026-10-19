"""OKF Token Baselines for PyTokenCalc.

Provider benchmarks, model efficiency comparisons, and cost predictors
for token counting across LLM providers.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Union


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


class OKFTokenBaselines:
    """Manage token baseline library."""

    def __init__(self, baseline_dir: Path = None):
        self.baseline_dir = baseline_dir or Path.cwd() / "token_baselines"

    def save_baseline(self, baseline: TokenBaseline) -> None:
        """Save token baseline."""
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{baseline.provider}_{baseline.model}_{baseline.task_type}.json"
        with open(self.baseline_dir / filename, 'w') as f:
            json.dump({
                'provider': baseline.provider,
                'model': baseline.model,
                'task_type': baseline.task_type,
                'avg_input_tokens': baseline.avg_input_tokens,
                'avg_output_tokens': baseline.avg_output_tokens,
                'samples': baseline.samples,
                'percentile_95_input': baseline.percentile_95_input,
                'percentile_95_output': baseline.percentile_95_output
            }, f, indent=2)

    def get_baseline(self, provider: str, model: str, task_type: str) -> Optional[TokenBaseline]:
        """Retrieve token baseline."""
        filename = f"{provider}_{model}_{task_type}.json"
        filepath = self.baseline_dir / filename

        if not filepath.exists():
            return None

        with open(filepath) as f:
            data = json.load(f)
            return TokenBaseline(**data)

    def compare_models(self, provider: str, task_type: str) -> Dict[str, Dict]:
        """Compare token efficiency across models."""
        results = {}

        for f in self.baseline_dir.glob(f"{provider}_*_{task_type}.json"):
            with open(f) as fp:
                data = json.load(fp)
                model = data['model']
                total_avg = data['avg_input_tokens'] + data['avg_output_tokens']
                results[model] = {
                    'avg_total_tokens': total_avg,
                    'input_tokens': data['avg_input_tokens'],
                    'output_tokens': data['avg_output_tokens']
                }

        return results

    def estimate_cost(self, provider: str, model: str, task_type: str,
                     input_tokens: int) -> Optional[float]:
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
        token counts, or ``None`` if no baseline exists for that
        provider/model/task combination.

    Raises:
        TypeError: If ``input_tokens`` is not an ``int``, or the matching
            baseline file is missing required fields.
        ValueError: If ``input_tokens`` is negative.
        json.JSONDecodeError: If the matching baseline file is not valid JSON.
    """
    if isinstance(input_tokens, bool) or not isinstance(input_tokens, int):
        raise TypeError(
            f"input_tokens must be an int, got {type(input_tokens).__name__}"
        )
    if input_tokens < 0:
        raise ValueError("input_tokens must be non-negative")

    store = OKFTokenBaselines(
        baseline_dir=Path(baseline_dir) if baseline_dir is not None else None
    )
    baseline = store.get_baseline(provider, model, task_type)
    if baseline is None:
        return None

    predicted_output = _predict_output_tokens(baseline, input_tokens)

    return BaselineEstimate(
        provider=baseline.provider,
        model=baseline.model,
        task_type=baseline.task_type,
        input_tokens=input_tokens,
        predicted_output_tokens=predicted_output,
        total_tokens=input_tokens + predicted_output,
        samples=baseline.samples,
    )
