"""OKF Token Baselines for PyTokenCalc.

Provider benchmarks, model efficiency comparisons, and cost predictors
for token counting across LLM providers.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import json


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


class OKFTokenBaselines:
    """Manage token baseline library."""

    def __init__(self, baseline_dir: Path = None):
        self.baseline_dir = baseline_dir or Path.cwd() / "token_baselines"
        self.baseline_dir.mkdir(exist_ok=True)

    def save_baseline(self, baseline: TokenBaseline) -> None:
        """Save token baseline."""
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
        """Estimate output tokens based on baseline."""
        baseline = self.get_baseline(provider, model, task_type)
        if not baseline:
            return None

        # Predict output based on input ratio
        input_output_ratio = baseline.avg_output_tokens / baseline.avg_input_tokens
        predicted_output = int(input_tokens * input_output_ratio)

        return input_tokens + predicted_output
