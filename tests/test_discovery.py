"""Tests for collection resource discovery."""

import tempfile
from pathlib import Path

from amplifier_collections import CollectionResources
from amplifier_collections import discover_collection_resources
from amplifier_collections import list_agents
from amplifier_collections import list_profiles


def test_discover_empty_collection():
    """Test discovering resources in empty collection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir)

        resources = discover_collection_resources(collection_path)

        assert resources.profiles == []
        assert resources.agents == []
        assert resources.context == []
        assert resources.scenario_tools == []
        assert resources.modules == []
        assert not resources.has_resources()


def test_discover_profiles():
    """Test discovering profile files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir)
        profiles_dir = collection_path / "profiles"
        profiles_dir.mkdir()

        (profiles_dir / "base.md").write_text("# Base profile")
        (profiles_dir / "advanced.md").write_text("# Advanced profile")

        resources = discover_collection_resources(collection_path)

        assert len(resources.profiles) == 2
        assert resources.profiles[0].name == "advanced.md"
        assert resources.profiles[1].name == "base.md"
        assert resources.has_resources()


def test_discover_agents():
    """Test discovering agent files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir)
        agents_dir = collection_path / "agents"
        agents_dir.mkdir()

        (agents_dir / "analyzer.md").write_text("# Analyzer")
        (agents_dir / "builder.md").write_text("# Builder")

        resources = discover_collection_resources(collection_path)

        assert len(resources.agents) == 2
        assert resources.agents[0].name == "analyzer.md"
        assert resources.agents[1].name == "builder.md"


def test_discover_context_recursive():
    """Test discovering context files recursively."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir)
        context_dir = collection_path / "context"
        context_dir.mkdir()
        subdir = context_dir / "patterns"
        subdir.mkdir()

        (context_dir / "intro.md").write_text("# Intro")
        (subdir / "design.md").write_text("# Design patterns")

        resources = discover_collection_resources(collection_path)

        assert len(resources.context) == 2
        # Sorted alphabetically
        names = [p.name for p in resources.context]
        assert "intro.md" in names
        assert "design.md" in names


def test_discover_scenario_tools():
    """Test discovering scenario tool directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir)
        tools_dir = collection_path / "scenario-tools"
        tools_dir.mkdir()

        # Valid tool (has pyproject.toml)
        tool1 = tools_dir / "analyzer"
        tool1.mkdir()
        (tool1 / "pyproject.toml").write_text("[project]\nname='analyzer'")

        # Invalid (no pyproject.toml)
        tool2 = tools_dir / "invalid"
        tool2.mkdir()

        resources = discover_collection_resources(collection_path)

        assert len(resources.scenario_tools) == 1
        assert resources.scenario_tools[0].name == "analyzer"


def test_discover_modules():
    """Test discovering module directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir)
        modules_dir = collection_path / "modules"
        modules_dir.mkdir()

        # Valid module
        mod1 = modules_dir / "hooks-custom"
        mod1.mkdir()
        (mod1 / "pyproject.toml").write_text("[project]\nname='hooks-custom'")

        resources = discover_collection_resources(collection_path)

        assert len(resources.modules) == 1
        assert resources.modules[0].name == "hooks-custom"


def test_list_profiles():
    """Test listing profile names."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir)
        profiles_dir = collection_path / "profiles"
        profiles_dir.mkdir()

        (profiles_dir / "base.md").write_text("# Base")
        (profiles_dir / "dev.md").write_text("# Dev")

        profile_names = list_profiles(collection_path)

        assert profile_names == ["base", "dev"]


def test_list_agents():
    """Test listing agent names."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir)
        agents_dir = collection_path / "agents"
        agents_dir.mkdir()

        (agents_dir / "analyzer.md").write_text("# Analyzer")
        (agents_dir / "builder.md").write_text("# Builder")

        agent_names = list_agents(collection_path)

        assert agent_names == ["analyzer", "builder"]


def test_resources_immutable():
    """Test that CollectionResources is frozen."""
    resources = CollectionResources(profiles=[], agents=[], context=[], scenario_tools=[], modules=[])

    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        resources.profiles = [Path("/new")]
