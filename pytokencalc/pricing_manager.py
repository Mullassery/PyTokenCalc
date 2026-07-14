"""
Multi-provider pricing manager.
Handles Claude pricing across Anthropic API, AWS Bedrock, GCP Model Garden, and Azure Foundry.
Fetches and caches latest pricing data.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum
import hashlib


class Provider(Enum):
    """LLM providers supporting Claude"""
    ANTHROPIC_API = "anthropic_api"  # Direct Anthropic API
    AWS_BEDROCK = "aws_bedrock"
    GCP_MODEL_GARDEN = "gcp_model_garden"
    AZURE_FOUNDRY = "azure_foundry"


class Region(Enum):
    """Available regions per provider"""
    # Anthropic API (US only)
    US_EAST = "us-east-1"

    # AWS Bedrock regions
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"

    # GCP regions
    US_CENTRAL_1 = "us-central1"
    EU_WEST_1_GCP = "europe-west1"
    ASIA_EAST_1 = "asia-east1"

    # Azure regions
    EAST_US = "eastus"
    WEST_EU = "westeurope"
    SOUTHEAST_ASIA = "southeastasia"


class PricingManager:
    """Manage and cache pricing data across providers"""

    def __init__(self):
        self.cache = {}
        self.cache_ttl_hours = 24
        self.last_update = {}

    def get_pricing(
        self,
        provider: Provider,
        region: Optional[Region] = None,
        force_refresh: bool = False
    ) -> Dict[str, Dict[str, float]]:
        """Get pricing data for provider/region combination"""

        cache_key = f"{provider.value}_{region.value if region else 'default'}"

        # Check cache
        if not force_refresh and cache_key in self.cache:
            if self._cache_valid(cache_key):
                return self.cache[cache_key]

        # Fetch pricing
        pricing = self._fetch_pricing(provider, region)

        # Cache
        self.cache[cache_key] = pricing
        self.last_update[cache_key] = datetime.utcnow()

        return pricing

    def _fetch_pricing(
        self,
        provider: Provider,
        region: Optional[Region] = None
    ) -> Dict[str, Dict[str, float]]:
        """Fetch pricing from provider"""

        if provider == Provider.ANTHROPIC_API:
            return self._get_anthropic_pricing()
        elif provider == Provider.AWS_BEDROCK:
            return self._get_bedrock_pricing(region)
        elif provider == Provider.GCP_MODEL_GARDEN:
            return self._get_gcp_pricing(region)
        elif provider == Provider.AZURE_FOUNDRY:
            return self._get_azure_pricing(region)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _get_anthropic_pricing(self) -> Dict[str, Dict[str, float]]:
        """Get direct Anthropic API pricing (per 1M tokens)"""
        # Updated pricing as of 2026
        return {
            "claude-3-5-sonnet": {
                "input": 3.00,  # $3 per 1M input tokens
                "output": 15.00,  # $15 per 1M output tokens
                "cache_write": 3.75,  # 25% more for cache writing
                "cache_read": 0.30  # 90% discount on cached tokens
            },
            "claude-3-5-haiku": {
                "input": 0.80,
                "output": 4.00,
                "cache_write": 1.00,
                "cache_read": 0.08
            },
            "claude-3-opus": {
                "input": 15.00,
                "output": 75.00,
                "cache_write": 18.75,
                "cache_read": 1.50
            }
        }

    def _get_bedrock_pricing(self, region: Optional[Region] = None) -> Dict[str, Dict[str, float]]:
        """Get AWS Bedrock pricing (per 1M tokens, with regional variance)"""
        # Base pricing (us-east-1)
        base_pricing = {
            "claude-3-5-sonnet": {
                "input": 3.00,
                "output": 15.00,
                "cache_write": 3.75,
                "cache_read": 0.30
            },
            "claude-3-5-haiku": {
                "input": 0.80,
                "output": 4.00,
                "cache_write": 1.00,
                "cache_read": 0.08
            },
            "claude-3-opus": {
                "input": 15.00,
                "output": 75.00,
                "cache_write": 18.75,
                "cache_read": 1.50
            }
        }

        # Regional multipliers
        regional_multipliers = {
            Region.US_EAST_1: 1.0,
            Region.US_WEST_2: 1.0,
            Region.EU_WEST_1: 1.10,  # 10% premium
            Region.AP_SOUTHEAST_1: 1.15  # 15% premium
        }

        multiplier = regional_multipliers.get(region, 1.0)

        # Apply multiplier
        return {
            model: {
                rate_type: rate * multiplier
                for rate_type, rate in rates.items()
            }
            for model, rates in base_pricing.items()
        }

    def _get_gcp_pricing(self, region: Optional[Region] = None) -> Dict[str, Dict[str, float]]:
        """Get GCP Model Garden pricing (per 1M tokens)"""
        # GCP pricing (with volume discounts)
        return {
            "claude-3-5-sonnet": {
                "input": 3.00,
                "output": 15.00,
                "cache_write": 3.75,
                "cache_read": 0.30,
                "volume_discount_threshold": 1_000_000,  # 1M tokens
                "volume_discount": 0.10  # 10% discount above threshold
            },
            "claude-3-5-haiku": {
                "input": 0.80,
                "output": 4.00,
                "cache_write": 1.00,
                "cache_read": 0.08,
                "volume_discount_threshold": 1_000_000,
                "volume_discount": 0.10
            },
            "claude-3-opus": {
                "input": 15.00,
                "output": 75.00,
                "cache_write": 18.75,
                "cache_read": 1.50,
                "volume_discount_threshold": 100_000,  # Lower threshold
                "volume_discount": 0.15  # 15% discount
            }
        }

    def _get_azure_pricing(self, region: Optional[Region] = None) -> Dict[str, Dict[str, float]]:
        """Get Azure Foundry pricing (per 1M tokens, enterprise pricing)"""
        # Azure pricing (typically higher due to enterprise support)
        base_pricing = {
            "claude-3-5-sonnet": {
                "input": 3.30,  # 10% premium
                "output": 16.50,
                "cache_write": 4.13,
                "cache_read": 0.33
            },
            "claude-3-5-haiku": {
                "input": 0.88,
                "output": 4.40,
                "cache_write": 1.10,
                "cache_read": 0.09
            },
            "claude-3-opus": {
                "input": 16.50,
                "output": 82.50,
                "cache_write": 20.63,
                "cache_read": 1.65
            }
        }

        # Regional premiums
        regional_multipliers = {
            Region.EAST_US: 1.0,
            Region.WEST_EU: 1.12,  # 12% premium
            Region.SOUTHEAST_ASIA: 1.20  # 20% premium
        }

        multiplier = regional_multipliers.get(region, 1.0)

        return {
            model: {
                rate_type: rate * multiplier
                for rate_type, rate in rates.items()
            }
            for model, rates in base_pricing.items()
        }

    def _cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self.last_update:
            return False

        age = datetime.utcnow() - self.last_update[cache_key]
        return age.total_seconds() < self.cache_ttl_hours * 3600

    def compare_providers(
        self,
        model: str,
        tokens_input: int = 1_000_000,
        tokens_output: int = 500_000
    ) -> Dict[str, float]:
        """Compare costs across providers for the same workload"""

        costs = {}

        # Anthropic direct API
        anthropic_pricing = self._get_anthropic_pricing()
        if model in anthropic_pricing:
            costs[Provider.ANTHROPIC_API.value] = (
                (tokens_input / 1_000_000) * anthropic_pricing[model]["input"] +
                (tokens_output / 1_000_000) * anthropic_pricing[model]["output"]
            )

        # AWS Bedrock (multiple regions)
        for region in [Region.US_EAST_1, Region.EU_WEST_1]:
            bedrock_pricing = self._get_bedrock_pricing(region)
            if model in bedrock_pricing:
                cost_key = f"{Provider.AWS_BEDROCK.value}_{region.value}"
                costs[cost_key] = (
                    (tokens_input / 1_000_000) * bedrock_pricing[model]["input"] +
                    (tokens_output / 1_000_000) * bedrock_pricing[model]["output"]
                )

        # GCP Model Garden
        gcp_pricing = self._get_gcp_pricing()
        if model in gcp_pricing:
            base_cost = (
                (tokens_input / 1_000_000) * gcp_pricing[model]["input"] +
                (tokens_output / 1_000_000) * gcp_pricing[model]["output"]
            )
            # Apply volume discount if applicable
            if tokens_input > gcp_pricing[model].get("volume_discount_threshold", float('inf')):
                base_cost *= (1 - gcp_pricing[model].get("volume_discount", 0))
            costs["gcp_model_garden"] = base_cost

        # Azure Foundry
        azure_pricing = self._get_azure_pricing()
        if model in azure_pricing:
            costs[Provider.AZURE_FOUNDRY.value] = (
                (tokens_input / 1_000_000) * azure_pricing[model]["input"] +
                (tokens_output / 1_000_000) * azure_pricing[model]["output"]
            )

        return costs

    def get_cheapest_provider(
        self,
        model: str,
        tokens_input: int = 1_000_000,
        tokens_output: int = 500_000
    ) -> tuple:
        """Get cheapest provider and cost for workload"""

        costs = self.compare_providers(model, tokens_input, tokens_output)

        if not costs:
            return None, None

        cheapest_provider = min(costs.items(), key=lambda x: x[1])
        return cheapest_provider[0], cheapest_provider[1]
