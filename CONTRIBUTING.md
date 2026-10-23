# Contributing to Orka3 CLI Claude Skill

Thank you for your interest in contributing to the Orka3 CLI Claude Skill! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion for improvement:

1. Check existing [GitHub Issues](https://github.com/macstadium/orka3-cli-claude-skill/issues) to see if it's already reported
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Your environment (Claude Code version, Orka3 CLI version)

### Suggesting Improvements

We welcome suggestions for:

- New command examples
- Additional workflow documentation
- Improved troubleshooting guidance
- Better natural language patterns
- Documentation clarifications

Please open an issue to discuss your idea before submitting a pull request.

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Test the skill locally by copying to `~/.claude/skills/orka3-cli`
5. Commit your changes with a clear message
6. Push to your fork
7. Open a pull request

### Pull Request Guidelines

- Keep changes focused and atomic
- Update documentation if adding new features
- Follow existing formatting and style
- Add examples where appropriate
- Test your changes with Claude Code

### Checking commands and flags against the CLI

The CLI drift check (`.github/workflows/cli-drift-check.yml`) runs on every pull request that touches `orka3-cli/`, and weekly. It compares the commands and flags in the skill with the help of a released CLI build, so an example that uses a flag the CLI doesn't have fails the check. It reports:

- **Errors:** a command heading, an example command, an example flag, or an Options list entry that the CLI doesn't have.
- **Warnings:** a CLI flag that a command reference's Options list leaves out. These fail the check only with `--strict`.

To run it locally, download the CLI version the workflow checks (`CLI_VERSION` in the workflow) and point the script at the binary. On macOS, expand the package without installing it:

```bash
VERSION=3.7.0-alpha
mkdir -p /tmp/orka-cli && cd /tmp/orka-cli
curl -fsSLO "https://cli-builds-public.s3.amazonaws.com/official/${VERSION}/orka3/macos/arm64/orka3.pkg"
pkgutil --expand-full orka3.pkg expanded
cd -
python3 scripts/cli-drift-check.py --cli /tmp/orka-cli/expanded/orka3.pkg/Payload/orka3
```

On Linux, download `.../official/${VERSION}/orka3/linux/amd64/orka3.tar.gz` and extract it instead. For 4.0 and later the CLI is `orka`, so replace `orka3` with `orka` in the URL and path. The script needs Python 3 and nothing else, and it doesn't contact a cluster.

A few conventions keep the check accurate:

- Mark a command that is gone from the CLI with "Removed in Orka X" or "Deprecated in Orka X" in its section, or in the intro of its `##` group. The CLI hides deprecated commands from its help, so the check skips marked commands instead of reporting them.
- Example lines that start with `orka3` are 3.x-only once the skill documents a 4.x `orka` CLI, and the check skips them. Against a 3.x CLI it skips `orka` lines instead. Use `--binary-name` to override the name the script reads from the CLI.
- List flags under a `**Options:**` label as `` - `--flag type` - description `` (or `` - `-f, --flag type` ``) so the check can compare them.

## File Structure

When contributing, understand the purpose of each file:

| Path | Purpose |
|------|---------|
| `skill/SKILL.md` | Main skill definition - core concepts, quick reference |
| `skill/references/commands/` | CLI syntax documentation organized by domain (7 files) |
| `skill/references/workflows/` | Multi-step task guides by topic (7 files) |
| `skill/references/troubleshooting/` | Problem diagnosis and solutions by issue type (4 files) |
| `scripts/build-skill.sh` | Builds `.skill` zip archive for distribution |
| `.github/workflows/release.yml` | Tag-triggered release pipeline |

All skill content lives under `skill/`. Development artifacts (README, LICENSE, scripts, CI) stay at the repo root.

## Style Guidelines

### Markdown

- Use ATX-style headers (`#`, `##`, `###`)
- Use fenced code blocks with language hints (```bash)
- Keep lines under 100 characters when practical
- Use consistent indentation (2 spaces)

### Code Examples

- Always test commands before documenting
- Include both common and advanced usage
- Show expected output where helpful
- Note architecture-specific commands (Intel vs Apple Silicon)

### Documentation

- Write in clear, concise English
- Use active voice
- Explain the "why" not just the "how"
- Include practical examples

## Testing Changes

Before submitting a pull request:

1. Copy the skill to your Claude Code skills directory:
   ```bash
   cp -r skill/* ~/.claude/skills/orka3-cli/
   ```

2. Test with Claude Code by asking questions like:
   - "How do I deploy a VM with Orka3?"
   - "Show me how to set up CI/CD"
   - "What's the command to cache images?"

3. Verify the skill provides accurate, helpful responses

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy toward other contributors

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks
- Publishing others' private information
- Other unprofessional conduct

### Enforcement

Project maintainers may remove, edit, or reject contributions that don't align with this Code of Conduct.

## Questions?

If you have questions about contributing:

- Open a GitHub issue for project-related questions
- Contact [MacStadium Support](https://support.macstadium.com) for Orka3-specific questions

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
