//! Cost analysis and recommendations generation

use crate::types::Operation;
use std::collections::HashMap;

pub struct CostAnalyzer;

impl CostAnalyzer {
    pub fn new() -> Self {
        Self
    }

    /// Generate daily cost breakdown
    pub fn daily_breakdown(&self, operations: &[Operation]) -> anyhow::Result<serde_json::Value> {
        if operations.is_empty() {
            return Ok(serde_json::json!({
                "period": "daily",
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "by_operation_type": {},
                "by_file_format": {},
                "by_mcp": {},
            }));
        }

        let mut total_cost = 0.0;
        let mut total_tokens = 0u32;
        let mut by_type: HashMap<String, (u32, f64)> = HashMap::new();
        let mut by_format: HashMap<String, (u32, f64)> = HashMap::new();
        let mut by_mcp: HashMap<String, (u32, f64)> = HashMap::new();

        for op in operations {
            // This is simplified - in production, we'd retrieve CostData from storage
            let cost_est = self.estimate_cost(op);
            total_cost += cost_est;
            total_tokens += op.tokens_input + op.tokens_output;

            // By operation type
            let op_type = format!("{:?}", op.operation_type);
            let entry = by_type.entry(op_type).or_insert((0, 0.0));
            entry.0 += 1;
            entry.1 += cost_est;

            // By file format
            if let Some(ref source) = op.file_source {
                let fmt = source.description().to_string();
                let entry = by_format.entry(fmt).or_insert((0, 0.0));
                entry.0 += 1;
                entry.1 += cost_est;
            }

            // By MCP
            if let Some(ref mcp) = op.mcp_name {
                let entry = by_mcp.entry(mcp.clone()).or_insert((0, 0.0));
                entry.0 += 1;
                entry.1 += cost_est;
            }
        }

        Ok(serde_json::json!({
            "period": "daily",
            "total_cost_usd": (total_cost * 100.0).round() / 100.0,
            "total_tokens": total_tokens,
            "by_operation_type": by_type.into_iter()
                .map(|(k, (count, cost))| (k, serde_json::json!({"count": count, "cost_usd": (cost*100.0).round()/100.0})))
                .collect::<HashMap<_, _>>(),
            "by_file_format": by_format.into_iter()
                .map(|(k, (count, cost))| (k, serde_json::json!({"count": count, "cost_usd": (cost*100.0).round()/100.0})))
                .collect::<HashMap<_, _>>(),
            "by_mcp": by_mcp.into_iter()
                .map(|(k, (count, cost))| (k, serde_json::json!({"calls": count, "cost_usd": (cost*100.0).round()/100.0})))
                .collect::<HashMap<_, _>>(),
        }))
    }

    /// Generate session diagnosis with root cause and recommendations
    pub fn session_diagnosis(&self, operations: &[Operation], session_id: &str) -> anyhow::Result<serde_json::Value> {
        if operations.is_empty() {
            return Ok(serde_json::json!({
                "session_id": session_id,
                "total_cost_usd": 0.0,
                "operations": 0,
                "diagnosis": "No operations in session"
            }));
        }

        let mut total_cost = 0.0;
        let mut by_type: HashMap<String, (u32, f64)> = HashMap::new();
        let mut by_format: HashMap<String, (u32, f64)> = HashMap::new();

        for op in operations {
            let cost = self.estimate_cost(op);
            total_cost += cost;

            let op_type = format!("{:?}", op.operation_type);
            let entry = by_type.entry(op_type).or_insert((0, 0.0));
            entry.0 += 1;
            entry.1 += cost;

            if let Some(ref source) = op.file_source {
                let fmt = format!("{:?}", source);
                let entry = by_format.entry(fmt).or_insert((0, 0.0));
                entry.0 += 1;
                entry.1 += cost;
            }
        }

        // Find biggest waste
        let (biggest_type, (biggest_count, biggest_cost)) = by_type
            .iter()
            .max_by(|a, b| a.1.1.partial_cmp(&b.1.1).unwrap())
            .map(|(k, v)| (k.clone(), v.clone()))
            .unwrap_or_default();

        let recommendations = self.generate_session_recommendations(&by_type, total_cost);

        Ok(serde_json::json!({
            "session_id": session_id,
            "total_cost_usd": (total_cost * 100.0).round() / 100.0,
            "operations": operations.len(),
            "duration_seconds": (operations.last().unwrap().timestamp - operations.first().unwrap().timestamp).num_seconds(),
            "by_operation_type": by_type.into_iter()
                .map(|(k, (count, cost))| (k, serde_json::json!({"count": count, "cost_usd": (cost*100.0).round()/100.0})))
                .collect::<HashMap<_, _>>(),
            "biggest_waste": {
                "type": biggest_type,
                "cost_usd": (biggest_cost * 100.0).round() / 100.0,
                "percentage": ((biggest_cost / total_cost) * 100.0).round() as u32,
                "count": biggest_count
            },
            "recommendations": recommendations
        }))
    }

    /// Get MCP cost ranking
    pub fn mcp_ranking(&self, operations: &[Operation]) -> anyhow::Result<serde_json::Value> {
        let mut mcp_costs: HashMap<String, (u32, f64)> = HashMap::new();

        for op in operations {
            if let Some(ref mcp) = op.mcp_name {
                let cost = self.estimate_cost(op);
                let entry = mcp_costs.entry(mcp.clone()).or_insert((0, 0.0));
                entry.0 += 1;
                entry.1 += cost;
            }
        }

        let mut ranking: Vec<_> = mcp_costs.into_iter().collect();
        ranking.sort_by(|a, b| b.1.1.partial_cmp(&a.1.1).unwrap());

        let total_mcp_cost: f64 = ranking.iter().map(|(_, (_, cost))| cost).sum();

        let ranked = ranking
            .into_iter()
            .enumerate()
            .map(|(idx, (name, (calls, cost)))| {
                serde_json::json!({
                    "rank": idx + 1,
                    "name": name,
                    "calls": calls,
                    "cost_usd": (cost * 100.0).round() / 100.0,
                    "avg_cost_per_call": ((cost / calls as f64) * 100.0).round() / 100.0
                })
            })
            .collect::<Vec<_>>();

        Ok(serde_json::json!({
            "period": "daily",
            "total_mcp_cost_usd": total_mcp_cost,
            "mcp_ranking": ranked
        }))
    }

    /// Generate optimization recommendations
    pub fn generate_recommendations(&self, _operations: &[Operation]) -> anyhow::Result<serde_json::Value> {
        // Placeholder: in production, this analyzes patterns and returns actionable fixes
        Ok(serde_json::json!({
            "recommendations": [
                {
                    "rank": 1,
                    "action": "Move PDFs from URL to local disk",
                    "effort_minutes": 5,
                    "expected_savings_usd": 3.60,
                    "roi_weekly": "$42"
                }
            ]
        }))
    }

    /// Detect spending anomalies
    pub fn detect_anomalies(&self, _operations: &[Operation]) -> anyhow::Result<serde_json::Value> {
        // Placeholder: in production, this uses ML to detect unusual patterns
        Ok(serde_json::json!({
            "anomalies": []
        }))
    }

    /// Estimate cost for an operation (simplified, actual cost in storage)
    fn estimate_cost(&self, op: &Operation) -> f64 {
        // Placeholder: real implementation uses CostData from storage
        let base = (op.tokens_input as f64 * 0.000003) + (op.tokens_output as f64 * 0.000015);
        let multiplier = op.file_source.as_ref().map(|fs| fs.multiplier()).unwrap_or(1.0);
        base * multiplier
    }

    /// Generate session-specific recommendations
    fn generate_session_recommendations(&self, by_type: &HashMap<String, (u32, f64)>, _total: f64) -> serde_json::Value {
        let recommendations: Vec<_> = by_type
            .iter()
            .filter(|(_, (count, _))| count > &3)
            .take(3)
            .map(|(type_name, (count, cost))| {
                serde_json::json!({
                    "type": type_name,
                    "count": count,
                    "cost_usd": (cost * 100.0).round() / 100.0,
                    "suggestion": format!("Optimize {} operations in this session", type_name)
                })
            })
            .collect();

        serde_json::json!(recommendations)
    }
}
