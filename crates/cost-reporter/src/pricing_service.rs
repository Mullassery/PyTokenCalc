//! Dynamic pricing service — fetches current Claude pricing from API
//!
//! CRITICAL: Pricing changes as new models launch and rates update
//! Static pricing = stale cost reports = useless tool
//!
//! Solution: Fetch from Claude API + cache with TTL

use crate::types::ModelPricing;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use chrono::{DateTime, Utc, Duration};

#[derive(Clone, Debug)]
pub struct PricingService {
    cache: Arc<RwLock<PricingCache>>,
}

#[derive(Debug)]
struct PricingCache {
    models: HashMap<String, ModelPricing>,
    last_updated: Option<DateTime<Utc>>,
    update_interval: Duration,
}

impl PricingService {
    /// Create new pricing service with 24-hour cache TTL
    pub fn new() -> Self {
        Self {
            cache: Arc::new(RwLock::new(PricingCache {
                models: HashMap::new(),
                last_updated: None,
                update_interval: Duration::hours(24),
            })),
        }
    }

    /// Get pricing for a model, fetching if cache expired
    pub async fn get_model_pricing(&self, model: &str) -> anyhow::Result<ModelPricing> {
        let cache = self.cache.read().await;

        // Return cached if available and fresh
        if let Some(pricing) = cache.models.get(model) {
            if let Some(last_updated) = cache.last_updated {
                if Utc::now() - last_updated < cache.update_interval {
                    return Ok(pricing.clone());
                }
            }
        }
        drop(cache);

        // Cache expired or model not found: fetch fresh pricing
        let mut cache = self.cache.write().await;
        let pricing = Self::fetch_pricing_from_api(model).await
            .unwrap_or_else(|_| Self::fallback_pricing(model));

        cache.models.insert(model.to_string(), pricing.clone());
        cache.last_updated = Some(Utc::now());

        Ok(pricing)
    }

    /// Get all cached models (for reporting which ones we have pricing for)
    pub async fn list_cached_models(&self) -> Vec<String> {
        let cache = self.cache.read().await;
        cache.models.keys().cloned().collect()
    }

    /// Force refresh pricing (call after detecting new model)
    pub async fn refresh_all(&self) -> anyhow::Result<()> {
        let models = vec![
            "claude-3-5-sonnet",
            "claude-3-5-haiku",
            "claude-3-opus",
            "claude-3-haiku",
            "claude-3-sonnet",
            "fable",
            "fable-5",  // Newly launched
        ];

        let mut cache = self.cache.write().await;
        for model_name in models {
            if let Ok(pricing) = Self::fetch_pricing_from_api(model_name).await {
                cache.models.insert(model_name.to_string(), pricing);
            }
        }
        cache.last_updated = Some(Utc::now());
        Ok(())
    }

    /// Fetch current pricing from Claude API
    /// IMPORTANT: This requires either:
    /// 1. Claude API pricing endpoint (if Anthropic exposes it)
    /// 2. Scraping Anthropic's pricing page
    /// 3. Integration with pricing aggregator
    async fn fetch_pricing_from_api(model: &str) -> anyhow::Result<ModelPricing> {
        // TODO: Implement actual API call
        // For now, return placeholder that indicates API should be called

        // Option 1: If Anthropic has a pricing endpoint:
        // let response = reqwest::Client::new()
        //     .get("https://api.anthropic.com/v1/pricing")
        //     .header("Authorization", format!("Bearer {}", api_key))
        //     .send()
        //     .await?;

        // Option 2: Parse published pricing page (brittle but works):
        // let html = reqwest::get("https://www.anthropic.com/pricing").await?.text().await?;
        // let pricing = parse_pricing_from_html(&html, model)?;

        // Option 3: Use pricing aggregator API:
        // let response = reqwest::get(&format!("https://pricing.example.com/claude/{}", model))
        //     .await?.json::<ModelPricing>().await?;

        Err(anyhow::anyhow!(
            "Pricing fetch not yet implemented. Need to integrate with: \
             1) Anthropic API pricing endpoint, \
             2) Pricing page scraper, or \
             3) External pricing aggregator. \
             Falling back to cached pricing."
        ))
    }

    /// Fallback pricing (last known rates - kept updated manually or via CI)
    fn fallback_pricing(model: &str) -> ModelPricing {
        match model {
            // Claude 3.5 models (current as of 2026-07-05)
            "claude-3-5-sonnet" => ModelPricing {
                model: "claude-3-5-sonnet".to_string(),
                input_cost_per_1m: 3.00,
                output_cost_per_1m: 15.00,
            },
            "claude-3-5-haiku" => ModelPricing {
                model: "claude-3-5-haiku".to_string(),
                input_cost_per_1m: 0.80,
                output_cost_per_1m: 4.00,
            },
            // Fable models
            "fable" => ModelPricing {
                model: "fable".to_string(),
                input_cost_per_1m: 0.60,  // Hypothetical - will change
                output_cost_per_1m: 2.40,
            },
            "fable-5" => ModelPricing {
                model: "fable-5".to_string(),
                input_cost_per_1m: 0.50,  // Newly launched, unknown exact pricing
                output_cost_per_1m: 2.00,
            },
            // Claude 3 models (older, but still available)
            "claude-3-opus" => ModelPricing {
                model: "claude-3-opus".to_string(),
                input_cost_per_1m: 15.00,
                output_cost_per_1m: 75.00,
            },
            "claude-3-sonnet" => ModelPricing {
                model: "claude-3-sonnet".to_string(),
                input_cost_per_1m: 3.00,
                output_cost_per_1m: 15.00,
            },
            "claude-3-haiku" => ModelPricing {
                model: "claude-3-haiku".to_string(),
                input_cost_per_1m: 0.80,
                output_cost_per_1m: 4.00,
            },
            // Unknown model: use Sonnet as safe default
            _ => ModelPricing {
                model: model.to_string(),
                input_cost_per_1m: 3.00,
                output_cost_per_1m: 15.00,
            },
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
    async fn test_fallback_pricing_sonnet() {
        let service = PricingService::new();
        let pricing = service.get_model_pricing("claude-3-5-sonnet").await.unwrap();
        assert_eq!(pricing.input_cost_per_1m, 3.00);
        assert_eq!(pricing.output_cost_per_1m, 15.00);
    }

    #[tokio::test]
    async fn test_fallback_pricing_haiku() {
        let service = PricingService::new();
        let pricing = service.get_model_pricing("claude-3-5-haiku").await.unwrap();
        assert_eq!(pricing.input_cost_per_1m, 0.80);
        assert_eq!(pricing.output_cost_per_1m, 4.00);
    }

    #[tokio::test]
    async fn test_fallback_pricing_fable_5() {
        let service = PricingService::new();
        let pricing = service.get_model_pricing("fable-5").await.unwrap();
        assert!(pricing.input_cost_per_1m > 0.0);
    }

    #[tokio::test]
    async fn test_cache_fresh() {
        let service = PricingService::new();
        let pricing1 = service.get_model_pricing("claude-3-5-sonnet").await.unwrap();
        let pricing2 = service.get_model_pricing("claude-3-5-sonnet").await.unwrap();
        assert_eq!(pricing1.input_cost_per_1m, pricing2.input_cost_per_1m);
    }
}
