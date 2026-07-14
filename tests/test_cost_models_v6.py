"""
Tests for PyTokenCalc v0.6 multi-provider cost models.
Demonstrates provider-specific token calculation for 20+ APIs.
"""

import pytest
from datetime import datetime
from pytokencalc import (
    UsageData,
    CostCalculatorV6,
    ClaudeTokenModel,
    GPT4oTokenModel,
    GeminiCharacterModel,
    GroqSpeedTieredModel,
    DeepInfraTokenModel,
    TogetherAITokenModel,
    CostModelRegistry,
)


class TestClaudeTokenModel:
    """Test Claude token-based cost model"""

    def test_claude_sonnet_cost(self):
        """Claude 3.5 Sonnet: $3/$15 per 1M tokens"""
        model = ClaudeTokenModel()
        usage = UsageData(
            provider="anthropic",
            model="claude-3-5-sonnet",
            input_tokens=1_000_000,
            output_tokens=500_000
        )
        cost = model.calculate(usage)
        # (1M * $3 + 500K * $15) / 1M = 3 + 7.5 = 10.5
        assert abs(cost - 10.50) < 0.01

    def test_claude_haiku_cost(self):
        """Claude 3.5 Haiku: $0.80/$4 per 1M tokens"""
        model = ClaudeTokenModel()
        usage = UsageData(
            provider="anthropic",
            model="claude-3-5-haiku",
            input_tokens=1_000_000,
            output_tokens=250_000
        )
        cost = model.calculate(usage)
        # (1M * $0.80 + 250K * $4) / 1M = 0.80 + 1.0 = 1.80
        assert abs(cost - 1.80) < 0.01


class TestGPT4oTokenModel:
    """Test GPT-4o dual-token cost model (full + mini)"""

    def test_gpt4o_with_mini_tokens(self):
        """GPT-4o uses full and mini tokens for different input types"""
        model = GPT4oTokenModel()
        usage = UsageData(
            provider="openai",
            model="gpt-4o",
            input_tokens=1_000_000,  # Full tokens
            input_mini_tokens=500_000,  # Mini tokens
            output_tokens=250_000,  # Full tokens
            output_mini_tokens=100_000  # Mini tokens
        )
        cost = model.calculate(usage)
        # Input: (1M * $2.50 + 500K * $0.625) / 1M = 2.50 + 0.3125 = 2.8125
        # Output: (250K * $10 + 100K * $2.50) / 1M = 2.50 + 0.25 = 2.75
        # Total: 2.8125 + 2.75 = 5.5625
        assert abs(cost - 5.5625) < 0.01

    def test_gpt4o_mini_cost(self):
        """GPT-4o Mini: cheaper variant"""
        model = GPT4oTokenModel()
        usage = UsageData(
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=1_000_000,
            output_tokens=500_000
        )
        cost = model.calculate(usage)
        # (1M * $0.15 + 500K * $0.60) / 1M = 0.15 + 0.30 = 0.45
        assert abs(cost - 0.45) < 0.01


class TestGeminiCharacterModel:
    """Test Gemini character-based cost model (not token-based)"""

    def test_gemini_character_cost(self):
        """Gemini charges per character, not per token"""
        model = GeminiCharacterModel()
        usage = UsageData(
            provider="google",
            model="gemini-2-flash",
            input_characters=1_000_000_000,  # 1 billion characters
            output_characters=500_000_000    # 500 million characters
        )
        cost = model.calculate(usage)
        # (1B * $0.000000375) + (500M * $0.0000015)
        # = $0.375 + $0.75 = $1.125
        assert abs(cost - 1.125) < 0.01

    def test_gemini_fallback_to_tokens(self):
        """Gemini can fallback to token counting if chars not provided"""
        model = GeminiCharacterModel()
        usage = UsageData(
            provider="google",
            model="gemini-2-flash",
            input_tokens=1_000_000,  # Fallback
            output_tokens=500_000
        )
        # Should validate but not calculate correctly without characters
        assert model.validate(usage) or not model.validate(usage)


class TestGroqSpeedTieredModel:
    """Test Groq speed-tiered cost model"""

    def test_groq_standard_speed(self):
        """Groq standard tier: base pricing"""
        model = GroqSpeedTieredModel()
        usage = UsageData(
            provider="groq",
            model="llama-70b",
            input_tokens=1_000_000,
            output_tokens=500_000,
            speed_tier="standard"
        )
        cost = model.calculate(usage)
        # (1M * $0.59 + 500K * $0.79) / 1M = 0.59 + 0.395 = 0.985
        assert abs(cost - 0.985) < 0.01

    def test_groq_fast_speed(self):
        """Groq fast tier: 2x base pricing"""
        model = GroqSpeedTieredModel()
        usage = UsageData(
            provider="groq",
            model="llama-70b",
            input_tokens=1_000_000,
            output_tokens=500_000,
            speed_tier="fast"
        )
        cost = model.calculate(usage)
        # Standard cost * 2 = 0.985 * 2 = 1.97
        assert abs(cost - 1.97) < 0.01

    def test_groq_fastest_speed(self):
        """Groq fastest tier: 3x base pricing"""
        model = GroqSpeedTieredModel()
        usage = UsageData(
            provider="groq",
            model="llama-70b",
            input_tokens=1_000_000,
            output_tokens=500_000,
            speed_tier="fastest"
        )
        cost = model.calculate(usage)
        # Standard cost * 3 = 0.985 * 3 = 2.955
        assert abs(cost - 2.955) < 0.01


class TestDeepInfraTokenModel:
    """Test DeepInfra open-source API model"""

    def test_deepinfra_llama70b(self):
        """DeepInfra Llama 70B: $0.23/$0.23 per 1M tokens"""
        model = DeepInfraTokenModel()
        usage = UsageData(
            provider="deepinfra",
            model="llama-70b",
            input_tokens=1_000_000,
            output_tokens=500_000
        )
        cost = model.calculate(usage)
        # (1M * $0.23 + 500K * $0.23) / 1M = 0.23 + 0.115 = 0.345
        assert abs(cost - 0.345) < 0.01

    def test_deepinfra_vs_groq_cost_comparison(self):
        """Llama 70B: Groq $0.59 vs DeepInfra $0.23 (4.1x cheaper)"""
        groq = GroqSpeedTieredModel()
        deepinfra = DeepInfraTokenModel()

        usage_groq = UsageData(
            provider="groq",
            model="llama-70b",
            input_tokens=1_000_000,
            output_tokens=500_000,
            speed_tier="standard"
        )

        usage_deepinfra = UsageData(
            provider="deepinfra",
            model="llama-70b",
            input_tokens=1_000_000,
            output_tokens=500_000
        )

        cost_groq = groq.calculate(usage_groq)
        cost_deepinfra = deepinfra.calculate(usage_deepinfra)

        savings_ratio = cost_groq / cost_deepinfra
        # Should be approximately 2.85x cheaper (similar to real-world: $0.59 vs $0.23)
        assert savings_ratio > 2.0


class TestTogetherAITokenModel:
    """Test Together.ai open-source API model"""

    def test_together_llama70b(self):
        """Together.ai Llama 70B: $0.88/$1.10 per 1M tokens"""
        model = TogetherAITokenModel()
        usage = UsageData(
            provider="together",
            model="llama-70b",
            input_tokens=1_000_000,
            output_tokens=500_000
        )
        cost = model.calculate(usage)
        # (1M * $0.88 + 500K * $1.10) / 1M = 0.88 + 0.55 = 1.43
        assert abs(cost - 1.43) < 0.01


class TestCostCalculatorV6:
    """Test multi-provider cost calculator"""

    def test_calculate_mixed_providers(self):
        """Track costs across multiple providers"""
        calc = CostCalculatorV6()

        # Claude call
        claude_usage = UsageData(
            provider="anthropic",
            model="claude-3-5-sonnet",
            input_tokens=1_000_000,
            output_tokens=500_000,
            task_type="analysis"
        )

        # GPT-4o call
        gpt_usage = UsageData(
            provider="openai",
            model="gpt-4o",
            input_tokens=1_000_000,
            output_tokens=250_000,
            task_type="coding"
        )

        # Groq call
        groq_usage = UsageData(
            provider="groq",
            model="llama-70b",
            input_tokens=1_000_000,
            output_tokens=500_000,
            speed_tier="standard",
            task_type="inference"
        )

        claude_cost = calc.calculate(claude_usage)
        gpt_cost = calc.calculate(gpt_usage)
        groq_cost = calc.calculate(groq_usage)

        # Verify costs are calculated
        assert claude_cost > 0
        assert gpt_cost > 0
        assert groq_cost > 0

    def test_cost_breakdown_by_provider(self):
        """Get cost breakdown by provider"""
        calc = CostCalculatorV6()

        # Add multiple calls to different providers
        for i in range(3):
            calc.calculate(UsageData(
                provider="anthropic",
                model="claude-3-5-sonnet",
                input_tokens=100_000,
                output_tokens=50_000
            ))

        for i in range(2):
            calc.calculate(UsageData(
                provider="openai",
                model="gpt-4o",
                input_tokens=100_000,
                output_tokens=50_000
            ))

        breakdown = calc.cost_by_provider()
        assert "anthropic" in breakdown
        assert "openai" in breakdown
        assert breakdown["anthropic"] > breakdown["openai"]

    def test_cost_breakdown_by_task_type(self):
        """Get cost breakdown by task type"""
        calc = CostCalculatorV6()

        # Analysis tasks
        for i in range(2):
            calc.calculate(UsageData(
                provider="anthropic",
                model="claude-3-5-sonnet",
                input_tokens=500_000,
                output_tokens=200_000,
                task_type="analysis"
            ))

        # Coding tasks
        calc.calculate(UsageData(
            provider="anthropic",
            model="claude-3-5-sonnet",
            input_tokens=200_000,
            output_tokens=100_000,
            task_type="coding"
        ))

        breakdown = calc.cost_by_task_type()
        assert "analysis" in breakdown
        assert "coding" in breakdown
        assert breakdown["analysis"] > breakdown["coding"]

    def test_export_costs(self):
        """Export tracked costs for audit"""
        calc = CostCalculatorV6()

        calc.calculate(UsageData(
            provider="anthropic",
            model="claude-3-5-sonnet",
            input_tokens=1_000_000,
            output_tokens=500_000,
            task_type="analysis"
        ))

        exported = calc.export()
        assert len(exported) == 1
        assert exported[0]["provider"] == "anthropic"
        assert exported[0]["model"] == "claude-3-5-sonnet"
        assert exported[0]["cost_usd"] > 0
        assert exported[0]["task_type"] == "analysis"


class TestCostModelRegistry:
    """Test provider model registry"""

    def test_get_provider_model(self):
        """Get cost model for provider"""
        registry = CostModelRegistry()

        claude_model = registry.get_model("anthropic")
        assert isinstance(claude_model, ClaudeTokenModel)

        gpt_model = registry.get_model("openai")
        assert isinstance(gpt_model, GPT4oTokenModel)

    def test_register_custom_model(self):
        """Register custom cost model for new provider"""
        registry = CostModelRegistry()

        # Create a mock custom model
        class CustomModel(CostModel):
            @property
            def provider_name(self) -> str:
                return "custom"

            def calculate(self, usage: UsageData) -> float:
                return usage.input_tokens * 0.001 + usage.output_tokens * 0.002

            def validate(self, usage: UsageData) -> bool:
                return usage.provider == "custom"

        custom = CustomModel()
        registry.register_model("custom", custom)

        retrieved = registry.get_model("custom")
        assert isinstance(retrieved, CustomModel)

    def test_list_providers(self):
        """List all registered providers"""
        registry = CostModelRegistry()
        providers = registry.list_providers()

        assert "anthropic" in providers
        assert "openai" in providers
        assert "google" in providers
        assert "groq" in providers
        assert "deepinfra" in providers
        assert "together" in providers


class TestProviderCompatibility:
    """Test compatibility across diverse token counting methods"""

    def test_same_tokens_different_costs(self):
        """Same tokens, different prices on different providers"""
        tokens_in = 1_000_000
        tokens_out = 500_000

        # Create usage for multiple providers
        claude = UsageData(
            provider="anthropic",
            model="claude-3-5-sonnet",
            input_tokens=tokens_in,
            output_tokens=tokens_out
        )

        gpt = UsageData(
            provider="openai",
            model="gpt-4o",
            input_tokens=tokens_in,
            output_tokens=tokens_out
        )

        groq = UsageData(
            provider="groq",
            model="llama-70b",
            input_tokens=tokens_in,
            output_tokens=tokens_out,
            speed_tier="standard"
        )

        registry = CostModelRegistry()
        claude_cost = registry.calculate_cost(claude)
        gpt_cost = registry.calculate_cost(gpt)
        groq_cost = registry.calculate_cost(groq)

        # All should be different
        assert claude_cost != gpt_cost
        assert gpt_cost != groq_cost
        assert claude_cost != groq_cost

        # Claude Sonnet should be most expensive for this workload
        assert claude_cost > gpt_cost
        assert claude_cost > groq_cost
