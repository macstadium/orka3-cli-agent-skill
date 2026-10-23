# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2.0.0 (Orka 4.0)

Draft, held until Orka 4.0 ships (GA around 2026-10-28). Verified against `releases/cluster/4.0` at `57f99689`, the published 4.0.0 CLI build, and macstadium-docs #383, #390, #394, #402, #406, #417, and #436. Major version because the CLI command changes.

### Changed

- **CLI renamed to `orka` (OK-6390).** Command examples, headings, and anchors use `orka`. `SKILL.md` has a new "Which CLI" section: `orka` is the 4.x CLI, `orka3` stays the 3.6 CLI, both install side by side and share the config file and the `orka` kubeconfig context, no alias ships, running the 4.0 CLI as `orka3` warns on stderr only, the optional `orka3` symlink bridge and its caveats, no `orka` Homebrew cask yet, and the legacy 2.x `orka` note. Intel-only and removed commands, the Intel to Apple silicon migration, and other 3.6-only steps stay `orka3`. The skill name and directory are unchanged.
- Android emulators are GA in Orka 4.0, no longer early access.
- Emulator commands resolve the namespace like `vm` (`--namespace`, `ORKA_DEFAULT_NAMESPACE`, the `orka` context, then `orka-default`); emulator configurations always live in `orka-default`.
- Workflow and troubleshooting examples use `orka rbac ... --role dev`. `rolebinding` is deprecated and hidden from `--help` in 4.0; 3.6 users get an `orka3 rb` note.
- NFS-hosted images, `image`, `remote-image`, `vm save`, and `vm commit` marked deprecated in 4.0, with the exact stderr warning.
- Pod quota text from 1.4.0 marked as Orka 3.6 and 3.7.0-alpha only.
- The 3.6.3+ same-name re-cache known issue is marked fixed in Orka 4.0.

### Added

- `emulator-commands.md`: `emulator-config create`/`list`/`delete` (aliases `emc`, `emuconfig`), `--config` and `--grpc` on deploy, `--grpc=false` and `--device-profile ""` overrides, gRPC endpoint section, list columns including `-o wide`, CLI JSON keys (`relayIp`, `relayPort`, `grpcPort`), `PairedVMStopped` and `EmulatorUnschedulable`, sizing and density (about 5 to 6 GB of host memory per emulator, memory is the usual limit, CPU and memory come from the device profile, animation `adb` commands), REST paths, and the Play Store ADB limitation as a 4.0 known issue.
- `vm-commands.md`: `--userdata` and `USERDATA-PHASE`, with run-once semantics, the meaning of `skipped`, the 3.7.0-alpha VM Tools exception, and script visibility through Kubernetes read access. Removed `vm resize --user`/`--password`. `vm` and `image` reject unknown subcommands with a non-zero exit.
- `admin-commands.md`: `rbac add-subject`/`list-subjects`/`remove-subject` with `--role admin|dev`, the MSDC-hosted `--role admin` limitation, and the `rolebinding` deprecation message.
- `rest-api.md`: "Orka 4.0 API Changes" (removed routes return `404`, `cluster-info` drops `gpuPassthroughEnabled`, Intel-only fields return `400`, `netBoost` accepted and ignored, webhook rejection messages, 3.6 objects can still be updated and deleted, deprecation headers), emulator configuration endpoints, `config` and `grpc` on deploy, `grpcRelayPort`, `userdata`, and the `/api/v1/rbac` routes.
- `upgrade-workflows.md`: "Upgrading to Orka 4.0" (requires 3.6, Intel worker nodes block the upgrade at the pre-check with no changes made, schedule with support), Orka-managed PDBs and other control plane changes, and the 4.0 per-node limits (`osx_node_orka_quota_job` default `2`, node pod quota `110`, emulators uncapped).
- `deployment-issues.md`: `Not enough disk space on node <NODE> to deploy the VM`, and Intel image or setting rejections on 4.0.
- `image-commands.md`, `image-issues.md`: `imagecache remove --all`/`--tags` skip uncached nodes (per-node `202`) on 4.0, cache record cleanup, and the 4.0 eviction fixes.
- `monitoring.md`: 4.0 operator metrics (`vm_namespace` label, pending-VM queue metrics, exponential buckets, `orka-webhooks` metrics endpoint).

### Removed

- Documented the Orka 4.0 removals rather than deleting them, since Orka 3.6 remains the last Intel release and is supported through March 2028: `orka3 vm start|stop|suspend|resume|revert`, `orka3 image generate`, the `orka3 iso` and `orka3 remote-iso` commands, the `--iso`, `--gpu`, `--system-serial`, `--disable-net-boost`, and `--legacy-io` flags on `vm deploy` and `vm-config create`, and `--user`/`--password` on `vm resize`.

### Fixed

- `emulator-commands.md` said gRPC on an emulator configuration was CLI-only. The REST API accepts `grpc` on configuration create and returns it in configuration responses.
- `emulator-commands.md` said `--device-profile` needed Orka 4.0. It was already in 3.7.0-alpha; 4.0 adds `--config` and `--grpc`.
- `emulator-commands.md` documented `--device`, `--cpu`, and `--memory` on `emulator deploy`, and a `--vm` filter on `emulator list`. The CLI has never accepted any of them. Removed, with a note so they don't get reintroduced.
- Em dashes replaced throughout the skill.

## [Unreleased] - 1.6.0

Ports Orka 3.x documentation changes from docs.macstadium.com (September to October 2026). Version tables, compatibility data, and known-issue lists are summarized with a link to the docs page instead of copied in full.

### Added

- `upgrade-workflows.md`: "Checking component versions" (`orka3 version` fields, `orka3 node list -o wide` `VERSION`/`RUNTIME`, `--client`, patch releases only bump changed components, link to the component matrix) and the on-prem `orka-ansible-onprem:3.6.4` installer re-pull note
- `image-workflows.md`: "macOS Guest Compatibility" summary (macOS 27 Golden Gate needs a 26.6.2+ host and more than 2 GB of RAM, macOS 27 isn't signed off as a host OS, `latest` on MacStadium images means latest published), hardened image tagging and pre-caching, VM Tools needs macOS 13+
- `image-issues.md`: known issue for in-place macOS 15.x and 26.x upgrades inside a VM, with the memory check and the installer workaround
- `admin-commands.md`, `auth-issues.md`: hosted-cluster admin limits and the managed `orka-admin` service account (`orka3 sa token orka-admin`)
- `migration-workflows.md`: NFS-to-OCI migration with Harbor, including CI/CD repointing
- `scaling-workflows.md`: node disk sizing from maximum provisioned size, and where to check storage usage
- `config-commands.md`: `config set --api-url` doesn't change the kubeconfig `server` entry; `orka3 version` output fields and `--client`
- `rest-api.md`: Android emulator REST endpoints (3.7.0-alpha)
- `emulator-commands.md`: `google_apis_playstore` images reject ADB (`device unauthorized`)
- `SKILL.md`: Essential Context bullets for component versions and macOS guest rules; reference table entries updated

### Changed

- Placeholders in command examples are `<UPPER_SNAKE>` matching orka3 help (for example `<SERVICE_ACCOUNT_NAME>`, `<VM_CONFIGURATION_NAME>`, `<ORKA_API_URL>`)
- "IP plan" references now say My Cloud

### Fixed

- `image-commands.md`: removed the `orka3 image list --arch amd64` example; `image list` has no `--arch` flag (drift check, skill PR #19)
- `emulator-commands.md`: the device-profile example no longer uses a Play Store image

## [1.5.0] - 2026-10-06

Folds in verified findings from Robert Elwell's Orka agent playbooks, which were tested against a live Orka 3.6.3 cluster. Every item was checked against the Orka 3.6 CLI help, the Orka source, the public docs, or the integration repos before inclusion.

### Added

- `references/commands/rest-api.md`: Swagger UI, bearer auth with service-account tokens, endpoint paths, the `items` list wrapper, `customMetadata` on deploy, save/commit/push request bodies
- `references/integrations/jenkins.md`: Orka by MacStadium plugin (v2.10) cloud and agent template fields, retention strategies, permanent agents, logging
- `references/workflows/monitoring.md`: node exporter and operator scrape targets, Orka operator metric names (3.6), macOS vs Linux memory metrics, alerts for disk-driven cache eviction and CI backlog
- `references/workflows/burst-workflows.md`: Orka Burst (3.3+) through the Portal API, with drain-before-disable ordering
- `SKILL.md`: Apple silicon 2-VM-per-node limit and slot-based capacity, Orka 3.6 as the last Intel release, bare-array `-o json` shape
- `vm-commands.md`: VM metadata server, `vm push` status values (`Ready`/`Failed`) and `-n`, guest `sync` before push/save/commit, save/commit require NFS image storage, display flag ranges, memory caps, `owner` in `vm list -o json`, deploy returns before macOS finishes booting
- `image-commands.md`, `image-issues.md`: cache timing and eviction, cache job cost, never remove a cache during a deploy, pre-3.5.1 custom-namespace caching bug, `Unauthorized` on push with a certificate-only kubeconfig
- `vm-config-commands.md`: configs always live in `orka-default`, no update command (blue/green rollout), half-node sizing
- `node-commands.md`, `admin-workflows.md`: `node namespace` is refused while VMs run (drain first), Apple silicon can't join custom-pods namespaces, cordoned nodes still show READY
- `admin-commands.md`: service-account token lifetime and revocation details, custom-pods toleration, `rb list-subjects` JSON shape
- `deployment-issues.md`: real 3.6 error strings, 2-VM limit error, cordoned-node symptom, RFC 1123 vs DNS-1035 name errors, on-prem node diagnosis
- `cicd-workflows.md`: CI concurrency at or below slot capacity, trap-based VM cleanup, leaked-VM cleanup by owner/prefix/age, integration smoke test
- `github-actions.md`: `GITHUB_PAT` (v1.1.15), `ORKA_NAMESPACE`, `MAX_RUNNERS`, tracker and deregistration settings, runner metric names
- `gitlab.md`, `buildkite.md`, `packer.md`: missing settings, defaults, and concurrency guidance

### Fixed

- TeamCity: plugin 2.0.1 installs from the JetBrains Marketplace (no `./gradlew build`), authenticates only with a service account token (no email/password), and the profile has Namespace and Node mappings fields; added the first-ARM-deploy timeout known issue
- Namespace resolution: `orka3 user login` and `orka3 user set-token` reset the `orka` context namespace to `orka-default`, so `ORKA_DEFAULT_NAMESPACE` is the lasting default; the precedence order applies only to `vm`, `node`, `imagecache`, `registrycredential`, `rolebinding`, `serviceaccount`; `orka3 upgrade service` always defaults to `orka-default`
- `monitoring.md`: added the Orka server metrics target at `/api/v1/metrics` (GET check, HEAD returns 404)
- VM Tools version guidance: match the cluster's release line, not its exact version (a 3.6.4 cluster runs VM Tools 3.6.0)
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
- `references/workflows/upgrade-workflows.md`: new "Host node macOS upgrades (3.7.0-alpha+)" section — macOS Tahoe host node upgrade support and the tunable per-node pod quota (`osx_node_orka_quota_pod`, default `4`)
- `SKILL.md`: Essential Context bullets for the pod quota/Tahoe upgrade facts and the self-service (not support-ticket-only) upgrade model for both MSDC and Orka Anywhere
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
