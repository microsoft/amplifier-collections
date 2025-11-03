---
last_updated: 2025-10-31
status: stable
audience: developers, collection-authors
---

# Collection Format Specification

**Technical contracts for collection structure, metadata, and discovery**

This document defines the authoritative specification for collection format. All collections MUST conform to these contracts. Collection authors and application developers reference this as the source of truth.

---

## Collection Directory Structure

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
      pyproject.toml

  modules/                # Auto-discovered if exists
    hooks-custom/
      __init__.py
      pyproject.toml

  README.md               # Collection documentation (recommended)
```

**Convention over configuration**: No manifest file lists resources. Structure IS the configuration.

---

## Package Structure for Installation

Collections are distributed as Python packages. When installed via `uv pip install` the resulting directory under `.amplifier/collections/<collection-name>/` MUST contain:

```
<collection-name>/
  agents/ …
  profiles/ …
  context/ …
  scenario-tools/ …
  templates/ …
  docs/ …

  <python_package>/              # project.name with hyphens → underscores
    __init__.py
    pyproject.toml               # runtime metadata copy

  *.dist-info/                   # pip-generated metadata
```

Implementation requirements:

1. **Root `pyproject.toml`** uses `setuptools` (or equivalent PEP 517 builder) so the project can be installed with `uv`/`pip`.
2. **Python package directory** named `project.name.replace('-', '_')` with minimal `__init__.py` and an embedded copy of `pyproject.toml`. The CLI reads this file after installation to recover metadata.
3. **MANIFEST.in** (or build backend equivalent) must include resource directories (`profiles/`, `agents/`, `context/`, `scenario-tools/`, `templates/`, `docs/`) plus metadata files so wheels contain the same layout as the source tree.

Collections MUST NOT rely on post-install git operations—installations are purely pip/uv driven.

---

## Discovery Algorithm

The amplifier-collections library discovers resources using filesystem conventions:

1. **Check `profiles/` exists** → glob `*.md` files (non-recursive)
2. **Check `agents/` exists** → glob `*.md` files (non-recursive)
3. **Check `context/` exists** → glob `**/*.md` files (recursive)
4. **Check `scenario-tools/` exists** → glob `*/` subdirectories
5. **Check `modules/` exists** → glob `*/` subdirectories with `__init__.py` or `pyproject.toml`

**Key points:**
- Profiles and agents: `*.md` files in top-level directory only
- Context: `**/*.md` files recursively (supports subdirectories)
- Scenario tools: Subdirectories (each tool is a directory)
- Modules: Subdirectories with Python package markers

**No configuration required** - presence of directory triggers discovery.

---

## Profile and Agent File Schema

Profiles and agents are authored as Markdown files but MUST begin with a YAML
front matter block delimited by `---` lines. The loader parses this front matter
into strongly typed Pydantic models; narrative Markdown that only shows “example”
YAML inside code fences is rejected.

**Profile file requirements (`profiles/*.md`):**

- First non-empty line is `---`.
- YAML front matter defines a `profile` block (`name`, `version`, `description`, `extends`), followed by optional sections such as `session`, `tools`, `hooks`, `providers`, `agents`, `ui`, etc.
- After the closing `---`, additional Markdown content is optional and is exposed to the user verbatim.
- Profile configuration fields map one-to-one with the public `Profile` model in `amplifier_profiles`.

**Agent file requirements (`agents/*.md`):**

- First non-empty line is `---`.
- YAML front matter defines `name` and `description`. Recommended optional fields: `model` (usually `inherit`), `capabilities`, `keywords`, `priority`, `config`.
- Body Markdown is treated as the agent’s system instructions.

**Validation notes:**

- Keys outside the documented schema raise validation errors.
- Omit provider overrides unless required; profiles inherit the active provider by default.
- Keep configuration in the front matter—do not place operational YAML in code blocks.

This schema matches the shipped collections (`toolkit`, `design-intelligence`, etc.) and is enforced during smoke tests.

---

## pyproject.toml Format

Every collection MUST have `pyproject.toml` at its root for metadata.

### Required Fields

```toml
[project]
name = "my-collection"          # REQUIRED: Collection identifier (use hyphens)
version = "1.0.0"               # REQUIRED: Semantic version
description = "Description"     # REQUIRED: One-line description
```

**Validation:**
- `name`: Must be valid Python package name (lowercase, hyphens allowed)
- `version`: Must follow semantic versioning (X.Y.Z)
- `description`: Non-empty string

### Optional Fields

```toml
[project.urls]
homepage = "https://docs.example.com"      # Documentation URL
repository = "https://github.com/..."      # Source repository

[tool.amplifier.collection]
author = "developer-name"                  # Creator name
capabilities = [                           # What this enables (list of strings)
    "Capability 1",
    "Capability 2"
]

[tool.amplifier.collection.requires]
foundation = "^1.0.0"                      # Dependency constraints
toolkit = "~1.2.0"
```

**Field Reference:**

| Section | Field | Type | Required | Purpose |
|---------|-------|------|----------|---------|
| `[project]` | `name` | string | **YES** | Collection identifier |
| `[project]` | `version` | string | **YES** | Semantic version (X.Y.Z) |
| `[project]` | `description` | string | **YES** | One-line description |
| `[project.urls]` | `homepage` | string | No | Documentation URL |
| `[project.urls]` | `repository` | string | No | Source repository |
| `[tool.amplifier.collection]` | `author` | string | No | Creator name |
| `[tool.amplifier.collection]` | `capabilities` | list[string] | No | What collection enables |
| `[tool.amplifier.collection.requires]` | `{collection-name}` | string | No | Version constraint for dependency |

**Parsing:**
- Uses Python stdlib `tomllib` (Python 3.11+)
- Validated with Pydantic models
- Frozen models prevent accidental modification

**Naming guidance:** `[project].name` is the canonical collection identifier.
Choose a short, hyphenated slug (e.g., `toolkit`, `design-intelligence`) and
avoid repository prefixes such as `amplifier-collection-`. The CLI exposes this
value directly in commands like `amplifier collection show <name>`.

---

## Dependency Constraints

Collections can declare dependencies using semantic versioning constraints:

```toml
[tool.amplifier.collection.requires]
foundation = "^1.0.0"     # Caret: compatible with 1.x.x
toolkit = "~1.2.0"        # Tilde: compatible with 1.2.x
other = ">=1.0.0,<2.0.0"  # Range: explicit bounds
exact = "==1.5.0"         # Exact: specific version only
```

**Constraint Operators:**

| Operator | Meaning | Example | Matches |
|----------|---------|---------|---------|
| `^` | Caret | `^1.2.3` | 1.2.3 ≤ version < 2.0.0 |
| `~` | Tilde | `~1.2.3` | 1.2.3 ≤ version < 1.3.0 |
| `>=`, `<` | Range | `>=1.0,<2.0` | 1.0.0 ≤ version < 2.0.0 |
| `==` | Exact | `==1.2.3` | version == 1.2.3 exactly |

**Current Behavior:**
- Dependencies are parsed and stored in metadata
- NOT automatically installed (manual installation required)
- Future versions may add automatic dependency resolution

---

## Search Path Precedence

Collections are resolved using **first-match-wins** strategy in precedence order:

**Order (highest to lowest precedence):**

1. **Project** - `.amplifier/collections/` (workspace-specific)
2. **User** - `~/.amplifier/collections/` (user-installed)
3. **Bundled** - Application-provided (system defaults)

**Example Resolution:**

```
Input: resolver.resolve("foundation")

Checks in order:
1. .amplifier/collections/foundation/              ← If exists, return this
2. ~/.amplifier/collections/foundation/            ← Else if exists, return this
3. <app>/data/collections/foundation/              ← Else if exists, return this
4. None                                            ← Not found
```

**Overriding Bundled Collections:**

Project and user collections override bundled:

```
.amplifier/collections/foundation/     ← Highest precedence (returned)
~/.amplifier/collections/foundation/   ← Shadowed
<app>/collections/foundation/          ← Shadowed
```

**Application Responsibility:**

Applications define search paths. Library provides resolution mechanism:

```python
# Example: CLI application paths
cli_paths = [
    Path(__file__).parent / "data" / "collections",  # Bundled (lowest)
    Path.home() / ".amplifier" / "collections",      # User
    Path(".amplifier/collections"),                   # Project (highest)
]

resolver = CollectionResolver(search_paths=cli_paths)
```

**Note:** Exact paths vary by application. This library provides the resolution mechanism.

---

## Lock File Format

The `collections.lock` file tracks installed collections.

### Location

Applications define lock file location:
- CLI: `.amplifier/collections.lock` (project) or `~/.amplifier/collections.lock` (user)
- Web: `/var/amplifier/workspaces/{workspace_id}/collections.lock`

### Format

```json
{
  "version": "1.0",
  "collections": {
    "my-collection": {
      "name": "my-collection",
      "source": "git+https://github.com/user/my-collection@v1.0.0",
      "commit": "abc123def456789...",
      "path": "/home/user/.amplifier/collections/my-collection",
      "installed_at": "2025-10-31T10:30:00Z"
    },
    "another-collection": {
      "name": "another-collection",
      "source": "git+https://github.com/org/another@main",
      "commit": "def456abc123...",
      "path": "/home/user/.amplifier/collections/another-collection",
      "installed_at": "2025-10-31T11:15:00Z"
    }
  }
}
```

**Field Specification:**

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `version` | string | **YES** | Lock file format version ("1.0") |
| `collections` | object | **YES** | Dictionary of collection entries (key = collection name) |
| `collections[].name` | string | **YES** | Collection name |
| `collections[].source` | string | **YES** | Installation source URI |
| `collections[].commit` | string\|null | **YES** | Git commit SHA (null if not git) |
| `collections[].path` | string | **YES** | Absolute installation path |
| `collections[].installed_at` | string | **YES** | ISO 8601 timestamp |

**Parsing:**
- Uses Python stdlib `json`
- Human-readable format
- Tool-compatible

---

## Package Structure for Installation

Collections follow **standard Python packaging** for pip/uv compatibility.

### Repository Layout

```
my-collection/                  # Git repository root
  pyproject.toml                # Build configuration (at root)
  MANIFEST.in                   # Data file inclusion
  README.md                     # Collection documentation

  my_collection/                # Package directory (hyphens → underscores!)
    __init__.py                 # Python package marker
    pyproject.toml              # Copy for runtime discovery

    profiles/                   # Collection resources
      my-profile.md
    agents/
      my-agent.md
    context/
      expertise.md
```

### Naming Convention

- **Collection name**: Use hyphens (e.g., `design-intelligence`)
- **Package directory**: Use underscores (e.g., `design_intelligence/`)

Python packaging automatically converts hyphens to underscores for package names.

### Required Files

**pyproject.toml (at root):**
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = {find = {}}

[tool.setuptools.package-data]
my_collection = ["*.toml", "**/*.md"]
```

**MANIFEST.in:**
```
include LICENSE
include README.md
include pyproject.toml
recursive-include my_collection *.md
recursive-include my_collection *.toml
```

**\_\_init\_\_.py:**
```python
"""My Collection - Data package."""
__version__ = "1.0.0"
```

### Installation Result

When users install via `uv pip install` or `amplifier collection add`:

```
~/.amplifier/collections/
  my-collection/              # Installation target directory
    my_collection/            # Package directory (from pip)
      __init__.py
      pyproject.toml
      profiles/
      agents/
      context/
```

**Auto-discovery:** amplifier-collections library discovers resources in both flat (git clone) and nested (pip install) structures automatically.

---

## Resource Type Specifications

### Profiles (profiles/*.md)

**Location:** `profiles/` directory
**Pattern:** `*.md` files (non-recursive)
**Format:** YAML frontmatter + configuration

**Discovery:** All `.md` files directly in `profiles/` directory.

### Agents (agents/*.md)

**Location:** `agents/` directory
**Pattern:** `*.md` files (non-recursive)
**Format:** YAML frontmatter + instructions

**Discovery:** All `.md` files directly in `agents/` directory.

**Note:** Agents are loaded via profiles. See [amplifier-profiles](https://github.com/microsoft/amplifier-profiles) for agent specification.

### Context (context/**/*.md)

**Location:** `context/` directory
**Pattern:** `**/*.md` files (recursive)
**Format:** Markdown files

**Discovery:** All `.md` files in `context/` and subdirectories (recursive).

**Organization:** Collections can organize context in subdirectories - all markdown files discovered automatically.

### Scenario Tools (scenario-tools/*/)

**Location:** `scenario-tools/` directory
**Pattern:** Subdirectories (each tool is a directory)
**Format:** Python packages with pyproject.toml

**Discovery:** All subdirectories in `scenario-tools/`.

**Requirements:**
- Each tool directory must contain `pyproject.toml`
- Tools may be installed via `uv tool install`

### Modules (modules/*/)

**Location:** `modules/` directory
**Pattern:** Subdirectories with `__init__.py` or `pyproject.toml`
**Format:** Python packages

**Discovery:** Subdirectories containing `__init__.py` or `pyproject.toml`.

**Requirements:**
- Must be valid Python packages
- Follow module type specifications (provider, tool, hook, orchestrator, context)

---

## Validation Rules

### Collection Validation

**Required:**
- ✓ `pyproject.toml` exists at root
- ✓ `[project]` section has `name`, `version`, `description`
- ✓ Collection name is valid Python package identifier

**Optional but validated if present:**
- `[tool.amplifier.collection]` section fields
- `[project.urls]` section fields
- Dependency constraints syntax

**Errors:**
- Missing pyproject.toml → `CollectionMetadataError`
- Invalid metadata → `CollectionMetadataError`
- Invalid directory structure → No error (directories optional)

### Metadata Validation

```python
# Valid
{
    "name": "my-collection",
    "version": "1.0.0",
    "description": "My collection"
}
# ✓ Passes

# Invalid - missing required field
{
    "name": "my-collection",
    "version": "1.0.0"
    # Missing description
}
# ✗ Raises: CollectionMetadataError("Required field missing: description")

# Invalid - bad version format
{
    "name": "my-collection",
    "version": "1.0",  # Not semantic versioning
    "description": "My collection"
}
# ✗ Raises: CollectionMetadataError("Invalid version format")
```

---

## Versioning and Compatibility

### Collection Versions

Collections use **semantic versioning** (X.Y.Z):

- **Major (X)**: Breaking changes to structure or contracts
- **Minor (Y)**: Backward-compatible additions (new resources)
- **Patch (Z)**: Bug fixes, documentation updates

**Examples:**
- `1.0.0` → `1.1.0`: Added new profile (backward-compatible)
- `1.1.0` → `2.0.0`: Changed directory structure (breaking)
- `1.1.0` → `1.1.1`: Fixed typo in context (non-breaking)

### Lock File Version

Lock file format is versioned independently:

```json
{
  "version": "1.0",  ← Lock file format version
  "collections": {...}
}
```

**Current version:** 1.0

**Future versions** may add fields while maintaining backward compatibility.

---

## Protocol Contracts

### InstallSourceProtocol

Collections are installed via sources implementing this protocol:

```python
from typing import Protocol
from pathlib import Path

class InstallSourceProtocol(Protocol):
    """Interface for collection installation sources."""

    async def install_to(self, target_dir: Path) -> None:
        """Install collection content to target directory.

        Args:
            target_dir: Directory to install into (must not exist)

        Raises:
            Exception: If installation fails
        """
        ...
```

**Standard Implementations** (from amplifier-module-resolution):
- `GitSource` - Git repositories via uv
- `FileSource` - Local directories

**Custom Implementations** (applications can create):
- `HttpZipSource` - HTTP zip downloads
- `DatabaseBlobSource` - Database-stored collections
- `RegistrySource` - Corporate artifact servers

**Contract Requirements:**
- Create `target_dir` if it doesn't exist
- Install all collection content to `target_dir`
- Raise exception on failure (don't return error codes)
- Be idempotent if possible

---

## File Format Specifications

### Profiles (*.md in profiles/)

See [Profile Authoring Guide](https://github.com/microsoft/amplifier-profiles/blob/main/docs/PROFILE_AUTHORING.md) for complete specification.

**Minimal structure:**
```markdown
---
name: profile-name
description: Profile description
---

session:
  orchestrator: loop-basic
  context: context-simple

providers:
  - module: provider-anthropic
    source: git+https://github.com/...
```

### Agents (*.md in agents/)

See [Agent Authoring Guide](https://github.com/microsoft/amplifier-profiles/blob/main/docs/AGENT_AUTHORING.md) for complete specification.

**Minimal structure:**
```markdown
---
meta:
  name: agent-name
  description: Agent description
---

Agent instructions here.
```

### Context (*.md in context/)

**Format:** Standard Markdown
**Requirements:** None (any valid markdown)
**Organization:** Can use subdirectories

### Scenario Tools

See [Scenario Tools Guide](https://github.com/microsoft/amplifier-dev/blob/main/docs/SCENARIO_TOOLS_GUIDE.md) for complete specification.

**Requirements:**
- Must be Python package with `pyproject.toml`
- Must define entry point for CLI usage
- Can use `amplifier_core.AmplifierSession` API

### Modules

See [Module Development Guide](https://github.com/microsoft/amplifier-dev/blob/main/docs/MODULE_DEVELOPMENT.md) for complete specification.

**Requirements:**
- Must be valid Python package
- Must define appropriate entry points
- Must conform to module type protocol

---

## Reference Implementation

**Example collection:** [amplifier-collection-design-intelligence](https://github.com/microsoft/amplifier-collection-design-intelligence)

This collection demonstrates:
- Complete directory structure
- Proper pyproject.toml format
- Package structure for pip installation
- Profiles, agents, context, and documentation

---

## Related Documentation

- **[User Guide](USER_GUIDE.md)** - Using collections
- **[Authoring Guide](AUTHORING.md)** - Creating collections
- **[API Reference](../README.md)** - Python API for developers

---

**Specification Version:** 1.0
**Last Updated:** 2025-10-31
