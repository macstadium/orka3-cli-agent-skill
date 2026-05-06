---
name: orka3-cli
description: >-
  Expert guidance for MacStadium's Orka3 CLI — managing macOS VMs, images,
  nodes, and CI/CD on Intel and Apple Silicon Mac hardware.
---

# Orka3 CLI — Quick Reference

**Current Version:** 3.5.2 | **Support:** support@macstadium.com

## Essential Context

Orka virtualizes macOS on physical Mac hardware. The CLI (`orka3`) manages VMs, images, nodes, namespaces, and access control.

**Architecture split** — Intel (`amd64`: Mac Pro, Intel Mac mini) and Apple Silicon (`arm64`: M1–M4 Mac mini, Mac Studio) have different command sets. Intel has power operations (`start`/`stop`/`suspend`/`resume`/`revert`), GPU passthrough, and ISO installs. ARM has OCI registry push (`vm push`), image caching (`imagecache`), and automatic disk resize.

**Auth lifecycle** — `orka3 login` opens a browser and stores a token in `~/.kube/config`. User tokens expire in **1 hour**. For anything automated (CI/CD, scripts, pipelines), use service accounts: `orka3 sa create <name>` then `orka3 sa token <name>` (default: 1 year, or `--no-expiration`).

**Execution contexts** — (1) Local machine: full CLI, interactive login. (2) CI/CD pipeline: ephemeral, service account tokens only, credentials via CI settings not `export`. (3) Claude Code: can probe the cluster directly. (4) Chat/conversation: suggest commands, can't execute.

**Async operations** — `vm save`, `vm commit`, `vm push`, `image copy`, `imagecache add` are all async. Check status with `orka3 image list <IMAGE>`, `orka3 ic info <IMAGE>`, or `orka3 vm get-push-status`.

**Shared disk (v3.5.2+)** — Attaches a shared disk to VMs on a host. Apple Silicon: **1 VM per node** when enabled. Requires Ansible config + per-host first-time formatting (see `shared-disk-workflows.md`).

**Namespace resolution (v3.5.2+)** — Priority: `--namespace` flag > `ORKA_DEFAULT_NAMESPACE` env var > kubeconfig context > `orka-default`.

**Kubernetes upgrade resilience (v3.6+)** — Most orka3 commands continue working during k8s control-plane upgrades. Only `login` and `vm push` require the API server; expect failures for those two until the upgrade completes.

## Quick CLI Guide

### Setup
```bash
orka3 config set --api-url <ORKA_API_URL>
orka3 login                                    # Browser-based auth
orka3 node list                                # Verify connectivity
```

### Deploy VMs
```bash
orka3 vm deploy --image ghcr.io/macstadium/orka-images/sonoma:latest
orka3 vm deploy my-vm --image <IMAGE> --cpu 4 --memory 8
orka3 vm deploy --image <IMAGE> --generate-name           # Unique suffix
orka3 vm deploy --image <IMAGE> --node <NODE>              # Target node
orka3 vm deploy --image <IMAGE> --tag <TAG> --tag-required # Node affinity
orka3 vm deploy --config <TEMPLATE>                        # From VM config
orka3 vm deploy --config <TEMPLATE> --cpu 6 --memory 16    # Override template
```

### List, Connect & Delete
```bash
orka3 vm list                       # All VMs
orka3 vm list my-vm                 # Filter by name
orka3 vm list -o wide               # Extended details (IP, ports, node)
orka3 vm delete <VM>
orka3 vm delete <VM1> <VM2>         # Multiple
# Connect: vnc://<VM-IP>:<Screenshare-port> (default creds: admin / admin)
```

### Save Work
```bash
orka3 vm save <VM> <NEW_IMAGE>      # New image, preserves original
orka3 vm commit <VM>                # Overwrites source image
orka3 vm push <VM> registry/img:tag # Push to OCI registry (ARM only)
# All three are async. Check: orka3 image list <IMAGE>
```

### Images
```bash
orka3 image list                    # Local images
orka3 image list <NAME>             # Filter by name
orka3 image copy <SRC> <DST>        # Async
orka3 image delete <IMAGE>
```

### Image Caching (ARM only)
```bash
orka3 ic add <IMAGE> --all                     # All nodes in namespace
orka3 ic add <IMAGE> --nodes <N1>,<N2>         # Specific nodes
orka3 ic add <IMAGE> --tags <TAG>              # Tagged nodes
orka3 ic info <IMAGE>                          # Check status
```

### VM Configs (Templates)
```bash
orka3 vmc create <NAME> --image <IMAGE> --cpu 4 --memory 8
orka3 vmc create <NAME> --image <IMAGE> --tag <TAG> --tag-required
orka3 vmc list                      # All configs
orka3 vmc list <NAME>               # Filter by name
orka3 vmc delete <NAME>
```

### Disk Resize
```bash
orka3 vm resize <VM> <SIZE_GB>                                  # ARM: automatic
orka3 vm resize <VM> <SIZE_GB> --user admin --password admin    # Intel: needs SSH
```

### Power Operations (Intel only)
```bash
orka3 vm start|stop|suspend|resume|revert <VM>
```

### Nodes
```bash
orka3 node list                     # All nodes
orka3 node list <NAME>              # Filter by name
orka3 node list -o wide             # CPU, memory, tags, VMs
orka3 node tag <NODE> <TAG>         # Admin: set affinity tag
orka3 node untag <NODE> <TAG>       # Admin: remove tag
orka3 node namespace <NODE> <NS>    # Admin: move node to namespace
```

### Namespaces & Access Control (Admin)
```bash
orka3 namespace create orka-<name>
orka3 namespace list
orka3 namespace delete orka-<name>                       # Must be empty first

orka3 rb add-subject --namespace <NS> --user <EMAIL>
orka3 rb add-subject --namespace <NS> --serviceaccount <SA_NS>:<SA_NAME>
orka3 rb list-subjects --namespace <NS>
orka3 rb remove-subject --namespace <NS> --user <EMAIL>
```

### Service Accounts
```bash
orka3 sa create <NAME>                          # In current namespace
orka3 sa create <NAME> -n <NS>                  # In specific namespace
orka3 sa token <NAME>                           # 1-year token (default)
orka3 sa token <NAME> --duration 24h            # Custom duration
orka3 sa token <NAME> --no-expiration           # Never expires
orka3 sa list
orka3 sa delete <NAME>
```

### OCI Registry Credentials (Admin)
```bash
orka3 regcred add <URL> --username "$USER" --password "$TOKEN"
orka3 regcred list                  # Also: regcred remove <SERVER>
```

### Output & Flags
```bash
-o wide|json|table    # Output format (table is default)
-n <namespace>        # Override namespace
--generate-name       # Auto-suffix for unique VM names
--timeout <minutes>   # Deployment timeout (default: 10)
```

**Aliases:** `vm-config` = `vmc`, `serviceaccount` = `sa`, `rolebinding` = `rb`, `registrycredential` = `regcred`, `imagecache` = `ic`

## Reference Files

Quick command syntax is above. Load references for complete workflows, detailed troubleshooting, or full flag documentation.

| Query type | File |
|------------|------|
| VM flags, Intel-only deploy options | `references/commands/vm-commands.md` |
| Image & imagecache flags | `references/commands/image-commands.md` |
| Node management flags | `references/commands/node-commands.md` |
| Namespace, SA, rolebinding flags | `references/commands/admin-commands.md` |
| Config, login, API URLs | `references/commands/config-commands.md` |
| VM config template flags | `references/commands/vm-config-commands.md` |
| Registry credential management | `references/commands/registry-commands.md` |
| CI/CD pipeline setup | `references/workflows/cicd-workflows.md` |
| Golden images, OCI workflows | `references/workflows/image-workflows.md` |
| Multi-namespace, tagging, RBAC | `references/workflows/admin-workflows.md` |
| Batch deployments, optimization | `references/workflows/scaling-workflows.md` |
| Intel → ARM migration, backup | `references/workflows/migration-workflows.md` |
| Shared disk setup, first-time init | `references/workflows/shared-disk-workflows.md` |
| **Any auth error or permission issue** | `references/troubleshooting/auth-issues.md` |
| **Any deployment failure or VM issue** | `references/troubleshooting/deployment-issues.md` |
| Async ops stuck, cache issues | `references/troubleshooting/image-issues.md` |
| Screen Sharing, SSH, ports | `references/troubleshooting/network-issues.md` |
| GitLab Custom/Shell executor | `references/integrations/gitlab.md` |
| Packer plugin (image builds) | `references/integrations/packer.md` |
| GitHub Actions (ephemeral runners) | `references/integrations/github-actions.md` |
| Buildkite (ephemeral/permanent agents) | `references/integrations/buildkite.md` |
| TeamCity cloud agent plugin | `references/integrations/teamcity.md` |
