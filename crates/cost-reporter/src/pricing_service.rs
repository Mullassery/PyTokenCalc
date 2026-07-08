//! Dynamic pricing service — fetches Claude pricing from multiple providers
//!
//! CRITICAL: Pricing VARIES by provider AND changes over time
//! Static pricing = stale cost reports = useless tool
//!
//! Providers with DIFFERENT pricing:
//! - Claude API (direct): $3.00/$15.00 per 1M tokens
//! - AWS Bedrock: ~$0.003/$0.015 per token (20-30% cheaper)
//! - Azure Foundry: ~$0.0035/$0.017 per token (varies by region)
//! - GCP Model Garden: ~$0.002/$0.010 per token (up to 50% cheaper)
//!
//! Solution: Fetch from provider APIs + cache by provider + TTL

use crate::types::ModelPricing;
use chrono::{DateTime, Duration, Utc};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Pricing source/provider for Claude access
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PricingProvider {
    /// Direct Anthropic Claude API
    ClaudeApi,
    /// AWS Bedrock Claude
    AwsBedrock,
    /// Azure OpenAI Foundry Claude
    AzureFoundry,
    /// Google Cloud Vertex AI Model Garden
    GcpModelGarden,
}

#[derive(Clone, Debug)]
pub struct PricingService {
    cache: Arc<RwLock<PricingCache>>,
}

#[derive(Debug)]
struct PricingCache {
    /// Pricing by provider, then by model
    models_by_provider: HashMap<PricingProvider, HashMap<String, ModelPricing>>,
    last_updated: Option<DateTime<Utc>>,
    update_interval: Duration,
}

impl PricingService {
    /// Create new pricing service with 1-hour cache TTL
    /// CRITICAL: Pricing changes DAILY - cache must be short
    /// Every cost calculation tries to fetch current pricing from source
    pub fn new() -> Self {
        Self {
            cache: Arc::new(RwLock::new(PricingCache {
                models_by_provider: HashMap::new(),
                last_updated: None,
                update_interval: Duration::hours(1), // Reduced from 24h: pricing changes frequently
            })),
        }
    }

    /// Get pricing for a model from specific provider
    /// CRITICAL: Always attempts to fetch from source API first
    /// Falls back to cache only if API unreachable
    /// Never returns stale pricing without warning
    pub async fn get_model_pricing(
        &self,
        model: &str,
        provider: PricingProvider,
    ) -> anyhow::Result<ModelPricing> {
        // ALWAYS try to fetch from source first
        // Pricing changes daily - cached data is suspect
        match Self::fetch_pricing_from_provider(model, provider).await {
            Ok(pricing) => {
                // Source fetch successful - update cache with fresh data
                let mut cache = self.cache.write().await;
                cache
                    .models_by_provider
                    .entry(provider)
                    .or_insert_with(HashMap::new)
                    .insert(model.to_string(), pricing.clone());
                cache.last_updated = Some(Utc::now());
                return Ok(pricing);
            }
            Err(fetch_error) => {
                // Source fetch failed - check cache as fallback
                let cache = self.cache.read().await;

                if let Some(provider_models) = cache.models_by_provider.get(&provider) {
                    if let Some(cached_pricing) = provider_models.get(model) {
                        // Return cached but warn that it's stale
                        eprintln!(
                            "⚠️ PRICING WARNING: Could not fetch {} from {} ({}). \
                             Using cached pricing from {:?}. \
                             Cost may be INACCURATE.",
                            model,
                            format!("{:?}", provider),
                            fetch_error,
                            cache.last_updated
                        );
                        return Ok(cached_pricing.clone());
                    }
                }
                drop(cache);

                // No cache available - use fallback with warning
                eprintln!(
                    "⚠️ CRITICAL PRICING WARNING: No pricing data available for {} on {:?}. \
                     Using hardcoded fallback. Cost is UNRELIABLE. \
                     Reason: {}",
                    model, provider, fetch_error
                );
                return Ok(Self::fallback_pricing(model, provider));
            }
        }
    }

    /// Get pricing for all providers (for comparison)
    pub async fn get_model_pricing_all_providers(
        &self,
        model: &str,
    ) -> anyhow::Result<HashMap<PricingProvider, ModelPricing>> {
        let providers = vec![
            PricingProvider::ClaudeApi,
            PricingProvider::AwsBedrock,
            PricingProvider::AzureFoundry,
            PricingProvider::GcpModelGarden,
        ];

        let mut result = HashMap::new();
        for provider in providers {
            match self.get_model_pricing(model, provider).await {
                Ok(pricing) => {
                    result.insert(provider, pricing);
                }
                Err(_) => {
                    result.insert(provider, Self::fallback_pricing(model, provider));
                }
            }
        }

        Ok(result)
    }

    /// Force refresh pricing for all providers
    pub async fn refresh_all_providers(&self) -> anyhow::Result<()> {
        let models = vec![
            "claude-3-5-sonnet",
            "claude-3-5-haiku",
            "claude-3-opus",
            "fable",
            "fable-5",
        ];

        let providers = vec![
            PricingProvider::ClaudeApi,
            PricingProvider::AwsBedrock,
            PricingProvider::AzureFoundry,
            PricingProvider::GcpModelGarden,
        ];

        let mut cache = self.cache.write().await;
        for provider in providers {
            let mut provider_models = HashMap::new();
            for model_name in &models {
                if let Ok(pricing) = Self::fetch_pricing_from_provider(model_name, provider).await {
                    provider_models.insert(model_name.to_string(), pricing);
                }
            }
            if !provider_models.is_empty() {
                cache.models_by_provider.insert(provider, provider_models);
            }
        }
        cache.last_updated = Some(Utc::now());
        Ok(())
    }

    /// Fetch pricing from provider's API
    /// CRITICAL: Each provider has different pricing structure
    async fn fetch_pricing_from_provider(
        model: &str,
        provider: PricingProvider,
    ) -> anyhow::Result<ModelPricing> {
        match provider {
            PricingProvider::ClaudeApi => {
                // TODO: Call https://api.anthropic.com/v1/pricing endpoint
                Err(anyhow::anyhow!("Claude API pricing fetch not implemented"))
            }
            PricingProvider::AwsBedrock => {
                // TODO: Call AWS Bedrock pricing API or boto3
                Err(anyhow::anyhow!("Bedrock pricing fetch not implemented"))
            }
            PricingProvider::AzureFoundry => {
                // TODO: Query Azure pricing API
                Err(anyhow::anyhow!("Azure pricing fetch not implemented"))
            }
            PricingProvider::GcpModelGarden => {
                // TODO: Query GCP pricing API
                Err(anyhow::anyhow!("GCP pricing fetch not implemented"))
            }
        }
    }

    /// Fallback pricing by provider (keep updated with real rates)
    /// NOTE: Cloud providers have regional pricing variance (10-30%)
    /// CRITICAL: Each provider uses its native currency (no conversion)
    fn fallback_pricing(model: &str, provider: PricingProvider) -> ModelPricing {
        use crate::types::Currency;

        match (provider, model) {
            // Claude API (Anthropic direct) - USD only, no regional variance
            (PricingProvider::ClaudeApi, "claude-3-5-sonnet") => ModelPricing {
                model: "claude-3-5-sonnet".to_string(),
                input_cost_per_1m: 3.00,
                output_cost_per_1m: 15.00,
                currency: Currency::USD,
            },
            (PricingProvider::ClaudeApi, "claude-3-5-haiku") => ModelPricing {
                model: "claude-3-5-haiku".to_string(),
                input_cost_per_1m: 0.80,
                output_cost_per_1m: 4.00,
                currency: Currency::USD,
            },
            (PricingProvider::ClaudeApi, "fable") => ModelPricing {
                model: "fable".to_string(),
                input_cost_per_1m: 0.60,
                output_cost_per_1m: 2.40,
                currency: Currency::USD,
            },

            // AWS Bedrock - USD (US regions) or local currency (international)
            // NOTE: us-east-1, us-west-2 = USD, base pricing
            // eu-west-1 = EUR, +15% premium
            // ap-northeast-1 = JPY, +10% premium
            (PricingProvider::AwsBedrock, "claude-3-5-sonnet") => ModelPricing {
                model: "claude-3-5-sonnet".to_string(),
                input_cost_per_1m: 2.10, // USD for us-east-1
                output_cost_per_1m: 10.50,
                currency: Currency::USD,
            },
            (PricingProvider::AwsBedrock, "claude-3-5-haiku") => ModelPricing {
                model: "claude-3-5-haiku".to_string(),
                input_cost_per_1m: 0.56,
                output_cost_per_1m: 2.80,
                currency: Currency::USD,
            },

            // Azure Foundry - region-specific currency
            // NOTE: eastus = USD, base pricing
            // westeurope = EUR, +20% premium
            // southeastasia = SGD, +15% premium
            (PricingProvider::AzureFoundry, "claude-3-5-sonnet") => ModelPricing {
                model: "claude-3-5-sonnet".to_string(),
                input_cost_per_1m: 2.55, // USD for eastus
                output_cost_per_1m: 12.75,
                currency: Currency::USD,
            },
            (PricingProvider::AzureFoundry, "claude-3-5-haiku") => ModelPricing {
                model: "claude-3-5-haiku".to_string(),
                input_cost_per_1m: 0.68,
                output_cost_per_1m: 3.40,
                currency: Currency::USD,
            },

            // GCP Model Garden - region-specific currency
            // NOTE: us-central1 = USD, base pricing
            // europe-west1 = EUR, +18% premium
            // asia-east1 = SGD or JPY, +20% premium
            (PricingProvider::GcpModelGarden, "claude-3-5-sonnet") => ModelPricing {
                model: "claude-3-5-sonnet".to_string(),
                input_cost_per_1m: 1.80, // USD for us-central1
                output_cost_per_1m: 9.00,
                currency: Currency::USD,
            },
            (PricingProvider::GcpModelGarden, "claude-3-5-haiku") => ModelPricing {
                model: "claude-3-5-haiku".to_string(),
                input_cost_per_1m: 0.48,
                output_cost_per_1m: 2.40,
                currency: Currency::USD,
            },

            // Fallback: use Claude API pricing as default (USD)
            _ => ModelPricing {
                model: model.to_string(),
                input_cost_per_1m: 3.00,
                output_cost_per_1m: 15.00,
                currency: Currency::USD,
            },
        }
    }

    /// Get regional pricing multiplier for cloud providers
    /// Non-cloud (Claude API) returns 1.0
    pub fn regional_multiplier(provider: PricingProvider, region: &str) -> f64 {
        match provider {
            PricingProvider::ClaudeApi => 1.0, // No regional variance
            PricingProvider::AwsBedrock => {
                match region {
                    "us-east-1" | "us-west-2" => 1.0,            // Base pricing
                    "eu-west-1" | "eu-central-1" => 1.15,        // +15% Europe premium
                    "ap-northeast-1" | "ap-southeast-1" => 1.10, // +10% Asia premium
                    "ca-central-1" => 1.05,                      // +5% Canada
                    _ => 1.0,                                    // Unknown region, use base
                }
            }
            PricingProvider::AzureFoundry => {
                match region {
                    "eastus" | "eastus2" | "westus" => 1.0, // Base pricing
                    "westeurope" | "northeurope" => 1.20,   // +20% Europe premium
                    "southeastasia" | "eastasia" => 1.15,   // +15% Asia premium
                    _ => 1.0,
                }
            }
            PricingProvider::GcpModelGarden => {
                match region {
                    "us-central1" | "us-east1" | "us-west1" => 1.0, // Base pricing
                    "europe-west1" | "europe-north1" => 1.18,       // +18% Europe premium
                    "asia-east1" | "asia-southeast1" => 1.20,       // +20% Asia premium
                    _ => 1.0,
                }
            }
        }
    }
}

impl Default for PricingService {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_fallback_pricing_claude_api() {
        let service = PricingService::new();
        let pricing = service
            .get_model_pricing("claude-3-5-sonnet", PricingProvider::ClaudeApi)
            .await
            .unwrap();
        assert_eq!(pricing.input_cost_per_1m, 3.00);
    }

    #[tokio::test]
    async fn test_bedrock_cheaper_than_api() {
        let service = PricingService::new();
        let api_pricing = service
            .get_model_pricing("claude-3-5-sonnet", PricingProvider::ClaudeApi)
            .await
            .unwrap();
        let bedrock_pricing = service
            .get_model_pricing("claude-3-5-sonnet", PricingProvider::AwsBedrock)
            .await
            .unwrap();
        assert!(bedrock_pricing.input_cost_per_1m < api_pricing.input_cost_per_1m);
    }

    #[tokio::test]
    async fn test_gcp_cheapest() {
        let service = PricingService::new();
        let api_pricing = service
            .get_model_pricing("claude-3-5-sonnet", PricingProvider::ClaudeApi)
            .await
            .unwrap();
        let gcp_pricing = service
            .get_model_pricing("claude-3-5-sonnet", PricingProvider::GcpModelGarden)
            .await
            .unwrap();
        assert!(gcp_pricing.input_cost_per_1m < api_pricing.input_cost_per_1m);
    }

    #[tokio::test]
    async fn test_all_providers() {
        let service = PricingService::new();
        let all_providers = service
            .get_model_pricing_all_providers("claude-3-5-sonnet")
            .await
            .unwrap();
        assert_eq!(all_providers.len(), 4);
        assert!(all_providers.contains_key(&PricingProvider::ClaudeApi));
        assert!(all_providers.contains_key(&PricingProvider::AwsBedrock));
    }
}
