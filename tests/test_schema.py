"""Tests for CollectionMetadata schema."""

import tempfile
from pathlib import Path

import pytest
from amplifier_collections import CollectionMetadata
from pydantic import ValidationError


def test_from_pyproject_basic():
    """Test loading metadata from minimal pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        toml_path = Path(tmpdir) / "pyproject.toml"
        toml_path.write_text("""
[project]
name = "test-collection"
version = "1.0.0"
description = "Test collection"
""")

        metadata = CollectionMetadata.from_pyproject(toml_path)

        assert metadata.name == "test-collection"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test collection"
        assert metadata.author == ""
        assert metadata.capabilities == []
        assert metadata.requires == {}


def test_from_pyproject_with_amplifier_section():
    """Test loading metadata with amplifier collection section."""
    with tempfile.TemporaryDirectory() as tmpdir:
        toml_path = Path(tmpdir) / "pyproject.toml"
        toml_path.write_text("""
[project]
name = "advanced-collection"
version = "2.0.0"
description = "Advanced collection"

[project.urls]
homepage = "https://example.com"
repository = "https://github.com/org/collection"

[tool.amplifier.collection]
author = "Test Author"
capabilities = ["Feature A", "Feature B"]
requires = {foundation = "^1.0.0"}
""")

        metadata = CollectionMetadata.from_pyproject(toml_path)

        assert metadata.name == "advanced-collection"
        assert metadata.version == "2.0.0"
        assert metadata.author == "Test Author"
        assert metadata.capabilities == ["Feature A", "Feature B"]
        assert metadata.requires == {"foundation": "^1.0.0"}
        assert metadata.homepage == "https://example.com"
        assert metadata.repository == "https://github.com/org/collection"


def test_from_pyproject_missing_file():
    """Test error when pyproject.toml doesn't exist."""
    with pytest.raises(FileNotFoundError):
        CollectionMetadata.from_pyproject(Path("/nonexistent/pyproject.toml"))


def test_from_pyproject_missing_project_section():
    """Test error when [project] section missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        toml_path = Path(tmpdir) / "pyproject.toml"
        toml_path.write_text("[tool]\nvalue = 1")

        with pytest.raises(KeyError, match="\\[project\\] section missing"):
            CollectionMetadata.from_pyproject(toml_path)


def test_metadata_immutable():
    """Test that metadata is frozen (immutable)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        toml_path = Path(tmpdir) / "pyproject.toml"
        toml_path.write_text("""
[project]
name = "test"
version = "1.0.0"
""")

        metadata = CollectionMetadata.from_pyproject(toml_path)

        with pytest.raises(ValidationError):
            metadata.name = "modified"
