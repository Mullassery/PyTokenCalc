"""User-friendly error messages with context and suggestions."""


class ErrorMessage:
    """Base error message with context and suggestions."""
    
    def __init__(self, title: str, message: str, suggestions: list = None, links: list = None):
        self.title = title
        self.message = message
        self.suggestions = suggestions or []
        self.links = links or []
    
    def format(self) -> str:
        """Format error message for display."""
        lines = [f"\n❌ {self.title}\n"]
        lines.append(f"   {self.message}\n")
        
        if self.suggestions:
            lines.append("   💡 Suggestions:")
            for suggestion in self.suggestions:
                lines.append(f"      • {suggestion}")
        
        if self.links:
            lines.append("\n   📚 Learn more:")
            for link in self.links:
                lines.append(f"      • {link}")
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        return self.format()


# Configuration Errors
MISSING_SMTP_CONFIG = ErrorMessage(
    title="SMTP Configuration Missing",
    message="Email alerts are not configured. PyCostAudit cannot send email notifications.",
    suggestions=[
        "Set PYCOSTAUDIT_SMTP_HOST environment variable (default: smtp.gmail.com)",
        "Set PYCOSTAUDIT_SMTP_USER with your email address",
        "Set PYCOSTAUDIT_SMTP_PASSWORD with your app password or email password",
        "For Gmail: Use an App Password, not your regular password",
        "Set PYCOSTAUDIT_FROM_EMAIL for the sender address",
    ],
    links=[
        "Gmail setup: https://support.google.com/accounts/answer/185833",
        "Docs: https://github.com/Mullassery/PyCostAudit#configuration",
    ]
)

MISSING_DATABASE = ErrorMessage(
    title="Database Configuration Error",
    message="Cannot initialize database. The database path is not writable.",
    suggestions=[
        "Check that the directory ~/.pycostaudit/ exists and is writable",
        "Ensure you have write permissions to the home directory",
        "Try: mkdir -p ~/.pycostaudit && chmod 700 ~/.pycostaudit",
        "Or set PYCOSTAUDIT_DATABASE_URL to a custom location",
    ],
    links=[
        "Configuration guide: https://github.com/Mullassery/PyCostAudit#installation",
    ]
)

INVALID_COST_DATA = ErrorMessage(
    title="Invalid Cost Data Format",
    message="Cannot process cost data. Check that all required fields are present and valid.",
    suggestions=[
        "Required fields: timestamp, model, tokens_in, tokens_out, cost_usd",
        "Timestamps must be ISO 8601 format: 2026-01-01T12:00:00Z",
        "Models must be valid Claude model names: claude-3-5-sonnet, claude-3-opus, etc.",
        "Token counts must be positive integers",
        "Cost must be a positive number",
    ],
    links=[
        "Data format: https://github.com/Mullassery/PyCostAudit#data-format",
    ]
)

API_AUTHENTICATION_FAILED = ErrorMessage(
    title="Anthropic API Authentication Failed",
    message="Cannot authenticate with Anthropic API. Check your API key.",
    suggestions=[
        "Verify ANTHROPIC_API_KEY environment variable is set",
        "Generate a new API key at https://console.anthropic.com/",
        "Ensure the key is not expired or revoked",
        "Check that there are no extra spaces in the key",
    ],
    links=[
        "API keys: https://console.anthropic.com/account/keys",
        "Authentication: https://docs.anthropic.com/claude/reference/getting-started-with-the-api",
    ]
)

FORECASTING_ERROR = ErrorMessage(
    title="Cost Forecasting Failed",
    message="Cannot generate cost forecast. Need more historical data or valid configuration.",
    suggestions=[
        "Ensure you have at least 7 days of historical cost data",
        "Check that all cost entries have valid dates and amounts",
        "Try a shorter forecast period (30 days instead of 90)",
        "Verify there are no outliers causing statistical issues",
    ],
    links=[
        "Forecasting guide: https://github.com/Mullassery/PyCostAudit#forecasting",
    ]
)

# Database Errors
DATABASE_CONNECTION_ERROR = ErrorMessage(
    title="Database Connection Failed",
    message="Cannot connect to database. Check connection string and database availability.",
    suggestions=[
        "For SQLite: Ensure the directory exists and is writable",
        "For PostgreSQL: Check host, port, username, password",
        "Verify database server is running and accessible",
        "Check firewall rules if using remote database",
    ],
    links=[
        "Database setup: https://github.com/Mullassery/PyCostAudit#database",
    ]
)

EXPORT_ERROR = ErrorMessage(
    title="Export Failed",
    message="Cannot export data to file. Check file path and disk space.",
    suggestions=[
        "Ensure the output directory exists and is writable",
        "Check that you have enough disk space",
        "Try a different format (CSV instead of Excel)",
        "Verify the file path doesn't contain invalid characters",
    ],
    links=[
        "Export formats: https://github.com/Mullassery/PyCostAudit#export",
    ]
)


def get_error_message(error_type: str) -> ErrorMessage:
    """Get formatted error message by type."""
    messages = {
        "MISSING_SMTP": MISSING_SMTP_CONFIG,
        "MISSING_DATABASE": MISSING_DATABASE,
        "INVALID_DATA": INVALID_COST_DATA,
        "API_AUTH": API_AUTHENTICATION_FAILED,
        "FORECASTING": FORECASTING_ERROR,
        "DB_CONNECTION": DATABASE_CONNECTION_ERROR,
        "EXPORT": EXPORT_ERROR,
    }
    return messages.get(error_type, ErrorMessage("Unknown Error", "An unexpected error occurred."))
