# amplifier-collections

**Convention-based collection discovery and management for Amplifier applications**

amplifier-collections provides collection lifecycle management through filesystem conventions. Collections are git repositories with well-known directory structure (profiles/, agents/, context/, etc.). The library discovers resources by convention, resolves collection names to paths, manages installation, and tracks installed collections via lock files.

---

## Documentation

- **[Quick Start](#quick-start)** - Get started in 5 minutes with Python API
- **[API Reference](#api-reference)** - Complete Python API documentation
- **[User Guide](docs/USER_GUIDE.md)** - Using collections (end-user guide)
- **[Collection Authoring](docs/AUTHORING.md)** - Creating collections (author guide)
- **[Specification](docs/SPECIFICATION.md)** - Technical contracts and formats
- **[Design Philosophy](#design-philosophy)** - Library design decisions

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

**→ See [Specification](docs/SPECIFICATION.md) for complete technical contracts**

### Convention Over Configuration

Collections use **directory structure** to define resources (no manifest file required). The library auto-discovers profiles, agents, context, scenario tools, and modules by checking for well-known directories.

Profiles and agents must start with YAML front matter as described in the
[Specification](docs/SPECIFICATION.md#profile-and-agent-file-schema); configuration
inside code fences is ignored.

**See:** [Collection Structure Specification](docs/SPECIFICATION.md#collection-directory-structure)

### Search Path Precedence

Collections resolve using **first-match-wins** in precedence order:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PROJECT (highest)                                         │
│    .amplifier/collections/                                   │
│    → Workspace-specific, overrides everything               │
├─────────────────────────────────────────────────────────────┤
│ 2. USER                                                      │
│    ~/.amplifier/collections/                                │
│    → User-installed, overrides bundled                      │
├─────────────────────────────────────────────────────────────┤
│ 3. BUNDLED (lowest)                                          │
│    <app>/data/collections/                                   │
│    → Application-provided defaults                           │
└─────────────────────────────────────────────────────────────┘
```

Applications define search paths; library provides resolution mechanism.

**See:** [Search Path Specification](docs/SPECIFICATION.md#search-path-precedence) for complete algorithm

### Pluggable Installation Sources

The library coordinates installation but doesn't dictate **how** collections are fetched.

**See:** [InstallSourceProtocol Specification](docs/SPECIFICATION.md#installsourceprotocol) for complete contract.

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

**See:** [pyproject.toml Format Specification](docs/SPECIFICATION.md#pyprojecttoml-format) for complete field reference and validation rules.

> **Naming tip:** `[project].name` becomes the collection ID surfaced by the CLI.
> Use a concise slug such as `toolkit` or `design-intelligence` and avoid
> repository prefixes (`amplifier-collection-`). This ensures commands like
> `amplifier collection show <name>` match user expectations.

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

**See:** [Discovery Algorithm Specification](docs/SPECIFICATION.md#discovery-algorithm)

**Helper utilities** for getting just names:

```python
from amplifier_collections import list_profiles, list_agents

# Get profile names (without .md extension)
profile_names = list_profiles(Path("/path/to/collection"))
# Returns: ['base', 'foundation', 'production']

# Get agent names (without .md extension)
agent_names = list_agents(Path("/path/to/collection"))
# Returns: ['analyzer', 'optimizer']
```

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

**See:** [Lock File Format Specification](docs/SPECIFICATION.md#lock-file-format) for complete format details.

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
from amplifier_collections import install_collection, CollectionLock, CollectionInstallError
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

## Utilities

### extract_collection_name_from_path

```python
from amplifier_collections import extract_collection_name_from_path
from pathlib import Path

# Extract collection name from path containing "/collections/"
path = Path("~/.amplifier/collections/foundation/profiles/base.md")
name = extract_collection_name_from_path(path)
# Returns: "foundation" (reads from pyproject.toml)
```

**Purpose**: Extract collection metadata name from any path within a collection.

**Algorithm**:
1. Walk up from path to find `/collections/` component
2. Read collection root's `pyproject.toml`
3. Return `[project].name` field

**Used by**: amplifier-profiles for collection:name resolution

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

**See:** [Validation Rules Specification](docs/SPECIFICATION.md#validation-rules) for complete requirements.

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

Different applications need different installation mechanisms (CLI uses git, Web uses HTTP, Enterprise uses artifact servers, Air-gapped uses local mirrors).

By accepting any `InstallSourceProtocol` implementation, the library remains application-agnostic.

**See:** [Protocol Contracts Specification](docs/SPECIFICATION.md#protocol-contracts) for complete contract requirements.

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
