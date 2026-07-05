//! CostReporter Python bindings using PyO3
//!
//! Exposes Rust core to Python as a native extension module

use pyo3::prelude::*;
use cost_reporter::CostReporter;
use pyo3::types::{PyDict, PyString};

#[pyclass]
pub struct Reporter {
    core: tokio::runtime::Runtime,
    reporter: Option<CostReporter>,
}

#[pymethods]
impl Reporter {
    #[new]
    pub fn new(db_path: &str) -> PyResult<Self> {
        let rt = tokio::runtime::Runtime::new()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(Reporter {
            core: rt,
            reporter: None,
        })
    }

    pub fn init(&mut self, db_path: &str) -> PyResult<()> {
        let reporter = self.core.block_on(async {
            CostReporter::new(db_path).await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        self.reporter = Some(reporter);
        Ok(())
    }

    pub fn save_memory(&mut self, context: &PyDict) -> PyResult<bool> {
        let context_json = serde_json::to_value(context)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        if let Some(reporter) = &mut self.reporter {
            self.core.block_on(async {
                reporter.save_memory(context_json).await
            }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
            Ok(true)
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Reporter not initialized"))
        }
    }

    pub fn observe(&self) -> PyResult<PyObject> {
        if let Some(reporter) = &self.reporter {
            let result = self.core.block_on(async {
                reporter.observe().await
            }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

            Python::with_gil(|py| {
                Ok(PyString::new(py, &result.to_string()).into())
            })
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Reporter not initialized"))
        }
    }

    pub fn audit(&self, filter: Option<&PyDict>) -> PyResult<PyObject> {
        if let Some(reporter) = &self.reporter {
            let filter_json = if let Some(f) = filter {
                Some(serde_json::to_value(f)
                    .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?)
            } else {
                None
            };

            let result = self.core.block_on(async {
                reporter.audit(filter_json).await
            }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

            Python::with_gil(|py| {
                Ok(PyString::new(py, &serde_json::to_string(&result)?).into())
            })
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Reporter not initialized"))
        }
    }
}

#[pymodule]
fn _core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Reporter>()?;
    Ok(())
}
