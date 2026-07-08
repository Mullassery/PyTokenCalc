//! MCP/Skill cost profiling
//! Tracks internal overhead: what SaaS MCPs actually cost vs claimed cost
//!
//! CRITICAL INSIGHT:
//! User thinks: "get_user MCP = 100 tokens"
//! Reality: MCP reads 5k docs + 2k HTML response = 7.1k tokens (71x overhead!)

use crate::types::{McpOverhead, McpProfile, Operation};
use std::collections::HashMap;

pub struct McpProfiler {
    profiles: HashMap<String, McpCallMetrics>,
}

#[derive(Debug, Clone)]
pub struct McpCallMetrics {
    /// MCP tool name
    pub name: String,
    /// Total calls made
    pub call_count: u32,
    /// Average claimed tokens per call
    pub avg_claimed_tokens: f32,
    /// Average actual tokens per call
    pub avg_actual_tokens: f32,
    /// Overhead multiplier (actual / claimed)
    pub overhead_multiplier: f32,
    /// Total overhead tokens (sum of all overhead)
    pub total_overhead_tokens: u32,
    /// Cost added by overhead
    pub overhead_cost_usd: f64,
}

impl McpProfiler {
    pub fn new() -> Self {
        Self {
            profiles: HashMap::new(),
        }
    }

    /// Profile an MCP call - measure actual vs claimed tokens
    pub fn profile_call(&mut self, operation: &Operation) {
        if let Some(profile) = &operation.mcp_profile {
            let metrics = self
                .profiles
                .entry(profile.mcp_name.clone())
                .or_insert_with(|| McpCallMetrics {
                    name: profile.mcp_name.clone(),
                    call_count: 0,
                    avg_claimed_tokens: 0.0,
                    avg_actual_tokens: 0.0,
                    overhead_multiplier: 0.0,
                    total_overhead_tokens: 0,
                    overhead_cost_usd: 0.0,
                });

            // Update metrics
            metrics.call_count += 1;
            metrics.total_overhead_tokens += profile.overhead_breakdown.total();

            // Recalculate averages
            let claimed_avg = (metrics.avg_claimed_tokens * (metrics.call_count - 1) as f32
                + profile.claimed_tokens as f32)
                / metrics.call_count as f32;
            let actual_avg = (metrics.avg_actual_tokens * (metrics.call_count - 1) as f32
                + profile.actual_tokens as f32)
                / metrics.call_count as f32;

            metrics.avg_claimed_tokens = claimed_avg;
            metrics.avg_actual_tokens = actual_avg;
            metrics.overhead_multiplier = actual_avg / claimed_avg.max(1.0);
        }
    }

    /// Get top MCPs by overhead
    pub fn top_overhead_mcps(&self, limit: usize) -> Vec<McpCallMetrics> {
        let mut sorted: Vec<_> = self.profiles.values().cloned().collect();
        sorted.sort_by(|a, b| b.total_overhead_tokens.cmp(&a.total_overhead_tokens));
        sorted.into_iter().take(limit).collect()
    }

    /// Get MCPs with highest overhead multiplier
    pub fn most_inefficient_mcps(&self, limit: usize) -> Vec<McpCallMetrics> {
        let mut sorted: Vec<_> = self.profiles.values().cloned().collect();
        sorted.sort_by(|a, b| {
            b.overhead_multiplier
                .partial_cmp(&a.overhead_multiplier)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        sorted.into_iter().take(limit).collect()
    }

    /// Generate report of MCP inefficiencies
    pub fn generate_report(&self) -> serde_json::Value {
        let top_overhead = self.top_overhead_mcps(5);
        let most_inefficient = self.most_inefficient_mcps(5);

        serde_json::json!({
            "mcp_profiling": {
                "total_mcps_profiled": self.profiles.len(),
                "top_by_overhead_tokens": top_overhead.iter().map(|m| {
                    serde_json::json!({
                        "name": m.name,
                        "calls": m.call_count,
                        "avg_claimed": (m.avg_claimed_tokens * 100.0).round() / 100.0,
                        "avg_actual": (m.avg_actual_tokens * 100.0).round() / 100.0,
                        "overhead_multiplier": (m.overhead_multiplier * 100.0).round() / 100.0,
                        "total_overhead_tokens": m.total_overhead_tokens,
                        "recommendation": if m.overhead_multiplier > 10.0 {
                            "CRITICAL: This MCP is extremely inefficient. Consider caching or replacing.".to_string()
                        } else if m.overhead_multiplier > 5.0 {
                            "WARNING: High overhead. Look for optimization opportunities.".to_string()
                        } else {
                            "OK".to_string()
                        }
                    })
                }).collect::<Vec<_>>(),
                "most_inefficient": most_inefficient.iter().map(|m| {
                    serde_json::json!({
                        "name": m.name,
                        "overhead_multiplier": (m.overhead_multiplier * 100.0).round() / 100.0,
                        "meaning": format!("{}x more expensive than claimed", (m.overhead_multiplier * 100.0).round() / 100.0),
                    })
                }).collect::<Vec<_>>(),
            }
        })
    }
}
