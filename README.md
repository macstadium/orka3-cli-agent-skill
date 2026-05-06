# Orka3 CLI Agent Skill

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Structured Markdown context for AI agents to work accurately with the Orka3 CLI. Load it into any agent that supports custom instructions or project context, and it will give you correct `orka3` commands instead of guessing.

## What's in this skill

| Path | Description |
|------|-------------|
| `orka3-cli/SKILL.md` | Core concepts, quick reference, v3.5.2 features, log sources |
| `orka3-cli/references/commands/` | Command syntax by domain: VM, image, node, admin, config, registry, vm-config |
| `orka3-cli/references/workflows/` | Step-by-step guides: CI/CD, scaling, migration, image prep, admin setup, shared disk |
| `orka3-cli/references/troubleshooting/` | Auth, deployment, image, and network issues |

## Agent compatibility

| Agent | Execution | Installation method |
|-------|-----------|---------------------|
| **Claude Code** | Runs `orka3` commands directly | Native skills directory |
| **Gemini CLI** | Runs `orka3` commands directly | Project context file |
| **Cursor** | Guidance only | Project or global rules |
| **Windsurf** | Guidance only | Project or global rules |
| **GitHub Copilot** | Guidance only | Repo instructions file |
| **Claude Desktop** | Guidance only | Project knowledge |
| **ChatGPT / other** | Guidance only | Custom instructions or file upload |

**Execution** means the agent can call `orka3` directly on your machine. **Guidance only** means the agent gives you the correct commands; you run them yourself. Either way, the skill content is the same.

> **Note:** When using an execution-capable agent, make sure you're connected to your Orka cluster via VPN before invoking CLI commands.

## Prerequisites

- Access to an Orka3 cluster
- Orka3 CLI installed and on your `$PATH` (`orka3`)
- The AI agent of your choice

## Installation

### Claude Code

Claude Code auto-discovers skills from `~/.claude/skills/`. Once installed, the skill appears as `/orka3-cli` and is invoked automatically when you ask about Orka3.

**Download from GitHub Releases (recommended)**

```bash
# Download the latest release from:
# https://github.com/macstadium/orka3-cli-agent-skill/releases
unzip orka3-cli-v*.skill -d ~/.claude/skills/orka3-cli
```

**Clone and copy**

```bash
git clone https://github.com/macstadium/orka3-cli-agent-skill.git
cp -r orka3-cli-agent-skill/orka3-cli ~/.claude/skills/orka3-cli
```

Restart Claude Code, then verify:

```
/orka3-cli
```

### Gemini CLI

Copy `SKILL.md` into your Gemini context file:

```bash
cat orka3-cli/SKILL.md >> ~/.gemini/GEMINI.md
```

To include the full reference content, append individual files from `orka3-cli/references/` as needed.

### Cursor

Add the skill as a project rule or a global rule.

**Project rule (applies to one repo)**

```bash
mkdir -p .cursor/rules
cp orka3-cli/SKILL.md .cursor/rules/orka3-cli.mdc
```

**Global rule (applies to all projects)**

```bash
mkdir -p ~/.cursor/rules
cp orka3-cli/SKILL.md ~/.cursor/rules/orka3-cli.mdc
```

You can also copy individual reference files into the same directory for deeper context.

### Windsurf

```bash
# Project-level
mkdir -p .windsurf/rules
cp orka3-cli/SKILL.md .windsurf/rules/orka3-cli.md

# Or global
mkdir -p ~/.windsurf/rules
cp orka3-cli/SKILL.md ~/.windsurf/rules/orka3-cli.md
```

### GitHub Copilot

Add the skill content to your repository's Copilot instructions file:

```bash
cat orka3-cli/SKILL.md >> .github/copilot-instructions.md
```

For personal use across all repos, go to **Settings > Copilot > Custom Instructions** in GitHub and paste the contents of `SKILL.md`.

### Claude Desktop

1. Create a new Project in Claude Desktop
2. Open project settings and add custom instructions
3. Paste the contents of `orka3-cli/SKILL.md` into the instructions field
4. Upload reference files from `orka3-cli/references/` as project knowledge

### Other agents

Most agents that support custom instructions or file upload will work. Load `orka3-cli/SKILL.md` as the base context. For broader coverage, also load the files under `references/commands/` and `references/workflows/`.

## Usage

Once loaded, ask your agent about anything Orka3-related:

```
"Deploy 3 VMs with macOS Sonoma"
"What flags does orka3 vm deploy accept?"
"Show me all running VMs in namespace dev"
"Set up a service account for CI/CD"
"Help me troubleshoot a failed VM deployment"
"Cache the Sequoia image across all nodes"
```

Execution-capable agents (Claude Code, Gemini CLI) will run the commands directly. Other agents will give you the correct syntax to run yourself.

## Capabilities

### VM management
- Deploy VMs from local or OCI images
- Configure CPU, memory, and disk resources
- Save and commit VM states to images
- Resize VM disks
- Power operations (Intel: start/stop/suspend/resume)

### Image management
- List, copy, and delete local images
- Cache images on nodes (Apple Silicon)
- Push images to OCI registries
- Generate empty images for OS installs (Intel)

### Infrastructure
- View and manage cluster nodes
- Tag nodes for workload affinity
- Create and manage namespaces
- Configure access control with rolebindings
- VM shared attached disk configuration (AWS and on-prem)
- Log sources for deep troubleshooting (v3.4+)

### Automation
- Create and manage service accounts
- Generate authentication tokens
- Create VM configuration templates
- Set up CI/CD pipelines

## Architecture support

| Feature | Intel (amd64) | Apple Silicon (arm64) |
|---------|---------------|----------------------|
| VM Deploy | Yes | Yes |
| Power Operations | Yes | No |
| GPU Passthrough | Yes | No |
| ISO Attach | Yes | No |
| Image Cache | No | Yes |
| OCI Push | No | Yes |

## Building from source

```bash
# Build with an explicit version
./scripts/build-skill.sh 1.2.0

# Or use the latest git tag
./scripts/build-skill.sh
```

The archive is written to `dist/orka3-cli-v<VERSION>.skill`.

## Documentation

- [MacStadium Orka Documentation](https://docs.macstadium.com)
- [Changelog](CHANGELOG.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Support

- Orka3 CLI issues: [MacStadium Support](https://support.macstadium.com)
- Skill issues: [GitHub Issues](https://github.com/macstadium/orka3-cli-agent-skill/issues)
