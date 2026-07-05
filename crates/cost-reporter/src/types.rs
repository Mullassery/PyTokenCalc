//! Core data types for cost tracking

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::collections::HashMap;

/// Billing plan/tier for Claude
/// CRITICAL: Pricing varies dramatically by plan
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum BillingPlan {
    /// Claude API (pay-per-token, highest per-token cost)
    Api,
    /// Claude Pro ($20/month, includes usage limits)
    Pro,
    /// Claude Max ($200/month, higher limits)
    Max,
    /// Enterprise (custom negotiated pricing, usually 20-50% discount)
    Enterprise,
}

/// Peak vs off-peak pricing
/// CRITICAL: Pricing varies by time of day (20-40% variance)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PricingTier {
    /// Off-peak hours (lower price, usually 10 PM - 6 AM local time)
    OffPeak,
    /// Standard hours (medium price, usually 6 AM - 5 PM local time)
    Standard,
    /// Peak hours (higher price, usually 5 PM - 10 PM local time, weekdays)
    Peak,
    /// Weekend (variable, some providers offer discounts)
    Weekend,
}

impl PricingTier {
    /// Determine pricing tier based on hour and day of week
    /// Takes local hour (0-23) and day of week (0=Sunday, 6=Saturday)
    pub fn from_local_time(hour: u32, weekday: u32) -> Self {
        // Weekend (Saturday=6, Sunday=0)
        if weekday == 0 || weekday == 6 {
            return PricingTier::Weekend;
        }

        // Weekday pricing tiers
        match hour {
            // Off-peak: 10 PM - 6 AM (22-5)
            22..=23 | 0..=5 => PricingTier::OffPeak,
            // Peak: 5 PM - 10 PM (17-21)
            17..=21 => PricingTier::Peak,
            // Standard: 6 AM - 5 PM (6-16)
            6..=16 => PricingTier::Standard,
            _ => PricingTier::Standard,
        }
    }

    pub fn description(&self) -> &'static str {
        match self {
            PricingTier::OffPeak => "Off-peak (10 PM - 6 AM) - Lowest price",
            PricingTier::Standard => "Standard (6 AM - 5 PM) - Regular price",
            PricingTier::Peak => "Peak (5 PM - 10 PM weekdays) - Higher price",
            PricingTier::Weekend => "Weekend - Variable pricing",
        }
    }

    /// Pricing multiplier for this tier
    /// OffPeak: 0.7x (30% discount from standard)
    /// Standard: 1.0x (baseline)
    /// Peak: 1.3x (30% premium over standard)
    /// Weekend: 0.85x (15% discount from standard)
    pub fn multiplier(&self) -> f64 {
        match self {
            PricingTier::OffPeak => 0.70,
            PricingTier::Standard => 1.00,
            PricingTier::Peak => 1.30,
            PricingTier::Weekend => 0.85,
        }
    }
}

/// Currency code (ISO 4217)
/// CRITICAL: Never convert currencies - FX risk is real
/// Report in original provider currency, not user's local currency
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Currency {
    /// US Dollar (Anthropic, AWS, GCP)
    USD,
    /// Euro (Azure Europe, some AWS regions)
    EUR,
    /// British Pound (Azure UK)
    GBP,
    /// Australian Dollar (Azure, AWS Australia)
    AUD,
    /// Canadian Dollar (AWS Canada)
    CAD,
    /// Japanese Yen (AWS, Azure Asia)
    JPY,
    /// Singapore Dollar (GCP, AWS Singapore)
    SGD,
    /// Indian Rupee (AWS India)
    INR,
    /// Chinese Yuan (GCP China)
    CNY,
}

impl Currency {
    pub fn symbol(&self) -> &'static str {
        match self {
            Currency::USD => "$",
            Currency::EUR => "€",
            Currency::GBP => "£",
            Currency::AUD => "A$",
            Currency::CAD => "C$",
            Currency::JPY => "¥",
            Currency::SGD => "S$",
            Currency::INR => "₹",
            Currency::CNY => "¥",
        }
    }

    pub fn code(&self) -> &'static str {
        match self {
            Currency::USD => "USD",
            Currency::EUR => "EUR",
            Currency::GBP => "GBP",
            Currency::AUD => "AUD",
            Currency::CAD => "CAD",
            Currency::JPY => "JPY",
            Currency::SGD => "SGD",
            Currency::INR => "INR",
            Currency::CNY => "CNY",
        }
    }

    pub fn decimal_places(&self) -> u32 {
        match self {
            // 0 decimal places
            Currency::JPY | Currency::CNY | Currency::INR => 0,
            // 2 decimal places (most currencies)
            _ => 2,
        }
    }
}

/// Data source types for MCP operations (database reads, S3 access, etc)
/// CRITICAL: These are massive token consumers - 100x-1000x more than simple file reads
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum DataSource {
    /// Database query (SQL, MongoDB, etc) - cost scales with result set size
    Database {
        /// Database type
        db_type: String, // "postgres", "mysql", "mongodb", "snowflake", etc
        /// Estimated rows returned
        row_count: u32,
        /// Approximate data size in MB
        data_size_mb: f32,
    },
    /// S3 bucket access
    S3 {
        /// Number of files listed/accessed
        file_count: u32,
        /// Total data size in MB
        data_size_mb: f32,
    },
    /// REST API call (with response payload)
    Api {
        /// API endpoint
        endpoint: String,
        /// Response size in KB
        response_size_kb: u32,
    },
    /// Data warehouse (Snowflake, BigQuery, Redshift, etc)
    DataWarehouse {
        /// Warehouse type
        warehouse_type: String,
        /// Rows returned
        row_count: u64, // Can be millions
        /// Columns selected
        column_count: u32,
        /// Approximate data size in MB
        data_size_mb: f32,
    },
}

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
    /// Markdown instruction context read (.claude/claude.md, agent.md, workflow.md, etc)
    /// CRITICAL: Can be 10x-50x more expensive than the actual operation
    InstructionContext,
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

/// Instruction context file loaded (adds to operation cost)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstructionFile {
    /// Filename (.claude/claude.md, agent.md, workflow.md, etc)
    pub filename: String,
    /// Token count of this file's content
    pub tokens: u32,
    /// Cost contribution from this file
    pub cost_usd: f64,
}

/// MCP internal overhead profiling
/// CRITICAL: SaaS MCP tools often read documentation and HTML internally
/// User thinks: "get_user MCP = 100 tokens"
/// Reality: MCP reads 5k of docs + 2k of API response HTML = 7.1k tokens (71x overhead!)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpProfile {
    /// MCP tool name
    pub mcp_name: String,
    /// What user thinks the call costs
    pub claimed_tokens: u32,
    /// What it ACTUALLY cost internally
    pub actual_tokens: u32,
    /// Breakdown of where the overhead comes from
    pub overhead_breakdown: McpOverhead,
    /// Cost multiplier vs claimed
    pub multiplier: f64,
}

/// Where MCP overhead actually comes from
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpOverhead {
    /// Reading API documentation (OpenAPI specs, README, examples)
    pub documentation_tokens: u32,
    /// API response parsing (HTML, JSON prettifying, formatting)
    pub response_parsing_tokens: u32,
    /// External resources (images in docs, CSS, JS, stylesheets)
    pub external_resources_tokens: u32,
    /// Error handling and validation logic
    pub validation_tokens: u32,
    /// Authentication/signing overhead
    pub auth_tokens: u32,
    /// Other internal processing
    pub other_tokens: u32,
}

impl McpOverhead {
    pub fn total(&self) -> u32 {
        self.documentation_tokens
            + self.response_parsing_tokens
            + self.external_resources_tokens
            + self.validation_tokens
            + self.auth_tokens
            + self.other_tokens
    }
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
    /// MCP profiling: internal overhead vs claimed cost
    /// e.g., "get_user" claims 100 tokens but reads 5k of docs internally
    pub mcp_profile: Option<McpProfile>,
    /// Data source type (database, S3, API, etc) - for MCP data operations
    pub data_source: Option<DataSource>,
    /// Timestamp (UTC)
    pub timestamp: chrono::DateTime<chrono::Utc>,
    /// User's timezone (e.g., "America/New_York", "Europe/London", "Asia/Tokyo")
    /// CRITICAL: Used for daily budget resets, session grouping, and team reporting
    pub user_timezone: Option<String>,
    /// Cloud region if using provider (e.g., "us-east-1", "eu-west-1", "asia-southeast1")
    /// CRITICAL: Cloud pricing varies by region (10-30% variance)
    pub cloud_region: Option<String>,
    /// Billing plan when operation occurred (Pro/Max/Enterprise/Api)
    /// CRITICAL: Pricing varies 200%+ between plans
    pub billing_plan: Option<BillingPlan>,
    /// Pricing tier based on time of day (peak/off-peak/standard/weekend)
    /// CRITICAL: Pricing varies 20-40% by hour
    /// Off-peak (10 PM-6 AM): 0.7x (30% discount)
    /// Standard (6 AM-5 PM): 1.0x (baseline)
    /// Peak (5 PM-10 PM weekdays): 1.3x (30% premium)
    /// Weekend: 0.85x (15% discount)
    pub pricing_tier: Option<PricingTier>,
    /// User who triggered this (if applicable)
    pub user: Option<String>,
    /// Tags for filtering
    pub tags: HashMap<String, String>,
    /// Instruction context files read for this operation
    /// CRITICAL COST MULTIPLIER: claude.md, agent.md, workflow.md, etc.
    pub instruction_files: Vec<InstructionFile>,
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
            user_timezone: None,
            cloud_region: None,
            billing_plan: None,
            pricing_tier: None,
            user: None,
            tags: HashMap::new(),
            instruction_files: Vec::new(),
            data_source: None,
            mcp_profile: None,
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

    pub fn with_instruction_files(mut self, files: Vec<InstructionFile>) -> Self {
        self.instruction_files = files;
        self
    }

    pub fn with_cloud_region(mut self, region: String) -> Self {
        self.cloud_region = Some(region);
        self
    }

    pub fn with_billing_plan(mut self, plan: BillingPlan) -> Self {
        self.billing_plan = Some(plan);
        self
    }

    pub fn with_pricing_tier(mut self, tier: PricingTier) -> Self {
        self.pricing_tier = Some(tier);
        self
    }

    /// Total tokens including instruction context
    pub fn total_tokens_with_context(&self) -> u32 {
        let instruction_tokens: u32 = self.instruction_files.iter().map(|f| f.tokens).sum();
        self.tokens_input + self.tokens_output + instruction_tokens
    }

    /// Estimate data-driven token explosion for this operation
    pub fn estimate_data_tokens(&self) -> u32 {
        match &self.data_source {
            Some(source) => source.estimate_tokens(),
            None => 0,
        }
    }

    pub fn with_data_source(mut self, source: DataSource) -> Self {
        self.data_source = Some(source);
        self
    }

    pub fn with_mcp_profile(mut self, profile: McpProfile) -> Self {
        self.mcp_profile = Some(profile);
        self
    }
}

impl DataSource {
    /// Estimate token count based on data volume
    /// CRITICAL: These are not linear - 1M rows = exponential token growth
    pub fn estimate_tokens(&self) -> u32 {
        match self {
            DataSource::Database { row_count, data_size_mb, .. } => {
                // Database result sets:
                // - 100 rows, 1MB: ~500 tokens
                // - 10k rows, 100MB: ~50,000 tokens
                // - 1M rows, 10GB: ~5,000,000 tokens
                // Rule: ~0.5 tokens per byte + 500 base
                let data_tokens = (data_size_mb * 1024.0 * 1024.0 * 0.5) as u32;
                let row_tokens = (*row_count as f32 * 5.0) as u32; // Each row adds overhead
                data_tokens + row_tokens + 500
            }
            DataSource::S3 { file_count, data_size_mb } => {
                // S3 bucket listing is expensive
                // - 10 files, 100MB: ~50k tokens (file listing overhead)
                // - 1000 files, 10GB: ~5M tokens
                let listing_tokens = (*file_count as f32 * 100.0) as u32; // Each file in listing
                let data_tokens = (data_size_mb * 1024.0 * 1024.0 * 0.5) as u32;
                listing_tokens + data_tokens + 1000
            }
            DataSource::Api { response_size_kb, .. } => {
                // API responses (usually JSON, less dense than raw data)
                // ~1 token per 4 bytes
                (*response_size_kb as f32 * 1024.0 * 0.25) as u32
            }
            DataSource::DataWarehouse { row_count, column_count, data_size_mb, .. } => {
                // Data warehouse queries are MASSIVE
                // - Snowflake 100k rows × 50 columns: ~250k tokens
                // - BigQuery 1M rows × 100 columns: ~2.5M tokens
                let data_tokens = (data_size_mb * 1024.0 * 1024.0 * 0.5) as u32;
                let row_tokens = (*row_count as f32 * 5.0) as u32;
                let column_tokens = (*column_count as f32 * 50.0) as u32; // Column metadata
                data_tokens + row_tokens + column_tokens + 2000
            }
        }
    }

    /// Cost multiplier for data source (compared to simple API call)
    /// A simple 100-token API call = baseline (1.0x)
    /// A 1M row database read = 50,000x+
    pub fn cost_multiplier(&self) -> f64 {
        let estimated_tokens = self.estimate_tokens();
        let baseline_tokens = 100.0;
        (estimated_tokens as f64 / baseline_tokens).max(1.0)
    }

    pub fn description(&self) -> String {
        match self {
            DataSource::Database { db_type, row_count, data_size_mb } => {
                format!("{} query: {} rows, {:.1}MB", db_type, row_count, data_size_mb)
            }
            DataSource::S3 { file_count, data_size_mb } => {
                format!("S3 access: {} files, {:.1}MB", file_count, data_size_mb)
            }
            DataSource::Api { endpoint, response_size_kb } => {
                format!("API {}: {}KB response", endpoint, response_size_kb)
            }
            DataSource::DataWarehouse { warehouse_type, row_count, column_count, data_size_mb } => {
                format!(
                    "{} query: {} rows × {} cols, {:.1}MB",
                    warehouse_type, row_count, column_count, data_size_mb
                )
            }
        }
    }
}

/// Calculated cost data for an operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostData {
    /// Operation ID
    pub operation_id: String,
    /// Total cost in original provider currency (NOT converted)
    pub cost: f64,
    /// Currency of cost (USD, EUR, GBP, etc.)
    /// CRITICAL: Never convert - always report in original currency
    pub currency: Currency,
    /// Actual tokens (after multiplier)
    pub tokens_actual: u32,
    /// Cost multiplier applied (file format or operation type)
    pub multiplier: f64,
    /// Breakdown: input cost + output cost (in original currency)
    pub input_cost: f64,
    pub output_cost: f64,
    /// When pricing was valid (critical for historical accuracy)
    pub pricing_timestamp: chrono::DateTime<chrono::Utc>,
    /// Source of pricing: "api", "cache", "fallback"
    /// CRITICAL: "fallback" means cost may be INACCURATE (pricing not fetched)
    pub pricing_source: String,
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
    /// Currency of this pricing (USD, EUR, GBP, etc.)
    /// CRITICAL: Never convert - report in original currency
    pub currency: Currency,
}

/// Pricing metadata for transparency
/// CRITICAL: Shows when pricing changed and if it went up/down
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PricingMetadata {
    /// When this pricing was fetched/cached
    pub fetch_timestamp: chrono::DateTime<chrono::Utc>,
    /// When pricing last changed (None if unknown)
    pub last_price_change: Option<chrono::DateTime<chrono::Utc>>,
    /// Source: "api", "cache", "fallback"
    pub source: String,
    /// Days since pricing fetched (for cache age)
    pub cache_age_days: u32,
}

impl ModelPricing {
    pub fn calculate_cost(&self, tokens_input: u32, tokens_output: u32) -> f64 {
        let input = (tokens_input as f64 / 1_000_000.0) * self.input_cost_per_1m;
        let output = (tokens_output as f64 / 1_000_000.0) * self.output_cost_per_1m;
        input + output
    }

    pub fn cost_ratio(&self, other: &ModelPricing, tokens_input: u32, tokens_output: u32) -> f64 {
        let my_cost = self.calculate_cost(tokens_input, tokens_output);
        let other_cost = other.calculate_cost(tokens_input, tokens_output);
        if other_cost > 0.0 {
            my_cost / other_cost
        } else {
            1.0
        }
    }
}

/// Model comparison for cost-aware model selection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelComparison {
    pub baseline_model: String,
    pub baseline_cost_usd: f64,
    pub comparisons: Vec<ModelCostDiff>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelCostDiff {
    pub model: String,
    pub cost_usd: f64,
    pub cost_diff_usd: f64,
    pub cost_ratio: f64,  // 1.0 = same cost, 2.0 = twice as expensive, 0.5 = half price
    pub savings_percentage: f64,  // Negative means more expensive
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
