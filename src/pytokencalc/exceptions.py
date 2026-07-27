"""Specific exception types for PyTokenCalc."""


class PyTokenCalcError(Exception):
    """Base exception for PyTokenCalc."""
    pass


class ValidationError(PyTokenCalcError):
    """Input validation failed."""
    pass


class TokenCountError(PyTokenCalcError):
    """Token counting failed."""
    pass


class ModelNotSupportedError(PyTokenCalcError):
    """Model is not supported by any registered tokenizer."""
    pass


class APIError(PyTokenCalcError):
    """API call failed (for API-based tokenizers)."""
    pass


class CacheError(PyTokenCalcError):
    """Cache operation failed."""
    pass
