# amplifier-collections

**Convention-based collection discovery and management for Amplifier applications**

amplifier-collections provides collection lifecycle management through filesystem conventions. Collections are git repositories with well-known directory structure (profiles/, agents/, context/, etc.). The library discovers resources by convention, resolves collection names to paths, manages installation, and tracks installed collections via lock files.

---

## Installation

```bash
# From PyPI (when published)
uv pip install amplifier-collections

# From git (development)
uv pip install git+https://github.com/microsoft/amplifier-collections@main

# For local development
cd amplifier-collections
uv pip install -e .

# Or using uv sync for development with dependencies
uv sync --dev
```

---

## Quick Start

```python
from amplifier_collections import (
    CollectionResolver,
    discover_collection_resources,
    install_collection,
    CollectionLock,
)
from pathlib import Path

# Define search paths for your application
search_paths = [
    Path("/var/amplifier/system/collections"),  # Bundled (lowest)
    Path.home() / ".amplifier" / "collections",  # User
    Path(".amplifier/collections"),              # Project (highest)
]

# Create resolver
resolver = CollectionResolver(search_paths=search_paths)

# Resolve collection name to path
foundation_path = resolver.resolve("foundation")

# Discover resources
resources = discover_collection_resources(foundation_path)
print(f"Found {len(resources.profiles)} profiles")
print(f"Found {len(resources.agents)} agents")

# Install new collection
from amplifier_module_resolution import GitSource

lock = CollectionLock(lock_path=Path(".amplifier/collections.lock"))
source = GitSource("git+https://github.com/user/my-collection@v1.0.0")

await install_collection(
    source=source,
    target_dir=Path(".amplifier/collections/my-collection"),
    lock=lock
)
```

---

## What This Library Provides

### Convention Over Configuration

Collections use **directory structure** to define resources (no manifest file required):

```
my-collection/
  pyproject.toml          # Metadata (required)

  profiles/               # Auto-discovered if exists
    optimized.md
    debug.md

  agents/                 # Auto-discovered if exists
    analyzer.md
    optimizer.md

  context/                # Auto-discovered if exists
    patterns.md
    examples/
      example1.md

  scenario-tools/         # Auto-discovered if exists
    my_tool/
      main.py

  modules/                # Auto-discovered if exists
    hooks-custom/
      __init__.py

  README.md               # Collection documentation
```

**Discovery process**:
1. Check if `profiles/` directory exists → glob `*.md` files
2. Check if `agents/` directory exists → glob `*.md` files
3. Check if `context/` directory exists → glob `**/*.md` recursively
4. Check if `scenario-tools/` directory exists → glob `*/` directories
5. Check if `modules/` directory exists → glob `*/` directories

**No configuration file** listing resources - structure IS the configuration.

### Search Path Precedence

Collections resolve in precedence order (highest first):

1. **Project** (`.amplifier/collections/`) - Workspace-specific
2. **User** (`~/.amplifier/collections/`) - User-installed
3. **Bundled** (app-provided) - System collections

**Apps inject paths**; library resolves:

```python
# CLI paths
cli_paths = [
    Path(__file__).parent / "data" / "collections",  # Bundled
    Path.home() / ".amplifier" / "collections",      # User
    Path(".amplifier/collections"),                   # Project
]

# Web paths (different conventions)
web_paths = [
    Path("/var/amplifier/system/collections"),       # Bundled
    Path(f"/var/amplifier/workspaces/{workspace_id}/collections"),  # Project
]

resolver = CollectionResolver(search_paths=paths)
```

### Pluggable Installation Sources

The library coordinates installation but doesn't dictate **how** collections are fetched:

```python
from typing import Protocol

class InstallSourceProtocol(Protocol):
    """Interface for collection installation sources."""

    async def install_to(self, target_dir: Path) -> None:
        """Install collection content to target directory."""
        ...
```

**Standard implementations** (from amplifier-module-resolution):
- `GitSource` - Git repositories via uv
- `FileSource` - Local directories (development)

**Custom implementations** (apps can create):
- `HttpZipSource` - HTTP zip downloads
- `DatabaseBlobSource` - Database-stored collections
- `RegistrySource` - Corporate artifact servers

Apps provide implementation; library uses the protocol.

---

## API Reference

### Metadata

#### CollectionMetadata

```python
from amplifier_collections import CollectionMetadata
from pathlib import Path

class CollectionMetadata(BaseModel):
    """Collection metadata from pyproject.toml."""
    model_config = ConfigDict(frozen=True)

    # From [project] section
    name: str
    version: str
    description: str = ""

    # From [tool.amplifier.collection] section
    author: str = ""
    capabilities: list[str] = Field(default_factory=list)
    requires: dict[str, str] = Field(default_factory=dict)

    # From [project.urls] section
    homepage: str | None = None
    repository: str | None = None

# Load metadata from collection
metadata = CollectionMetadata.from_pyproject(
    Path("/path/to/collection/pyproject.toml")
)

print(f"{metadata.name} v{metadata.version}")
print(f"Author: {metadata.author}")
print(f"Capabilities: {', '.join(metadata.capabilities)}")
```

### Resolution

#### CollectionResolver

```python
from amplifier_collections import CollectionResolver
from pathlib import Path

class CollectionResolver:
    """Resolve collection names to filesystem paths."""

    def __init__(self, search_paths: list[Path]):
        """Initialize with app-specific search paths.

        Args:
            search_paths: Paths to search in precedence order (lowest to highest)
        """

# Create resolver
resolver = CollectionResolver(search_paths=[...])

# Resolve collection name to path
path = resolver.resolve("foundation")
# Returns: Path | None (highest precedence match, or None if not found)

# List all available collections
collections = resolver.list_collections()
# Returns: list[tuple[str, Path]] with precedence resolved
# Example: [("foundation", Path(...)), ("custom", Path(...))]
```

### Discovery

#### CollectionResources

```python
from amplifier_collections import CollectionResources, discover_collection_resources
from pathlib import Path

class CollectionResources(BaseModel):
    """Discovered resources in a collection."""
    model_config = ConfigDict(frozen=True)

    profiles: list[Path] = Field(default_factory=list)
    agents: list[Path] = Field(default_factory=list)
    context: list[Path] = Field(default_factory=list)
    scenario_tools: list[Path] = Field(default_factory=list)
    modules: list[Path] = Field(default_factory=list)

# Discover resources by convention
resources = discover_collection_resources(Path("/path/to/collection"))

# Access discovered resources
for profile in resources.profiles:
    print(f"Profile: {profile.name}")

for agent in resources.agents:
    print(f"Agent: {agent.name}")
```

**Discovery algorithm**:
- `profiles/`: `*.md` files
- `agents/`: `*.md` files
- `context/`: `**/*.md` recursively
- `scenario-tools/`: `*/` subdirectories
- `modules/`: `*/` subdirectories with `__init__.py`

### Installation

#### install_collection

```python
from amplifier_collections import install_collection, CollectionLock, CollectionInstallError
from amplifier_module_resolution import GitSource
from pathlib import Path

# Create installation source
source = GitSource("git+https://github.com/user/collection@v1.0.0")

# Create lock file manager
lock = CollectionLock(lock_path=Path(".amplifier/collections.lock"))

# Install collection
try:
    metadata = await install_collection(
        source=source,
        target_dir=Path(".amplifier/collections/my-collection"),
        lock=lock
    )
    print(f"Installed {metadata.name} v{metadata.version}")
except CollectionInstallError as e:
    print(f"Installation failed: {e.message}")
```

**Installation process**:
1. Source installs content to target directory
2. Validate `pyproject.toml` exists
3. Parse metadata
4. Discover resources
5. Add entry to lock file (if lock provided)

#### uninstall_collection

```python
from amplifier_collections import uninstall_collection

await uninstall_collection(
    collection_name="my-collection",
    collections_dir=Path(".amplifier/collections"),
    lock=lock
)
```

**Uninstallation process**:
1. Remove collection directory
2. Remove lock entry (if lock provided)

### Lock File Management

#### CollectionLock

```python
from amplifier_collections import CollectionLock, CollectionLockEntry
from pathlib import Path

class CollectionLock:
    """Manage collection lock file."""

    def __init__(self, lock_path: Path):
        """Initialize with lock file path."""

# Create lock manager
lock = CollectionLock(lock_path=Path(".amplifier/collections.lock"))

# Add entry (direct parameters - simpler than constructing object)
lock.add_entry(
    name="my-collection",
    source="git+https://github.com/user/my-collection@v1.0.0",
    commit="abc123def456",  # Git commit SHA (or None if not git)
    path=Path(".amplifier/collections/my-collection")
)

# Get entry
entry = lock.get_entry("my-collection")
if entry:
    print(f"Installed: {entry.installed_at}")
    print(f"Commit: {entry.commit}")

# List all entries
for entry in lock.list_entries():
    print(f"{entry.name} @ {entry.commit[:7]}")

# Remove entry
lock.remove_entry("my-collection")
```

---

## Usage Examples

### CLI Application

```python
from amplifier_collections import CollectionResolver, discover_collection_resources
from pathlib import Path

# CLI defines search paths
search_paths = [
    Path(__file__).parent / "data" / "collections",  # Bundled
    Path.home() / ".amplifier" / "collections",      # User
    Path(".amplifier/collections"),                   # Project
]

resolver = CollectionResolver(search_paths=search_paths)

# List available collections
for name, path in resolver.list_collections():
    metadata = CollectionMetadata.from_pyproject(path / "pyproject.toml")
    resources = discover_collection_resources(path)

    print(f"\n{name} v{metadata.version}")
    print(f"  Profiles: {len(resources.profiles)}")
    print(f"  Agents: {len(resources.agents)}")
    print(f"  Context files: {len(resources.context)}")

# Resolve specific collection
foundation = resolver.resolve("foundation")
if foundation:
    resources = discover_collection_resources(foundation)
    # Use resources...
```

### Web Application

```python
from amplifier_collections import CollectionResolver, discover_collection_resources

class WebCollectionService:
    """Web service for collection management."""

    def __init__(self, workspace_id: str):
        # Web-specific paths
        self.search_paths = [
            Path("/var/amplifier/system/collections"),
            Path(f"/var/amplifier/workspaces/{workspace_id}/collections"),
        ]
        self.resolver = CollectionResolver(search_paths=self.search_paths)

    async def get_collection_info(self, name: str) -> dict:
        """Get collection information for API response."""
        path = self.resolver.resolve(name)
        if not path:
            return {"error": "Collection not found"}

        metadata = CollectionMetadata.from_pyproject(path / "pyproject.toml")
        resources = discover_collection_resources(path)

        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "profiles": [p.stem for p in resources.profiles],
            "agents": [a.stem for a in resources.agents],
            "context_files": len(resources.context),
        }

    async def list_collections(self) -> list[dict]:
        """List all available collections."""
        results = []
        for name, path in self.resolver.list_collections():
            info = await self.get_collection_info(name)
            results.append(info)
        return results
```

### Custom Installation Source

```python
from amplifier_collections import install_collection, CollectionLock, InstallError
import httpx
import zipfile

class HttpZipSource:
    """HTTP zip download installation source."""

    def __init__(self, url: str):
        self.url = url

    async def install_to(self, target_dir: Path) -> None:
        """Download and extract zip to target."""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url)
            response.raise_for_status()

            # Write to temporary file
            temp_zip = target_dir.parent / f"{target_dir.name}.zip"
            temp_zip.write_bytes(response.content)

            # Extract to target
            with zipfile.ZipFile(temp_zip) as zf:
                zf.extractall(target_dir)

            # Cleanup
            temp_zip.unlink()

# Use custom source
lock = CollectionLock(lock_path=Path(".amplifier/collections.lock"))
source = HttpZipSource("https://cdn.example.com/collections/my-collection-v1.0.0.zip")

await install_collection(
    source=source,
    target_dir=Path(".amplifier/collections/my-collection"),
    lock=lock
)
```

### Testing

```python
from amplifier_collections import CollectionResolver, discover_collection_resources
from pathlib import Path
import tempfile

def test_collection_discovery():
    """Test collection resource discovery."""

    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir) / "test-collection"
        collection_path.mkdir()

        # Create test structure
        (collection_path / "profiles").mkdir()
        (collection_path / "profiles" / "test.md").write_text("# Test profile")

        (collection_path / "agents").mkdir()
        (collection_path / "agents" / "helper.md").write_text("# Test agent")

        # Discover resources
        resources = discover_collection_resources(collection_path)

        assert len(resources.profiles) == 1
        assert len(resources.agents) == 1
        assert resources.profiles[0].name == "test.md"
```

---

## Collection Metadata Format

### pyproject.toml

Collections declare metadata in standard Python packaging format:

```toml
[project]
name = "my-collection"                    # Required: Collection identifier
version = "1.0.0"                         # Required: Semantic version
description = "My expertise collection"   # Required: One-line description

[project.urls]
homepage = "https://docs.example.com"     # Optional: Documentation URL
repository = "https://github.com/..."     # Optional: Source repository

[tool.amplifier.collection]
author = "developer-name"                 # Optional: Creator name
capabilities = [                          # Optional: What this enables
    "What this collection enables",
    "What expertise it provides"
]
requires = {                              # Optional: Dependencies
    foundation = "^1.0.0",
    toolkit = "^1.2.0"
}
```

**Parsing**: Uses stdlib `tomllib` (Python 3.11+) with Pydantic validation.

### collections.lock

Lock file tracks installed collections:

```json
{
  "version": "1.0",
  "collections": {
    "my-collection": {
      "name": "my-collection",
      "source": "git+https://github.com/user/my-collection@v1.0.0",
      "commit": "abc123def456789...",
      "path": "/home/user/.amplifier/collections/my-collection",
      "installed_at": "2025-10-28T10:30:00Z"
    }
  }
}
```

**Format**: JSON for human readability and tool compatibility.

---

## API Reference

### CollectionResolver

```python
class CollectionResolver:
    """Resolve collection names to filesystem paths."""

    def __init__(self, search_paths: list[Path]):
        """Initialize with app-specific search paths.

        Args:
            search_paths: Paths to search in precedence order (lowest to highest)
                          Searches in REVERSE order (highest precedence first)
        """

    def resolve(self, collection_name: str) -> Path | None:
        """Resolve collection name to installation path.

        Searches search_paths in reverse order (highest precedence first).

        Args:
            collection_name: Name of collection (e.g., "foundation")

        Returns:
            Path to collection directory if found, None otherwise

        Example:
            >>> resolver = CollectionResolver(search_paths=[...])
            >>> path = resolver.resolve("foundation")
            >>> if path:
            ...     print(f"Found at {path}")
        """

    def list_collections(self) -> list[tuple[str, Path]]:
        """List all available collections with their paths.

        Deduplicates by name, keeping highest precedence path.

        Returns:
            List of (collection_name, path) tuples

        Example:
            >>> for name, path in resolver.list_collections():
            ...     print(f"{name}: {path}")
            foundation: /home/user/.amplifier/collections/foundation
            custom: .amplifier/collections/custom
        """
```

### Resource Discovery

```python
from amplifier_collections import CollectionResources, discover_collection_resources

class CollectionResources(BaseModel):
    """Discovered resources in a collection."""
    model_config = ConfigDict(frozen=True)

    profiles: list[Path] = Field(default_factory=list)
    agents: list[Path] = Field(default_factory=list)
    context: list[Path] = Field(default_factory=list)
    scenario_tools: list[Path] = Field(default_factory=list)
    modules: list[Path] = Field(default_factory=list)

def discover_collection_resources(collection_path: Path) -> CollectionResources:
    """Discover resources in collection by convention.

    Checks for well-known directories:
    - profiles/*.md
    - agents/*.md
    - context/**/*.md (recursive)
    - scenario-tools/*/
    - modules/*/ (with __init__.py or pyproject.toml)

    Args:
        collection_path: Path to collection root directory

    Returns:
        CollectionResources with discovered paths

    Example:
        >>> resources = discover_collection_resources(Path("my-collection"))
        >>> print(f"Profiles: {[p.stem for p in resources.profiles]}")
        Profiles: ['optimized', 'debug']
    """

def list_profiles(collection_path: Path) -> list[str]:
    """List profile names in collection (convenience helper).

    Args:
        collection_path: Path to collection directory

    Returns:
        List of profile names (without .md extension)

    Example:
        >>> profiles = list_profiles(Path("~/.amplifier/collections/foundation"))
        >>> print(profiles)
        ['base', 'foundation', 'production', 'test']
    """

def list_agents(collection_path: Path) -> list[str]:
    """List agent names in collection (convenience helper).

    Args:
        collection_path: Path to collection directory

    Returns:
        List of agent names (without .md extension)

    Example:
        >>> agents = list_agents(Path("~/.amplifier/collections/developer-expertise"))
        >>> print(agents)
        ['bug-hunter', 'modular-builder', 'researcher', 'zen-architect']
    """
```

### Utilities

```python
from amplifier_collections import extract_collection_name_from_path

def extract_collection_name_from_path(search_path: Path) -> str | None:
    """Extract collection metadata name from path containing /collections/.

    Reads pyproject.toml to get authoritative name (not directory name).
    Handles both flat and nested packaging structures.

    Args:
        search_path: Path containing "collections" component
                    (e.g., ~/.amplifier/collections/dir-name/profiles/)

    Returns:
        Collection metadata name (e.g., "design-intelligence")
        or None if not a collection path or metadata unreadable

    Example:
        >>> # Directory name may differ from metadata name
        >>> path = Path("~/.amplifier/collections/amplifier-collection-design-intelligence/profiles/")
        >>> extract_collection_name_from_path(path)
        'design-intelligence'  # From pyproject.toml, not directory name

        >>> # Non-collection path
        >>> path = Path("~/.amplifier/profiles/")
        >>> extract_collection_name_from_path(path)
        None

    Note:
        After app layer directory normalization, directory name should equal metadata name.
        This function is defensive and always reads metadata regardless.
    """
```

### Installation Management

```python
from amplifier_collections import install_collection, uninstall_collection, CollectionInstallError

async def install_collection(
    source: InstallSourceProtocol,
    target_dir: Path,
    lock: CollectionLock | None = None
) -> CollectionMetadata:
    """Install collection from source.

    Process:
    1. Source installs content to target_dir (via source.install_to)
    2. Validate pyproject.toml exists
    3. Parse metadata
    4. Discover resources
    5. Add entry to lock file (if lock provided)

    Args:
        source: Installation source implementing InstallSourceProtocol
        target_dir: Directory to install into (must not exist)
        lock: Optional lock file manager

    Returns:
        CollectionMetadata from installed collection

    Raises:
        CollectionInstallError: If installation fails at any step

    Example:
        >>> from amplifier_module_resolution import GitSource
        >>> source = GitSource("git+https://github.com/org/collection@v1.0.0")
        >>> metadata = await install_collection(source, target_dir, lock)
        >>> print(f"Installed {metadata.name}")
    """

async def uninstall_collection(
    collection_name: str,
    collections_dir: Path,
    lock: CollectionLock | None = None
) -> None:
    """Uninstall collection.

    Process:
    1. Remove collection directory
    2. Remove lock entry (if lock provided)

    Args:
        collection_name: Name of collection to remove
        collections_dir: Parent directory containing collections
        lock: Optional lock file manager

    Raises:
        CollectionInstallError: If uninstallation fails

    Example:
        >>> await uninstall_collection("my-collection", Path("..."), lock)
    """
```

### Lock File Management

```python
from amplifier_collections import CollectionLock, CollectionLockEntry
from dataclasses import dataclass

class CollectionLock:
    """Manage collection lock file."""

    def __init__(self, lock_path: Path):
        """Initialize with lock file path.

        Args:
            lock_path: Path to collections.lock file (app-specific)
        """

    def add_entry(
        self,
        name: str,
        source: str,
        commit: str | None,
        path: Path
    ) -> None:
        """Add or update collection entry.

        Args:
            name: Collection name
            source: Git source URI
            commit: Git commit SHA (None if not git)
            path: Installation path

        If collection already exists, updates it (overwrites).
        """

    def remove_entry(self, collection_name: str) -> None:
        """Remove collection entry.

        No-op if collection not in lock file.
        """

    def get_entry(self, collection_name: str) -> CollectionLockEntry | None:
        """Get collection entry by name.

        Returns:
            Entry if found, None otherwise
        """

    def list_entries(self) -> list[CollectionLockEntry]:
        """List all installed collections.

        Returns:
            List of all lock entries
        """

    def is_installed(self, name: str) -> bool:
        """Check if collection is in lock file.

        Args:
            name: Collection name

        Returns:
            True if collection is tracked
        """

@dataclass
class CollectionLockEntry:
    """Single entry in collection lock file."""

    name: str
    source: str
    commit: str | None  # Git commit SHA for reproducibility
    path: str           # Installation path as string (for JSON)
    installed_at: str   # ISO 8601 timestamp
```

---

## Error Handling

### Exceptions

```python
from amplifier_collections import (
    CollectionError,
    CollectionInstallError,
    CollectionMetadataError,
    CollectionNotFoundError,
)

# Base exception
class CollectionError(Exception):
    """Base exception for collection operations."""
    def __init__(self, message: str, context: dict | None = None):
        self.message = message
        self.context = context or {}

# Installation errors
class CollectionInstallError(CollectionError):
    """Collection installation failed."""

# Metadata errors
class CollectionMetadataError(CollectionError):
    """Invalid or missing collection metadata."""

# Not found errors
class CollectionNotFoundError(CollectionError):
    """Collection not found in search paths."""

# Usage
try:
    metadata = CollectionMetadata.from_pyproject(path / "pyproject.toml")
except CollectionMetadataError as e:
    print(f"Error: {e.message}")
    print(f"File: {e.context.get('file')}")
```

### Validation

**Required metadata**:
- `pyproject.toml` must exist
- `[project]` section must have: `name`, `version`, `description`

**Optional metadata**:
- `[tool.amplifier.collection]` section (validated if present)
- `[project.urls]` section (validated if present)

```python
# Invalid collection (missing pyproject.toml)
resources = discover_collection_resources(Path("/invalid/path"))
# Raises: CollectionMetadataError("Collection missing pyproject.toml")

# Invalid metadata (missing required field)
# Raises: CollectionMetadataError("Required field missing: name")
```

---

## Design Philosophy

### Mechanism, Not Policy

The library provides collection **mechanism**:
- **How** to discover resources (convention-based scanning)
- **How** to resolve names (search path precedence)
- **How** to install (coordinate source.install_to)
- **How** to track (lock file management)

Applications provide collection **policy**:
- **Where** to search (path conventions)
- **What** source type to use (git vs HTTP vs database)
- **When** to install (manual vs automatic)

### Convention Over Configuration

**Why no manifest file?**

**Alternative**: `collection.json` listing resources

```json
{
  "profiles": ["profiles/optimized.md", "profiles/debug.md"],
  "agents": ["agents/analyzer.md"]
}
```

**Problems**:
- Maintenance burden (must update manifest when adding files)
- Drift risk (manifest disagrees with filesystem)
- Duplication (manifest repeats what filesystem already shows)

**Solution**: Directory structure IS the configuration

**Benefits**:
- Self-documenting (ls shows what's available)
- Impossible to drift (scan always matches reality)
- Simpler (no extra file to maintain)

### Protocol-Based Installation

**Why InstallSourceProtocol?**

Different applications need different installation mechanisms:

| Application | Source Type | Mechanism |
|-------------|-------------|-----------|
| CLI | Git repositories | uv pip install from git |
| Web | HTTP zip files | Download + extract |
| Enterprise | Artifact server | Corporate registry API |
| Air-gapped | Local mirror | File copy from cache |

By accepting any `InstallSourceProtocol` implementation, the library remains application-agnostic.

---

## Dependencies

### Runtime

**Required**:
- pydantic >=2.0 (metadata validation, frozen models)
- Python >=3.11 (stdlib: tomllib, pathlib, json)

**Optional** (via protocols):
- Collection installation source (app provides)

### Development

- pytest >=8.0
- pytest-asyncio (async test support)

**Philosophy**: Minimal runtime dependencies (pydantic only, stdlib otherwise) with protocol-based integration for optional features.

---

## Testing

### Running Tests

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Or using uv sync
uv sync --dev

# Run tests
pytest

# Run with coverage
pytest --cov=amplifier_collections --cov-report=html
```

### Test Coverage

The library includes comprehensive tests:

- **Unit tests**: Metadata parsing, resource discovery, path resolution
- **Integration tests**: Install/uninstall with mock sources, multi-scope resolution
- **Protocol tests**: Mock InstallSourceProtocol, verify any source works
- **Edge cases**: Missing metadata, empty collections, invalid structures

Target coverage: >90%

---

## Design Decisions

### Why Frozen Pydantic Models?

```python
class CollectionMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
```

**Benefit**: Immutability prevents accidental modification, clearer data flow
**Trade-off**: Create new instances to change (worth it for safety)

### Why Lock File?

**Alternative**: No tracking of installed collections

**Problem**: Can't list what's installed, can't uninstall, can't detect versions

**Solution**: JSON lock file with installation metadata

**Benefits**:
- Know what's installed, when, from where
- Support uninstallation
- Enable reproducibility
- Track source for updates

### Why Dependency Declaration Without Resolution?

**Current**: Parse `requires` field, don't install recursively

**Rationale**: YAGNI - manual dependency installation sufficient initially

**Future**: Add recursive installation after proving the need

---

## Philosophy Compliance

### Kernel Philosophy ✅

**"Mechanism, not policy"**:
- ✅ Library: How to discover/install collections (mechanism)
- ✅ App: Where to search, which source type to use (policy)

**"Extensibility through composition"**:
- ✅ Custom sources via InstallSourceProtocol (not config flags)
- ✅ Search paths injectable (not hardcoded)

**"Text-first, inspectable surfaces"**:
- ✅ pyproject.toml (standard Python packaging)
- ✅ collections.lock (JSON, human-readable)
- ✅ Convention-based directories (self-documenting)

### Ruthless Simplicity ✅

**No caching**: Directory scans on demand
- YAGNI - File I/O fast enough
- Add if profiling shows bottleneck

**No dependency resolution**: Parse requirements, don't auto-install
- YAGNI - Manual installation sufficient
- Add recursive install if proven needed

**No version constraint validation**: Record versions, don't validate
- YAGNI - Constraint checking not needed yet
- Add semver validation if conflicts occur

**Convention over configuration**: No manifest file
- Simpler than maintaining separate config
- Self-documenting structure

---

## Future Enhancements

**Only add when proven needed through real usage**:

### Scenario Tool Installation
- **Add when**: Users request automatic scenario tool installation
- **Add how**: Run `uv tool install` for each discovered scenario tool
- **Why not now**: YAGNI - apps can handle if needed (policy), library focuses on discovery (mechanism)

### Dependency Resolution
- **Add when**: Users request automatic dependency installation
- **Add how**: Recursive install with cycle detection

### Version Constraint Validation
- **Add when**: Version conflicts cause real problems
- **Add how**: Semver parsing and constraint checking

### Resource Caching
- **Add when**: Performance profiling shows resolution bottleneck
- **Add how**: Simple dict cache with invalidation

### Built-in HTTP Source
- **Add when**: Multiple apps request HTTP installation
- **Add how**: Add HttpZipSource to library

**Current approach**: YAGNI - ship minimal, grow based on evidence.

---

## Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

---

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
