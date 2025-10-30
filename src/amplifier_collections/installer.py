"""Collection installation mechanism (protocol-based).

Per KERNEL_PHILOSOPHY: Mechanism not policy - library doesn't know HOW to install,
apps provide InstallSourceProtocol implementations.

Per IMPLEMENTATION_PHILOSOPHY:
- Protocol-based: Apps provide sources (GitSource, HttpZipSource, etc.)
- Target path injection: Apps determine WHERE to install
- Ruthless simplicity: Core mechanism only

REFACTORED from CLI: All policy decisions (paths, sources) removed - apps inject them.
"""

import logging
import shutil
from pathlib import Path

from .discovery import discover_collection_resources
from .exceptions import CollectionInstallError
from .lock import CollectionLock
from .protocols import InstallSourceProtocol
from .schema import CollectionMetadata

logger = logging.getLogger(__name__)


async def install_collection(
    source: InstallSourceProtocol,
    target_dir: Path,
    lock: CollectionLock | None = None,
) -> CollectionMetadata:
    """
    Install collection from source (protocol-based, mechanism only).

    Apps provide:
    - source: How to fetch collection (GitSource, HttpZipSource, FileSource, etc.)
    - target_dir: Where to install (app policy)
    - lock: Optional lock manager (app policy)

    Process:
    1. Source installs content to target_dir (via source.install_to)
    2. Validate pyproject.toml exists
    3. Parse metadata
    4. Discover resources
    5. Add entry to lock file (if provided)

    Args:
        source: Installation source implementing InstallSourceProtocol
        target_dir: Directory to install into (app determines location, must not exist)
        lock: Optional lock file manager

    Returns:
        CollectionMetadata from installed collection

    Raises:
        CollectionInstallError: If installation fails at any step

    Example:
        >>> from amplifier_module_resolution import GitSource
        >>> source = GitSource("git+https://github.com/org/collection@v1.0.0")
        >>> lock = CollectionLock(lock_file_path=Path(".amplifier/collections.lock"))
        >>> metadata = await install_collection(
        ...     source=source,
        ...     target_dir=Path(".amplifier/collections/my-collection"),
        ...     lock=lock
        ... )
        >>> print(f"Installed {metadata.name}")
    """
    try:
        # Step 1: Source installs to target_dir
        logger.info(f"Installing collection to {target_dir}")
        await source.install_to(target_dir)

        # Step 2: Validate pyproject.toml exists
        pyproject_path = target_dir / "pyproject.toml"
        if not pyproject_path.exists():
            raise CollectionInstallError(
                f"No pyproject.toml found in collection at {target_dir}", context={"target_dir": str(target_dir)}
            )

        # Step 3: Parse metadata
        metadata = CollectionMetadata.from_pyproject(pyproject_path)
        logger.debug(f"Collection name: {metadata.name}")

        # Step 4: Discover resources (validation)
        resources = discover_collection_resources(target_dir)
        logger.debug(f"Discovered resources: {resources}")

        # Step 5: Add to lock file (if provided)
        if lock is not None:
            # Try to get commit SHA if source has it
            commit_sha = getattr(source, "commit_sha", None)
            source_uri = getattr(source, "uri", "unknown")

            lock.add_entry(
                name=metadata.name,
                source=source_uri,
                commit=commit_sha,
                path=target_dir,
            )
            logger.debug(f"Added {metadata.name} to lock file")

        logger.info(f"Successfully installed collection: {metadata.name}")
        return metadata

    except Exception as e:
        if isinstance(e, CollectionInstallError):
            raise
        raise CollectionInstallError(f"Failed to install collection: {e}") from e


async def uninstall_collection(
    collection_name: str,
    collections_dir: Path,
    lock: CollectionLock | None = None,
) -> None:
    """
    Uninstall collection (mechanism only, apps inject paths).

    Process:
    1. Remove collection directory
    2. Remove lock entry (if provided)

    Args:
        collection_name: Name of collection to remove
        collections_dir: Parent directory containing collections (app policy)
        lock: Optional lock file manager

    Raises:
        CollectionInstallError: If collection not found or removal failed

    Example:
        >>> await uninstall_collection(
        ...     collection_name="my-collection",
        ...     collections_dir=Path(".amplifier/collections"),
        ...     lock=lock
        ... )
    """
    collection_path = collections_dir / collection_name

    if not collection_path.exists():
        raise CollectionInstallError(
            f"Collection '{collection_name}' not found at {collection_path}",
            context={"collection_name": collection_name, "collections_dir": str(collections_dir)},
        )

    try:
        logger.info(f"Uninstalling collection: {collection_name}")
        shutil.rmtree(collection_path)

        # Remove from lock file (if provided)
        if lock is not None:
            lock.remove_entry(collection_name)
            logger.debug(f"Removed {collection_name} from lock file")

        logger.info(f"Successfully uninstalled: {collection_name}")

    except Exception as e:
        raise CollectionInstallError(f"Failed to uninstall collection '{collection_name}': {e}") from e
