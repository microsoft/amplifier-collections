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
- `profiles/` - Profile definitions (*.md files)
- `agents/` - Agent definitions (*.md files)
- `context/` - Shared knowledge (**/*.md recursive)
- `scenario-tools/` - CLI tools (subdirectories)
- `modules/` - Amplifier modules (Python packages)

**Convention over configuration**: Structure IS the configuration - no manifest file needed.

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

**Key sections:**
- `[build-system]` - Required for pip/uv installation
- `[tool.setuptools]` - Package discovery configuration
- `[tool.setuptools.package-data]` - Include data files (markdown, toml)
- `[tool.amplifier.collection.requires]` - Dependencies (note subsection format)

### Step 3: Add Package Structure

Collections follow **standard Python packaging**. Create a package directory (hyphens → underscores):

```bash
# Create package directory (hyphens → underscores!)
PACKAGE_NAME=$(python3 -c "print('my-collection'.replace('-', '_'))")
mkdir $PACKAGE_NAME  # my_collection

# Minimal __init__.py
cat > $PACKAGE_NAME/__init__.py << 'EOF'
"""My Collection - Data package."""
__version__ = "1.0.0"
EOF

# Copy pyproject.toml into package for runtime discovery
cp pyproject.toml $PACKAGE_NAME/

# Move resource directories into package
mv profiles agents context $PACKAGE_NAME/

# Create MANIFEST.in to include data files in wheels
cat > MANIFEST.in << 'EOF'
# Include metadata files in wheel
include LICENSE
include README.md
include pyproject.toml

# Include all collection data from package
recursive-include my_collection *.md
recursive-include my_collection *.toml
EOF
```

**Final structure**:
```
my-collection/                  # Git repo root
  pyproject.toml                # Build configuration (at root)
  MANIFEST.in                   # Data file inclusion rules
  README.md

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

**Why this structure:**
- **Standard Python packaging**: Works with `pip`, `uv`, and all Python tools
- **Nested structure**: When installed via `uv pip install`, creates proper package hierarchy
- **Auto-discovery**: amplifier-collections library finds resources in both flat (git clone) and nested (pip install) structures
- **No normalization needed**: Structure preserved as Python packaging creates it

**When installed by users**:
```
~/.amplifier/collections/
  my-collection/              # Installation target
    my_collection/            # Package directory (automatic from pip)
      pyproject.toml
      profiles/
      agents/
      context/
```

Amplifier automatically discovers resources regardless of structure depth.

**See**: [amplifier-collection-design-intelligence](https://github.com/microsoft/amplifier-collection-design-intelligence) for complete working example.

---

## Adding Resources

### Add Profiles (profiles/*.md)

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

### Add Agents (agents/*.md)

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

### Add Context (context/**/*.md)

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

### Add Scenario Tools (scenario-tools/*/)

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

### Add Modules (modules/*/)

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

```markdown
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

## Resources

- **Profiles**: [List and describe your profiles]
- **Agents**: [List and describe your agents] (loaded via profiles, see [Agent Authoring](https://github.com/microsoft/amplifier-profiles/blob/main/docs/AGENT_AUTHORING.md))
- **Context**: [Describe shared knowledge]
- **Scenario Tools**: [List and describe tools]

## Documentation

[Links to additional documentation]
```

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
```

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
