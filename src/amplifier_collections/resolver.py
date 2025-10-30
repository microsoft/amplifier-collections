"""Collection resolver - Resolve collection names to paths.

CRITICAL (KERNEL_PHILOSOPHY): Search paths are app policy, not library mechanism.

Per KERNEL_PHILOSOPHY:
- "Could two teams want different behavior?" → YES (search order is policy)
- Different apps could resolve collections differently
- Kernel doesn't know about collections

Per AGENTS.md: Ruthless simplicity - direct filesystem checks, no caching complexity.

REFACTORED from CLI: Search paths must be injected by app, not hardcoded.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _has_matching_name(pyproject_path: Path, expected_name: str) -> bool:
    """Check if pyproject.toml has matching collection name.

    Args:
        pyproject_path: Path to pyproject.toml file
        expected_name: Expected collection name

    Returns:
        True if names match, False otherwise
    """
    try:
        import tomllib

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        actual_name = data.get("project", {}).get("name")
        return actual_name == expected_name
    except Exception:
        return False


class CollectionResolver:
    """
    Resolve collection names to installation paths (with injected search paths).

    This class implements mechanism for resolving names. Apps inject POLICY (search paths).

    Different applications could:
    - Use different search orders
    - Add custom search locations
    - Implement different precedence rules

    Philosophy:
    - Simple, direct filesystem checks
    - No caching (YAGNI - optimize if needed later)
    - Clear error messages
    """

    def __init__(self, search_paths: list[Path]):
        """Initialize resolver with app-provided search paths.

        Args:
            search_paths: List of paths to search in precedence order (lowest to highest).
                         For example: [bundled, user, project] where project has highest precedence.

        Example:
            >>> search_paths = [
            ...     Path("/var/app/collections"),  # Bundled (lowest)
            ...     Path.home() / ".amplifier" / "collections",  # User
            ...     Path.cwd() / ".amplifier" / "collections",  # Project (highest)
            ... ]
            >>> resolver = CollectionResolver(search_paths=search_paths)
        """
        self.search_paths = search_paths

    def resolve(self, collection_name: str) -> Path | None:
        """
        Resolve collection name to installation path.

        Supports both structure types and naming patterns:
        - Flat: collections/name/pyproject.toml (git clone, manual)
        - Nested: collections/name/pkg_name/pyproject.toml (pip install)
        - Directory names may differ from collection names (e.g., repo name vs metadata name)

        Per RUTHLESS_SIMPLICITY: Search by metadata name, not directory name.
        Per WORK_WITH_STANDARDS: Python packaging creates nested structure.

        Searches in reverse precedence order (highest first).

        Args:
            collection_name: Name of collection from pyproject.toml metadata (e.g., "design-intelligence")

        Returns:
            Path to collection root (where pyproject.toml is) if found, None otherwise

        Example:
            >>> resolver = CollectionResolver(search_paths=[...])
            >>> path = resolver.resolve("design-intelligence")
            >>> # Finds ~/.amplifier/collections/amplifier-collection-design-intelligence/
            >>> # by reading pyproject.toml files, not matching directory names
        """
        # Search in reverse order (highest precedence first)
        for search_path in reversed(self.search_paths):
            if not search_path.exists():
                continue

            # Try directory name match first (fast path)
            candidate = search_path / collection_name
            if candidate.exists() and candidate.is_dir():
                # Strategy 1: Flat structure with matching directory name
                if (candidate / "pyproject.toml").exists() and _has_matching_name(
                    candidate / "pyproject.toml", collection_name
                ):
                    return candidate.resolve()

                # Strategy 2: Nested package structure with matching directory name
                package_name = collection_name.replace("-", "_")
                nested_candidate = candidate / package_name
                if (
                    nested_candidate.exists()
                    and (nested_candidate / "pyproject.toml").exists()
                    and _has_matching_name(nested_candidate / "pyproject.toml", collection_name)
                ):
                    return nested_candidate.resolve()

            # Slow path: Directory name doesn't match metadata name
            # (e.g., repo "amplifier-collection-X" but metadata "X")
            # Search all subdirectories
            for subdir in search_path.iterdir():
                if not subdir.is_dir() or subdir.name.startswith("."):
                    continue

                # Check flat structure
                if (subdir / "pyproject.toml").exists() and _has_matching_name(
                    subdir / "pyproject.toml", collection_name
                ):
                    return subdir.resolve()

                # Check nested structure
                for nested in subdir.iterdir():
                    if (
                        nested.is_dir()
                        and (nested / "pyproject.toml").exists()
                        and _has_matching_name(nested / "pyproject.toml", collection_name)
                    ):
                        return nested.resolve()

        return None

    def resolve_collection_path(self, collection_name: str) -> Path | None:
        """Alias for resolve() to match CollectionResolverProtocol.

        Args:
            collection_name: Name of collection

        Returns:
            Path to collection if found, None otherwise
        """
        return self.resolve(collection_name)

    def list_collections(self) -> list[tuple[str, Path]]:
        """
        List all available collections by METADATA name.

        Returns list of (metadata_name, collection_root_path) tuples.
        Higher precedence collections override lower precedence.

        Per RUTHLESS_SIMPLICITY: Metadata is single source of truth.
        Per DRY: Reads metadata for canonical name.

        Returns:
            List of (collection_name, collection_path) tuples

        Example:
            >>> resolver = CollectionResolver(search_paths=[...])
            >>> collections = resolver.list_collections()
            >>> for name, path in collections:
            ...     print(f"{name}: {path}")
            design-intelligence: ~/.amplifier/collections/design-intelligence/design_intelligence
            foundation: <package>/data/collections/foundation
        """
        collections = {}

        # Iterate in precedence order (lowest to highest)
        # Higher precedence overwrites lower in dictionary
        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            for collection_dir in search_path.iterdir():
                if not collection_dir.is_dir() or collection_dir.name.startswith("."):
                    continue

                # Find collection root and read metadata
                metadata_name = None
                collection_root = None

                # Try flat structure
                if (collection_dir / "pyproject.toml").exists():
                    try:
                        from .schema import CollectionMetadata

                        metadata = CollectionMetadata.from_pyproject(collection_dir / "pyproject.toml")
                        metadata_name = metadata.name
                        collection_root = collection_dir.resolve()
                    except Exception as e:
                        logger.debug(f"Could not read metadata from {collection_dir}: {e}")

                # Try nested structure if flat didn't work
                if metadata_name is None:
                    # Check immediate subdirectories
                    for item in collection_dir.iterdir():
                        if (
                            item.is_dir()
                            and not item.name.startswith(".")
                            and not item.name.endswith(".dist-info")
                            and (item / "pyproject.toml").exists()
                        ):
                            try:
                                from .schema import CollectionMetadata

                                metadata = CollectionMetadata.from_pyproject(item / "pyproject.toml")
                                metadata_name = metadata.name
                                collection_root = item.resolve()
                                break
                            except Exception as e:
                                logger.debug(f"Could not read metadata from {item}: {e}")

                # Add to collections if found (higher precedence overwrites)
                if metadata_name and collection_root:
                    collections[metadata_name] = collection_root

        return list(collections.items())
