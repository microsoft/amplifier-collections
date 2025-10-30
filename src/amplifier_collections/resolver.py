"""Collection resolver - Resolve collection names to paths.

CRITICAL (KERNEL_PHILOSOPHY): Search paths are app policy, not library mechanism.

Per KERNEL_PHILOSOPHY:
- "Could two teams want different behavior?" → YES (search order is policy)
- Different apps could resolve collections differently
- Kernel doesn't know about collections

Per AGENTS.md: Ruthless simplicity - direct filesystem checks, no caching complexity.

REFACTORED from CLI: Search paths must be injected by app, not hardcoded.
"""

from pathlib import Path


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

        Searches in reverse precedence order (highest first).

        Args:
            collection_name: Name of collection (e.g., "foundation")

        Returns:
            Path to collection directory if found, None otherwise

        Example:
            >>> resolver = CollectionResolver(search_paths=[...])
            >>> path = resolver.resolve("foundation")
            >>> # Returns ~/.amplifier/collections/foundation or bundled path
        """
        # Search in reverse order (highest precedence first)
        for search_path in reversed(self.search_paths):
            candidate = search_path / collection_name

            # Check if directory exists and has pyproject.toml
            if candidate.exists() and candidate.is_dir() and (candidate / "pyproject.toml").exists():
                return candidate.resolve()

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
        List all available collections with their paths.

        Returns list of (name, path) tuples. Higher precedence collections
        override lower precedence (e.g., user overrides bundled).

        Returns:
            List of (collection_name, collection_path) tuples

        Example:
            >>> resolver = CollectionResolver(search_paths=[...])
            >>> collections = resolver.list_collections()
            >>> for name, path in collections:
            ...     print(f"{name}: {path}")
            foundation: ~/.amplifier/collections/foundation
            developer-expertise: /bundled/data/collections/developer-expertise
        """
        collections = {}

        # Iterate in precedence order (lowest to highest)
        # Higher precedence overwrites lower in dictionary
        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            for collection_dir in search_path.iterdir():
                if not collection_dir.is_dir():
                    continue

                # Valid collection must have pyproject.toml
                if (collection_dir / "pyproject.toml").exists():
                    # Higher precedence overwrites
                    collections[collection_dir.name] = collection_dir

        return list(collections.items())
