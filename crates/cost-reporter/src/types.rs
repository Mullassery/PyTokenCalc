//! Core data types for cost tracking

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::collections::HashMap;

/// Operation type (what costs money)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum OperationType {
    /// LLM API call (base cost, minimal overhead)
    ApiCall,
    /// File read (1x-4.2x multiplier depending on source)
    FileRead,
    /// Browser scrape/render (55x more than file read)
    BrowserOp,
    /// MCP invocation (1.5x-3x multiplier)
    McpInvocation,
    /// Git operation (0.8x overhead)
    GitOp,
    /// Database query (1.2x-5x multiplier)
    DatabaseQuery,
}

/// File source determines cost multiplier (36x variance: CSV vs PDF URL)
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum FileSource {
    /// CSV pasted (1.0x baseline: 300 tokens for 2MB)
    CsvPasted,
    /// CSV from local disk (1.0x)
    CsvLocal,
    /// PDF from local disk (1.2x: parsing overhead)
    PdfLocal,
    /// PDF via URL (3.6x: download + parse)
    PdfUrl,
    /// Image via URL (4.2x: high resolution)
    ImageUrl,
    /// Stream/socket (2.8x: protocol overhead)
    Stream,
    /// MCP invocation (2.4x: protocol overhead)
    McpStream,
    /// Unknown source (1.0x baseline)
    Unknown,
}

impl FileSource {
    /// Cost multiplier for this file source (how many times more expensive than baseline)
    pub fn multiplier(&self) -> f64 {
        match self {
            FileSource::CsvPasted => 1.0,
            FileSource::CsvLocal => 1.0,
            FileSource::PdfLocal => 1.2,
            FileSource::PdfUrl => 3.6,
            FileSource::ImageUrl => 4.2,
            FileSource::Stream => 2.8,
            FileSource::McpStream => 2.4,
            FileSource::Unknown => 1.0,
        }
    }

    pub fn description(&self) -> &'static str {
        match self {
            FileSource::CsvPasted => "CSV pasted",
            FileSource::CsvLocal => "CSV local disk",
            FileSource::PdfLocal => "PDF local disk",
            FileSource::PdfUrl => "PDF via URL (3.6x more expensive)",
            FileSource::ImageUrl => "Image via URL (4.2x more expensive)",
            FileSource::Stream => "Stream/socket",
            FileSource::McpStream => "MCP stream",
            FileSource::Unknown => "Unknown source",
        }
    }
}

/// A single operation that cost money
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Operation {
    /// Unique operation ID
    pub id: String,
    /// Session this operation belongs to
    pub session_id: Option<String>,
    /// Type of operation (what it was)
    pub operation_type: OperationType,
    /// Input tokens
    pub tokens_input: u32,
    /// Output tokens
    pub tokens_output: u32,
    /// Model used
    pub model: String,
    /// File source (if applicable)
    pub file_source: Option<FileSource>,
    /// MCP name (if MCP invocation)
    pub mcp_name: Option<String>,
    /// Timestamp (UTC)
    pub timestamp: chrono::DateTime<chrono::Utc>,
    /// User who triggered this (if applicable)
    pub user: Option<String>,
    /// Tags for filtering
    pub tags: HashMap<String, String>,
}

impl Operation {
    pub fn new(
        operation_type: OperationType,
        tokens_input: u32,
        tokens_output: u32,
        model: String,
    ) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            session_id: None,
            operation_type,
            tokens_input,
            tokens_output,
            model,
            file_source: None,
            mcp_name: None,
            timestamp: chrono::Utc::now(),
            user: None,
            tags: HashMap::new(),
        }
    }

    pub fn with_session(mut self, session_id: String) -> Self {
        self.session_id = Some(session_id);
        self
    }

    pub fn with_file_source(mut self, source: FileSource) -> Self {
        self.file_source = Some(source);
        self
    }

    pub fn with_mcp(mut self, mcp_name: String) -> Self {
        self.mcp_name = Some(mcp_name);
        self
    }

    pub fn with_user(mut self, user: String) -> Self {
        self.user = Some(user);
        self
    }

    pub fn with_tag(mut self, key: String, value: String) -> Self {
        self.tags.insert(key, value);
        self
    }
}

/// Calculated cost data for an operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostData {
    /// Operation ID
    pub operation_id: String,
    /// Total cost in USD
    pub cost_usd: f64,
    /// Actual tokens (after multiplier)
    pub tokens_actual: u32,
    /// Cost multiplier applied (file format or operation type)
    pub multiplier: f64,
    /// Breakdown: input cost + output cost
    pub input_cost_usd: f64,
    pub output_cost_usd: f64,
}

/// A session groups related operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    /// Unique session ID
    pub id: String,
    /// Human-readable name (e.g., "debug-auth", "feature/search")
    pub name: Option<String>,
    /// When session started
    pub started_at: chrono::DateTime<chrono::Utc>,
    /// When session ended (None if ongoing)
    pub ended_at: Option<chrono::DateTime<chrono::Utc>>,
    /// Tags (e.g., {"branch": "main", "feature": "auth"})
    pub tags: HashMap<String, String>,
    /// All operations in this session
    pub operation_ids: Vec<String>,
    /// Total cost (calculated at end)
    pub total_cost_usd: Option<f64>,
}

impl Session {
    pub fn new(name: Option<String>) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            started_at: chrono::Utc::now(),
            ended_at: None,
            tags: HashMap::new(),
            operation_ids: Vec::new(),
            total_cost_usd: None,
        }
    }

    pub fn with_tag(mut self, key: String, value: String) -> Self {
        self.tags.insert(key, value);
        self
    }

    pub fn add_operation(&mut self, operation_id: String) {
        if !self.operation_ids.contains(&operation_id) {
            self.operation_ids.push(operation_id);
        }
    }

    pub fn end(&mut self) -> chrono::Duration {
        self.ended_at = Some(chrono::Utc::now());
        self.ended_at.unwrap() - self.started_at
    }

    pub fn duration_seconds(&self) -> u64 {
        let end = self.ended_at.unwrap_or_else(chrono::Utc::now);
        (end - self.started_at).num_seconds() as u64
    }
}

/// Model pricing (per 1M tokens)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelPricing {
    pub model: String,
    /// Input cost per 1M tokens
    pub input_cost_per_1m: f64,
    /// Output cost per 1M tokens (usually higher)
    pub output_cost_per_1m: f64,
}

impl ModelPricing {
    pub fn calculate_cost(&self, tokens_input: u32, tokens_output: u32) -> f64 {
        let input = (tokens_input as f64 / 1_000_000.0) * self.input_cost_per_1m;
        let output = (tokens_output as f64 / 1_000_000.0) * self.output_cost_per_1m;
        input + output
    }
}

/// Aggregated cost breakdown
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostBreakdown {
    pub by_operation_type: HashMap<String, CostSummary>,
    pub by_file_format: HashMap<String, CostSummary>,
    pub by_mcp: HashMap<String, McpCostSummary>,
    pub by_user: HashMap<String, CostSummary>,
    pub total_cost_usd: f64,
    pub total_tokens: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostSummary {
    pub count: u32,
    pub cost_usd: f64,
    pub tokens: u32,
    pub percentage: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpCostSummary {
    pub calls: u32,
    pub cost_usd: f64,
    pub tokens: u32,
    pub avg_cost_per_call: f64,
}
