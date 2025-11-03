---
last_updated: 2025-10-31
status: stable
audience: collection-authors
---

# Collection Authoring Guide

**Purpose**: Learn how to create shareable collections of Amplifier expertise.

This guide teaches you how to package profiles, agents, context, scenario tools, and modules into collections that others can install and use.

---

## Table of Contents

- [Collection Structure](#collection-structure)
- [Collection Metadata](#collection-metadata)
- [Creating Your Collection](#creating-your-collection)
- [Package Structure](#package-structure)
- [Adding Resources](#adding-resources)
- [Publishing](#publishing)
- [Dependency Declarations](#dependency-declarations)
- [FAQ](#faq)

---

## Collection Structure

Collections follow a **well-known directory convention**. Resources are auto-discovered based on directory presence - no manifest file required.

**→ See [Collection Structure Specification](SPECIFICATION.md#collection-directory-structure) for complete technical contract**

**Key directories:**

- `profiles/` - Profile definitions (\*.md files)
- `agents/` - Agent definitions (\*.md files)
- `context/` - Shared knowledge (\*_/_.md recursive)
- `scenario-tools/` - CLI tools (subdirectories)
- `modules/` - Amplifier modules (Python packages)

**Convention over configuration**: Structure IS the configuration - no manifest file needed.

---

## Writing Profiles and Agents

Profiles and agents are Markdown documents with YAML front matter. The front matter
defines everything the loader needs; the remaining Markdown is optional narrative
for humans.

**Profiles (`profiles/*.md`):**

```markdown
---
profile:
  name: toolkit-dev
  version: 1.0.0
  description: Toolkit development configuration
  extends: foundation
session:
  orchestrator:
    module: loop-streaming
    source: git+https://github.com/microsoft/amplifier-module-loop-streaming@main
  context:
    module: context-simple
agents:
  dirs:
    - ./agents
---

# Optional Markdown body
```

- Place every operational field (session, tools, hooks, providers, ui, etc.) inside the YAML block.
- Avoid “example” YAML code fences—those are ignored during parsing.
- Profiles inherit the currently active provider unless you add an explicit override.

**Agents (`agents/*.md`):**

```markdown
---
name: tool-builder
description: Agent that helps build scenario tools
model: inherit
capabilities:
  - tool-scaffolding
---

# System instructions here...
```

- Required fields: `name`, `description`.
- Recommended: `model: inherit` plus `capabilities`/`keywords` to aid discovery.

When in doubt, copy an existing shipped profile or agent (for example, the Toolkit
collection) and adjust the front matter fields instead of moving configuration
into the prose section.

---

## Collection Metadata

Every collection requires a `pyproject.toml` file with metadata.

**→ See [pyproject.toml Format Specification](SPECIFICATION.md#pyprojecttoml-format) for complete field reference**

**Example:**

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-collection"
version = "1.0.0"
description = "My expertise collection"

[tool.amplifier.collection]
author = "Your Name"
capabilities = ["What this enables"]

[tool.amplifier.collection.requires]
foundation = "^1.0.0"  # Dependencies
```

**Required fields:** `name`, `version`, `description` (in `[project]` section)

**Why pyproject.toml?** Standard Python packaging enables installation via `uv` and `pip`.

---

## Creating Your Collection

### Step 1: Create Directory Structure

```bash
mkdir my-collection
cd my-collection

# Create well-known directories (all optional, auto-discovered)
mkdir -p profiles agents context scenario-tools modules
```

### Step 2: Create pyproject.toml

Collections follow **standard Python packaging conventions**. Even data-only collections (pure markdown) need minimal package structure for proper installation.

```bash
# Create basic pyproject.toml at repository root
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-collection"
version = "1.0.0"
description = "My expertise collection"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
authors = [
    {name = "Your Name"}
]

[project.urls]
repository = "https://github.com/user/my-collection"

[tool.setuptools]
packages = {find = {}}

[tool.setuptools.package-data]
my_collection = ["*.toml", "**/*.md"]

[tool.amplifier.collection]
author = "Your Name"
capabilities = [
    "What this collection enables",
    "What expertise it provides"
]

[tool.amplifier.collection.requires]
# foundation = "^1.0.0"  # Optional dependencies
EOF
```

> **Naming tip:** The value of `[project].name` becomes the collection ID that end
> users reference via the CLI (`amplifier collection show <name>`). Keep it short
> and drop repository prefixes such as `amplifier-collection-`. For example, the
> repository `amplifier-collection-toolkit` uses `[project].name = "toolkit"` so
> users run `amplifier collection show toolkit`.

**Key sections:**

- `[build-system]` - Required for pip/uv installation
- `[tool.setuptools]` - Package discovery configuration
- `[tool.setuptools.package-data]` - Include data files (markdown, toml)
- `[tool.amplifier.collection.requires]` - Dependencies (note subsection format)

### Step 3: Add Package Structure

Collections follow **standard Python packaging**. Create a package directory (hyphens → underscores) alongside the resource directories.

**→ See [Package Structure Specification](SPECIFICATION.md#package-structure-for-installation) for complete technical contract**

```bash
# Create package directory (hyphens → underscores!)
PACKAGE_NAME=$(python3 -c "print('my-collection'.replace('-', '_'))")
mkdir -p $PACKAGE_NAME  # my_collection

# Minimal __init__.py (keeps package importable)
cat > $PACKAGE_NAME/__init__.py << 'EOF'
"""My Collection - resource package."""
__all__ = ()
EOF

# Copy pyproject.toml into package for runtime discovery metadata
cp pyproject.toml $PACKAGE_NAME/

# Create MANIFEST.in to include data files in wheels
cat > MANIFEST.in << 'EOF'
# Metadata
include LICENSE
include CODE_OF_CONDUCT.md
include SECURITY.md
include SUPPORT.md
include README.md
include pyproject.toml

# Collection resources (remain at repo root)
recursive-include agents *
recursive-include profiles *
recursive-include context *
recursive-include scenario-tools *
recursive-include templates *
recursive-include docs *

# Package metadata copied into the wheel
recursive-include my_collection *.py *.toml
EOF
```

**Final structure** (resources stay at the repository root):

```
my-collection/
  pyproject.toml                   # Build configuration
  MANIFEST.in
  README.md
  LICENSE …                        # Metadata files

  agents/                          # Collection resources
  profiles/
  context/
  scenario-tools/
  templates/
  docs/

  my_collection/                   # Python package (hyphens → underscores)
    __init__.py
    pyproject.toml                 # Copied from root for runtime discovery
```

**When installed by users** (`uv pip install git+https://…`):

```
~/.amplifier/collections/my-collection/
  agents/
  profiles/
  context/
  scenario-tools/
  templates/
  docs/
  my_collection/
    __init__.py
    pyproject.toml
  *.dist-info/
```

The CLI relies on this layout to locate resources after installation—no manual renaming or git fallback required.

**See**: [amplifier-collection-design-intelligence](https://github.com/microsoft/amplifier-collection-design-intelligence) for complete working example.

---

## Adding Resources

### Add Profiles (profiles/\*.md)

Profiles define capability configurations:

```markdown
---
name: my-profile
description: My specialized profile
---

# Configuration

session:
orchestrator: loop-streaming
context: context-persistent

providers:

- module: provider-anthropic
  source: git+https://github.com/microsoft/amplifier-module-provider-anthropic@main
  config:
  model: claude-opus-4-1

context:

- @my-collection:context/expertise.md
```

**See**: [Profile Authoring Guide](https://github.com/microsoft/amplifier-profiles/blob/main/docs/PROFILE_AUTHORING.md) for complete profile syntax.

### Add Agents (`agents/*.md`)

Agents define specialized AI personas:

```markdown
---
meta:
  name: my-agent
  description: Specialized expert in [domain]

tools:
  - module: tool-filesystem
  - module: tool-bash
---

You are a specialized expert in [domain].

[Agent instructions using @my-collection:context/... references]
```

**Note**: Agents are loaded via profiles. See [Agent Authoring Guide](https://github.com/microsoft/amplifier-profiles/blob/main/docs/AGENT_AUTHORING.md) for complete agent syntax and delegation patterns.

### Add Context (`context/**/*.md`)

Context files contain shared knowledge that profiles and agents can reference:

```markdown
# Expertise Domain Knowledge

[Shared knowledge that profiles and agents reference via @mentions]

## Key Concepts

...

## Examples

...

## Best Practices

...
```

**Note**: Context files can be organized in subdirectories - all `**/*.md` files are auto-discovered recursively.

### Add Scenario Tools (`scenario-tools/*`)

Scenario tools are sophisticated CLI tools built with AmplifierSession:

```
scenario-tools/
  my_analyzer/
    main.py                 # Entry point with AmplifierSession usage
    pyproject.toml          # Package metadata for uv tool install

    analyzer/core.py        # Analytical config (temp=0.3)
    synthesizer/core.py     # Creative config (temp=0.7)

    README.md               # User guide
    HOW_TO_BUILD.md         # Builder guide
```

**See**: [Scenario Tools Guide](https://github.com/microsoft/amplifier-dev/blob/main/docs/SCENARIO_TOOLS_GUIDE.md) for complete tutorial on building sophisticated CLI tools.

**See**: [Toolkit Guide](https://github.com/microsoft/amplifier-dev/blob/main/docs/TOOLKIT_GUIDE.md) for toolkit utilities available when building scenario tools.

### Add Modules (`modules/*`)

Collections can include custom Amplifier modules (providers, tools, hooks, orchestrators):

```
modules/
  hooks-custom/
    __init__.py
    pyproject.toml
    hook.py
```

Each module needs its own `pyproject.toml` with entry points. See [Module Development Guide](https://github.com/microsoft/amplifier-dev/blob/main/docs/MODULE_DEVELOPMENT.md) for complete module authoring guidance.

---

## Publishing

### Step 1: Document Your Collection

Create `README.md` at repository root:

````markdown
# My Collection

## What This Provides

[Description of expertise and capabilities]

## Quick Start

```bash
# Install
amplifier collection add git+https://github.com/user/my-collection

# Use the profile
amplifier profile use my-collection:my-profile

# Start session with profile (agents loaded automatically)
amplifier run "your task here"
```
````

## Resources

- **Profiles**: [List and describe your profiles]
- **Agents**: [List and describe your agents] (loaded via profiles, see [Agent Authoring](https://github.com/microsoft/amplifier-profiles/blob/main/docs/AGENT_AUTHORING.md))
- **Context**: [Describe shared knowledge]
- **Scenario Tools**: [List and describe tools]

## Documentation

[Links to additional documentation]

````

### Step 2: Publish to Git

```bash
git init
git add .
git commit -m "Initial collection"

# Create repository on GitHub
# Then push
git remote add origin https://github.com/user/my-collection.git
git push -u origin main

# Tag releases for versioning
git tag v1.0.0
git push origin v1.0.0
````

### Step 3: Share

Users can now install your collection:

```bash
# Install specific version (recommended)
amplifier collection add git+https://github.com/user/my-collection@v1.0.0

# Or install latest from main branch
amplifier collection add git+https://github.com/user/my-collection@main
```

---

## Dependency Declarations

Collections can declare dependencies on other collections.

**→ See [Dependency Constraints Specification](SPECIFICATION.md#dependency-constraints) for complete constraint syntax**

**Example:**

```toml
[tool.amplifier.collection.requires]
foundation = "^1.0.0"     # Compatible with 1.x.x
toolkit = "~1.2.0"        # Compatible with 1.2.x
```

**Current behavior:** Dependencies parsed but NOT auto-installed. Users install dependencies manually.

---

## FAQ

### Q: Why do I need pyproject.toml at both root and in package?

**A**: Standard Python packaging requirement:

- **Root `pyproject.toml`** - Tells `setuptools` how to build the package
- **Package `pyproject.toml`** - Copied into package for runtime discovery by amplifier-collections

Include the package copy via:

```toml
[tool.setuptools.package-data]
my_collection = ["*.toml", "**/*.md"]
```

### Q: Why do collection names use hyphens but package names use underscores?

**A**: Python packaging convention:

- **Collection names**: Use hyphens (e.g., `design-intelligence`)
- **Package directories**: Use underscores (e.g., `design_intelligence/`)

Amplifier automatically handles this conversion when resolving collections.

### Q: Can users install via git clone instead of `amplifier collection add`?

**A**: Yes! Both installation methods work:

```bash
# Method 1: Application command (nested structure from pip install)
amplifier collection add git+https://github.com/user/my-collection

# Method 2: git clone (flat structure)
git clone https://github.com/user/my-collection ~/.amplifier/collections/my-collection
```

The amplifier-collections library discovers resources in both structures automatically.

### Q: Which structure should I use when creating collections?

**A**: Use **nested structure** (standard Python packaging) as shown in this guide.

**Benefits:**

- Works with all Python tools (`pip`, `uv`, `twine`)
- Can be published to PyPI if desired
- Follows industry standards
- Auto-discovered by Amplifier regardless of how users install

### Q: What if my collection has both markdown and Python code?

**A**: Same structure works for both:

```
my-collection/
  my_collection/
    __init__.py
    pyproject.toml

    # Data files
    profiles/
    agents/
    context/

    # Python modules
    hooks/
      my_hook.py

    # Scenario tools
    tools/
      analyzer.py
```

The package can contain both data files and Python code.

### Q: How do I test my collection before publishing?

**A**: Install locally from your development directory:

```bash
# Install in editable mode
cd my-collection
uv pip install -e .

# Or have users install from local path
amplifier collection add /path/to/my-collection
```

Test all resources load correctly, profiles work, agents delegate, etc.

### Q: Should I include tests for my collection?

**A**: Recommended for collections with:

- Custom Python modules (hooks, tools, orchestrators)
- Scenario tools with complex logic
- Non-trivial agent delegation patterns

Not required for:

- Simple profile/agent/context collections (pure markdown)

### Q: Can I publish to PyPI?

**A**: Yes! Collections using standard Python packaging can be published to PyPI:

```bash
# Build distribution
python -m build

# Upload to PyPI (requires account and twine)
python -m twine upload dist/*
```

Then users can install via:

```bash
uv pip install my-collection
```

However, git-based distribution is more common for Amplifier collections.

---

## Best Practices

### 1. Version Your Releases

Use semantic versioning and git tags:

```bash
git tag v1.0.0
git tag v1.1.0  # Backward-compatible additions
git tag v2.0.0  # Breaking changes
git push --tags
```

Users can pin to specific versions:

```bash
amplifier collection add git+https://github.com/user/my-collection@v1.0.0
```

### 2. Document Dependencies Clearly

If your collection depends on others:

- Declare in `[tool.amplifier.collection.requires]`
- Document in README.md
- Provide installation order

### 3. Provide Examples

Include example usage in README:

- How to install
- How to use profiles
- How to run scenario tools
- Common patterns

### 4. Keep Focused

Collections should have clear purpose:

- **Good**: "Memory optimization expertise" (focused)
- **Bad**: "Everything for development" (unfocused)

Focused collections are easier to:

- Maintain
- Document
- Use
- Compose

### 5. Follow Conventions

- Use well-known directory names (`profiles/`, `agents/`, `context/`)
- Use `.md` for profiles, agents, context
- Use hyphens in collection names
- Follow Python packaging standards

---

## Related Documentation

- **[Collections User Guide](USER_GUIDE.md)** - Using collections
- **[amplifier-collections API Reference](../README.md)** - Python API for developers
- [Scenario Tools Guide](https://github.com/microsoft/amplifier-dev/blob/main/docs/SCENARIO_TOOLS_GUIDE.md) - Building sophisticated CLI tools
- [Toolkit Guide](https://github.com/microsoft/amplifier-dev/blob/main/docs/TOOLKIT_GUIDE.md) - Toolkit utilities for scenario tools
- **[Profile Authoring](https://github.com/microsoft/amplifier-profiles/blob/main/docs/PROFILE_AUTHORING.md)** - Creating profiles
- **[Agent Authoring](https://github.com/microsoft/amplifier-profiles/blob/main/docs/AGENT_AUTHORING.md)** - Creating agents
- [Module Development](https://github.com/microsoft/amplifier-dev/blob/main/docs/MODULE_DEVELOPMENT.md) - Creating custom modules

---

## Example Collections

Study these for inspiration:

- [amplifier-collection-design-intelligence](https://github.com/microsoft/amplifier-collection-design-intelligence) - Complete working example with profiles, agents, context, and documentation

---

**Document Version**: 1.0
**Last Updated**: 2025-10-31
