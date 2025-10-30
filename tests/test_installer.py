"""Tests for collection installer (protocol-based)."""

import tempfile
from pathlib import Path

import pytest
from amplifier_collections import CollectionInstallError
from amplifier_collections import CollectionLock
from amplifier_collections import install_collection
from amplifier_collections import uninstall_collection


class MockSource:
    """Mock installation source for testing."""

    def __init__(self, collection_name: str, create_pyproject: bool = True):
        self.collection_name = collection_name
        self.create_pyproject = create_pyproject
        self.uri = f"mock://{collection_name}"
        self.commit_sha = "abc123def456"

    async def install_to(self, target_dir: Path) -> None:
        """Mock installation - creates directory with pyproject.toml."""
        target_dir.mkdir(parents=True, exist_ok=True)

        if self.create_pyproject:
            pyproject = target_dir / "pyproject.toml"
            pyproject.write_text(f"""
[project]
name = "{self.collection_name}"
version = "1.0.0"
description = "Test collection"
""")


@pytest.mark.asyncio
async def test_install_collection_basic():
    """Test basic collection installation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "my-collection"
        source = MockSource("my-collection")

        metadata = await install_collection(source=source, target_dir=target_dir)

        assert metadata.name == "my-collection"
        assert metadata.version == "1.0.0"
        assert target_dir.exists()
        assert (target_dir / "pyproject.toml").exists()


@pytest.mark.asyncio
async def test_install_collection_with_lock():
    """Test installation updates lock file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "test-col"
        lock_path = Path(tmpdir) / "test.lock"
        lock = CollectionLock(lock_path=lock_path)

        source = MockSource("test-col")

        await install_collection(source=source, target_dir=target_dir, lock=lock)

        # Check lock file
        assert lock.is_installed("test-col")
        entry = lock.get_entry("test-col")
        assert entry is not None  # Verify entry exists before accessing attributes
        assert entry.name == "test-col"
        assert entry.source == "mock://test-col"
        assert entry.commit == "abc123def456"


@pytest.mark.asyncio
async def test_install_collection_missing_pyproject():
    """Test error when collection has no pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "invalid"
        source = MockSource("invalid", create_pyproject=False)

        with pytest.raises(CollectionInstallError, match="No pyproject.toml found"):
            await install_collection(source=source, target_dir=target_dir)


@pytest.mark.asyncio
async def test_uninstall_collection():
    """Test collection uninstallation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a collection
        collections_dir = Path(tmpdir) / "collections"
        collections_dir.mkdir()
        collection_path = collections_dir / "test-col"
        collection_path.mkdir()
        (collection_path / "pyproject.toml").write_text("[project]\nname='test-col'\nversion='1.0.0'")

        # Uninstall
        await uninstall_collection(collection_name="test-col", collections_dir=collections_dir)

        assert not collection_path.exists()


@pytest.mark.asyncio
async def test_uninstall_collection_with_lock():
    """Test uninstallation removes lock entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collections_dir = Path(tmpdir) / "collections"
        collections_dir.mkdir()
        collection_path = collections_dir / "test-col"
        collection_path.mkdir()
        (collection_path / "pyproject.toml").write_text("[project]\nname='test-col'\nversion='1.0.0'")

        lock_path = Path(tmpdir) / "test.lock"
        lock = CollectionLock(lock_path=lock_path)
        lock.add_entry(name="test-col", source="src", commit=None, path=collection_path)

        await uninstall_collection(collection_name="test-col", collections_dir=collections_dir, lock=lock)

        assert not lock.is_installed("test-col")


@pytest.mark.asyncio
async def test_uninstall_nonexistent_collection():
    """Test error when uninstalling nonexistent collection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collections_dir = Path(tmpdir)

        with pytest.raises(CollectionInstallError, match="not found"):
            await uninstall_collection(collection_name="nonexistent", collections_dir=collections_dir)


def test_find_collection_root_flat_structure():
    """Test _find_collection_root with flat structure."""
    from amplifier_collections.installer import _find_collection_root  # type: ignore

    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "my-collection"
        target_dir.mkdir()
        (target_dir / "pyproject.toml").write_text("[project]\nname='my-collection'")

        root = _find_collection_root(target_dir)
        assert root == target_dir


def test_find_collection_root_nested_structure():
    """Test _find_collection_root with nested pip install structure."""
    from amplifier_collections.installer import _find_collection_root  # type: ignore

    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "my-collection"
        package_dir = target_dir / "my_collection"
        package_dir.mkdir(parents=True)
        (package_dir / "pyproject.toml").write_text("[project]\nname='my-collection'")

        root = _find_collection_root(target_dir)
        assert root == package_dir  # Points to nested location


def test_find_collection_root_not_found():
    """Test _find_collection_root returns None when pyproject.toml missing."""
    from amplifier_collections.installer import _find_collection_root  # type: ignore

    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "empty"
        target_dir.mkdir()

        root = _find_collection_root(target_dir)
        assert root is None


class MockNestedSource:
    """Mock source that creates nested package structure like pip install."""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.uri = f"mock://{collection_name}"
        self.commit_sha = "nested123"

    async def install_to(self, target_dir: Path) -> None:
        """Create nested structure: target_dir/pkg_name/pyproject.toml."""
        package_name = self.collection_name.replace("-", "_")
        package_dir = target_dir / package_name
        package_dir.mkdir(parents=True, exist_ok=True)

        (package_dir / "pyproject.toml").write_text(
            f"""
[project]
name = "{self.collection_name}"
version = "2.0.0"
description = "Nested test collection"
"""
        )


@pytest.mark.asyncio
async def test_install_collection_nested_structure():
    """Test installer handles nested package structure from pip install."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "design-intelligence"
        source = MockNestedSource("design-intelligence")

        metadata = await install_collection(source=source, target_dir=target_dir)

        # Should handle nested structure
        assert metadata.name == "design-intelligence"
        assert metadata.version == "2.0.0"

        # pyproject.toml should be in package subdirectory
        package_dir = target_dir / "design_intelligence"
        assert (package_dir / "pyproject.toml").exists()
