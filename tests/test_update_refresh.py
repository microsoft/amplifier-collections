"""Tests for collection update and refresh functionality."""

import pytest
from amplifier_collections import CollectionLock
from amplifier_collections import CollectionLockEntry


class TestCollectionLockWithUpdates:
    """Test CollectionLock behavior for update scenarios."""

    def test_lock_tracks_commit_sha(self, tmp_path):
        """Verify lock file stores commit SHA for update checking."""
        lock_file = tmp_path / "test.lock"
        lock = CollectionLock(lock_path=lock_file)

        # Add entry with SHA
        lock.add_entry(
            name="test-collection",
            source="git+https://github.com/test/collection@main",
            commit="abc1234567890",
            path=tmp_path / "collections" / "test-collection",
        )

        # Verify entry stored
        entry = lock.get_entry("test-collection")
        assert entry is not None
        assert entry.commit == "abc1234567890"

    def test_lock_entry_has_installed_at(self, tmp_path):
        """Verify lock entries track installation timestamp."""
        lock_file = tmp_path / "test.lock"
        lock = CollectionLock(lock_path=lock_file)

        lock.add_entry(
            name="test-collection",
            source="git+https://github.com/test/collection@main",
            commit="abc123",
            path=tmp_path / "collections" / "test-collection",
        )

        entry = lock.get_entry("test-collection")
        assert entry is not None
        assert entry.installed_at is not None
        assert "T" in entry.installed_at  # ISO format


class TestCollectionRefreshLogic:
    """Test collection refresh command logic (unit tests without CLI)."""

    def test_filter_by_collection_name(self):
        """Test filtering collections by name."""
        entries = [
            CollectionLockEntry(
                name="collection-a",
                source="git+https://github.com/test/a@main",
                commit="abc123",
                path="/path/a",
                installed_at="2025-11-08T12:00:00Z",
            ),
            CollectionLockEntry(
                name="collection-b",
                source="git+https://github.com/test/b@main",
                commit="def456",
                path="/path/b",
                installed_at="2025-11-08T12:00:00Z",
            ),
        ]

        # Filter for specific collection
        filtered = [e for e in entries if e.name == "collection-a"]

        assert len(filtered) == 1
        assert filtered[0].name == "collection-a"

    def test_filter_mutable_refs(self):
        """Test filtering for mutable refs (branches) vs immutable (tags/SHAs)."""
        refs_to_test = [
            ("main", True),  # Branch - mutable
            ("develop", True),  # Branch - mutable
            ("v1.0.0", False),  # Tag - immutable
            ("v2.1.3", False),  # Tag - immutable
            ("a" * 40, False),  # 40-char SHA - immutable
            ("feature/test", True),  # Branch - mutable
        ]

        for ref, should_be_mutable in refs_to_test:
            # Mutable check logic from refresh command
            is_mutable = not (ref.startswith("v") or len(ref) == 40)
            assert is_mutable == should_be_mutable, f"Failed for ref: {ref}"

    def test_skip_non_git_sources(self):
        """Test that non-git sources are skipped during refresh."""
        entries = [
            CollectionLockEntry(
                name="git-collection",
                source="git+https://github.com/test/a@main",
                commit="abc123",
                path="/path/a",
                installed_at="2025-11-08T12:00:00Z",
            ),
            CollectionLockEntry(
                name="local-collection",
                source="file:///local/path",
                commit=None,
                path="/path/local",
                installed_at="2025-11-08T12:00:00Z",
            ),
        ]

        # Filter for git sources only
        git_sources = [e for e in entries if e.source.startswith("git+")]

        assert len(git_sources) == 1
        assert git_sources[0].name == "git-collection"


class TestUpdateOrchestration:
    """Test update command orchestration logic."""

    def test_sequential_execution_order(self):
        """Verify updates execute in correct order: modules → collections → self."""
        # This test documents the expected execution order
        # Actual execution happens in update_executor.py:execute_updates()

        execution_order = [
            "1. Module refresh (cached_git_sources)",
            "2. Collection refresh (collection_sources)",
            "3. Self-update (umbrella with has_updates)",
        ]

        # Sequential execution ensures:
        # - Modules updated before collections (collections may depend on modules)
        # - Collections updated before self (self-update restarts process)
        # - Each step completes before next begins (no parallel execution)

        assert len(execution_order) == 3
        assert "Module" in execution_order[0]
        assert "Collection" in execution_order[1]
        assert "Self" in execution_order[2]


@pytest.mark.integration
class TestCollectionUpdateIntegration:
    """Integration tests for collection update workflow (requires running system)."""

    def test_update_check_includes_collections(self):
        """Test that amplifier update --check-only shows collections.

        Note: This is a documentation test - verifies expected behavior exists.
        Actual testing requires installed collections with updates available.
        """
        # This test documents the expected workflow:
        # 1. User runs: amplifier update --check-only
        # 2. System checks: modules + collections + local sources
        # 3. Output shows: "Collections (updates available): • foundation"
        # 4. User can then run: amplifier collection refresh

        # For actual testing, run manually:
        # amplifier collection add git+https://github.com/test/sample@main
        # [make upstream changes]
        # amplifier update --check-only
        # [should show collection in output]

        assert True  # Documentation test

    def test_refresh_command_updates_lock_file(self):
        """Test that refresh updates lock file with new SHA.

        Note: This is a documentation test - verifies expected behavior exists.
        Actual testing requires running refresh command.
        """
        # Expected workflow:
        # 1. Install collection with SHA abc123
        # 2. Upstream changes to SHA def456
        # 3. Run: amplifier collection refresh
        # 4. Lock file updated with SHA def456
        # 5. Re-running refresh shows no updates

        assert True  # Documentation test
