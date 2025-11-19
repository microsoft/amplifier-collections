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


def _find_collection_root(target_dir: Path) -> Path | None:
    """Find collection root by locating pyproject.toml.

    Supports both structures:
    - Flat: target_dir/pyproject.toml (git clone, manual)
    - Nested: target_dir/pkg_name/pyproject.toml (pip install)

    Args:
        target_dir: Installation target directory

    Returns:
        Path to collection root (where pyproject.toml is), or None if not found

    Note:
        Uses same discovery pattern as CollectionResolver for consistency.
        Per RUTHLESS_SIMPLICITY: Accept structure as-is.
    """
    # Strategy 1: Flat structure
    if (target_dir / "pyproject.toml").exists():
        return target_dir

    # Strategy 2: Nested package structure
    # Search immediate subdirectories for pyproject.toml
    for item in target_dir.iterdir():
        if item.is_dir() and not item.name.startswith(".") and (item / "pyproject.toml").exists():
            return item

    return None


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

        # Step 2: Find collection root (where pyproject.toml is)
        # Supports both structures:
        # - Flat: target_dir/pyproject.toml (git clone, manual)
        # - Nested: target_dir/pkg_name/pyproject.toml (pip install)
        # Per RUTHLESS_SIMPLICITY: Use same pattern as CollectionResolver
        collection_root = _find_collection_root(target_dir)

        if not collection_root:
            raise CollectionInstallError(
                f"No pyproject.toml found in {target_dir}.\n"
                f"Expected at:\n"
                f"  - {target_dir / 'pyproject.toml'} (flat structure), or\n"
                f"  - {target_dir / '*' / 'pyproject.toml'} (pip install structure)",
                context={"target_dir": str(target_dir)},
            )

        pyproject_path = collection_root / "pyproject.toml"
        logger.debug(f"Collection root: {collection_root}")

        # Step 3: Parse metadata
        metadata = CollectionMetadata.from_pyproject(pyproject_path)
        logger.debug(f"Collection name: {metadata.name}")

        # Step 4: Discover resources from actual collection root (not target_dir!)
        # This is critical for data-only collections installed via uv pip install
        resources = discover_collection_resources(collection_root)
        logger.debug(f"Discovered resources: {resources}")

        # Step 5: Build module metadata for lock file
        module_metadata: dict[str, dict[str, str]] = {}
        for module_path in resources.modules:
            module_name = module_path.name
            # Store relative path from target_dir (installation root)
            relative_path = module_path.relative_to(target_dir)
            module_metadata[module_name] = {
                "path": str(relative_path),
                "type": "unknown",  # Could extract from entry points, but start simple
            }
            logger.debug(f"Registered module: {module_name} at {relative_path}")

        # Step 6: Add to lock file (if provided)
        if lock is not None:
            # Try to get commit SHA if source has it
            commit_sha = getattr(source, "commit_sha", None)
            source_uri = getattr(source, "uri", "unknown")

            lock.add_entry(
                name=metadata.name,
                source=source_uri,
                commit=commit_sha,
                path=target_dir,
                modules=module_metadata,
            )
            logger.debug(f"Added {metadata.name} to lock file with {len(module_metadata)} modules")

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
