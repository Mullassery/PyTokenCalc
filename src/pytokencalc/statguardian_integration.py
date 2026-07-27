"""StatGuardian Integration for PyTokenCalc.

Deep embedding of quality validation in token counting pipeline.
Ensures every token count is validated for accuracy and provider reliability.
"""

from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
import json
from datetime import datetime


@dataclass
class TokenCountValidation:
    """Result of token count validation."""

    is_valid: bool
    compliance_score: float  # 0-100
    severity: str  # critical, warning, info
    issues: List[str]
    metadata: Dict[str, Any]


class TokenCountContract:
    """Quality contract for token counting."""

    def __init__(self):
        self.name = "token_count_quality"
        self.rules = {
            "min_tokens": 1,
            "max_tokens": 1000000,
            "baseline_tolerance_pct": 5.0,
            "confidence_threshold": 0.85,
        }

    def validate_count(self, count: int, baseline: Optional[int] = None) -> Dict:
        """Validate a token count against contract rules."""
        issues = []
        severity = "info"

        # Check range
        if count < self.rules["min_tokens"]:
            issues.append(f"Token count {count} below minimum {self.rules['min_tokens']}")
            severity = "critical"
        elif count > self.rules["max_tokens"]:
            issues.append(f"Token count {count} exceeds maximum {self.rules['max_tokens']}")
            severity = "critical"

        # Check baseline deviation
        if baseline and count > 0:
            deviation_pct = abs(count - baseline) / baseline * 100
            if deviation_pct > self.rules["baseline_tolerance_pct"]:
                issues.append(
                    f"Token count deviation {deviation_pct:.1f}% exceeds tolerance "
                    f"{self.rules['baseline_tolerance_pct']}%"
                )
                severity = "warning"

        return {
            "is_valid": severity != "critical",
            "severity": severity,
            "issues": issues,
        }


class ModelEfficiencyContract:
    """Quality contract for model efficiency baselines."""

    def __init__(self):
        self.name = "model_efficiency_quality"
        self.rules = {
            "min_samples": 50,
            "min_output_ratio": 0.1,
            "max_output_ratio": 2.0,
            "min_stability": 0.85,
        }

    def validate_baseline(self, baseline: Dict) -> Dict:
        """Validate model efficiency baseline."""
        issues = []
        severity = "info"

        # Check sample size
        if baseline.get("samples", 0) < self.rules["min_samples"]:
            issues.append(
                f"Insufficient samples {baseline.get('samples', 0)} "
                f"< {self.rules['min_samples']}"
            )
            severity = "warning"

        # Check efficiency ratio
        ratio = baseline.get("output_tokens", 0) / max(baseline.get("input_tokens", 1), 1)
        if ratio < self.rules["min_output_ratio"] or ratio > self.rules["max_output_ratio"]:
            issues.append(f"Efficiency ratio {ratio:.2f} outside acceptable range")
            severity = "warning"

        # Check stability
        if baseline.get("stability", 1.0) < self.rules["min_stability"]:
            issues.append(
                f"Low stability {baseline.get('stability', 1.0):.2f} "
                f"< {self.rules['min_stability']}"
            )
            severity = "warning"

        return {"is_valid": severity != "critical", "severity": severity, "issues": issues}


class CostPredictionContract:
    """Quality contract for cost predictions."""

    def __init__(self):
        self.name = "cost_prediction_quality"
        self.rules = {
            "max_error_pct": 15.0,
            "min_confidence": 0.70,
            "min_model_coverage": 0.80,
        }

    def validate_prediction(self, prediction: Dict, actual: Optional[float] = None) -> Dict:
        """Validate cost prediction."""
        issues = []
        severity = "info"

        # Check confidence
        if prediction.get("confidence", 0) < self.rules["min_confidence"]:
            issues.append(
                f"Low confidence {prediction.get('confidence', 0):.2f} "
                f"< {self.rules['min_confidence']}"
            )
            severity = "warning"

        # Check model coverage
        if prediction.get("model_coverage", 0) < self.rules["min_model_coverage"]:
            issues.append(
                f"Low model coverage {prediction.get('model_coverage', 0):.1%} "
                f"< {self.rules['min_model_coverage']:.0%}"
            )
            severity = "warning"

        # Check prediction error against actual
        if actual and prediction.get("predicted_cost", 0) > 0:
            error_pct = abs(prediction["predicted_cost"] - actual) / actual * 100
            if error_pct > self.rules["max_error_pct"]:
                issues.append(f"Prediction error {error_pct:.1f}% exceeds tolerance")
                severity = "warning"

        return {"is_valid": severity != "critical", "severity": severity, "issues": issues}


class ProviderReliabilityContract:
    """Quality contract for provider API reliability."""

    def __init__(self):
        self.name = "provider_reliability"
        self.rules = {
            "max_response_time_ms": 5000,
            "max_error_rate": 0.05,
            "min_availability": 0.99,
            "min_consistency": 0.95,
        }

    def validate_provider(self, provider_metrics: Dict) -> Dict:
        """Validate provider API metrics."""
        issues = []
        severity = "info"

        # Check response time
        if provider_metrics.get("response_time_ms", 0) > self.rules["max_response_time_ms"]:
            issues.append(
                f"Slow response {provider_metrics.get('response_time_ms', 0)}ms "
                f"> {self.rules['max_response_time_ms']}ms"
            )
            severity = "warning"

        # Check error rate
        if provider_metrics.get("error_rate", 0) > self.rules["max_error_rate"]:
            issues.append(f"High error rate {provider_metrics.get('error_rate', 0):.1%}")
            severity = "warning"

        # Check availability
        if provider_metrics.get("availability", 1.0) < self.rules["min_availability"]:
            issues.append(
                f"Low availability {provider_metrics.get('availability', 1.0):.2%} "
                f"< {self.rules['min_availability']:.0%}"
            )
            severity = "critical"

        # Check consistency
        if provider_metrics.get("consistency", 1.0) < self.rules["min_consistency"]:
            issues.append(
                f"Low consistency {provider_metrics.get('consistency', 1.0):.2%}"
            )
            severity = "warning"

        return {"is_valid": severity != "critical", "severity": severity, "issues": issues}


class StatGuardianTokenCounter:
    """Wrapper that adds quality validation to token counting."""

    def __init__(self, token_counter):
        self.counter = token_counter
        self.token_contract = TokenCountContract()
        self.efficiency_contract = ModelEfficiencyContract()
        self.prediction_contract = CostPredictionContract()
        self.provider_contract = ProviderReliabilityContract()
        self.validation_log_dir = Path.cwd() / "token_validations"
        self.validation_log_dir.mkdir(exist_ok=True)

    def count_with_validation(self, text: str, model: str, baseline: Optional[int] = None) -> Dict:
        """Count tokens with quality validation."""
        # Count tokens
        result = self.counter.count(text, model)
        token_count = result.get("tokens") if isinstance(result, dict) else result.tokens

        # Validate token count
        validation = self.token_contract.validate_count(token_count, baseline)

        # Log validation
        self._log_validation(
            {
                "timestamp": datetime.now().isoformat(),
                "model": model,
                "token_count": token_count,
                "baseline": baseline,
                "validation": validation,
            }
        )

        return {
            "token_count": token_count,
            "validation": validation,
            "compliance_score": self._calculate_compliance_score(validation),
            "original_result": result,
        }

    def predict_cost_with_validation(self, model: str, token_count: int) -> Dict:
        """Predict cost with quality validation."""
        # Get prediction
        prediction = self.counter.predict_cost(model, token_count)

        # Validate prediction
        validation = self.prediction_contract.validate_prediction(prediction)

        return {
            "prediction": prediction,
            "validation": validation,
            "compliance_score": self._calculate_compliance_score(validation),
        }

    def validate_provider(self, provider: str, metrics: Dict) -> Dict:
        """Validate provider reliability."""
        validation = self.provider_contract.validate_provider(metrics)

        self._log_validation(
            {
                "timestamp": datetime.now().isoformat(),
                "provider": provider,
                "metrics": metrics,
                "validation": validation,
            }
        )

        return {
            "provider": provider,
            "validation": validation,
            "compliance_score": self._calculate_compliance_score(validation),
        }

    def _calculate_compliance_score(self, validation: Dict) -> float:
        """Calculate compliance score (0-100)."""
        if validation["severity"] == "critical":
            return 0.0
        elif validation["severity"] == "warning":
            return 70.0
        else:
            return 100.0

    def _log_validation(self, entry: Dict) -> None:
        """Log validation entry."""
        log_file = self.validation_log_dir / f"validations_{datetime.now():%Y%m%d}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
