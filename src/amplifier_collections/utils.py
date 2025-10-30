"""Collection utilities for name extraction and metadata handling.

Per DRY: Central utilities eliminate duplicated path parsing across consumers.
Per RUTHLESS_SIMPLICITY: Metadata is single source of truth.
"""

import logging
from pathlib import Path

from .schema import CollectionMetadata

logger = logging.getLogger(__name__)


def extract_collection_name_from_path(search_path: Path) -> str | None:
    """Extract collection metadata name from search path.

    Given a search path containing "/collections/" component,
    walks up to find collection root and reads metadata name.

    Per RUTHLESS_SIMPLICITY: Metadata is single source of truth.
    Per DRY: Central function eliminates duplicated path parsing.

    Args:
        search_path: Path containing "collections" component
                    (e.g., ~/.amplifier/collections/dir-name/profiles/)

    Returns:
        Collection metadata name (e.g., "design-intelligence")
        or None if not a collection path or metadata unreadable

    Examples:
        >>> # Flat structure
        >>> path = Path("~/.amplifier/collections/design-intelligence/profiles/")
        >>> extract_collection_name_from_path(path)
        'design-intelligence'

        >>> # Nested structure
        >>> path = Path("~/.amplifier/collections/dir/pkg/profiles/")
        >>> extract_collection_name_from_path(path)
        'design-intelligence'  # From metadata, not directory

        >>> # Non-collection path
        >>> path = Path("~/.amplifier/profiles/")
        >>> extract_collection_name_from_path(path)
        None

    Note:
        Eliminates need for manual path parsing:
        - No `parts.index("collections")`
        - No `collection_dir.name` assumptions
        - Reads pyproject.toml for authoritative name

        After app layer normalization, directory name SHOULD equal metadata name,
        but this function is defensive and reads metadata regardless.
    """
    # Must contain "collections" in path
    if "collections" not in search_path.parts:
        return None

    # Find collections index
    try:
        collections_idx = search_path.parts.index("collections")
    except ValueError:
        return None

    # Directory immediately after "collections" is collection directory
    if collections_idx + 1 >= len(search_path.parts):
        return None

    # Reconstruct collection directory path
    collection_dir = Path(*search_path.parts[: collections_idx + 2])
    # e.g., ~/.amplifier/collections/design-intelligence/

    # Strategy 1: Flat structure (pyproject.toml at collection dir)
    if (collection_dir / "pyproject.toml").exists():
        try:
            metadata = CollectionMetadata.from_pyproject(collection_dir / "pyproject.toml")
            return metadata.name
        except Exception as e:
            logger.debug(f"Could not read metadata from {collection_dir / 'pyproject.toml'}: {e}")

    # Strategy 2: Nested structure (pyproject.toml in package subdirectory)
    # Check immediate subdirectories
    try:
        for item in collection_dir.iterdir():
            if (
                item.is_dir()
                and not item.name.startswith(".")
                and not item.name.endswith(".dist-info")
                and (item / "pyproject.toml").exists()
            ):
                try:
                    metadata = CollectionMetadata.from_pyproject(item / "pyproject.toml")
                    return metadata.name
                except Exception as e:
                    logger.debug(f"Could not read metadata from {item / 'pyproject.toml'}: {e}")
                    continue
    except Exception as e:
        logger.debug(f"Error scanning {collection_dir}: {e}")

    # Fallback: Use directory name if metadata unreadable
    # This should not happen after app layer normalization, but defensive
    logger.warning(
        f"Could not read collection metadata from {collection_dir}, "
        f"falling back to directory name: {collection_dir.name}"
    )
    return collection_dir.name
