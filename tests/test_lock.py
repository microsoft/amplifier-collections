"""Tests for CollectionLock with injected lock path."""

import tempfile
from pathlib import Path

from amplifier_collections import CollectionLock


def test_lock_with_injected_path():
    """Test lock uses injected path (not hardcoded)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / "custom.lock"

        lock = CollectionLock(lock_path=lock_path)

        assert lock.lock_path == lock_path
        assert not lock_path.exists()  # Not created until first save


def test_add_and_get_entry():
    """Test adding and retrieving lock entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / "test.lock"
        lock = CollectionLock(lock_path=lock_path)

        # Add entry
        lock.add_entry(
            name="test-collection",
            source="git+https://github.com/org/test@main",
            commit="abc123",
            path=Path("/path/to/collection"),
        )

        # Retrieve entry
        entry = lock.get_entry("test-collection")
        assert entry is not None
        assert entry.name == "test-collection"
        assert entry.source == "git+https://github.com/org/test@main"
        assert entry.commit == "abc123"
        assert entry.path == "/path/to/collection"


def test_remove_entry():
    """Test removing lock entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / "test.lock"
        lock = CollectionLock(lock_path=lock_path)

        lock.add_entry(name="test", source="git://test", commit=None, path=Path("/test"))

        assert lock.is_installed("test")

        lock.remove_entry("test")

        assert not lock.is_installed("test")
        assert lock.get_entry("test") is None


def test_list_entries():
    """Test listing all lock entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / "test.lock"
        lock = CollectionLock(lock_path=lock_path)

        lock.add_entry(name="col1", source="src1", commit=None, path=Path("/col1"))
        lock.add_entry(name="col2", source="src2", commit="xyz", path=Path("/col2"))

        entries = lock.list_entries()

        assert len(entries) == 2
        names = [e.name for e in entries]
        assert "col1" in names
        assert "col2" in names


def test_lock_persistence():
    """Test that lock file persists across instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / "test.lock"

        # First instance
        lock1 = CollectionLock(lock_path=lock_path)
        lock1.add_entry(name="persistent", source="src", commit=None, path=Path("/test"))

        # Second instance (should load from file)
        lock2 = CollectionLock(lock_path=lock_path)

        assert lock2.is_installed("persistent")
        entry = lock2.get_entry("persistent")
        assert entry is not None  # Verify entry exists before accessing attributes
        assert entry.name == "persistent"
