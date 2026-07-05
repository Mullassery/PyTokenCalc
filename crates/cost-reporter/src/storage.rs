//! Persistent storage backend (SQLite or PostgreSQL)

use std::sync::Arc;

#[derive(Clone)]
pub struct StorageBackend {
    // TODO: SQLx connection pool
}

impl StorageBackend {
    pub async fn new(db_path: &str) -> anyhow::Result<Arc<Self>> {
        // TODO: Initialize SQLite or PostgreSQL connection
        Ok(Arc::new(Self {}))
    }
}
