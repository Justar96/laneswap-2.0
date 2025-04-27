"""
Custom exceptions for the LaneSwap system.
"""

class LaneSwapError(Exception):
    """Base exception for all LaneSwap errors."""
    pass


class ServiceNotFoundError(LaneSwapError):
    """Raised when a service is not found."""
    pass


class StorageError(LaneSwapError):
    """Raised when there's an error with storage operations."""
    pass


class NotifierError(LaneSwapError):
    """Raised when there's an error with notification operations."""
    pass


class ValidationError(LaneSwapError):
    """Raised when validation fails."""
    pass


class ConfigurationError(LaneSwapError):
    """Raised when there's an error in configuration."""
    pass


class ExecutionError(LaneSwapError):
    """Raised when there's an error during function execution tracking."""
    pass
