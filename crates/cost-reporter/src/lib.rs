//! CostReporter Core — Real-time LLM cost tracking and analysis
//!
//! Rust core for handling:
//! - Silent operation tracking (API calls, file reads, MCP invocations)
//! - Session-based cost grouping (root cause analysis)
//! - File format cost multipliers (36x variance: CSV vs PDF URL)
//! - Operation type isolation (55x variance: browser vs file)
//! - MCP profiling (rank skills by cost)
//! - SQLite persistence (local, private)

pub mod types;
pub mod cost_tracker;
pub mod session;
pub mod file_format_profiler;
pub mod operation_profiler;
pub mod mcp_profiler;
pub mod storage;
pub mod analyzer;
pub mod pricing_service;

pub use types::{Operation, OperationType, FileSource, Session, CostData};
pub use cost_tracker::CostTracker;
pub use session::SessionManager;
pub use storage::StorageBackend;
pub use analyzer::CostAnalyzer;
pub use pricing_service::PricingService;

#[derive(Debug, Clone)]
pub struct CostReporter {
    tracker: std::sync::Arc<tokio::sync::Mutex<CostTracker>>,
    storage: StorageBackend,
}

impl CostReporter {
    pub async fn new(db_path: &str) -> anyhow::Result<Self> {
        let storage = StorageBackend::new(db_path).await?;
        let tracker = CostTracker::new(storage.clone());

        Ok(Self {
            tracker: std::sync::Arc::new(tokio::sync::Mutex::new(tracker)),
            storage,
        })
    }

    /// Track a single operation (called silently in background)
    pub async fn track_operation(&self, operation: Operation) -> anyhow::Result<CostData> {
        let mut tracker = self.tracker.lock().await;
        let cost_data = tracker.calculate_cost(&operation)?;
        self.storage.save_operation(&operation, &cost_data).await?;
        Ok(cost_data)
    }

    /// Start a new session (manual or auto-detected)
    pub async fn start_session(&self, session_name: Option<String>) -> anyhow::Result<String> {
        let mut tracker = self.tracker.lock().await;
        let session = tracker.create_session(session_name)?;
        self.storage.save_session(&session).await?;
        Ok(session.id.clone())
    }

    /// End current session and aggregate costs
    pub async fn end_session(&self, session_id: &str) -> anyhow::Result<serde_json::Value> {
        let mut tracker = self.tracker.lock().await;
        let session_summary = tracker.finalize_session(session_id)?;
        self.storage.update_session_summary(session_id, &session_summary).await?;
        Ok(session_summary)
    }

    /// Tag current session
    pub async fn tag_session(&self, session_id: &str, key: String, value: String) -> anyhow::Result<()> {
        let mut tracker = self.tracker.lock().await;
        tracker.tag_session(session_id, key, value)?;
        Ok(())
    }

    /// Get today's cost breakdown (by operation type, file format, MCP)
    pub async fn analyze_daily(&self) -> anyhow::Result<serde_json::Value> {
        let operations = self.storage.get_operations_since_hours(24).await?;
        let analyzer = CostAnalyzer::new();
        Ok(analyzer.daily_breakdown(&operations)?)
    }

    /// Get session cost breakdown with diagnosis
    pub async fn analyze_session(&self, session_id: &str) -> anyhow::Result<serde_json::Value> {
        let operations = self.storage.get_session_operations(session_id).await?;
        let analyzer = CostAnalyzer::new();
        Ok(analyzer.session_diagnosis(&operations, session_id)?)
    }

    /// Get MCP cost ranking
    pub async fn analyze_mcp_costs(&self) -> anyhow::Result<serde_json::Value> {
        let operations = self.storage.get_operations_since_hours(24).await?;
        let analyzer = CostAnalyzer::new();
        Ok(analyzer.mcp_ranking(&operations)?)
    }

    /// Get optimization recommendations
    pub async fn get_recommendations(&self) -> anyhow::Result<serde_json::Value> {
        let operations = self.storage.get_operations_since_hours(24).await?;
        let analyzer = CostAnalyzer::new();
        Ok(analyzer.generate_recommendations(&operations)?)
    }

    /// Detect cost anomalies
    pub async fn detect_anomalies(&self) -> anyhow::Result<serde_json::Value> {
        let operations = self.storage.get_operations_since_hours(168).await?; // 1 week
        let analyzer = CostAnalyzer::new();
        Ok(analyzer.detect_anomalies(&operations)?)
    }

    /// Compare model costs for informed model selection
    /// Returns cost differences across all available models
    /// CRITICAL: Users see cost impact BEFORE switching models
    pub async fn compare_models(&self, tokens_input: u32, tokens_output: u32) -> anyhow::Result<serde_json::Value> {
        let analyzer = CostAnalyzer::new();
        let comparison = analyzer.compare_model_costs(tokens_input, tokens_output);
        Ok(serde_json::to_value(comparison)?)
    }
}
