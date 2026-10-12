"""Specific exception types for PyTokenCalc."""


class PyTokenCalcError(Exception):
    """Base exception for PyTokenCalc."""


class ValidationError(PyTokenCalcError):
    """Input validation failed."""


class TokenCountError(PyTokenCalcError):
    """Token counting failed."""


class ModelNotSupportedError(PyTokenCalcError):
    """Model is not supported by any registered tokenizer."""


class APIError(PyTokenCalcError):
    """API call failed (for API-based tokenizers)."""


class CacheError(PyTokenCalcError):
    """Cache operation failed."""
