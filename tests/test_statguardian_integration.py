"""Tests for StatGuardian integration in PyTokenCalc."""

import pytest
from pytokencalc.statguardian_integration import (
    TokenCountContract,
    ModelEfficiencyContract,
    CostPredictionContract,
    ProviderReliabilityContract,
    StatGuardianTokenCounter,
)


class TestTokenCountContract:
    """Test token count validation."""

    def setup_method(self):
        self.contract = TokenCountContract()

    def test_valid_count(self):
        result = self.contract.validate_count(100)
        assert result["is_valid"] is True
        assert result["severity"] == "info"
        assert len(result["issues"]) == 0

    def test_count_below_minimum(self):
        result = self.contract.validate_count(0)
        assert result["is_valid"] is False
        assert result["severity"] == "critical"
        assert len(result["issues"]) > 0

    def test_count_exceeds_maximum(self):
        result = self.contract.validate_count(1000001)
        assert result["is_valid"] is False
        assert result["severity"] == "critical"

    def test_baseline_deviation_within_tolerance(self):
        result = self.contract.validate_count(105, baseline=100)
        assert result["is_valid"] is True
        assert result["severity"] == "info"

    def test_baseline_deviation_exceeds_tolerance(self):
        result = self.contract.validate_count(110, baseline=100)
        assert result["is_valid"] is True
        assert result["severity"] == "warning"
        assert any("deviation" in issue.lower() for issue in result["issues"])

    def test_large_valid_count(self):
        result = self.contract.validate_count(500000)
        assert result["is_valid"] is True
        assert result["severity"] == "info"


class TestModelEfficiencyContract:
    """Test model efficiency baseline validation."""

    def setup_method(self):
        self.contract = ModelEfficiencyContract()

    def test_valid_baseline(self):
        baseline = {
            "samples": 100,
            "input_tokens": 1000,
            "output_tokens": 500,
            "stability": 0.95,
        }
        result = self.contract.validate_baseline(baseline)
        assert result["is_valid"] is True
        assert result["severity"] == "info"

    def test_insufficient_samples(self):
        baseline = {"samples": 30, "input_tokens": 1000, "output_tokens": 500}
        result = self.contract.validate_baseline(baseline)
        assert result["is_valid"] is True
        assert result["severity"] == "warning"
        assert any("samples" in issue.lower() for issue in result["issues"])

    def test_efficiency_ratio_too_high(self):
        baseline = {
            "samples": 100,
            "input_tokens": 1000,
            "output_tokens": 3000,  # ratio = 3.0 (exceeds 2.0 max)
            "stability": 0.95,
        }
        result = self.contract.validate_baseline(baseline)
        assert result["severity"] == "warning"

    def test_efficiency_ratio_too_low(self):
        baseline = {
            "samples": 100,
            "input_tokens": 1000,
            "output_tokens": 50,  # ratio = 0.05 (below 0.1 min)
            "stability": 0.95,
        }
        result = self.contract.validate_baseline(baseline)
        assert result["severity"] == "warning"

    def test_low_stability(self):
        baseline = {
            "samples": 100,
            "input_tokens": 1000,
            "output_tokens": 500,
            "stability": 0.75,
        }
        result = self.contract.validate_baseline(baseline)
        assert result["severity"] == "warning"
        assert any("stability" in issue.lower() for issue in result["issues"])


class TestCostPredictionContract:
    """Test cost prediction validation."""

    def setup_method(self):
        self.contract = CostPredictionContract()

    def test_valid_prediction(self):
        prediction = {
            "predicted_cost": 10.0,
            "confidence": 0.85,
            "model_coverage": 0.90,
        }
        result = self.contract.validate_prediction(prediction)
        assert result["is_valid"] is True
        assert result["severity"] == "info"

    def test_low_confidence(self):
        prediction = {
            "predicted_cost": 10.0,
            "confidence": 0.60,
            "model_coverage": 0.90,
        }
        result = self.contract.validate_prediction(prediction)
        assert result["severity"] == "warning"

    def test_low_model_coverage(self):
        prediction = {
            "predicted_cost": 10.0,
            "confidence": 0.85,
            "model_coverage": 0.70,
        }
        result = self.contract.validate_prediction(prediction)
        assert result["severity"] == "warning"

    def test_prediction_error_within_tolerance(self):
        prediction = {
            "predicted_cost": 10.5,
            "confidence": 0.85,
            "model_coverage": 0.90,
        }
        result = self.contract.validate_prediction(prediction, actual=10.0)
        assert result["is_valid"] is True

    def test_prediction_error_exceeds_tolerance(self):
        prediction = {
            "predicted_cost": 12.0,
            "confidence": 0.85,
            "model_coverage": 0.90,
        }
        result = self.contract.validate_prediction(prediction, actual=10.0)
        assert result["severity"] == "warning"
        assert any("error" in issue.lower() for issue in result["issues"])


class TestProviderReliabilityContract:
    """Test provider API reliability validation."""

    def setup_method(self):
        self.contract = ProviderReliabilityContract()

    def test_healthy_provider(self):
        metrics = {
            "response_time_ms": 500,
            "error_rate": 0.01,
            "availability": 0.995,
            "consistency": 0.98,
        }
        result = self.contract.validate_provider(metrics)
        assert result["is_valid"] is True
        assert result["severity"] == "info"

    def test_slow_response(self):
        metrics = {
            "response_time_ms": 6000,
            "error_rate": 0.01,
            "availability": 0.99,
            "consistency": 0.98,
        }
        result = self.contract.validate_provider(metrics)
        assert result["severity"] == "warning"

    def test_high_error_rate(self):
        metrics = {
            "response_time_ms": 500,
            "error_rate": 0.10,
            "availability": 0.99,
            "consistency": 0.98,
        }
        result = self.contract.validate_provider(metrics)
        assert result["severity"] == "warning"

    def test_low_availability(self):
        metrics = {
            "response_time_ms": 500,
            "error_rate": 0.01,
            "availability": 0.98,  # Below 0.99
            "consistency": 0.98,
        }
        result = self.contract.validate_provider(metrics)
        assert result["is_valid"] is False
        assert result["severity"] == "critical"

    def test_low_consistency(self):
        metrics = {
            "response_time_ms": 500,
            "error_rate": 0.01,
            "availability": 0.99,
            "consistency": 0.90,
        }
        result = self.contract.validate_provider(metrics)
        assert result["severity"] == "warning"


class TestStatGuardianTokenCounter:
    """Test StatGuardian wrapper."""

    def test_wrapper_initialization(self):
        # Mock counter
        class MockCounter:
            def count(self, text, model):
                return {"tokens": 100}

            def predict_cost(self, model, count):
                return {"predicted_cost": 0.01, "confidence": 0.9}

        counter = MockCounter()
        validated = StatGuardianTokenCounter(counter)

        assert validated.counter == counter
        assert validated.token_contract is not None
        assert validated.validation_log_dir.exists()

    def test_count_with_validation(self):
        class MockCounter:
            def count(self, text, model):
                return {"tokens": 100}

        counter = MockCounter()
        validated = StatGuardianTokenCounter(counter)
        result = validated.count_with_validation("test", "gpt-4")

        assert "token_count" in result
        assert result["token_count"] == 100
        assert "validation" in result
        assert "compliance_score" in result
        assert result["validation"]["is_valid"] is True

    def test_cost_prediction_with_validation(self):
        class MockCounter:
            def predict_cost(self, model, token_count):
                return {
                    "predicted_cost": 0.01,
                    "confidence": 0.85,
                    "model_coverage": 0.90,
                }

        counter = MockCounter()
        validated = StatGuardianTokenCounter(counter)
        result = validated.predict_cost_with_validation("gpt-4", 1000)

        assert "prediction" in result
        assert "validation" in result
        assert "compliance_score" in result

    def test_provider_validation(self):
        class MockCounter:
            pass

        counter = MockCounter()
        validated = StatGuardianTokenCounter(counter)

        metrics = {
            "response_time_ms": 500,
            "error_rate": 0.01,
            "availability": 0.995,
            "consistency": 0.98,
        }
        result = validated.validate_provider("openai", metrics)

        assert "provider" in result
        assert result["provider"] == "openai"
        assert "validation" in result
        assert result["compliance_score"] == 100.0

    def test_compliance_score_calculation(self):
        class MockCounter:
            pass

        counter = MockCounter()
        validated = StatGuardianTokenCounter(counter)

        # Critical severity
        assert validated._calculate_compliance_score({"severity": "critical"}) == 0.0

        # Warning severity
        assert validated._calculate_compliance_score({"severity": "warning"}) == 70.0

        # Info severity
        assert validated._calculate_compliance_score({"severity": "info"}) == 100.0
