"""
Unit tests for cost model and provider implementations.
"""

import pytest
from datetime import datetime
from pytokencalc.cost_model import (
    Cost,
    OpenAIProvider,
    BedrockProvider,
    GeminiProvider,
    ProviderRegistry,
    CostTracker,
)


class TestOpenAIProvider:
    """Tests for OpenAI cost calculator"""

    @pytest.fixture
    def provider(self):
        return OpenAIProvider()

    def test_detect_gpt4_call(self, provider):
        call_data = {'model': 'gpt-4'}
        assert provider.detect_call(call_data) is True

    def test_detect_gpt5_call(self, provider):
        call_data = {'model': 'gpt-5'}
        assert provider.detect_call(call_data) is True

    def test_detect_non_openai_call(self, provider):
        call_data = {'model': 'claude-3-sonnet'}
        assert provider.detect_call(call_data) is False

    def test_calculate_gpt4_cost(self, provider):
        call_data = {
            'model': 'gpt-4',
        }
        response_data = {
            'usage': {
                'prompt_tokens': 1000,
                'completion_tokens': 500,
            }
        }

        cost = provider.calculate_cost(call_data, response_data)

        assert cost.provider == 'openai'
        assert cost.model == 'gpt-4'
        assert cost.input_tokens == 1000
        assert cost.output_tokens == 500
        assert cost.input_cost == pytest.approx(0.030)  # 1000/1000 * 0.03
        assert cost.output_cost == pytest.approx(0.030)  # 500/1000 * 0.06
        assert cost.total_cost == pytest.approx(0.060)

    def test_calculate_gpt4_vision_cost(self, provider):
        call_data = {
            'model': 'gpt-4-vision',
            'vision': True,
        }
        response_data = {
            'usage': {
                'prompt_tokens': 1000,
                'completion_tokens': 500,
            }
        }

        cost = provider.calculate_cost(call_data, response_data)

        # Vision premium should be applied to input cost
        expected_input = 0.030 * 1.25  # 25% premium
        assert cost.input_cost == pytest.approx(expected_input)

    def test_unknown_model_raises_error(self, provider):
        call_data = {'model': 'gpt-100'}
        response_data = {'usage': {'prompt_tokens': 100, 'completion_tokens': 50}}

        with pytest.raises(ValueError, match="Unknown OpenAI model"):
            provider.calculate_cost(call_data, response_data)

    def test_validate_pricing(self, provider):
        assert provider.validate_pricing() is True


class TestBedrockProvider:
    """Tests for AWS Bedrock cost calculator"""

    @pytest.fixture
    def provider(self):
        return BedrockProvider()

    def test_detect_claude_bedrock_call(self, provider):
        call_data = {'modelId': 'anthropic.claude-3-opus'}
        assert provider.detect_call(call_data) is True

    def test_detect_llama_bedrock_call(self, provider):
        call_data = {'modelId': 'meta.llama2-70b-chat'}
        assert provider.detect_call(call_data) is True

    def test_detect_non_bedrock_call(self, provider):
        call_data = {'modelId': 'gpt-4'}
        assert provider.detect_call(call_data) is False

    def test_calculate_claude3_opus_cost(self, provider):
        call_data = {'modelId': 'anthropic.claude-3-opus'}
        response_data = {
            'usage': {
                'inputTokens': 2000,
                'outputTokens': 1000,
            }
        }

        cost = provider.calculate_cost(call_data, response_data)

        assert cost.provider == 'bedrock'
        assert cost.model == 'anthropic.claude-3-opus'
        assert cost.input_tokens == 2000
        assert cost.output_tokens == 1000
        assert cost.input_cost == pytest.approx(0.030)  # 2000/1000 * 0.015
        assert cost.output_cost == pytest.approx(0.075)  # 1000/1000 * 0.075

    def test_provisioned_throughput_discount(self, provider):
        call_data = {
            'modelId': 'anthropic.claude-3-opus',
            'provisioned_throughput_arn': 'arn:aws:bedrock:...',
        }
        response_data = {
            'usage': {
                'inputTokens': 1000,
                'outputTokens': 500,
            }
        }

        cost = provider.calculate_cost(call_data, response_data)

        # Should have 10% discount applied
        assert cost.details['provisioned_discount'] == 0.1
        expected_input = (1000 / 1000 * 0.015) * 0.9
        assert cost.input_cost == pytest.approx(expected_input)

    def test_unknown_model_raises_error(self, provider):
        call_data = {'modelId': 'anthropic.unknown-model'}
        response_data = {'usage': {'inputTokens': 100, 'outputTokens': 50}}

        with pytest.raises(ValueError, match="Unknown Bedrock model"):
            provider.calculate_cost(call_data, response_data)

    def test_validate_pricing(self, provider):
        assert provider.validate_pricing() is True


class TestGeminiProvider:
    """Tests for Google Gemini cost calculator"""

    @pytest.fixture
    def provider(self):
        return GeminiProvider()

    def test_detect_gemini_call(self, provider):
        call_data = {'model': 'gemini-pro'}
        assert provider.detect_call(call_data) is True

    def test_detect_non_gemini_call(self, provider):
        call_data = {'model': 'gpt-4'}
        assert provider.detect_call(call_data) is False

    def test_calculate_gemini_cost(self, provider):
        call_data = {'model': 'gemini-pro'}
        response_data = {
            'usage_metadata': {
                'prompt_token_count': 1000,
                'candidates_token_count': 500,
            }
        }

        cost = provider.calculate_cost(call_data, response_data)

        assert cost.provider == 'gemini'
        assert cost.model == 'gemini-pro'
        assert cost.input_tokens == 1000
        assert cost.output_tokens == 500
        expected_input = (1000 / 1000) * 0.000125
        expected_output = (500 / 1000) * 0.000375
        assert cost.input_cost == pytest.approx(expected_input)
        assert cost.output_cost == pytest.approx(expected_output)

    def test_unknown_model_raises_error(self, provider):
        call_data = {'model': 'gemini-unknown'}
        response_data = {'usage_metadata': {'prompt_token_count': 100, 'candidates_token_count': 50}}

        with pytest.raises(ValueError, match="Unknown Gemini model"):
            provider.calculate_cost(call_data, response_data)

    def test_validate_pricing(self, provider):
        assert provider.validate_pricing() is True


class TestProviderRegistry:
    """Tests for provider registry"""

    @pytest.fixture
    def registry(self):
        return ProviderRegistry()

    def test_detect_openai_provider(self, registry):
        call_data = {'model': 'gpt-4'}
        provider = registry.detect_provider(call_data)
        assert provider is not None
        assert provider.name == 'openai'

    def test_detect_bedrock_provider(self, registry):
        call_data = {'modelId': 'anthropic.claude-3-opus'}
        provider = registry.detect_provider(call_data)
        assert provider is not None
        assert provider.name == 'bedrock'

    def test_detect_gemini_provider(self, registry):
        call_data = {'model': 'gemini-pro'}
        provider = registry.detect_provider(call_data)
        assert provider is not None
        assert provider.name == 'gemini'

    def test_detect_unknown_provider(self, registry):
        call_data = {'model': 'unknown-model'}
        provider = registry.detect_provider(call_data)
        assert provider is None

    def test_get_provider_by_name(self, registry):
        provider = registry.get_provider('openai')
        assert provider is not None
        assert provider.name == 'openai'

    def test_get_unknown_provider_by_name(self, registry):
        provider = registry.get_provider('unknown')
        assert provider is None

    def test_list_providers(self, registry):
        providers = registry.list_providers()
        assert 'openai' in providers
        assert 'bedrock' in providers
        assert 'gemini' in providers

    def test_case_insensitive_provider_lookup(self, registry):
        provider = registry.get_provider('OPENAI')
        assert provider is not None
        assert provider.name == 'openai'


class TestCostTracker:
    """Tests for cost tracker"""

    @pytest.fixture
    def tracker(self):
        return CostTracker()

    def test_track_openai_call(self, tracker):
        call_data = {'model': 'gpt-4'}
        response_data = {
            'usage': {
                'prompt_tokens': 100,
                'completion_tokens': 50,
            }
        }

        cost = tracker.track_api_call(call_data, response_data)

        assert cost is not None
        assert cost.provider == 'openai'
        assert len(tracker.costs) == 1

    def test_track_multiple_calls(self, tracker):
        call_data_1 = {'model': 'gpt-4'}
        response_data_1 = {'usage': {'prompt_tokens': 100, 'completion_tokens': 50}}

        call_data_2 = {'modelId': 'anthropic.claude-3-opus'}
        response_data_2 = {'usage': {'inputTokens': 200, 'outputTokens': 100}}

        tracker.track_api_call(call_data_1, response_data_1)
        tracker.track_api_call(call_data_2, response_data_2)

        assert len(tracker.costs) == 2

    def test_get_total_cost(self, tracker):
        call_data = {'model': 'gpt-4'}
        response_data = {
            'usage': {
                'prompt_tokens': 1000,
                'completion_tokens': 500,
            }
        }

        tracker.track_api_call(call_data, response_data)
        total = tracker.get_total_cost()

        assert total == pytest.approx(0.060)

    def test_cost_by_provider(self, tracker):
        # Track OpenAI call
        tracker.track_api_call(
            {'model': 'gpt-4'},
            {'usage': {'prompt_tokens': 1000, 'completion_tokens': 500}}
        )

        # Track Bedrock call
        tracker.track_api_call(
            {'modelId': 'anthropic.claude-3-opus'},
            {'usage': {'inputTokens': 2000, 'outputTokens': 1000}}
        )

        breakdown = tracker.cost_by_provider()

        assert 'openai' in breakdown
        assert 'bedrock' in breakdown
        assert breakdown['openai'] == pytest.approx(0.060)
        assert breakdown['bedrock'] == pytest.approx(0.105)

    def test_cost_by_model(self, tracker):
        tracker.track_api_call(
            {'model': 'gpt-4'},
            {'usage': {'prompt_tokens': 1000, 'completion_tokens': 500}}
        )

        breakdown = tracker.cost_by_model()

        assert 'gpt-4' in breakdown
        assert breakdown['gpt-4'] == pytest.approx(0.060)

    def test_get_costs_with_filter(self, tracker):
        tracker.track_api_call(
            {'model': 'gpt-4'},
            {'usage': {'prompt_tokens': 100, 'completion_tokens': 50}}
        )

        tracker.track_api_call(
            {'modelId': 'anthropic.claude-3-opus'},
            {'usage': {'inputTokens': 200, 'outputTokens': 100}}
        )

        openai_costs = tracker.get_costs(provider='openai')
        assert len(openai_costs) == 1
        assert openai_costs[0].provider == 'openai'

    def test_clear_costs(self, tracker):
        tracker.track_api_call(
            {'model': 'gpt-4'},
            {'usage': {'prompt_tokens': 100, 'completion_tokens': 50}}
        )

        assert len(tracker.costs) == 1

        tracker.clear()

        assert len(tracker.costs) == 0

    def test_export_costs(self, tracker):
        tracker.track_api_call(
            {'model': 'gpt-4'},
            {'usage': {'prompt_tokens': 100, 'completion_tokens': 50}}
        )

        exported = tracker.export_costs()

        assert len(exported) == 1
        assert 'id' in exported[0]
        assert 'timestamp' in exported[0]
        assert 'provider' in exported[0]
        assert 'total_cost' in exported[0]

    def test_unknown_provider_returns_none(self, tracker):
        call_data = {'model': 'unknown-model'}
        response_data = {'usage': {'prompt_tokens': 100, 'completion_tokens': 50}}

        cost = tracker.track_api_call(call_data, response_data)

        assert cost is None
        assert len(tracker.costs) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
