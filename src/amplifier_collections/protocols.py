"""Protocols for collection installation sources.

Per KERNEL_PHILOSOPHY: Protocol-based extensibility over configuration.
Per IMPLEMENTATION_PHILOSOPHY: Composition over inheritance.
"""

from pathlib import Path
from typing import Protocol


class InstallSourceProtocol(Protocol):
    """Protocol for collection installation sources.

    Apps can provide any implementation (GitSource, HttpZipSource, FileSource, etc.).
    The library only requires this interface.

    Example implementations:
    - GitSource: Git repositories (via amplifier-module-resolution)
    - HttpZipSource: HTTP zip downloads
    - FileSource: Local directories for development
    """

    async def install_to(self, target_dir: Path) -> None:
        """Install collection content to target directory.

        Args:
            target_dir: Directory to install into (will be created if needed)

        Raises:
            Exception: If installation fails
        """
        ...
