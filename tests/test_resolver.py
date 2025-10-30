"""Tests for CollectionResolver with injected paths."""

import tempfile
from pathlib import Path

from amplifier_collections import CollectionResolver


def test_resolver_with_injected_paths():
    """Test resolver uses injected search paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create search paths
        bundled = base / "bundled"
        user = base / "user"
        project = base / "project"

        for path in [bundled, user, project]:
            path.mkdir()

        # Create collections in different locations
        (bundled / "foundation").mkdir()
        (bundled / "foundation" / "pyproject.toml").write_text("[project]\nname='foundation'\nversion='1.0.0'")

        (user / "custom").mkdir()
        (user / "custom" / "pyproject.toml").write_text("[project]\nname='custom'\nversion='1.0.0'")

        # Test with injected paths (bundled → user → project precedence)
        resolver = CollectionResolver(search_paths=[bundled, user, project])

        # Should find foundation in bundled
        foundation_path = resolver.resolve("foundation")
        assert foundation_path is not None
        assert foundation_path.name == "foundation"

        # Should find custom in user
        custom_path = resolver.resolve("custom")
        assert custom_path is not None
        assert custom_path.name == "custom"

        # Should not find nonexistent
        assert resolver.resolve("nonexistent") is None


def test_resolver_precedence():
    """Test that higher precedence paths override lower."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        bundled = base / "bundled"
        user = base / "user"

        bundled.mkdir()
        user.mkdir()

        # Create same collection in both locations (different versions)
        (bundled / "test-col").mkdir()
        (bundled / "test-col" / "pyproject.toml").write_text(
            "[project]\nname='test-col'\nversion='1.0.0'\ndescription='Bundled'"
        )

        (user / "test-col").mkdir()
        (user / "test-col" / "pyproject.toml").write_text(
            "[project]\nname='test-col'\nversion='2.0.0'\ndescription='User'"
        )

        # Resolver with [bundled, user] - user has higher precedence
        resolver = CollectionResolver(search_paths=[bundled, user])

        # Should resolve to user version (higher precedence)
        path = resolver.resolve("test-col")
        assert path is not None
        assert path.parent.name == "user"


def test_list_collections():
    """Test listing all collections with deduplication."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        bundled = base / "bundled"
        user = base / "user"

        bundled.mkdir()
        user.mkdir()

        # Bundled collections
        (bundled / "foundation").mkdir()
        (bundled / "foundation" / "pyproject.toml").write_text("[project]\nname='foundation'\nversion='1.0.0'")

        # User collections (including override of foundation)
        (user / "foundation").mkdir()
        (user / "foundation" / "pyproject.toml").write_text("[project]\nname='foundation'\nversion='2.0.0'")

        (user / "custom").mkdir()
        (user / "custom" / "pyproject.toml").write_text("[project]\nname='custom'\nversion='1.0.0'")

        resolver = CollectionResolver(search_paths=[bundled, user])

        collections = resolver.list_collections()

        # Should have 2 collections (foundation deduplicated to user version)
        assert len(collections) == 2
        names = [name for name, path in collections]
        assert "foundation" in names
        assert "custom" in names

        # Foundation should be from user (higher precedence)
        foundation_entry = [path for name, path in collections if name == "foundation"][0]
        assert foundation_entry.parent.name == "user"


def test_resolver_ignores_nonexistent_paths():
    """Test that resolver handles nonexistent search paths gracefully."""
    nonexistent = Path("/nonexistent/path")
    resolver = CollectionResolver(search_paths=[nonexistent])

    # Should not crash
    assert resolver.resolve("anything") is None
    assert resolver.list_collections() == []


def test_resolver_nested_structure():
    """Test resolver handles nested package structure from pip install."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create nested structure (as pip install creates)
        # Collection name: my-collection
        # Package name: my_collection (hyphens → underscores)
        collection_dir = base / "collections" / "my-collection"
        package_dir = collection_dir / "my_collection"
        package_dir.mkdir(parents=True)

        # pyproject.toml in package directory (nested)
        (package_dir / "pyproject.toml").write_text("[project]\nname='my-collection'\nversion='1.0.0'")

        # Create resources in package directory
        (package_dir / "profiles").mkdir()
        (package_dir / "profiles" / "test.md").write_text("# Test profile")

        resolver = CollectionResolver(search_paths=[base / "collections"])

        # Should find collection in nested structure
        found = resolver.resolve("my-collection")
        assert found is not None
        assert found == package_dir  # Points to package directory
        assert (found / "pyproject.toml").exists()


def test_resolver_flat_vs_nested_precedence():
    """Test that flat structure takes precedence over nested when both exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        collection_dir = base / "collections" / "test-col"

        # Create both flat and nested structures
        collection_dir.mkdir(parents=True)

        # Flat structure at root
        (collection_dir / "pyproject.toml").write_text("[project]\nname='test-col'\nversion='1.0.0'")

        # Nested structure in package subdir
        package_dir = collection_dir / "test_col"
        package_dir.mkdir()
        (package_dir / "pyproject.toml").write_text("[project]\nname='test-col'\nversion='2.0.0'")

        resolver = CollectionResolver(search_paths=[base / "collections"])

        # Should prefer flat structure
        found = resolver.resolve("test-col")
        assert found is not None
        assert found == collection_dir  # Not the nested one


def test_resolver_hyphen_to_underscore_conversion():
    """Test that resolver handles hyphen to underscore package name conversion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Collection with hyphens: design-intelligence
        # Package with underscores: design_intelligence
        collection_dir = base / "collections" / "design-intelligence"
        package_dir = collection_dir / "design_intelligence"
        package_dir.mkdir(parents=True)

        (package_dir / "pyproject.toml").write_text("[project]\nname='design-intelligence'\nversion='1.0.0'")

        resolver = CollectionResolver(search_paths=[base / "collections"])

        # Should find using hyphen name
        found = resolver.resolve("design-intelligence")
        assert found is not None
        assert found == package_dir
        assert (found / "pyproject.toml").exists()


def test_list_collections_mixed_structures():
    """Test listing collections with mixed flat and nested structures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        collections_path = base / "collections"
        collections_path.mkdir()

        # Flat structure collection
        flat_col = collections_path / "flat-collection"
        flat_col.mkdir()
        (flat_col / "pyproject.toml").write_text("[project]\nname='flat-collection'\nversion='1.0.0'")

        # Nested structure collection
        nested_col = collections_path / "nested-collection"
        nested_pkg = nested_col / "nested_collection"
        nested_pkg.mkdir(parents=True)
        (nested_pkg / "pyproject.toml").write_text("[project]\nname='nested-collection'\nversion='1.0.0'")

        resolver = CollectionResolver(search_paths=[collections_path])

        collections = resolver.list_collections()

        # Should find both
        assert len(collections) == 2
        names = [name for name, path in collections]
        assert "flat-collection" in names
        assert "nested-collection" in names

        # Verify paths point to collection roots
        flat_entry = [path for name, path in collections if name == "flat-collection"][0]
        assert flat_entry == flat_col

        nested_entry = [path for name, path in collections if name == "nested-collection"][0]
        assert nested_entry == nested_pkg  # Points to nested location


def test_resolver_directory_name_differs_from_metadata():
    """Test resolver finds collections when directory name differs from metadata name.

    Real-world case: repo "amplifier-collection-design-intelligence"
                     but metadata name "design-intelligence"
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Directory name has prefix, metadata name doesn't
        repo_dir = base / "collections" / "amplifier-collection-design-intelligence"
        repo_dir.mkdir(parents=True)

        # Flat structure with mismatched name
        (repo_dir / "pyproject.toml").write_text("[project]\nname='design-intelligence'\nversion='1.0.0'")

        resolver = CollectionResolver(search_paths=[base / "collections"])

        # Should find by metadata name, not directory name
        found = resolver.resolve("design-intelligence")
        assert found is not None
        assert found == repo_dir
        assert (found / "pyproject.toml").exists()


def test_resolver_nested_with_mismatched_directory_name():
    """Test resolver finds nested collections with mismatched directory names."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Repo directory name differs from metadata
        repo_dir = base / "collections" / "amplifier-collection-design-intelligence"
        package_dir = repo_dir / "design_intelligence"
        package_dir.mkdir(parents=True)

        (package_dir / "pyproject.toml").write_text("[project]\nname='design-intelligence'\nversion='1.0.0'")

        resolver = CollectionResolver(search_paths=[base / "collections"])

        # Should find by metadata name via slow path
        found = resolver.resolve("design-intelligence")
        assert found is not None
        assert found == package_dir


def test_list_collections_returns_metadata_names():
    """Verify list_collections() returns metadata names, not directory names."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        collections_path = base / "collections"
        collections_path.mkdir()

        # Create collection with mismatched names
        # Directory: amplifier-collection-test
        # Metadata: test-collection
        collection_dir = collections_path / "amplifier-collection-test"
        collection_dir.mkdir()
        (collection_dir / "pyproject.toml").write_text(
            """[project]
name = "test-collection"
version = "1.0.0"
"""
        )

        resolver = CollectionResolver(search_paths=[collections_path])
        collections = resolver.list_collections()

        # Should return metadata name, not directory name
        assert len(collections) == 1
        name, path = collections[0]
        assert name == "test-collection"  # Metadata name
        assert "amplifier-collection-test" not in name  # Not directory name
