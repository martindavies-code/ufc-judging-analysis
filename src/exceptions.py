"""Custom exception hierarchy for UFC Judging Analysis pipeline."""


class UFCDataError(Exception):
    """Base exception for all domain and operational errors in UFC Judging Analysis."""


class ValidationError(UFCDataError, ValueError):
    """Raised when user input, URL, file path, or data validation fails."""


class NetworkScrapeError(UFCDataError, IOError):
    """Raised when an HTTP request fails or network timeout occurs."""


class ParseExtractionError(UFCDataError, ValueError):
    """Raised when HTML parsing or tabular score extraction fails."""


class StorageError(UFCDataError, IOError):
    """Raised when database or filesystem operations fail."""
