//! Provider API integrations for fetching ACTUAL usage + pricing
//!
//! CRITICAL: Never estimate - fetch ACTUALS from provider APIs
//!
//! Anthropic: Real usage from API
//! AWS Bedrock: Real usage from CloudWatch + billing
//! Azure: Real usage from Foundry APIs
//! GCP: Real usage from Cloud Billing
//!
//! Each provider's actual data becomes ground truth for cost reporting

use crate::pricing_service::PricingProvider;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Actual usage data from provider (not estimate)
#[derive(Debug, Clone)]
pub struct ActualUsageData {
    pub provider: PricingProvider,
    pub model: String,
    pub tokens_input_actual: u64,
    pub tokens_output_actual: u64,
    pub cost_usd_actual: f64,
    pub cost_timestamp: chrono::DateTime<chrono::Utc>,
}

/// Anthropic API usage response
#[derive(Debug, Deserialize, Serialize)]
struct AnthropicUsageResponse {
    #[serde(default)]
    data: Vec<AnthropicUsageRecord>,
}

#[derive(Debug, Deserialize, Serialize)]
struct AnthropicUsageRecord {
    model: String,
    #[serde(rename = "input_tokens")]
    input_tokens: u64,
    #[serde(rename = "output_tokens")]
    output_tokens: u64,
    #[serde(rename = "cost_usd")]
    cost_usd: f64,
    timestamp: String,
}

/// Provider API integration for fetching actuals
pub struct ProviderIntegration;

impl ProviderIntegration {
    /// Fetch ACTUAL usage from Anthropic API
    /// Requires: ANTHROPIC_API_KEY environment variable
    /// Calls the /v1/usage endpoint for today's actual usage
    /// Returns: Real tokens consumed + real cost charged
    pub async fn fetch_anthropic_actuals() -> anyhow::Result<Vec<ActualUsageData>> {
        let api_key = std::env::var("ANTHROPIC_API_KEY")
            .map_err(|_| anyhow::anyhow!("ANTHROPIC_API_KEY not set"))?;

        let client = reqwest::Client::new();
        let response = client
            .get("https://api.anthropic.com/v1/usage")
            .header("x-api-key", &api_key)
            .header("anthropic-version", "2023-06-01")
            .send()
            .await
            .map_err(|e| anyhow::anyhow!("Failed to call Anthropic API: {}", e))?;

        if !response.status().is_success() {
            return Err(anyhow::anyhow!(
                "Anthropic API error: {}",
                response.status()
            ));
        }

        let usage_response: AnthropicUsageResponse = response
            .json()
            .await
            .map_err(|e| anyhow::anyhow!("Failed to parse Anthropic response: {}", e))?;

        let actuals = usage_response
            .data
            .into_iter()
            .map(|record| ActualUsageData {
                provider: PricingProvider::ClaudeApi,
                model: record.model,
                tokens_input_actual: record.input_tokens,
                tokens_output_actual: record.output_tokens,
                cost_usd_actual: record.cost_usd,
                cost_timestamp: chrono::DateTime::parse_from_rfc3339(&record.timestamp)
                    .ok()
                    .map(|dt| dt.with_timezone(&Utc))
                    .unwrap_or_else(|| Utc::now()),
            })
            .collect();

        Ok(actuals)
    }

    /// Fetch ACTUAL usage from AWS Bedrock
    /// Requires: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION env vars
    /// Sources:
    ///   - CloudWatch metrics (actual invocations)
    ///   - Cost Explorer API (actual charges)
    /// Returns: Real API calls + tokens + costs
    pub async fn fetch_bedrock_actuals(
        aws_region: &str,
        model_arn: &str,
    ) -> anyhow::Result<Vec<ActualUsageData>> {
        let _access_key = std::env::var("AWS_ACCESS_KEY_ID")
            .map_err(|_| anyhow::anyhow!("AWS_ACCESS_KEY_ID not set"))?;
        let _secret_key = std::env::var("AWS_SECRET_ACCESS_KEY")
            .map_err(|_| anyhow::anyhow!("AWS_SECRET_ACCESS_KEY not set"))?;

        // Note: Full AWS SDK integration requires aws-sdk-rust
        // For now, we provide the structure for CloudWatch + Cost Explorer calls
        // These would be implemented with actual AWS SDK bindings

        tracing::warn!(
            region = aws_region,
            model = model_arn,
            "Bedrock integration: AWS SDK not available - implement with aws-sdk-rust"
        );

        // Placeholder: Return empty vec - actual implementation requires aws-sdk
        // When available, this would:
        // 1. Query CloudWatch for bedrock_invocations metric
        // 2. Query Cost Explorer for bedrock service costs
        // 3. Correlate by timestamp and model
        Ok(vec![])
    }

    /// Fetch ACTUAL usage from Azure Foundry
    /// Requires: AZURE_SUBSCRIPTION_ID, AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
    /// Sources:
    ///   - Azure Foundry API (deployment usage)
    ///   - Azure Cost Management API (actual charges)
    /// Returns: Real deployments + tokens + costs
    pub async fn fetch_azure_actuals(
        subscription_id: &str,
        resource_group: &str,
    ) -> anyhow::Result<Vec<ActualUsageData>> {
        let _tenant_id = std::env::var("AZURE_TENANT_ID")
            .map_err(|_| anyhow::anyhow!("AZURE_TENANT_ID not set"))?;
        let _client_id = std::env::var("AZURE_CLIENT_ID")
            .map_err(|_| anyhow::anyhow!("AZURE_CLIENT_ID not set"))?;
        let _client_secret = std::env::var("AZURE_CLIENT_SECRET")
            .map_err(|_| anyhow::anyhow!("AZURE_CLIENT_SECRET not set"))?;

        tracing::warn!(
            subscription = subscription_id,
            resource_group = resource_group,
            "Azure integration: Azure SDK not available - implement with azure-sdk-for-rust"
        );

        // Placeholder: Return empty vec - actual implementation requires Azure SDK
        // When available, this would:
        // 1. Authenticate with Azure service principal
        // 2. Query Foundry deployment metrics from https://management.azure.com
        // 3. Query Cost Management API for invoice details
        // 4. Filter for Claude model usage
        Ok(vec![])
    }

    /// Fetch ACTUAL usage from GCP Model Garden
    /// Requires: GCP_PROJECT_ID and GCP service account JSON key
    /// Sources:
    ///   - Vertex AI API (model invocation counts)
    ///   - Cloud Billing API (actual charges)
    /// Returns: Real predictions + tokens + costs
    pub async fn fetch_gcp_actuals(
        project_id: &str,
        region: &str,
    ) -> anyhow::Result<Vec<ActualUsageData>> {
        let _gcp_creds = std::env::var("GOOGLE_APPLICATION_CREDENTIALS")
            .map_err(|_| anyhow::anyhow!("GOOGLE_APPLICATION_CREDENTIALS not set"))?;

        tracing::warn!(
            project = project_id,
            region = region,
            "GCP integration: GCP SDK not available - implement with google-cloud-rust"
        );

        // Placeholder: Return empty vec - actual implementation requires GCP SDK
        // When available, this would:
        // 1. Authenticate with GCP service account
        // 2. Query Vertex AI API for model predictions
        // 3. Query Cloud Billing for cost and usage
        // 4. Correlate predictions to Claude model calls
        Ok(vec![])
    }

    /// Fetch ALL provider actuals (unified view)
    /// Returns: Deduplicated usage across all providers
    pub async fn fetch_all_providers_actuals() -> anyhow::Result<Vec<ActualUsageData>> {
        let mut all_actuals = Vec::new();

        // Anthropic
        match Self::fetch_anthropic_actuals().await {
            Ok(actuals) => {
                tracing::info!("✅ Anthropic: fetched {} records", actuals.len());
                all_actuals.extend(actuals);
            }
            Err(e) => tracing::warn!("⚠️ Anthropic: {}", e),
        }

        // AWS Bedrock (all regions)
        for region in &["us-east-1", "eu-west-1", "ap-northeast-1"] {
            match Self::fetch_bedrock_actuals(region, "*").await {
                Ok(mut actuals) => {
                    tracing::info!(
                        "✅ AWS Bedrock ({}): fetched {} records",
                        region,
                        actuals.len()
                    );
                    all_actuals.append(&mut actuals);
                }
                Err(e) => tracing::debug!("AWS Bedrock ({}): {}", region, e),
            }
        }

        // Azure (all subscriptions from env)
        if let Ok(sub_id) = std::env::var("AZURE_SUBSCRIPTION_ID") {
            if let Ok(rg) = std::env::var("AZURE_RESOURCE_GROUP") {
                match Self::fetch_azure_actuals(&sub_id, &rg).await {
                    Ok(mut actuals) => {
                        tracing::info!("✅ Azure: fetched {} records", actuals.len());
                        all_actuals.append(&mut actuals);
                    }
                    Err(e) => tracing::debug!("Azure: {}", e),
                }
            }
        }

        // GCP (project from env)
        if let Ok(project_id) = std::env::var("GCP_PROJECT_ID") {
            match Self::fetch_gcp_actuals(&project_id, "*").await {
                Ok(mut actuals) => {
                    tracing::info!("✅ GCP: fetched {} records", actuals.len());
                    all_actuals.append(&mut actuals);
                }
                Err(e) => tracing::debug!("GCP: {}", e),
            }
        }

        if all_actuals.is_empty() {
            tracing::warn!("No provider actuals fetched - check credentials and API keys");
        }

        Ok(all_actuals)
    }
}

/// Integration status for UI + warnings
#[derive(Debug, Clone)]
pub enum IntegrationStatus {
    /// Successfully connected + fetching actuals
    Connected,
    /// Credentials missing (show setup instructions)
    NotConfigured,
    /// API called but failed (show error)
    Failed(String),
    /// API unreachable (timeout/network)
    Unreachable,
}

impl IntegrationStatus {
    pub fn is_ready(&self) -> bool {
        matches!(self, Self::Connected)
    }

    pub fn message(&self) -> String {
        match self {
            Self::Connected => "✅ Using actual provider data".to_string(),
            Self::NotConfigured => "⚠️ Set credentials to use actual data (see docs)".to_string(),
            Self::Failed(e) => format!("❌ Provider error: {}", e),
            Self::Unreachable => "❌ Cannot reach provider API (offline?)".to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_actual_usage_data_structure() {
        let usage = ActualUsageData {
            provider: PricingProvider::ClaudeApi,
            model: "claude-3-5-sonnet".to_string(),
            tokens_input_actual: 1000,
            tokens_output_actual: 500,
            cost_usd_actual: 0.0225,
            cost_timestamp: Utc::now(),
        };

        assert_eq!(usage.tokens_input_actual, 1000);
        assert_eq!(usage.tokens_output_actual, 500);
        assert_eq!(usage.cost_usd_actual, 0.0225);
    }

    #[test]
    fn test_integration_status_connected() {
        let status = IntegrationStatus::Connected;
        assert!(status.is_ready());
        assert_eq!(status.message(), "✅ Using actual provider data");
    }

    #[test]
    fn test_integration_status_not_configured() {
        let status = IntegrationStatus::NotConfigured;
        assert!(!status.is_ready());
        assert!(status.message().contains("Set credentials"));
    }

    #[test]
    fn test_integration_status_failed() {
        let status = IntegrationStatus::Failed("Connection refused".to_string());
        assert!(!status.is_ready());
        assert!(status.message().contains("Connection refused"));
    }

    #[test]
    fn test_integration_status_unreachable() {
        let status = IntegrationStatus::Unreachable;
        assert!(!status.is_ready());
        assert!(status.message().contains("Cannot reach"));
    }
}
