# Orka CLI Agent Skill

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Structured Markdown context that gives AI agents correct Orka CLI commands instead of guesses. It covers `orka` (Orka 4.x) and `orka3` (Orka 3.x), and tells the agent which one to use.

## What's in it

| Path | Contents |
|------|----------|
| `orka-cli/SKILL.md` | Core concepts, which CLI to use, quick reference |
| `orka-cli/references/commands/` | Commands and flags: VM, image, emulator, node, admin, config, registry, VM config, upgrade, REST API |
| `orka-cli/references/workflows/` | CI/CD, scaling, image prep, admin setup, shared disk, upgrades, migration, monitoring, Orka Burst, licensing |
| `orka-cli/references/integrations/` | GitHub Actions, GitLab, Buildkite, Jenkins, TeamCity, Packer |
| `orka-cli/references/troubleshooting/` | Auth, deployment, image, and network issues |

Claude Code and Gemini CLI can run `orka` commands for you. Other agents use the same content to give you the command to run yourself.

> **Important:** Agents make mistakes, especially with destructive operations like deleting VMs or changing namespaces. Review what the agent plans to do before you confirm it. Running commands against your cluster also needs an authenticated CLI and network access to the cluster, for example over VPN.

## Prerequisites

- Access to an Orka cluster
- The Orka CLI on your `$PATH`: `orka` for 4.x, `orka3` for 3.x. Both can be installed side by side.

## Install

### Claude Code

Download the `.skill` archive from [Releases](https://github.com/macstadium/orka-cli-agent-skill/releases) and unzip it into your skills directory:

```bash
unzip orka-cli-v*.skill -d ~/.claude/skills/orka-cli
```

Or copy it from a clone:

```bash
git clone https://github.com/macstadium/orka-cli-agent-skill.git
cp -r orka-cli-agent-skill/orka-cli ~/.claude/skills/orka-cli
```

Restart Claude Code. The skill loads automatically when you ask about Orka, or run `/orka-cli`.

> Upgrading from the `orka3-cli` skill? Delete `~/.claude/skills/orka3-cli` first.

### Other agents

Load `orka-cli/SKILL.md` as context. For deeper coverage, add files from `orka-cli/references/`.

| Agent | Command or step |
|-------|-----------------|
| Gemini CLI | `cat orka-cli/SKILL.md >> ~/.gemini/GEMINI.md` |
| Cursor | `cp orka-cli/SKILL.md .cursor/rules/orka-cli.mdc` (or `~/.cursor/rules/` for all projects) |
| Windsurf | `cp orka-cli/SKILL.md .windsurf/rules/orka-cli.md` (or `~/.windsurf/rules/`) |
| GitHub Copilot | `cat orka-cli/SKILL.md >> .github/copilot-instructions.md` |
| Claude Desktop | Add `SKILL.md` to a project's instructions and upload reference files as project knowledge, or upload the `.skill` archive in **Settings > Capabilities > Skills** |

## Pair it with the docs MCP server

The skill handles "do this in Orka." The [MacStadium docs MCP server](https://docs.macstadium.com/mcp) handles "what does this Orka feature do." To add it to Claude Code:

```bash
claude mcp add --transport http macstadium-docs https://docs.macstadium.com/mcp
```

For other tools, see [Use these docs with AI tools](https://docs.macstadium.com/macstadium/macstadium-overview/use-these-docs-with-ai-tools).

## Example prompts

```
"What flags does orka vm deploy accept?"
"Show me all running VMs in namespace dev"
"Set up a service account for CI/CD"
"Deploy an Android emulator next to my VM"
```

## Build from source

```bash
./scripts/build-skill.sh 2.0.0   # or omit the version to use the latest git tag
```

The archive is written to `dist/orka-cli-v<VERSION>.skill`.

## More

- [Orka documentation](https://docs.macstadium.com)
- [Changelog](CHANGELOG.md) and [contributing](CONTRIBUTING.md)
- Orka CLI issues: [MacStadium Support](https://support.macstadium.com). Skill issues: [GitHub Issues](https://github.com/macstadium/orka-cli-agent-skill/issues)

Apache License 2.0. See [LICENSE](LICENSE).
