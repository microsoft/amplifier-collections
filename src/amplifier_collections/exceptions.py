"""Collection-specific exceptions.

Per IMPLEMENTATION_PHILOSOPHY: Clear, actionable error messages.
"""


class CollectionError(Exception):
    """Base exception for collection operations."""

    def __init__(self, message: str, context: dict | None = None):
        """Initialize with message and optional context.

        Args:
            message: Human-readable error message
            context: Optional dict with additional context (file paths, etc.)
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}


class CollectionInstallError(CollectionError):
    """Collection installation failed."""


class CollectionMetadataError(CollectionError):
    """Invalid or missing collection metadata."""


class CollectionNotFoundError(CollectionError):
    """Collection not found in search paths."""
