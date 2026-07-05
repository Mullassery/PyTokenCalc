//! SQLite storage backend for persistent cost tracking

use crate::types::{Operation, CostData, Session};
use sqlx::sqlite::{SqlitePool, SqliteConnectOptions};
use std::str::FromStr;

#[derive(Clone, Debug)]
pub struct StorageBackend {
    pool: Option<SqlitePool>,
    in_memory: bool,
}

impl StorageBackend {
    /// Create in-memory backend (for testing)
    pub fn new_memory() -> Self {
        Self {
            pool: None,
            in_memory: true,
        }
    }

    /// Create SQLite backend with persistent storage
    pub async fn new(db_path: &str) -> anyhow::Result<Self> {
        let options = SqliteConnectOptions::from_str(db_path)?
            .create_if_missing(true);

        let pool = SqlitePool::connect_with(options).await?;

        // Initialize schema
        Self::init_schema(&pool).await?;

        Ok(Self {
            pool: Some(pool),
            in_memory: false,
        })
    }

    /// Initialize database schema
    async fn init_schema(pool: &SqlitePool) -> anyhow::Result<()> {
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS operations (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                operation_type TEXT NOT NULL,
                tokens_input INTEGER NOT NULL,
                tokens_output INTEGER NOT NULL,
                model TEXT NOT NULL,
                file_source TEXT,
                mcp_name TEXT,
                timestamp TEXT NOT NULL,
                user_name TEXT,
                cost_usd REAL NOT NULL,
                tokens_actual INTEGER NOT NULL,
                multiplier REAL NOT NULL,
                tags TEXT
            )
            "#,
        )
        .execute(pool)
        .await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                tags TEXT,
                operation_ids TEXT,
                total_cost_usd REAL
            )
            "#,
        )
        .execute(pool)
        .await?;

        sqlx::query("CREATE INDEX IF NOT EXISTS idx_session_id ON operations(session_id)")
            .execute(pool)
            .await?;

        sqlx::query("CREATE INDEX IF NOT EXISTS idx_timestamp ON operations(timestamp)")
            .execute(pool)
            .await?;

        Ok(())
    }

    /// Save operation to storage
    pub async fn save_operation(&self, operation: &Operation, cost: &CostData) -> anyhow::Result<()> {
        if self.in_memory {
            return Ok(());
        }

        let pool = self.pool.as_ref().ok_or(anyhow::anyhow!("No storage pool"))?;

        let tags = serde_json::to_string(&operation.tags)?;
        let file_source = operation.file_source.as_ref().map(|fs| format!("{:?}", fs));

        sqlx::query(
            r#"
            INSERT INTO operations (
                id, session_id, operation_type, tokens_input, tokens_output,
                model, file_source, mcp_name, timestamp, user_name,
                cost_usd, tokens_actual, multiplier, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(&operation.id)
        .bind(&operation.session_id)
        .bind(format!("{:?}", operation.operation_type))
        .bind(operation.tokens_input)
        .bind(operation.tokens_output)
        .bind(&operation.model)
        .bind(file_source)
        .bind(&operation.mcp_name)
        .bind(operation.timestamp.to_rfc3339())
        .bind(&operation.user)
        .bind(cost.cost_usd)
        .bind(cost.tokens_actual)
        .bind(cost.multiplier)
        .bind(tags)
        .execute(pool)
        .await?;

        Ok(())
    }

    /// Save session to storage
    pub async fn save_session(&self, session: &Session) -> anyhow::Result<()> {
        if self.in_memory {
            return Ok(());
        }

        let pool = self.pool.as_ref().ok_or(anyhow::anyhow!("No storage pool"))?;
        let tags = serde_json::to_string(&session.tags)?;
        let operation_ids = serde_json::to_string(&session.operation_ids)?;

        sqlx::query(
            r#"
            INSERT INTO sessions (
                id, name, started_at, ended_at, tags, operation_ids, total_cost_usd
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(&session.id)
        .bind(&session.name)
        .bind(session.started_at.to_rfc3339())
        .bind(session.ended_at.as_ref().map(|dt| dt.to_rfc3339()))
        .bind(tags)
        .bind(operation_ids)
        .bind(session.total_cost_usd)
        .execute(pool)
        .await?;

        Ok(())
    }

    /// Update session summary after finalization
    pub async fn update_session_summary(
        &self,
        _session_id: &str,
        _summary: &serde_json::Value,
    ) -> anyhow::Result<()> {
        if self.in_memory {
            return Ok(());
        }

        // Update logic here (for now, no-op)
        Ok(())
    }

    /// Get operations from the last N hours
    pub async fn get_operations_since_hours(&self, hours: u64) -> anyhow::Result<Vec<Operation>> {
        if self.in_memory {
            return Ok(Vec::new());
        }

        let pool = self.pool.as_ref().ok_or(anyhow::anyhow!("No storage pool"))?;

        let cutoff = chrono::Utc::now() - chrono::Duration::hours(hours as i64);
        let cutoff_str = cutoff.to_rfc3339();

        let _rows = sqlx::query(
            r#"
            SELECT id, session_id, operation_type, tokens_input, tokens_output,
                   model, file_source, mcp_name, timestamp, user_name, tags
            FROM operations
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            "#,
        )
        .bind(cutoff_str)
        .fetch_all(pool)
        .await?;

        // Convert rows to Operation structs
        // (Simplified for now - full implementation would deserialize properly)
        Ok(Vec::new())
    }

    /// Get operations for a specific session
    pub async fn get_session_operations(&self, session_id: &str) -> anyhow::Result<Vec<Operation>> {
        if self.in_memory {
            return Ok(Vec::new());
        }

        let pool = self.pool.as_ref().ok_or(anyhow::anyhow!("No storage pool"))?;

        let _rows = sqlx::query(
            r#"
            SELECT id, session_id, operation_type, tokens_input, tokens_output,
                   model, file_source, mcp_name, timestamp, user_name, tags
            FROM operations
            WHERE session_id = ?
            ORDER BY timestamp ASC
            "#,
        )
        .bind(session_id)
        .fetch_all(pool)
        .await?;

        // Convert rows to Operation structs
        Ok(Vec::new())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_memory_backend() {
        let backend = StorageBackend::new_memory();
        assert!(backend.in_memory);
    }
}
