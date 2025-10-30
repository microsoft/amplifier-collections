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
