---
name: orka3-cli
description: >-
  Expert guidance for MacStadium's Orka3 CLI — managing macOS virtualization
  infrastructure including VMs, images, nodes, namespaces, CI/CD pipelines,
  and early-access Android emulators on Intel and Apple Silicon Mac hardware.
---

# Orka3 CLI Skill

## Essential Context

Orka runs macOS VMs on physical Mac hardware in two architectures: Intel (amd64) — Mac Pro, Intel Mac mini, iMac Pro — and Apple Silicon (arm64) — M1/M2/M3/M4 Mac mini, Mac Studio. They have different command sets: ARM gets `vm push` and `imagecache`; Intel gets power operations (`start`/`stop`/`suspend`/`resume`/`revert`), ISO management, and GPU passthrough.

User tokens expire in 1 hour. All automation and CI/CD must use service accounts (`orka3 sa create`, `orka3 sa token`), which support long-lived or non-expiring tokens.

Four execution contexts: local machine (full CLI), CI/CD (ephemeral containers — env vars injected at runtime, failed VMs often auto-deleted), Claude Code (has CLI access — probe with `orka3 node list`), and chat (no CLI access — answer from documentation only).

Image save, commit, push, and caching are async. Always pair with the status-check command: `orka3 image list <IMAGE>`, `orka3 imagecache info <IMAGE>`, or `orka3 vm get-push-status <JOB>`.

Namespace resolution (v3.5.2+): `--namespace` flag > `ORKA_DEFAULT_NAMESPACE` env var > kubeconfig context > `orka-default`. Some features (shared disk, namespace auto-detection, macOS Tahoe) require v3.5.2+.

Kubernetes upgrade resilience (v3.6+): Most orka3 commands continue working during k8s control-plane upgrades. Only `login` and `vm push` require the API server; expect failures for those two until the upgrade completes.

VM network isolation (v3.6+, Apple Silicon only): MacStadium can configure per-cluster allow/deny rules by CIDR block to restrict VM network access. Configured by support, not via CLI. Contact support@macstadium.com to set up.

Android Emulators (Apple Silicon, 3.7+ early access): `orka3 emulator deploy|list|delete` runs an Android emulator on the same host node as a running macOS VM, connected over an ADB relay. Not GA, not for production. Network isolation is node-level (any VM on the node can reach any emulator on it), NAT only, and ephemeral (no persistent AVD state). See `references/commands/emulator-commands.md`.

## Quick CLI Guide

### Setup
```bash
orka3 config set --api-url <ORKA_API_URL>
orka3 login
orka3 node list                            # Verify connectivity
```

### Deploy VMs
```bash
orka3 vm deploy --image <IMAGE>                        # Simplest form
orka3 vm deploy --image <IMAGE> --cpu 6 --memory 16    # With resources
orka3 vm deploy my-vm --image <IMAGE>                  # Named VM
orka3 vm deploy --image ghcr.io/org/repo/image:tag     # From OCI registry
orka3 vm deploy --config <TEMPLATE>                    # From VM config
orka3 vm deploy --config <TEMPLATE> --cpu 8            # Template + overrides
```

### Manage VMs
```bash
orka3 vm list                              # Basic info
orka3 vm list -o wide                      # Extended details
orka3 vm list <VM_NAME>                    # Filter by name
orka3 vm delete <VM_NAME>
orka3 vm delete <VM1> <VM2>               # Multiple
```
Connect via Screen Sharing: `vnc://<VM-IP>:<Screenshare-port>` (default creds: `admin`/`admin`)

### Save Work
```bash
orka3 vm save <VM> <NEW_IMAGE>             # New image, preserves original
orka3 vm commit <VM>                       # Overwrites original image
orka3 vm push <VM> registry/image:tag      # Push to OCI (ARM only)
# All three async. Check: orka3 image list <IMAGE>
```

### Images
```bash
orka3 image list                           # All images
orka3 image list <IMAGE>                   # Filter / check status
orka3 image copy <SRC> <DST>
orka3 image delete <IMAGE>
```

### Image Caching (ARM only)
```bash
orka3 imagecache add <IMAGE> --nodes <N1>,<N2>
orka3 imagecache add <IMAGE> --all         # All nodes in namespace
orka3 imagecache add <IMAGE> --tags <TAG>  # Tagged nodes
orka3 imagecache remove <IMAGE> --all      # Remove from all nodes (v3.6.3+)
orka3 imagecache remove <IMAGE> --nodes <N1>,<N2>
orka3 imagecache remove <IMAGE> --tags <TAG>
orka3 imagecache info <IMAGE>              # Check status
```

### Android Emulators (Apple Silicon, early access, v3.7.0-alpha+)
```bash
orka3 emulator deploy --vm <VM>                                 # Defaults: android-36, pixel_9, google_apis
orka3 emulator deploy --vm <VM> --platform android-35 --device pixel_8
orka3 emulator list --vm <VM>
orka3 emulator delete <EMULATOR>
# Connect using the response's adbRelayIP/adbRelayPort, never a hardcoded IP:
adb connect <adbRelayIP>:<adbRelayPort>
```

### VM Config Templates
```bash
orka3 vm-config create <NAME> --image <IMAGE> --cpu 6 --memory 12
orka3 vm-config create <NAME> --image <IMAGE> --tag <TAG> --tag-required
orka3 vm-config list
orka3 vm-config list <NAME>                # Filter by name
orka3 vm-config delete <NAME>
```

### Nodes
```bash
orka3 node list                            # All nodes
orka3 node list -o wide                    # With tags, capacity
orka3 node list <NODE>                     # Filter by name
orka3 node tag <NODE> <TAG>                # Tag for affinity (admin)
orka3 node untag <NODE> <TAG>
orka3 node namespace <NODE> <NS>           # Move between namespaces (admin)
```

### Namespaces & Access (Admin)
```bash
orka3 namespace create <NAME>
orka3 namespace list
orka3 namespace delete <NAME>              # Must be empty
orka3 rb add-subject --namespace <NS> --user <EMAIL>
orka3 rb add-subject --namespace <NS> --serviceaccount <SA_NS>:<SA_NAME>
orka3 rb list-subjects --namespace <NS>
orka3 rb remove-subject --namespace <NS> --user <EMAIL>
```

### Service Accounts
```bash
orka3 sa create <NAME>
orka3 sa create <NAME> --namespace <NS>
orka3 sa token <NAME>                      # Default: 1 year
orka3 sa token <NAME> --duration 1h
orka3 sa token <NAME> --no-expiration
orka3 sa list
```

### Power Operations (Intel only)
```bash
orka3 vm start <VM>
orka3 vm stop <VM>
orka3 vm suspend <VM>
orka3 vm resume <VM>
orka3 vm revert <VM>                       # Revert to base image
```

### Disk Resize
```bash
orka3 vm resize <VM> <SIZE_GB>                                          # ARM (automatic)
orka3 vm resize <VM> <SIZE_GB> --user "$VM_USER" --password "$VM_PWD"   # Intel (needs SSH)
```

### OCI Registry Credentials (Admin)
```bash
orka3 regcred add <URL> --username "$USER" --password "$TOKEN"
orka3 regcred list
orka3 regcred delete <NAME>
```

### Output & Flags
- `-o, --output`: `table` (default) | `wide` | `json`
- `-n, --namespace`: target namespace (default: `orka-default`)
- `--generate-name`: auto-generate VM name
- Aliases: `vm-config`→`vmc` `serviceaccount`→`sa` `rolebinding`→`rb` `registrycredential`→`regcred` `imagecache`→`ic`

## Reference Files

Most questions are answerable from this file. Load references for full flag details, complex workflows, or troubleshooting.

| Query type | File |
|------------|------|
| VM flags (deploy/save/commit/push/resize) | `references/commands/vm-commands.md` |
| Image & imagecache flags | `references/commands/image-commands.md` |
| Android emulator flags (early access, v3.7.0-alpha+) | `references/commands/emulator-commands.md` |
| Registry credential management | `references/commands/registry-commands.md` |
| Namespace, SA, rolebinding flags | `references/commands/admin-commands.md` |
| Node list/tag/namespace flags | `references/commands/node-commands.md` |
| CLI config, login, completion | `references/commands/config-commands.md` |
| VM config template flags | `references/commands/vm-config-commands.md` |
| CI/CD pipeline setup | `references/workflows/cicd-workflows.md` |
| Custom images, OCI workflows | `references/workflows/image-workflows.md` |
| Multi-namespace, tagging, RBAC | `references/workflows/admin-workflows.md` |
| Scaling, load testing, disk mgmt | `references/workflows/scaling-workflows.md` |
| Intel→ARM migration, backup | `references/workflows/migration-workflows.md` |
| VM shared attached disk (v3.5.2+) | `references/workflows/shared-disk-workflows.md` |
| Cluster upgrades, Kubernetes upgrades, AWS upgrades | `references/workflows/upgrade-workflows.md` |
| License management, seat activation, LicenseSpring portal | `references/workflows/license-management.md` |
| Token/permission errors | `references/troubleshooting/auth-issues.md` |
| Resource errors, VM issues | `references/troubleshooting/deployment-issues.md` |
| Async ops, image caching issues, 3.6.4 fixes | `references/troubleshooting/image-issues.md` |
| Screen Sharing, SSH, ports | `references/troubleshooting/network-issues.md` |
| GitLab Custom/Shell executor | `references/integrations/gitlab.md` |
| Packer plugin (image builds) | `references/integrations/packer.md` |
| GitHub Actions (ephemeral runners) | `references/integrations/github-actions.md` |
| Buildkite (ephemeral/permanent agents) | `references/integrations/buildkite.md` |
| TeamCity cloud agent plugin | `references/integrations/teamcity.md` |

If you need full Orka documentation beyond what's in this skill, it's available via MCP at `https://docs.macstadium.com/mcp`. Prefer the skill contents first for CLI tasks.
