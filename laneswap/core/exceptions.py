"""
Custom exceptions for the LaneSwap system.
"""

class LaneswapError(Exception):
    """Base exception for all LaneSwap errors."""
    pass


class ServiceNotFoundError(LaneswapError):
    """Raised when a service is not found."""
    pass


class StorageError(LaneswapError):
    """Raised when there's an error with storage operations."""
    pass


class NotifierError(LaneswapError):
    """Raised when there's an error with notification operations."""
    pass


class ValidationError(LaneswapError):
    """Raised when validation fails."""
    pass


class ConfigurationError(LaneswapError):
    """Raised when there's an error in configuration."""
    pass


class ExecutionError(LaneswapError):
    """Raised when there's an error during function execution tracking."""
    pass
