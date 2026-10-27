# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - Unreleased

Folds in verified findings from Robert Elwell's Orka agent playbooks, which were tested against a live Orka 3.6.3 cluster. Every item was checked against the Orka 3.6 CLI help, the Orka source, the public docs, or the integration repos before inclusion.

### Added

- `references/commands/rest-api.md`: Swagger UI, bearer auth with service-account tokens, endpoint paths, the `items` list wrapper, `customMetadata` on deploy, save/commit/push request bodies
- `references/integrations/jenkins.md`: Orka by MacStadium plugin (v2.10) cloud and agent template fields, retention strategies, permanent agents, logging
- `references/workflows/monitoring.md`: node exporter and operator scrape targets, Orka operator metric names (3.6), macOS vs Linux memory metrics, alerts for disk-driven cache eviction and CI backlog
- `references/workflows/burst-workflows.md`: Orka Burst (3.3+) through the Portal API, with drain-before-disable ordering
- `SKILL.md`: Apple silicon 2-VM-per-node limit and slot-based capacity, Orka 3.6 as the last Intel release, bare-array `-o json` shape
- `vm-commands.md`: VM metadata server, `vm push` status values (`Ready`/`Failed`) and `-n`, guest `sync` before push/save/commit, save/commit require NFS image storage, display flag ranges, memory caps, `owner` in `vm list -o json`, deploy returns before macOS finishes booting
- `image-commands.md`, `image-issues.md`: cache timing and eviction, cache job cost, never remove a cache during a deploy, pre-3.5.2 custom-namespace caching bugs, `Unauthorized` on push with a certificate-only kubeconfig
- `vm-config-commands.md`: configs always live in `orka-default`, no update command (blue/green rollout), half-node sizing
- `node-commands.md`, `admin-workflows.md`: `node namespace` is refused while VMs run (drain first), Apple silicon can't join custom-pods namespaces, cordoned nodes still show READY
- `admin-commands.md`: service-account token lifetime and revocation details, custom-pods toleration, `rb list-subjects` JSON shape
- `deployment-issues.md`: real 3.6 error strings, 2-VM limit error, cordoned-node symptom, RFC 1123 vs DNS-1035 name errors, on-prem node diagnosis
- `cicd-workflows.md`: CI concurrency at or below slot capacity, trap-based VM cleanup, leaked-VM cleanup by owner/prefix/age, integration smoke test
- `github-actions.md`: `GITHUB_PAT` (v1.1.15), `ORKA_NAMESPACE`, `MAX_RUNNERS`, tracker and deregistration settings, runner metric names
- `gitlab.md`, `buildkite.md`, `packer.md`: missing settings, defaults, and concurrency guidance

### Fixed

- TeamCity: plugin 2.0.2 installs from the JetBrains Marketplace (no `./gradlew build`), authenticates only with a service account token (no email/password), and the profile has Namespace and Node mappings fields; added the first-ARM-deploy timeout known issue
- Namespace resolution: `orka3 user login` and `orka3 user set-token` reset the `orka` context namespace to `orka-default`, so `ORKA_DEFAULT_NAMESPACE` is the lasting default; the precedence order applies only to `vm`, `node`, `imagecache`, `registrycredential`, `rolebinding`, `serviceaccount`; `orka3 upgrade service` always defaults to `orka-default`
- `monitoring.md`: added the Orka server metrics target at `/api/v1/metrics` (GET check, HEAD returns 404)
- VM Tools version guidance: any VM Tools 3.6.0 or later work on both 3.6 and 4.0 clusters (the 4.0.0 Homebrew release includes the fix for 3.6 hosts); 4.0 VM Tools are needed only for User Data
- VM metadata: Orka reserves six exact keys (`orka_vm_id`, `orka_vm_name`, `orka_base_image`, `orka_cpu`, `orka_memory`, `orka_node_name`), not the `orka_` prefix
- Image cache: a cache job requests 0.5 CPU from the scheduler, separate from what it uses; disk I/O is what slows running VMs. Eviction removes the least recently used images, not the oldest
- `monitoring.md`: node exporter is installed by MacStadium's provisioning, so it's only present on MacStadium-hosted clusters
- `upgrade-workflows.md`: removed the claim that service account tokens must be regenerated after an upgrade; no release note requires it
- `burst-workflows.md`: the cluster ID query uses `nodes`, not `edges { node }` (`OrkaServiceConnection` has only `nodes` and `pageInfo`)
- `packer.md`: check a timed-out push with `orka3 vm get-push-status -n <BUILDER_NS>`; the argument is a push job name, not the VM name
- `gitlab.md`: warn that the upstream `troubleshooting.md` exists only on `master` and its mount-the-key advice doesn't work
- `jenkins.md`: removed the Orka 4.0 section; this release covers 3.x only
- Image cache: the custom-namespace fix is complete in 3.5.2, not 3.5.1; eviction triggers only when the pull needs more space than is free, with no percentage threshold
- `SKILL.md`: `orka3 upgrade` JSON output is an object, not an array; `emulator` (3.7.0-alpha) uses the shared namespace resolver
- `node-commands.md`: added `allocatableGpu`, `availableGpu`, `os`, and `upgradeAgent` JSON keys
- `admin-commands.md`: `--no-expiration` wins without an error when passed with `--duration`
- `deployment-issues.md`: the required-tag error is multi-line
- Android emulator commands: `--platform` and `--image-type` are required with no defaults, the device flag is `--device-profile`, `emulator list` has no `--vm` filter, and connection details are `RELAY-IP`/`RELAY-PORT` (`relayIp`/`relayPort`), not `adbRelayIP`/`adbRelayPort`
- `-o json` examples: `.[]` and `.[0].name`, not `.items[]` or `.name`
- `orka3 vmc create` examples no longer pass `--namespace` (the flag doesn't exist)
- `orka3 regcred remove <SERVER>`, not `regcred delete <NAME>`; `--password-stdin` instead of `--password`
- Imagecache states are `Ready`, `Caching`, `Failed`, `Removing`, `RemoveFailed`
- Apple silicon `vm resize` needs Orka VM Tools in the guest; it isn't automatic
- `orka3 namespace list` is admin-only
- Packer: `packer_push_timeout` isn't in plugin v3.1.2; debug flags are `no_delete_vm`/`no_create_image`
- GitHub Actions: classic PATs are supported; private keys must be PKCS#1 RSA; `GITHUB_API_URL` is ignored
- GitLab: the SSH key must be the contents of the `ORKA_SSH_KEY_FILE` CI/CD variable; a mounted key file is ignored, and it can't be masked because it's multi-line
- Removed `grep`, `awk`, and `sort` pipes on CLI output in favor of built-in filtering or `-o json | jq`

## [1.4.0] - 2026-09-11

### Added

- `references/commands/emulator-commands.md` — Android emulator command reference (early access, Orka 3.7.0-alpha+, Apple Silicon only): `orka3 emulator deploy`/`list`/`delete` syntax, flags, `adbRelayIP`/`adbRelayPort` connection notes, and known limitations (node-level network isolation, NAT-only, ephemeral AVD state, no SDK pre-caching)
- `SKILL.md`: Android Emulators bullet in Essential Context, command examples under Quick CLI Guide, and a new Reference Files row for `emulator-commands.md`
- `references/troubleshooting/image-issues.md`: "Fixed in Orka 3.6.4" section covering the caching-job deadline fix (`cache_job_active_deadline_seconds`), the 3.6.3 cache-eviction regression fix, and the `--enable-custom-pods` role binding fix; new "Known Issue" section for the open 3.6.3+ re-caching bug (same-name image commits skipping re-cache) with workaround
- `references/troubleshooting/auth-issues.md`: note on the 3.6.4 fix for missing `orka-dev` role bindings on `--enable-custom-pods` namespaces, and manual remediation via MacStadium support for namespaces created before the fix
- `references/commands/admin-commands.md`: cross-reference note on the same `--enable-custom-pods` role binding fix under `orka3 namespace create`
- `references/workflows/upgrade-workflows.md`: real Upgrade Service v2 self-service command flow (`orka3 upgrade run/status/history/versions`, `orka3 upgrade service status/agents`), replacing the stale v1 "MacStadium pushes upgrades" description
- `references/workflows/upgrade-workflows.md`: new "Orka Anywhere upgrades (self-service, AWS-hosted or on-premises)" section — Ansible-based idempotent re-upgrade process, `osx_node_orka_engine_version`/`osx_node_orka_vk_version` version-pin vars, and the v1→v2 Upgrade Service migration script for Anywhere clusters
- `references/workflows/upgrade-workflows.md`: new "Per-node pod quota (Apple silicon)" section, split by version: 3.6 fixed default of `4`, 3.7.0-alpha tunable `osx_node_orka_quota_pod` (default `4`), 4.0 `osx_node_orka_quota_pod` of `110` plus `osx_node_orka_quota_job` (default `2`) for cache and push jobs
- `references/workflows/upgrade-workflows.md` and `SKILL.md`: upgrading to Orka 4.0 is support-led; the Upgrade Service can't perform it yet
- `SKILL.md`: Essential Context bullets for the per-node pod quota and the self-service (not support-ticket-only) upgrade model for both MSDC and Orka Anywhere
- `references/troubleshooting/image-issues.md`: new "Problem: `imagecache remove` fails or isn't recognized despite an up-to-date CLI" entry — this is a cluster-side version gate (3.6.3+), not a CLI one, a real, repeated customer point of confusion
- `references/workflows/upgrade-workflows.md`: Upgrade Service troubleshooting (30-minute admission limit, quarantined releases, `STALE` after 90 seconds without a lease renewal, skip reasons in `upgrade status -o json`), read-only access for status/history/versions, and availability by deployment
- `references/workflows/upgrade-workflows.md`: Webhooks PodDisruptionBudget guidance for 3.6 vs. 4.0, including deleting a custom `app: orka-webhooks` PDB before upgrading to 4.0
- `references/workflows/upgrade-workflows.md`: warning not to pin `osx_node_orka_engine_version` to the release version on-prem (`official/3.6.4` returns HTTP 403 on every node)

### Fixed

- `orka3-cli/SKILL.md`: replaced content that had silently regressed to the pre-PR#5 format (stale "Current Version: 3.5.2" banner, verbose prose) in commit `2205675`; rebuilt from the actively-maintained rewrite so it matches the reference files, which had continued to receive updates through 3.6.3 independently of `SKILL.md`
- `SKILL.md`: corrected "Orka Cluster Upgrades" framing, upgrades are self-service via the CLI as of 3.6+ Upgrade Service v2, not support-ticket-initiated only
- `references/troubleshooting/image-issues.md`: the `imagecache remove` entry now checks cluster version with `orka3 version` and `orka3 node list -o wide`, since `orka3 upgrade versions` reports `unknown` before the first Upgrade Service v2 run
- `SKILL.md`: the "Claude Code" execution-context bullet now names Gemini CLI too and generalizes to "execution-capable agent," matching the skill's own documented multi-agent compatibility (see README)

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
