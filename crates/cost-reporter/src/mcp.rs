//! MCP (Model Context Protocol) server implementation

use serde_json::Value;

pub struct MCPHandler;

impl MCPHandler {
    pub async fn handle(&self, message: Value) -> anyhow::Result<Value> {
        // TODO: Handle MCP protocol messages from Claude Code
        Ok(Value::Null)
    }
}
