//! CostReporter Python FFI (PyO3)
//! Exposes Rust core to Python as native extension module

use pyo3::prelude::*;
use cost_reporter::{CostReporter, Operation, OperationType, FileSource};
use std::sync::Arc;
use tokio::sync::Mutex;

/// Python wrapper for CostReporter
#[pyclass]
pub struct PyCostReporter {
    reporter: Arc<Mutex<CostReporter>>,
}

#[pymethods]
impl PyCostReporter {
    /// Initialize CostReporter with SQLite database
    #[new]
    pub fn new(db_path: &str) -> PyResult<Self> {
        let rt = tokio::runtime::Handle::current();
        let reporter = rt.block_on(async {
            CostReporter::new(db_path).await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(Self {
            reporter: Arc::new(Mutex::new(reporter)),
        })
    }

    /// Track an operation (called silently in background)
    pub fn track_operation(
        &self,
        operation_type: &str,
        tokens_input: u32,
        tokens_output: u32,
        model: &str,
        session_id: Option<&str>,
        user: Option<&str>,
        file_source: Option<&str>,
        mcp_name: Option<&str>,
        user_timezone: Option<&str>,
        cloud_region: Option<&str>,
        billing_plan: Option<&str>,
        pricing_tier: Option<&str>,
    ) -> PyResult<String> {
        let op_type = match operation_type {
            "api_call" => OperationType::ApiCall,
            "file_read" => OperationType::FileRead,
            "browser_op" => OperationType::BrowserOp,
            "mcp_invocation" => OperationType::McpInvocation,
            "git_op" => OperationType::GitOp,
            "database_query" => OperationType::DatabaseQuery,
            "instruction_context" => OperationType::InstructionContext,
            _ => OperationType::ApiCall,
        };

        let file_src = file_source.and_then(|src| match src {
            "csv_pasted" => Some(FileSource::CsvPasted),
            "csv_local" => Some(FileSource::CsvLocal),
            "pdf_local" => Some(FileSource::PdfLocal),
            "pdf_url" => Some(FileSource::PdfUrl),
            "image_url" => Some(FileSource::ImageUrl),
            "stream" => Some(FileSource::Stream),
            "mcp_stream" => Some(FileSource::McpStream),
            _ => None,
        });

        let mut op = Operation::new(op_type, tokens_input, tokens_output, model.to_string());
        if let Some(sid) = session_id {
            op = op.with_session(sid.to_string());
        }
        if let Some(u) = user {
            op = op.with_user(u.to_string());
        }
        if let Some(src) = file_src {
            op = op.with_file_source(src);
        }
        if let Some(mcp) = mcp_name {
            op = op.with_mcp(mcp.to_string());
        }
        if let Some(tz) = user_timezone {
            op.user_timezone = Some(tz.to_string());
        }
        if let Some(region) = cloud_region {
            op.cloud_region = Some(region.to_string());
        }
        if let Some(plan) = billing_plan {
            op.billing_plan = match plan {
                "api" => Some(cost_reporter::BillingPlan::Api),
                "pro" => Some(cost_reporter::BillingPlan::Pro),
                "max" => Some(cost_reporter::BillingPlan::Max),
                "enterprise" => Some(cost_reporter::BillingPlan::Enterprise),
                _ => None,
            };
        }
        if let Some(tier) = pricing_tier {
            op.pricing_tier = match tier {
                "peak" => Some(cost_reporter::PricingTier::Peak),
                "off_peak" | "offpeak" => Some(cost_reporter::PricingTier::OffPeak),
                "standard" => Some(cost_reporter::PricingTier::Standard),
                "weekend" => Some(cost_reporter::PricingTier::Weekend),
                _ => None,
            };
        }

        let rt = tokio::runtime::Handle::current();
        let cost_data = rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.track_operation(op).await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let result = serde_json::json!({
            "operation_id": cost_data.operation_id,
            "cost_usd": cost_data.cost_usd,
            "tokens_actual": cost_data.tokens_actual,
            "multiplier": cost_data.multiplier,
            "input_cost_usd": cost_data.input_cost_usd,
            "output_cost_usd": cost_data.output_cost_usd,
        });
        Ok(serde_json::to_string(&result).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?)
    }

    /// Start a session
    pub fn start_session(&self, session_name: Option<&str>) -> PyResult<String> {
        let rt = tokio::runtime::Handle::current();
        rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.start_session(session_name.map(|s| s.to_string())).await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    /// End a session and get summary
    pub fn end_session(&self, session_id: &str) -> PyResult<String> {
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.end_session(session_id).await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(serde_json::to_string(&result).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?)
    }

    /// Tag a session
    pub fn tag_session(&self, session_id: &str, key: &str, value: &str) -> PyResult<()> {
        let rt = tokio::runtime::Handle::current();
        rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.tag_session(session_id, key.to_string(), value.to_string()).await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    /// Analyze today's costs
    pub fn analyze_daily(&self) -> PyResult<String> {
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.analyze_daily().await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(serde_json::to_string(&result).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?)
    }

    /// Analyze a session's costs
    pub fn analyze_session(&self, session_id: &str) -> PyResult<String> {
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.analyze_session(session_id).await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(serde_json::to_string(&result).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?)
    }

    /// Analyze MCP costs
    pub fn analyze_mcp_costs(&self) -> PyResult<String> {
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.analyze_mcp_costs().await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(serde_json::to_string(&result).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?)
    }

    /// Get optimization recommendations
    pub fn get_recommendations(&self) -> PyResult<String> {
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.get_recommendations().await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(serde_json::to_string(&result).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?)
    }

    /// Detect spending anomalies
    pub fn detect_anomalies(&self) -> PyResult<String> {
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.detect_anomalies().await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(serde_json::to_string(&result).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?)
    }

    /// Compare model costs for informed model selection
    pub fn compare_models(&self, tokens_input: u32, tokens_output: u32) -> PyResult<String> {
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.compare_models(tokens_input, tokens_output).await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(serde_json::to_string(&result).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?)
    }

    /// Forecast quarterly spending with pricing disclaimer
    pub fn forecast_quarterly(&self) -> PyResult<String> {
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.forecast_quarterly().await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(serde_json::to_string(&result).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?)
    }

    /// Compare billing plans (Pro vs Max vs Enterprise vs API)
    pub fn compare_billing_plans(&self) -> PyResult<String> {
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let reporter = self.reporter.lock().await;
            reporter.compare_billing_plans().await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(serde_json::to_string(&result).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?)
    }
}

/// Initialize Python module
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyCostReporter>()?;
    Ok(())
}
