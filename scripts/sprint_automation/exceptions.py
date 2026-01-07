"""
Custom exceptions for sprint lifecycle operations.

These exceptions provide clear error categorization for different
types of failures that can occur during sprint automation.
"""


class SprintLifecycleError(Exception):
    """Base exception for sprint lifecycle operations."""

    pass


class GitError(SprintLifecycleError):
    """Git operation failed."""

    pass


class FileOperationError(SprintLifecycleError):
    """File operation failed."""

    pass


class ValidationError(SprintLifecycleError):
    """Validation check failed."""

    pass
