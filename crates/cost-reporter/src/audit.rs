//! Immutable audit logging for compliance

use crate::storage::StorageBackend;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sqlx::Row;
use std::sync::Arc;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AuditEventType {
    UserLogin,
    UserLogout,
    UserCreated,
    UserDeleted,
    RoleChanged,
    PermissionGranted,
    PermissionRevoked,
    DataAccessed,
    DataCreated,
    DataUpdated,
    DataDeleted,
    ConfigChanged,
    ApiKeyCreated,
    ApiKeyDeleted,
    UnauthorizedAccess,
    SuspiciousActivity,
}

impl AuditEventType {
    fn to_string(&self) -> String {
        match self {
            Self::UserLogin => "user_login".to_string(),
            Self::UserLogout => "user_logout".to_string(),
            Self::UserCreated => "user_created".to_string(),
            Self::UserDeleted => "user_deleted".to_string(),
            Self::RoleChanged => "role_changed".to_string(),
            Self::PermissionGranted => "permission_granted".to_string(),
            Self::PermissionRevoked => "permission_revoked".to_string(),
            Self::DataAccessed => "data_accessed".to_string(),
            Self::DataCreated => "data_created".to_string(),
            Self::DataUpdated => "data_updated".to_string(),
            Self::DataDeleted => "data_deleted".to_string(),
            Self::ConfigChanged => "config_changed".to_string(),
            Self::ApiKeyCreated => "api_key_created".to_string(),
            Self::ApiKeyDeleted => "api_key_deleted".to_string(),
            Self::UnauthorizedAccess => "unauthorized_access".to_string(),
            Self::SuspiciousActivity => "suspicious_activity".to_string(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEvent {
    pub id: String,
    pub timestamp: DateTime<Utc>,
    pub event_type: AuditEventType,
    pub user_id: String,
    pub org_id: String,
    pub resource_type: String,
    pub resource_id: String,
    pub action: String,
    pub description: String,
    pub ip_address: String,
    pub status: String,
    pub error_message: Option<String>,
}

#[derive(Clone)]
pub struct AuditLogger {
    storage: Arc<StorageBackend>,
}

impl AuditLogger {
    pub fn new(storage: Arc<StorageBackend>) -> Self {
        Self { storage }
    }

    /// Log an audit event to the immutable audit trail
    pub async fn log(&self, event: AuditEvent) -> anyhow::Result<()> {
        if let Some(pool) = self.storage.get_pool() {
            let event_type_str = event.event_type.to_string();
            let timestamp_str = event.timestamp.to_rfc3339();
            let error_msg = event.error_message.clone();

            sqlx::query(
                r#"
                INSERT INTO audit_logs (
                    id, timestamp, event_type, user_id, org_id,
                    resource_type, resource_id, action, description,
                    ip_address, status, error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                "#,
            )
            .bind(&event.id)
            .bind(&timestamp_str)
            .bind(&event_type_str)
            .bind(&event.user_id)
            .bind(&event.org_id)
            .bind(&event.resource_type)
            .bind(&event.resource_id)
            .bind(&event.action)
            .bind(&event.description)
            .bind(&event.ip_address)
            .bind(&event.status)
            .bind(&error_msg)
            .execute(pool)
            .await
            .map_err(|e| anyhow::anyhow!("Failed to log audit event: {}", e))?;

            tracing::debug!(
                "✅ Audit event logged: {} ({})",
                event.event_type.to_string(),
                event.id
            );
        }

        Ok(())
    }

    /// Retrieve audit logs with optional filtering
    pub async fn get_logs(
        &self,
        org_id: &str,
        limit: Option<i64>,
    ) -> anyhow::Result<Vec<AuditEvent>> {
        if let Some(pool) = self.storage.get_pool() {
            let limit_val = limit.unwrap_or(100).min(1000);

            let rows = sqlx::query(
                r#"
                SELECT
                    id, timestamp, event_type, user_id, org_id,
                    resource_type, resource_id, action, description,
                    ip_address, status, error_message
                FROM audit_logs
                WHERE org_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                "#,
            )
            .bind(org_id)
            .bind(limit_val)
            .fetch_all(pool)
            .await
            .map_err(|e| anyhow::anyhow!("Failed to retrieve audit logs: {}", e))?;

            let events = rows
                .iter()
                .filter_map(|row| {
                    let timestamp_str: String = row.get("timestamp");
                    let event_type_str: String = row.get("event_type");

                    DateTime::parse_from_rfc3339(&timestamp_str)
                        .ok()
                        .map(|dt| dt.with_timezone(&Utc))
                        .map(|timestamp| AuditEvent {
                            id: row.get("id"),
                            timestamp,
                            event_type: match event_type_str.as_str() {
                                "user_login" => AuditEventType::UserLogin,
                                "user_logout" => AuditEventType::UserLogout,
                                "unauthorized_access" => AuditEventType::UnauthorizedAccess,
                                "suspicious_activity" => AuditEventType::SuspiciousActivity,
                                _ => AuditEventType::DataAccessed,
                            },
                            user_id: row.get("user_id"),
                            org_id: row.get("org_id"),
                            resource_type: row.get("resource_type"),
                            resource_id: row.get("resource_id"),
                            action: row.get("action"),
                            description: row.get("description"),
                            ip_address: row.get("ip_address"),
                            status: row.get("status"),
                            error_message: row.get("error_message"),
                        })
                })
                .collect();

            Ok(events)
        } else {
            Ok(vec![])
        }
    }

    /// Get failed access attempts
    pub async fn get_failed_events(&self, org_id: &str) -> anyhow::Result<Vec<AuditEvent>> {
        if let Some(pool) = self.storage.get_pool() {
            let rows = sqlx::query(
                r#"
                SELECT
                    id, timestamp, event_type, user_id, org_id,
                    resource_type, resource_id, action, description,
                    ip_address, status, error_message
                FROM audit_logs
                WHERE org_id = ? AND status = 'failure'
                ORDER BY timestamp DESC
                LIMIT 100
                "#,
            )
            .bind(org_id)
            .fetch_all(pool)
            .await
            .map_err(|e| anyhow::anyhow!("Failed to retrieve failed events: {}", e))?;

            let events = rows
                .iter()
                .filter_map(|row| {
                    let timestamp_str: String = row.get("timestamp");

                    DateTime::parse_from_rfc3339(&timestamp_str)
                        .ok()
                        .map(|dt| dt.with_timezone(&Utc))
                        .map(|timestamp| AuditEvent {
                            id: row.get("id"),
                            timestamp,
                            event_type: AuditEventType::DataAccessed,
                            user_id: row.get("user_id"),
                            org_id: row.get("org_id"),
                            resource_type: row.get("resource_type"),
                            resource_id: row.get("resource_id"),
                            action: row.get("action"),
                            description: row.get("description"),
                            ip_address: row.get("ip_address"),
                            status: row.get("status"),
                            error_message: row.get("error_message"),
                        })
                })
                .collect();

            Ok(events)
        } else {
            Ok(vec![])
        }
    }
}

impl AuditEvent {
    pub fn new(
        event_type: AuditEventType,
        user_id: String,
        org_id: String,
        resource_type: String,
        resource_id: String,
        action: String,
        description: String,
        ip_address: String,
    ) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            timestamp: Utc::now(),
            event_type,
            user_id,
            org_id,
            resource_type,
            resource_id,
            action,
            description,
            ip_address,
            status: "success".to_string(),
            error_message: None,
        }
    }

    pub fn with_failure(mut self, error: String) -> Self {
        self.status = "failure".to_string();
        self.error_message = Some(error);
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_audit_event_creation() {
        let event = AuditEvent::new(
            AuditEventType::UserLogin,
            "user123".to_string(),
            "org456".to_string(),
            "user".to_string(),
            "user789".to_string(),
            "login".to_string(),
            "User logged in".to_string(),
            "192.168.1.1".to_string(),
        );

        assert_eq!(event.user_id, "user123");
        assert_eq!(event.org_id, "org456");
        assert_eq!(event.status, "success");
        assert!(event.error_message.is_none());
    }

    #[test]
    fn test_audit_event_with_failure() {
        let event = AuditEvent::new(
            AuditEventType::UnauthorizedAccess,
            "user123".to_string(),
            "org456".to_string(),
            "report".to_string(),
            "report789".to_string(),
            "access".to_string(),
            "Unauthorized access attempt".to_string(),
            "192.168.1.2".to_string(),
        )
        .with_failure("Permission denied".to_string());

        assert_eq!(event.status, "failure");
        assert_eq!(event.error_message, Some("Permission denied".to_string()));
    }

    #[test]
    fn test_audit_event_type_to_string() {
        assert_eq!(AuditEventType::UserLogin.to_string(), "user_login");
        assert_eq!(
            AuditEventType::UnauthorizedAccess.to_string(),
            "unauthorized_access"
        );
        assert_eq!(AuditEventType::ApiKeyCreated.to_string(), "api_key_created");
    }
}
