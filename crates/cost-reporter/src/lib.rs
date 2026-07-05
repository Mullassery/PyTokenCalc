//! ClaudeBeacon Core — High-performance memory, observability, and audit system
//!
//! Rust core for handling:
//! - Persistent project memory (SQLite/PostgreSQL)
//! - Tool call observability tracking
//! - Audit logging for compliance
//! - Session management

pub mod memory;
pub mod observability;
pub mod audit;
pub mod storage;
pub mod mcp;

pub use memory::MemoryManager;
pub use observability::ObservabilityTracker;
pub use audit::AuditLogger;
pub use storage::StorageBackend;

#[derive(Debug)]
pub struct BeaconCore {
    memory: MemoryManager,
    observability: ObservabilityTracker,
    audit: AuditLogger,
    storage: StorageBackend,
}

impl BeaconCore {
    pub async fn new(db_path: &str) -> anyhow::Result<Self> {
        let storage = StorageBackend::new(db_path).await?;
        
        Ok(Self {
            memory: MemoryManager::new(storage.clone()),
            observability: ObservabilityTracker::new(),
            audit: AuditLogger::new(storage.clone()),
            storage,
        })
    }

    /// Save project context to memory
    pub async fn save_memory(&mut self, context: serde_json::Value) -> anyhow::Result<()> {
        self.memory.save(context).await?;
        Ok(())
    }

    /// Get observability data for current session
    pub async fn observe(&self) -> anyhow::Result<serde_json::Value> {
        self.observability.get_summary().await
    }

    /// Get audit logs (optionally filtered)
    pub async fn audit(&self, filter: Option<serde_json::Value>) -> anyhow::Result<Vec<serde_json::Value>> {
        self.audit.get_logs(filter).await
    }
}
