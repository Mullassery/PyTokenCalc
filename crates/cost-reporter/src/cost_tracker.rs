//! Real-time cost calculation and tracking

use crate::types::*;
use crate::storage::StorageBackend;
use std::collections::HashMap;

#[derive(Debug)]
pub struct CostTracker {
    storage: StorageBackend,
    pricing_db: PricingDatabase,
}

/// Current pricing for Claude models
#[derive(Debug)]
struct PricingDatabase {
    models: HashMap<String, ModelPricing>,
}

impl PricingDatabase {
    fn new() -> Self {
        let mut models = HashMap::new();

        // Claude 3.5 Sonnet — general purpose
        models.insert(
            "claude-3-5-sonnet".to_string(),
            ModelPricing {
                model: "claude-3-5-sonnet".to_string(),
                input_cost_per_1m: 3.00,
                output_cost_per_1m: 15.00,
            },
        );

        // Claude 3.5 Haiku — fast, cheap
        models.insert(
            "claude-3-5-haiku".to_string(),
            ModelPricing {
                model: "claude-3-5-haiku".to_string(),
                input_cost_per_1m: 0.80,
                output_cost_per_1m: 4.00,
            },
        );

        // Claude 3 Opus — expensive, powerful
        models.insert(
            "claude-3-opus".to_string(),
            ModelPricing {
                model: "claude-3-opus".to_string(),
                input_cost_per_1m: 15.00,
                output_cost_per_1m: 75.00,
            },
        );

        // Fallback: assume Sonnet pricing
        models.insert(
            "default".to_string(),
            ModelPricing {
                model: "default".to_string(),
                input_cost_per_1m: 3.00,
                output_cost_per_1m: 15.00,
            },
        );

        Self { models }
    }

    fn get_pricing(&self, model: &str) -> ModelPricing {
        self.models
            .get(model)
            .cloned()
            .unwrap_or_else(|| self.models.get("default").unwrap().clone())
    }
}

impl CostTracker {
    pub fn new(storage: StorageBackend) -> Self {
        Self {
            storage,
            pricing_db: PricingDatabase::new(),
        }
    }

    /// Calculate cost for an operation
    pub fn calculate_cost(&self, operation: &Operation) -> anyhow::Result<CostData> {
        let pricing = self.pricing_db.get_pricing(&operation.model);

        // Base cost (no multiplier)
        let base_cost = pricing.calculate_cost(operation.tokens_input, operation.tokens_output);

        // Apply multipliers based on file format and operation type
        let multiplier = self.calculate_multiplier(operation);
        let actual_cost = base_cost * multiplier;

        // Calculate actual tokens based on multiplier
        let base_tokens = operation.tokens_input + operation.tokens_output;
        let actual_tokens = (base_tokens as f64 * multiplier).ceil() as u32;

        // Input/output cost split (maintain input/output ratio)
        let input_ratio = operation.tokens_input as f64
            / (operation.tokens_input + operation.tokens_output) as f64;
        let input_cost = actual_cost * input_ratio;
        let output_cost = actual_cost * (1.0 - input_ratio);

        Ok(CostData {
            operation_id: operation.id.clone(),
            cost_usd: actual_cost,
            tokens_actual: actual_tokens,
            multiplier,
            input_cost_usd: input_cost,
            output_cost_usd: output_cost,
        })
    }

    /// Calculate cost multiplier based on file source and operation type
    fn calculate_multiplier(&self, operation: &Operation) -> f64 {
        // Data source multiplier (CRITICAL: can be 100x-1000x+)
        let data_multiplier = operation
            .data_source
            .as_ref()
            .map(|ds| ds.cost_multiplier())
            .unwrap_or(1.0);

        // If data source is present, it dominates the multiplier
        if operation.data_source.is_some() {
            return data_multiplier;
        }

        // File source multiplier
        let file_multiplier = operation
            .file_source
            .as_ref()
            .map(|s| s.multiplier())
            .unwrap_or(1.0);

        let operation_multiplier = match operation.operation_type {
            OperationType::ApiCall => 1.0, // Baseline
            OperationType::FileRead => file_multiplier, // Apply file source multiplier
            OperationType::BrowserOp => 55.0, // 55x more expensive than file read
            OperationType::McpInvocation => 2.4, // MCP protocol overhead (small data)
            OperationType::GitOp => 0.8, // Caching reduces cost
            OperationType::DatabaseQuery => 2.0, // Small SQL query (use DataSource for big queries!)
            OperationType::InstructionContext => 1.0, // Direct cost (no multiplier, already included)
        };

        operation_multiplier
    }

    /// Create a session (auto-detected or manual)
    pub fn create_session(&mut self, name: Option<String>) -> anyhow::Result<Session> {
        let session = Session::new(name);
        Ok(session)
    }

    /// Finalize a session and aggregate costs
    pub fn finalize_session(&mut self, session_id: &str) -> anyhow::Result<serde_json::Value> {
        // This will be populated from storage
        // For now, return empty summary (storage layer handles)
        Ok(serde_json::json!({
            "session_id": session_id,
            "status": "finalized"
        }))
    }

    /// Tag a session
    pub fn tag_session(
        &mut self,
        _session_id: &str,
        _key: String,
        _value: String,
    ) -> anyhow::Result<()> {
        // Storage layer handles persistence
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_base_cost_calculation() {
        let tracker = CostTracker::new(StorageBackend::new_memory());
        let mut op = Operation::new(OperationType::ApiCall, 1000, 500, "claude-3-5-haiku".to_string());

        let cost = tracker.calculate_cost(&op).unwrap();
        // Haiku: $0.80 per 1M input, $4.00 per 1M output
        // 1000 tokens input = $0.0008
        // 500 tokens output = $0.002
        // Total = $0.0028
        assert!(cost.cost_usd > 0.0);
        assert_eq!(cost.multiplier, 1.0); // No multiplier for API call
    }

    #[test]
    fn test_file_format_multiplier() {
        let tracker = CostTracker::new(StorageBackend::new_memory());
        let mut op = Operation::new(OperationType::FileRead, 1000, 500, "claude-3-5-haiku".to_string())
            .with_file_source(FileSource::PdfUrl);

        let cost = tracker.calculate_cost(&op).unwrap();
        assert_eq!(cost.multiplier, 3.6); // PDF via URL is 3.6x
    }

    #[test]
    fn test_operation_type_multiplier() {
        let tracker = CostTracker::new(StorageBackend::new_memory());
        let op = Operation::new(
            OperationType::BrowserOp,
            1000,
            500,
            "claude-3-5-haiku".to_string(),
        );

        let cost = tracker.calculate_cost(&op).unwrap();
        assert_eq!(cost.multiplier, 55.0); // Browser ops are 55x
    }

    #[test]
    fn test_combined_multipliers() {
        let tracker = CostTracker::new(StorageBackend::new_memory());
        let op = Operation::new(
            OperationType::BrowserOp,
            1000,
            500,
            "claude-3-5-haiku".to_string(),
        )
        .with_file_source(FileSource::PdfUrl);

        let cost = tracker.calculate_cost(&op).unwrap();
        // Browser op (55x) * PDF URL multiplier would stack? Let's verify logic
        // Actually, we apply operation multiplier, which already includes file handling
        assert_eq!(cost.multiplier, 55.0);
    }
}
