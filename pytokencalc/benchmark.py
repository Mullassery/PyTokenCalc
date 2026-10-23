"""Offline token-count parity benchmark.

Feed it JSONL samples containing a prompt and provider-reported usage, and it
compares PyTokenCalc's local token count with the provider's authoritative
count. No provider API calls are made by this module.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Optional, Tuple

from .reconcile import parse_usage
from .tokenizers.registry import get_global_registry


@dataclass(frozen=True)
class ParitySampleResult:
    model: str
    provider: Optional[str]
    prompt: str
    prompt_tokens: int
    provider_tokens: int
    absolute_error: int
    percent_error: Optional[float]
    exact: bool

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "provider": self.provider,
            "prompt": self.prompt,
            "prompt_tokens": self.prompt_tokens,
            "provider_tokens": self.provider_tokens,
            "absolute_error": self.absolute_error,
            "percent_error": self.percent_error,
            "exact": self.exact,
        }


@dataclass(frozen=True)
class ParitySummary:
    results: Tuple[ParitySampleResult, ...]

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def exact_matches(self) -> int:
        return sum(1 for result in self.results if result.exact)

    @property
    def exact_match_rate(self) -> float:
        return self.exact_matches / self.count if self.count else 0.0

    @property
    def mean_absolute_error(self) -> float:
        if not self.results:
            return 0.0
        return sum(result.absolute_error for result in self.results) / self.count

    @property
    def mean_absolute_percent_error(self) -> Optional[float]:
        values = [
            result.percent_error
            for result in self.results
            if result.percent_error is not None
        ]
        return sum(values) / len(values) if values else None

    @property
    def max_absolute_error(self) -> int:
        return max((result.absolute_error for result in self.results), default=0)

    @property
    def p95_absolute_error(self) -> int:
        if not self.results:
            return 0
        ordered = sorted(result.absolute_error for result in self.results)
        index = max(0, math.ceil(0.95 * len(ordered)) - 1)
        return ordered[index]

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "exact_matches": self.exact_matches,
            "exact_match_rate": self.exact_match_rate,
            "mean_absolute_error": self.mean_absolute_error,
            "mean_absolute_percent_error": self.mean_absolute_percent_error,
            "max_absolute_error": self.max_absolute_error,
            "p95_absolute_error": self.p95_absolute_error,
            "results": [result.to_dict() for result in self.results],
        }


def load_samples(path: str) -> List[Mapping[str, Any]]:
    """Load one sample object per non-empty JSONL line."""
    samples: List[Mapping[str, Any]] = []
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            sample = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(sample, Mapping):
            raise ValueError(f"{path}:{line_number}: sample must be a JSON object")
        samples.append(sample)
    return samples


def benchmark_counts(
    samples: Iterable[Mapping[str, Any]],
    *,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    registry: Any = None,
) -> ParitySummary:
    """Compare local prompt-token counts with provider-reported usage."""
    counter_registry = registry if registry is not None else get_global_registry()
    results: List[ParitySampleResult] = []

    for index, sample in enumerate(samples):
        if not isinstance(sample, Mapping):
            raise TypeError(f"sample {index} must be a mapping")
        sample_model = sample.get("model") or model
        if not sample_model:
            raise ValueError(f"sample {index} has no model")
        sample_provider = sample.get("provider") or provider
        prompt = sample.get("prompt", sample.get("text"))
        if not isinstance(prompt, str):
            raise ValueError(f"sample {index} requires a string prompt/text")

        response = sample.get("response", sample)
        usage = parse_usage(response, sample_provider)
        local_tokens = counter_registry.count_tokens(
            str(sample_model), prompt, sample_provider
        ).input_tokens
        provider_tokens = usage.input_tokens
        error = abs(local_tokens - provider_tokens)
        percent = (error / provider_tokens * 100.0) if provider_tokens else None
        results.append(
            ParitySampleResult(
                model=str(sample_model),
                provider=sample_provider,
                prompt=prompt,
                prompt_tokens=local_tokens,
                provider_tokens=provider_tokens,
                absolute_error=error,
                percent_error=percent,
                exact=local_tokens == provider_tokens,
            )
        )

    return ParitySummary(tuple(results))
