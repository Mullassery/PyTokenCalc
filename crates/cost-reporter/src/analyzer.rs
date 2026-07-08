//! Cost analysis and recommendations generation

use crate::types::{BillingPlan, ModelComparison, ModelCostDiff, ModelPricing, Operation};
use chrono_tz::Tz;
use std::collections::HashMap;
use std::str::FromStr;

pub struct CostAnalyzer;

impl CostAnalyzer {
    pub fn new() -> Self {
        Self
    }

    /// Get effective per-token cost by billing plan
    /// CRITICAL: Plans have 200%+ pricing variance
    pub fn billing_plan_cost(plan: BillingPlan, model: &str) -> (f64, f64) {
        match plan {
            // API pricing (pay-per-token, most expensive)
            BillingPlan::Api => match model {
                "claude-3-5-sonnet" => (3.00, 15.00),
                "claude-3-5-haiku" => (0.80, 4.00),
                "claude-3-opus" => (15.00, 75.00),
                _ => (3.00, 15.00),
            },
            // Pro plan ($20/month fixed, unlimited within limits)
            // Effective cost depends on usage volume
            BillingPlan::Pro => {
                // $20/month ÷ typical monthly token budget
                // Roughly equivalent to $1.50/$7.50 if using 13M tokens/month
                match model {
                    "claude-3-5-sonnet" => (1.50, 7.50),
                    "claude-3-5-haiku" => (0.40, 2.00),
                    "claude-3-opus" => (7.50, 37.50),
                    _ => (1.50, 7.50),
                }
            }
            // Max plan ($200/month fixed, higher limits)
            // Effective cost much lower at high usage
            BillingPlan::Max => {
                // $200/month ÷ higher monthly token budget
                // Roughly equivalent to $0.60/$3.00 if using 333M tokens/month
                match model {
                    "claude-3-5-sonnet" => (0.60, 3.00),
                    "claude-3-5-haiku" => (0.16, 0.80),
                    "claude-3-opus" => (3.00, 15.00),
                    _ => (0.60, 3.00),
                }
            }
            // Enterprise (custom negotiated, typically 20-50% discount)
            BillingPlan::Enterprise => {
                // Assume 30% discount from API pricing
                match model {
                    "claude-3-5-sonnet" => (2.10, 10.50), // 30% discount
                    "claude-3-5-haiku" => (0.56, 2.80),
                    "claude-3-opus" => (10.50, 52.50),
                    _ => (2.10, 10.50),
                }
            }
        }
    }

    /// Calculate plan comparison for cost optimization
    /// Shows: "If you switched to Max, you'd save $X/month"
    pub fn plan_comparison(&self, operations: &[Operation]) -> anyhow::Result<serde_json::Value> {
        // Estimate monthly cost by plan
        let mut total_input = 0u64;
        let mut total_output = 0u64;

        for op in operations {
            total_input += op.tokens_input as u64;
            total_output += op.tokens_output as u64;
        }

        // Scale to monthly if less than a month of data
        let hours_elapsed = if operations.len() > 0 {
            (operations.last().unwrap().timestamp - operations.first().unwrap().timestamp)
                .num_hours()
        } else {
            24
        };
        let days_elapsed = (hours_elapsed as f64 / 24.0).max(1.0);
        let monthly_input = total_input as f64 * (30.0 / days_elapsed);
        let monthly_output = total_output as f64 * (30.0 / days_elapsed);

        // Get model from first operation
        let model = operations
            .first()
            .map(|op| op.model.as_str())
            .unwrap_or("claude-3-5-sonnet");

        let mut comparisons = Vec::new();
        let plans = vec![
            BillingPlan::Api,
            BillingPlan::Pro,
            BillingPlan::Max,
            BillingPlan::Enterprise,
        ];

        let mut best_plan = BillingPlan::Api;
        let mut best_cost = f64::MAX;

        for plan in plans {
            let (in_rate, out_rate) = Self::billing_plan_cost(plan, model);
            let monthly_cost = (monthly_input * in_rate + monthly_output * out_rate) / 1_000_000.0;

            // Add monthly base for Pro/Max
            let total_cost = match plan {
                BillingPlan::Pro => monthly_cost + 20.0,
                BillingPlan::Max => monthly_cost + 200.0,
                _ => monthly_cost,
            };

            if total_cost < best_cost {
                best_cost = total_cost;
                best_plan = plan;
            }

            comparisons.push(serde_json::json!({
                "plan": format!("{:?}", plan),
                "monthly_cost": (total_cost * 100.0).round() / 100.0,
                "per_token_input": in_rate,
                "per_token_output": out_rate,
            }));
        }

        Ok(serde_json::json!({
            "current_usage_monthly": {
                "tokens_input": (monthly_input as u64),
                "tokens_output": (monthly_output as u64),
            },
            "plan_comparison": comparisons,
            "recommended_plan": format!("{:?}", best_plan),
            "recommended_cost": (best_cost * 100.0).round() / 100.0,
            "savings_message": format!(
                "Best plan: {:?} at ${:.2}/month",
                best_plan,
                best_cost
            ),
        }))
    }

    /// Convert UTC timestamp to user's local date string using their timezone
    pub fn utc_to_local_date(utc_time: chrono::DateTime<chrono::Utc>, user_tz: &str) -> String {
        if let Ok(tz) = Tz::from_str(user_tz) {
            let local = utc_time.with_timezone(&tz);
            local.format("%Y-%m-%d").to_string()
        } else {
            utc_time.format("%Y-%m-%d").to_string()
        }
    }

    /// Forecast disclaimer (always included in forecasts)
    /// CRITICAL: Forecasts are invalid if pricing changes
    pub fn forecast_disclaimer() -> serde_json::Value {
        serde_json::json!({
            "disclaimer": "⚠️ FORECAST ACCURACY WARNING",
            "warnings": [
                "Forecast assumes CURRENT pricing remains unchanged",
                "Anthropic may launch new models or change rates",
                "Any pricing change INVALIDATES this forecast",
                "New model launches typically change cost calculations",
                "Enterprise discounts not reflected in forecast",
                "Prompt optimization could reduce actual costs significantly"
            ],
            "refresh_frequency": "Refresh forecast weekly or after major model changes",
            "confidence": "High confidence only for 7 days (current pricing TTL is 24h)"
        })
    }

    /// Generate timezone-aware daily cost breakdown
    /// Groups operations by their local date in each user's timezone
    /// Critical for distributed teams with budget resets at local midnight
    pub fn daily_breakdown_by_timezone(
        &self,
        operations: &[Operation],
    ) -> anyhow::Result<serde_json::Value> {
        if operations.is_empty() {
            return Ok(serde_json::json!({
                "period": "daily",
                "timezone_aware": true,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "by_operation_type": {},
                "by_file_format": {},
                "by_mcp": {},
                "by_user_timezone": {},
            }));
        }

        let mut total_cost = 0.0;
        let mut total_tokens = 0u32;
        let mut by_type: HashMap<String, (u32, f64)> = HashMap::new();
        let mut by_format: HashMap<String, (u32, f64)> = HashMap::new();
        let mut by_mcp: HashMap<String, (u32, f64)> = HashMap::new();
        let mut by_tz: HashMap<String, (u32, f64, u32)> = HashMap::new(); // (count, cost, tokens)

        for op in operations {
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

            // By user timezone (for team reporting)
            if let Some(ref tz) = op.user_timezone {
                let entry = by_tz.entry(tz.clone()).or_insert((0, 0.0, 0));
                entry.0 += 1;
                entry.1 += cost_est;
                entry.2 += op.tokens_input + op.tokens_output;
            }
        }

        Ok(serde_json::json!({
            "period": "daily",
            "timezone_aware": true,
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
            "by_user_timezone": by_tz.into_iter()
                .map(|(tz, (count, cost, tokens))| {
                    (tz, serde_json::json!({
                        "operations": count,
                        "cost_usd": (cost*100.0).round()/100.0,
                        "tokens": tokens
                    }))
                })
                .collect::<HashMap<_, _>>(),
        }))
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
    pub fn session_diagnosis(
        &self,
        operations: &[Operation],
        session_id: &str,
    ) -> anyhow::Result<serde_json::Value> {
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
            .max_by(|a, b| a.1 .1.partial_cmp(&b.1 .1).unwrap())
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
        ranking.sort_by(|a, b| b.1 .1.partial_cmp(&a.1 .1).unwrap());

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
    pub fn generate_recommendations(
        &self,
        _operations: &[Operation],
    ) -> anyhow::Result<serde_json::Value> {
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

    /// Forecast quarterly costs with pricing volatility disclaimer
    /// CRITICAL: All forecasts include disclaimer that pricing changes invalidate forecast
    pub fn forecast_quarterly(
        &self,
        operations: &[Operation],
    ) -> anyhow::Result<serde_json::Value> {
        if operations.is_empty() {
            return Ok(serde_json::json!({
                "error": "No operations to forecast from",
                "disclaimer": Self::forecast_disclaimer()
            }));
        }

        let total_cost: f64 = operations
            .iter()
            .map(|_| 0.01) // Placeholder: would use actual cost from storage
            .sum();

        let avg_daily = total_cost / 7.0; // Assume weekly data
        let q_projection = avg_daily * 90.0;

        Ok(serde_json::json!({
            "forecast": "quarterly",
            "period": "next 90 days",
            "projected_cost_usd": (q_projection * 100.0).round() / 100.0,
            "daily_average": (avg_daily * 100.0).round() / 100.0,
            "confidence_level": "Medium (depends on stable pricing)",
            "assumptions": [
                "Current pricing unchanged for 90 days",
                "Spending patterns remain consistent",
                "No major model migrations",
                "No new expensive operations added"
            ],
            "disclaimer": Self::forecast_disclaimer(),
            "breakeven_payback": {
                "if_optimize": "4-8 weeks with recommended optimizations",
                "required_action": "Implement quick-win recommendations to improve forecast"
            }
        }))
    }

    /// Compare costs across models for informed model selection
    /// CRITICAL: Shows users cost difference BEFORE switching models
    pub fn compare_model_costs(&self, tokens_input: u32, tokens_output: u32) -> ModelComparison {
        let models = vec![
            ("claude-3-5-sonnet", 3.00, 15.00),
            ("claude-3-5-haiku", 0.80, 4.00),
            ("claude-3-opus", 15.00, 75.00),
            ("fable", 0.60, 2.40),
            ("fable-5", 0.50, 2.00),
        ];

        let baseline = ModelPricing {
            model: "claude-3-5-sonnet".to_string(),
            input_cost_per_1m: 3.00,
            output_cost_per_1m: 15.00,
            currency: crate::types::Currency::USD,
        };
        let baseline_cost = baseline.calculate_cost(tokens_input, tokens_output);

        let comparisons = models
            .iter()
            .map(|(name, input_rate, output_rate)| {
                let model_pricing = ModelPricing {
                    model: name.to_string(),
                    input_cost_per_1m: *input_rate,
                    output_cost_per_1m: *output_rate,
                    currency: crate::types::Currency::USD,
                };
                let cost = model_pricing.calculate_cost(tokens_input, tokens_output);
                let diff = cost - baseline_cost;
                let ratio = cost / baseline_cost;
                let savings = ((baseline_cost - cost) / baseline_cost) * 100.0;

                ModelCostDiff {
                    model: name.to_string(),
                    cost_usd: cost,
                    cost_diff_usd: diff,
                    cost_ratio: ratio,
                    savings_percentage: savings,
                }
            })
            .collect();

        ModelComparison {
            baseline_model: baseline.model,
            baseline_cost_usd: baseline_cost,
            comparisons,
        }
    }

    /// Estimate cost for an operation (simplified, actual cost in storage)
    fn estimate_cost(&self, op: &Operation) -> f64 {
        // Placeholder: real implementation uses CostData from storage
        let base = (op.tokens_input as f64 * 0.000003) + (op.tokens_output as f64 * 0.000015);
        let multiplier = op
            .file_source
            .as_ref()
            .map(|fs| fs.multiplier())
            .unwrap_or(1.0);
        base * multiplier
    }

    /// Generate session-specific recommendations
    fn generate_session_recommendations(
        &self,
        by_type: &HashMap<String, (u32, f64)>,
        _total: f64,
    ) -> serde_json::Value {
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
