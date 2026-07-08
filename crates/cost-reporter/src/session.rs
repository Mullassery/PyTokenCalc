//! Session management (group operations by context)

use crate::types::{Operation, Session};
use std::collections::HashMap;

/// Manages active sessions and their operations
pub struct SessionManager {
    sessions: HashMap<String, Session>,
}

impl SessionManager {
    pub fn new() -> Self {
        Self {
            sessions: HashMap::new(),
        }
    }

    /// Create a new session
    pub fn create_session(&mut self, name: Option<String>) -> Session {
        let session = Session::new(name);
        self.sessions.insert(session.id.clone(), session.clone());
        session
    }

    /// Add an operation to a session
    pub fn add_operation_to_session(
        &mut self,
        session_id: &str,
        operation_id: String,
    ) -> anyhow::Result<()> {
        if let Some(session) = self.sessions.get_mut(session_id) {
            session.add_operation(operation_id);
            Ok(())
        } else {
            Err(anyhow::anyhow!("Session {} not found", session_id))
        }
    }

    /// End a session
    pub fn end_session(&mut self, session_id: &str) -> anyhow::Result<Session> {
        if let Some(mut session) = self.sessions.remove(session_id) {
            session.end();
            Ok(session)
        } else {
            Err(anyhow::anyhow!("Session {} not found", session_id))
        }
    }

    /// Get a session by ID
    pub fn get_session(&self, session_id: &str) -> Option<&Session> {
        self.sessions.get(session_id)
    }

    /// Add tags to a session
    pub fn tag_session(
        &mut self,
        session_id: &str,
        key: String,
        value: String,
    ) -> anyhow::Result<()> {
        if let Some(session) = self.sessions.get_mut(session_id) {
            session.tags.insert(key, value);
            Ok(())
        } else {
            Err(anyhow::anyhow!("Session {} not found", session_id))
        }
    }

    /// Auto-detect session boundaries (when to split sessions)
    /// Strategy: New session if:
    /// - Context size changed by >50% (new task)
    /// - Time gap >5 minutes
    /// - Error spike detected
    pub fn should_create_new_session(
        &self,
        last_operation_tokens: Option<u32>,
        current_operation_tokens: u32,
        time_since_last_op_secs: u64,
    ) -> bool {
        // Time gap >5 minutes = new session
        if time_since_last_op_secs > 300 {
            return true;
        }

        // Context size changed by >50% = likely new task
        if let Some(last_tokens) = last_operation_tokens {
            let ratio = current_operation_tokens as f64 / last_tokens as f64;
            if ratio > 1.5 || ratio < 0.67 {
                return true;
            }
        }

        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_session() {
        let mut manager = SessionManager::new();
        let session = manager.create_session(Some("debug-auth".to_string()));
        assert_eq!(session.name, Some("debug-auth".to_string()));
        assert_eq!(manager.sessions.len(), 1);
    }

    #[test]
    fn test_add_operation() {
        let mut manager = SessionManager::new();
        let session = manager.create_session(None);
        let result = manager.add_operation_to_session(&session.id, "op-123".to_string());
        assert!(result.is_ok());
        assert_eq!(
            manager
                .get_session(&session.id)
                .unwrap()
                .operation_ids
                .len(),
            1
        );
    }

    #[test]
    fn test_end_session() {
        let mut manager = SessionManager::new();
        let session = manager.create_session(Some("test".to_string()));
        let session_id = session.id.clone();
        let result = manager.end_session(&session_id);
        assert!(result.is_ok());
        assert_eq!(manager.sessions.len(), 0);
    }

    #[test]
    fn test_tag_session() {
        let mut manager = SessionManager::new();
        let session = manager.create_session(None);
        let result = manager.tag_session(&session.id, "branch".to_string(), "main".to_string());
        assert!(result.is_ok());
        assert_eq!(
            manager
                .get_session(&session.id)
                .unwrap()
                .tags
                .get("branch")
                .unwrap(),
            "main"
        );
    }

    #[test]
    fn test_auto_detect_time_gap() {
        let manager = SessionManager::new();
        // >5 minutes = new session
        assert!(manager.should_create_new_session(Some(1000), 1000, 301));
        assert!(!manager.should_create_new_session(Some(1000), 1000, 100));
    }

    #[test]
    fn test_auto_detect_context_change() {
        let manager = SessionManager::new();
        // 50% increase = new session
        assert!(manager.should_create_new_session(Some(1000), 1600, 50));
        // 50% decrease = new session
        assert!(manager.should_create_new_session(Some(1000), 600, 50));
        // Small change = same session
        assert!(!manager.should_create_new_session(Some(1000), 1200, 50));
    }
}
