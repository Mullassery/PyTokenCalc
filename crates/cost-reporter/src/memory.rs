//! Persistent project memory management
//!
//! Stores and retrieves project context across sessions

use serde_json::Value;
use std::sync::Arc;
use crate::storage::StorageBackend;

#[derive(Clone)]
pub struct MemoryManager {
    storage: Arc<StorageBackend>,
}

impl MemoryManager {
    pub fn new(storage: Arc<StorageBackend>) -> Self {
        Self { storage }
    }

    pub async fn save(&mut self, context: Value) -> anyhow::Result<()> {
        // TODO: Save context to database
        // - Serialize context to JSON
        // - Store with timestamp
        // - Summarize to avoid token waste
        Ok(())
    }

    pub async fn retrieve(&self) -> anyhow::Result<Value> {
        // TODO: Retrieve latest context
        Ok(Value::Null)
    }
}
