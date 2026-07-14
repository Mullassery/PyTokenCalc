"""Specific exception types for better error handling."""

class CostAuditError(Exception):
    """Base exception for PyCostAudit."""
    pass


class DatabaseError(CostAuditError):
    """Database operation failed."""
    pass


class ConfigurationError(CostAuditError):
    """Configuration is invalid or missing."""
    pass


class ValidationError(CostAuditError):
    """Input validation failed."""
    pass


class AuthenticationError(CostAuditError):
    """Authentication/credentials failed."""
    pass


class APIError(CostAuditError):
    """API call failed."""
    pass


class ProcessingError(CostAuditError):
    """Data processing error."""
    pass


class CalculationError(ProcessingError):
    """Cost calculation error."""
    pass


class ForecastingError(ProcessingError):
    """Forecasting calculation failed."""
    pass


class ExportError(CostAuditError):
    """Export operation failed."""
    pass


class AlertError(CostAuditError):
    """Alert delivery failed."""
    pass
