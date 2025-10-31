---
last_updated: 2025-10-31
status: stable
audience: users
---

# Collections User Guide

## What Are Collections?

Collections are **shareable bundles** of Amplifier expertise that package related resources together for distribution via git repositories. A collection can include:

- **Profiles** - Capability configurations
- **Agents** - Specialized AI personas
- **Context** - Shared knowledge and prompts
- **Scenario Tools** - Sophisticated CLI tools built with AmplifierSession
- **Modules** - Provider, tool, hook, and orchestrator modules

**Example**: The `memory-solution` collection might include:
- Profile for memory-optim

ized configuration
- Agent specialized in memory analysis
- Context docs explaining memory management patterns
- Scenario tool that automates memory optimization
- Hook module that tracks memory usage

**Key principle**: Collections use **convention over configuration**. The directory structure defines what resources are available - no manifest file needed.

---

## Quick Start

### Installing a Collection

Collections are typically distributed as git repositories and installed using command-line tools provided by your Amplifier application (e.g., amplifier-app-cli).

**Example installation** (using amplifier-app-cli):
```bash
# Install from git repository
amplifier collection add git+https://github.com/user/memory-solution@v1.0.0

# Install to project only (not user-global)
amplifier collection add git+https://github.com/user/memory-solution@v1.0.0 --local
```

**Note**: These CLI commands are implemented by the application layer (like amplifier-app-cli). The amplifier-collections library provides the underlying mechanisms that applications use. See your application's documentation for specific command syntax.

### Using Collection Resources

Once installed, collection resources can be used via the application's interface:

**Example usage** (with amplifier-app-cli):
```bash
# Use a profile from a collection
amplifier profile use memory-solution:optimized

# Profiles can include agents that are then available in sessions
# See https://github.com/microsoft/amplifier-profiles/blob/main/docs/AGENT_AUTHORING.md for agent details

# Reference context in profiles/agents via @mentions
@memory-solution:context/patterns.md
```

### Listing Collections

**Example** (with amplifier-app-cli):
```bash
# List all installed collections
amplifier collection list

# Show collection details
amplifier collection show memory-solution
```

---

## Using Collections

### Discovering Collection Resources

Collection profiles and agents appear in list commands with `collection:name` format.

**Example output** (from amplifier-app-cli):
```bash
# List all profiles (includes collection profiles)
amplifier profile list

# Example output:
# base                         bundled
# design-intelligence:designer user-collection
# developer-expertise:dev      bundled
# foundation:base              bundled

# List all agents (includes collection agents)
amplifier agent list

# Example output:
# zen-architect                           bundled
# design-intelligence:art-director        user-collection
# developer-expertise:zen-architect       bundled
```

**Source labels:**
- `bundled` - Shipped with application
- `user-collection` - Installed to user directory
- `project-collection` - Installed to project directory

### Referencing Collection Resources

Collections use the **@mention syntax** with collection names:

```
@collection-name:path/to/resource
```

**Examples**:
```markdown
# In a profile
extends: foundation:profiles/base.md

context:
  - @foundation:context/shared/common-agent-base.md
  - @memory-solution:context/patterns.md

# In an agent
@memory-solution:context/examples.md
```

**Shortcuts**:
```
@user:path          →  ~/.amplifier/path (or app-specific user dir)
@project:path       →  .amplifier/path (or app-specific project dir)
@path               →  Direct path (unchanged)
```

### Search Path Precedence

Collections resolve in precedence order: Project → User → Bundled (highest to lowest).

**See:** [Search Path Specification](SPECIFICATION.md#search-path-precedence) for complete details.

**Note**: Exact paths depend on your application's configuration.

---

## Bundled Collections

Applications may ship with bundled collections. Here are examples from amplifier-app-cli:

### foundation

**Purpose**: Base profiles and shared context for all users

**Location**: `<package>/data/collections/foundation/`

**Contents**:
- Profiles: `base.md`, `foundation.md`, `production.md`, `test.md`
- Context: Shared philosophies and patterns
- Independent (no dependencies)

**Usage**:
```bash
# Use foundation base profile
amplifier profile use foundation:base

# Or with full path
amplifier profile use foundation:profiles/base.md
```

**In your profiles**:
```markdown
# Extend foundation base (both syntaxes work)
extends: foundation:base

# Or full path
extends: foundation:profiles/base.md

# Reference context
context:
  - @foundation:context/IMPLEMENTATION_PHILOSOPHY.md
```

### developer-expertise

**Purpose**: Development-focused profiles and specialized agents

**Location**: `<package>/data/collections/developer-expertise/`

**Contents**:
- Profiles: `dev.md`, `full.md`
- Agents: `zen-architect.md`, `bug-hunter.md`, `modular-builder.md`, `researcher.md`
- Depends on: `foundation`

**Usage**:
```bash
# Use dev profile (includes all agents)
amplifier profile use developer-expertise:dev

# Or with full path
amplifier profile use developer-expertise:profiles/dev.md

# Agents are loaded with the profile and available for delegation
# Start a session with the dev profile
amplifier run "design an auth system"

# The session has access to zen-architect, bug-hunter, modular-builder, researcher
```

---

## Advanced Topics

### Overriding Bundled Collections

Collections are searched in precedence order (highest first):

1. **Project**: `.amplifier/collections/` (highest precedence)
2. **User**: `~/.amplifier/collections/`
3. **Bundled**: `<package>/data/collections/` (lowest precedence)

**Override bundled collections**:
```bash
# Install custom foundation to user directory
amplifier collection add git+https://github.com/yourteam/custom-foundation

# Your version takes precedence over bundled
amplifier profile use foundation:base  # Uses your version
```

### Scenario Tool Installation

Collections can include sophisticated scenario tools. These may be automatically installed when you add the collection (depending on your application's behavior):

```bash
# Add collection with scenario tools (amplifier-app-cli example)
amplifier collection add git+https://github.com/user/memory-solution

# Tools might be installed automatically
memory-analyzer --help  # Now available in PATH

# Or use via uvx
uvx --from memory-solution memory-analyzer [args]
```

See [SCENARIO_TOOLS_GUIDE](https://github.com/microsoft/amplifier-dev/blob/main/docs/SCENARIO_TOOLS_GUIDE.md) for creating scenario tools.

---

## Troubleshooting

### Collection not found

**Error**: `Collection 'xyz' not found`

**Check**:
```bash
# List installed collections
amplifier collection list

# Check search paths (paths depend on application)
ls ~/.amplifier/collections/
ls .amplifier/collections/
```

**Fix**: Install the collection
```bash
amplifier collection add git+https://github.com/user/xyz
```

### Resource not found in collection

**Error**: `Resource 'profiles/optimized.md' not found in collection 'memory-solution'`

**Check**:
```bash
# Show collection resources
amplifier collection show memory-solution

# Manually inspect (path depends on where it's installed)
ls ~/.amplifier/collections/memory-solution/profiles/
```

**Fix**: Ensure collection has that resource, or use correct path

### Missing dependencies

**Error**: Collection requires dependencies not yet installed

**Resolution**:
```bash
# Check collection metadata for dependencies
amplifier collection show <name>

# Install dependencies manually first
amplifier collection add git+https://github.com/org/dependency@v1.0.0

# Then install the collection
amplifier collection add git+https://github.com/org/collection@v1.0.0
```

**Note**: Current implementation requires manual dependency installation. Automatic dependency resolution may be added in future versions.

### Scenario tool not in PATH

**Error**: `command not found: memory-analyzer`

**Check**:
```bash
# Verify tool installation (if using uv)
uv tool list | grep memory-analyzer
```

**Fix**: Reinstall collection
```bash
amplifier collection remove memory-solution
amplifier collection add git+https://github.com/user/memory-solution
```

---

## Reference

### @Mention Patterns

| Pattern | Resolves To | Example |
|---------|-------------|---------|
| `@collection:path` | Collection resource | `@foundation:context/shared/common-agent-base.md` |
| `@user:path` | User directory | `@user:profiles/custom.md` → `~/.amplifier/profiles/custom.md` |
| `@project:path` | Project directory | `@project:context/notes.md` → `.amplifier/context/notes.md` |
| `@path` | Direct path | `@docs/guide.md` → `./docs/guide.md` |

### Resource Types

| Directory | Contains | Used By |
|-----------|----------|---------|
| `profiles/` | Profile definitions (.md) | Profile loading systems |
| `agents/` | Agent definitions (.md) | Loaded via profiles (see [amplifier-profiles](https://github.com/microsoft/amplifier-profiles)) |
| `context/` | Shared knowledge (.md) | @mentions in profiles/agents |
| `scenario-tools/` | CLI tools | Installed to PATH |
| `modules/` | Provider/tool/hook modules | Profiles reference via source URLs |

---

## Related Documentation

- **[Collection Authoring Guide](AUTHORING.md)** - Creating your own collections
- **[amplifier-collections API Reference](../README.md)** - Python API for developers
- [Scenario Tools Guide](https://github.com/microsoft/amplifier-dev/blob/main/docs/SCENARIO_TOOLS_GUIDE.md) - Creating sophisticated CLI tools
- **[Profile Authoring](https://github.com/microsoft/amplifier-profiles/blob/main/docs/PROFILE_AUTHORING.md)** - Creating profiles that use collections
- **[Agent Authoring](https://github.com/microsoft/amplifier-profiles/blob/main/docs/AGENT_AUTHORING.md)** - Creating agents that use collections
- [Context Loading](https://github.com/microsoft/amplifier-dev/blob/main/docs/CONTEXT_LOADING.md) - @mention syntax details

---

**Document Version**: 1.0
**Last Updated**: 2025-10-31
