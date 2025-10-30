"""Tests for collection utilities."""

import tempfile
from pathlib import Path

from amplifier_collections.utils import extract_collection_name_from_path


def test_extract_collection_name_flat_structure():
    """Extract metadata name from flat collection structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create flat structure
        collection_dir = Path(tmpdir) / "collections" / "amplifier-collection-test"
        collection_dir.mkdir(parents=True)

        (collection_dir / "pyproject.toml").write_text(
            """[project]
name = "test-collection"
version = "1.0.0"
"""
        )

        profiles_dir = collection_dir / "profiles"
        profiles_dir.mkdir()

        # Extract from profiles search path
        name = extract_collection_name_from_path(profiles_dir)

        # Should return metadata name, not directory name
        assert name == "test-collection"


def test_extract_collection_name_nested_structure():
    """Extract metadata name from nested pip install structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create nested structure (as uv pip install creates)
        collection_dir = Path(tmpdir) / "collections" / "amplifier-collection-test"
        package_dir = collection_dir / "test_collection"
        package_dir.mkdir(parents=True)

        (package_dir / "pyproject.toml").write_text(
            """[project]
name = "test-collection"
version = "1.0.0"
"""
        )

        profiles_dir = package_dir / "profiles"
        profiles_dir.mkdir()

        # Extract from nested profiles search path
        name = extract_collection_name_from_path(profiles_dir)

        assert name == "test-collection"


def test_extract_collection_name_hybrid_packaging():
    """Extract name when resources at parent, pyproject in package."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_dir = Path(tmpdir) / "collections" / "test-dir"
        package_dir = collection_dir / "test_package"
        package_dir.mkdir(parents=True)

        (package_dir / "pyproject.toml").write_text(
            """[project]
name = "test-name"
version = "1.0.0"
"""
        )

        # Resources at parent
        profiles_dir = collection_dir / "profiles"
        profiles_dir.mkdir()

        # Extract from parent-level profiles
        name = extract_collection_name_from_path(profiles_dir)

        assert name == "test-name"


def test_extract_collection_name_not_collection_path():
    """Return None for paths not under collections/."""
    path = Path("/tmp/random/profiles")
    name = extract_collection_name_from_path(path)
    assert name is None


def test_extract_collection_name_fallback_to_directory():
    """Fallback to directory name if metadata unreadable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_dir = Path(tmpdir) / "collections" / "test-dir"
        profiles_dir = collection_dir / "profiles"
        profiles_dir.mkdir(parents=True)

        # No pyproject.toml - should fallback
        name = extract_collection_name_from_path(profiles_dir)

        # Should return directory name as fallback
        assert name == "test-dir"


def test_extract_collection_name_from_agents_dir():
    """Extract works from agents directory too."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_dir = Path(tmpdir) / "collections" / "my-collection"
        collection_dir.mkdir(parents=True)

        (collection_dir / "pyproject.toml").write_text(
            """[project]
name = "metadata-name"
version = "1.0.0"
"""
        )

        agents_dir = collection_dir / "agents"
        agents_dir.mkdir()

        # Extract from agents search path
        name = extract_collection_name_from_path(agents_dir)

        assert name == "metadata-name"


def test_extract_collection_name_from_deep_nested_path():
    """Extract from deeply nested paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_dir = Path(tmpdir) / "collections" / "repo-name"
        collection_dir.mkdir(parents=True)

        (collection_dir / "pyproject.toml").write_text(
            """[project]
name = "actual-name"
version = "1.0.0"
"""
        )

        # Deep nested path
        deep_path = collection_dir / "context" / "subdir" / "file.md"
        deep_path.parent.mkdir(parents=True)

        # Should walk up and find collection root
        name = extract_collection_name_from_path(deep_path)

        assert name == "actual-name"
