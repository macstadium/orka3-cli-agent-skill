# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-08-24

### Added

- `references/commands/emulator-commands.md` — Android emulator command reference (early access, Orka 3.7.0-alpha+, Apple Silicon only): `orka3 emulator deploy`/`list`/`delete` syntax, flags, `adbRelayIP`/`adbRelayPort` connection notes, and known limitations (node-level network isolation, NAT-only, ephemeral AVD state, no SDK pre-caching)
- `SKILL.md`: Android Emulators bullet in Essential Context, command examples under Quick CLI Guide, and a new Reference Files row for `emulator-commands.md`
- `references/troubleshooting/image-issues.md`: "Fixed in Orka 3.6.4" section covering the caching-job deadline fix (`cache_job_active_deadline_seconds`), the 3.6.3 cache-eviction regression fix, and the `--enable-custom-pods` role binding fix; new "Known Issue" section for the open 3.6.3+ re-caching bug (same-name image commits skipping re-cache) with workaround
- `references/troubleshooting/auth-issues.md`: note on the 3.6.4 fix for missing `orka-dev` role bindings on `--enable-custom-pods` namespaces, and manual remediation via MacStadium support for namespaces created before the fix
- `references/commands/admin-commands.md`: cross-reference note on the same `--enable-custom-pods` role binding fix under `orka3 namespace create`

### Fixed

- `orka3-cli/SKILL.md`: replaced content that had silently regressed to the pre-PR#5 format (stale "Current Version: 3.5.2" banner, verbose prose) in commit `2205675`; rebuilt from the actively-maintained rewrite so it matches the reference files, which had continued to receive updates through 3.6.3 independently of `SKILL.md`

## [1.3.0] - 2026-07-14

### Added

- `references/workflows/upgrade-workflows.md` — on-prem and hosted upgrade process, Kubernetes upgrade impact and post-upgrade verification, AWS upgrade via SSH and SSM methods, Upgrade Service (`orka3 version` / `kubectl get orkanodes`)
- `references/workflows/license-management.md` — LicenseSpring portal auth, seat usage, node activation revocation, AWS license key override, automated expiry notifications
- `orka3 imagecache remove` (GA in 3.6.3) — full command reference in `image-commands.md`: syntax, `--nodes`/`--tags`/`--all` flags, removal states (`Removing`/`Failed`), edge cases (no-op if not cached, immediate cleanup if node gone)
- `upgrade-workflows.md` and `license-management.md` added to SKILL.md reference table
- Integrations directory added to README reference table

### Changed

- `SKILL.md`: added VM network isolation note (v3.6+, Apple Silicon only) and Kubernetes upgrade resilience note (v3.6+)
- `references/commands/vm-commands.md`: UDP/TCP protocol suffix documented for `--ports` flag
- `references/commands/config-commands.md`: `orka3 version` now shows Upgrade Service operator version; `kubectl get orkanodes -o wide` shows per-node agent version
- `references/integrations/github-actions.md`: corrected `MANAGE_RUNNER_SCALE_SETS` default (`false`, not `true`); added `ORKA_VM_METADATA` and `METRICS_POLL_INTERVAL`; added ECDSA private key support note; consolidated orphaned VM cleanup note; removed undocumented `VM_TRACKER_INTERVAL`
- `references/integrations/packer.md`: added bridge networking note
- `references/workflows/image-workflows.md`: updated VM Tools note to reflect automated GHCR updates

## [1.2.1] - 2026-02-11

### Fixed

- Release workflow: added `workflow_dispatch` fallback so releases can be manually triggered from the Actions tab when tag-push triggers don't fire (known GitHub Actions quirk with tags created through the Releases UI)

### Changed

- Updated `SKILL.md` frontmatter description to include "command syntax", "flag reference", and "exact flags and options" — signals Claude to invoke the skill when it needs CLI syntax help, not just for natural-language VM management requests
- Added "What Is a Claude Code Skill?" section to README explaining auto-discovery, `/orka3-cli` slash command, and auto-invocation
- Added post-install verification step to README

## [1.2.0] - 2026-02-11

### Changed

- Moved skill content (`SKILL.md`, `references/`) into `skill/` subdirectory to separate installable content from development artifacts
- Updated installation instructions: download `.skill` from GitHub Releases or copy `skill/*`
- Updated Claude Desktop instructions to reference `.skill` archive upload

### Added

- `scripts/build-skill.sh` — builds a `.skill` zip archive from `skill/` directory
- `.github/workflows/release.yml` — tag-triggered pipeline that creates GitHub Releases with `.skill` archive attached
- `.gitignore` for build artifacts, OS files, and editor files
- "Building from Source" section in README

### Removed

- `orka3-skill-combined.md` — 97KB maintenance burden; users should install the skill or reference individual files instead
- `references/archive/` — superseded v1.0.0 monolithic files (preserved in git history)

## [1.1.0] - 2026-02-05

### Added

- Orka 3.5.2 features in `SKILL.md`: namespace auto-detection, shared attached disks, macOS Tahoe/Sequoia compatibility
- Log sources reference (v3.4+) in `SKILL.md` and deployment troubleshooting
- Shared disk workflows (`references/workflows/shared-disk-workflows.md`)
- Default namespace detection section in `references/commands/config-commands.md`
- Combined skill file (`orka3-skill-combined.md`) for Claude Desktop projects
- VPN connection note for Claude Code users in README
- "Before You Respond" section in `SKILL.md` requiring environment probing (architecture, version, context) before answering any question or executing any command
- Operating Guidelines section in `SKILL.md` (formerly "Documentation & Troubleshooting Guidelines") with:
  - CLI patterns: Use built-in filtering instead of piping to grep
  - CI/CD authentication: Always use service accounts, never user tokens
  - Environment variables: Must be in CI/CD settings, not shell export
  - Network connectivity: Use curl to `/api/v1/cluster-info`, avoid ping
  - Troubleshooting approach: Trust CLI errors, understand execution context
  - Pre-flight checklist for all responses (not just documentation)
  - Example patterns for SSH troubleshooting in CI/CD environments

### Changed

- Restructured reference docs from 3 monolithic files into 18 domain-specific files under `references/commands/`, `references/workflows/`, and `references/troubleshooting/`
- Original monolithic files moved to `references/archive/`
- Updated SKILL.md with new reference documentation index pointing to chunked files
- Expanded README with Claude Code vs Regular Claude guidance, installation options, architecture support table

### Security

Addressed [W007] warning from Invariant MCP-scan (insecure credential handling, risk: 0.80):

- Updated OCI registry credential examples to use environment variables (`$REGISTRY_TOKEN`) instead of inline tokens
- Updated VM resize examples to use environment variables (`$VM_USER`, `$VM_PASSWORD`) for credentials
- Added security notes explaining that MacStadium base images use default credentials (`admin`/`admin`) which should be changed for production

Run `uvx mcp-scan@latest --skills` to verify.

### Documentation

- Added "Problem-Solving Approach" section with guidelines:
  - Define the problem first - push back on vague requests
  - Map the user journey before jumping to solutions
  - For Orka integrations: READ THE REPO ARCHITECTURE FIRST
  - Design/stub before implementing
  - Verify context and source of truth
  - Humans review every output

- Added "Pre-Flight Checklist for Documentation" with verification steps:
  - Problem definition and scope
  - Read the integration code first
  - Authentication patterns (service accounts only for CI/CD)
  - CLI patterns (no grep, use built-in filtering)
  - Execution context awareness
  - Content structure (one approach per problem)
  - Security (no hardcoded credentials)
  - Coherence check (cascade through all sections)

## [1.0.0] - 2026-01-29

### Added

- Initial release of the Orka3 CLI Claude Skill
- Main skill definition (`SKILL.md`) with:
  - Core concepts (architecture types, components, authentication)
  - Getting started workflow
  - Quick VM operations reference
  - Image management commands
  - VM lifecycle operations
  - VM configuration templates
  - Node management
  - Namespace management
  - Access control (RBAC)
  - Common workflow summaries
  - Command patterns and flags
  - Architecture-specific features
  - Best practices

- Complete command reference (`references/command-reference.md`) with:
  - Configuration commands
  - Authentication commands
  - Service account commands
  - Image commands
  - Image cache commands (Apple Silicon)
  - OCI registry commands
  - VM commands (deploy, list, delete, save, commit, push, resize, power ops)
  - VM configuration commands
  - Node commands
  - Namespace commands
  - RBAC commands
  - Utility commands

- Workflow documentation (`references/workflows.md`) with:
  - Initial setup workflow
  - CI/CD pipeline setup
  - Custom image preparation
  - Multi-namespace team setup
  - Image caching for fast deployments
  - OCI registry integration
  - Scaling VMs for load testing
  - VM disk management
  - Node affinity and tagging strategy
  - Disaster recovery and backup
  - Troubleshooting deployment issues
  - Migration from Intel to Apple Silicon
  - Resource optimization

- Troubleshooting guide (`references/troubleshooting.md`) with:
  - Authentication issues
  - VM deployment issues
  - Image management issues
  - Namespace and access issues
  - Network and connectivity issues
  - Performance issues
  - Common error messages
  - Prevention tips

### Features

- Natural language to Orka3 CLI command translation
- Support for both Intel (amd64) and Apple Silicon (arm64) architectures
- VM lifecycle management
- Image management (local and OCI)
- Node operations and tagging
- Namespace and RBAC management
- Service account management for CI/CD automation
