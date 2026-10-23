---
name: orka3-cli
description: >-
  Expert guidance for MacStadium's Orka CLI (`orka` for Orka 4.x, `orka3` for
  Orka 3.x): managing macOS virtualization infrastructure including VMs,
  images, nodes, namespaces, CI/CD pipelines, and Android emulators on Apple
  Silicon Mac hardware, plus Intel on Orka 3.6 and earlier.
---

# Orka3 CLI Skill

## Which CLI: `orka` (Orka 4.x) or `orka3` (Orka 3.x)

Starting with Orka 4.0, the CLI command is `orka`. Examples in this skill use `orka`. On Orka 3.6 and earlier, the CLI is `orka3`: replace `orka` with `orka3` in the examples. Commands and flags marked as removed in Orka 4.0, and other 3.x-only content (Intel VMs, the Intel-to-Apple-silicon migration, 3.6-only behavior), only exist in `orka3` and are written that way. Check which CLI you have with `orka version --client` or `orka3 version --client`.

- **Both CLIs can be installed side by side.** `orka3` stays the 3.6 CLI; installing the 4.0 CLI doesn't replace it. Use `orka3` for 3.6 clusters and `orka` for 4.0 clusters. MacStadium doesn't ship an `orka3` alias. Commands, flags, and output are otherwise unchanged, apart from the Intel removals.
- **They share one configuration.** `orka` and `orka3` read the same config file and the same `orka` kubeconfig context. Switching between a 3.6 cluster and a 4.0 cluster still means running `config set --api-url` and logging in again, whichever CLI you run.
- **Running the 4.0 CLI as `orka3`** prints `Warning: orka3 is deprecated. Orka 4.0 renamed the CLI to orka; update your scripts to call orka.` to stderr and then runs normally. Standard output is unchanged, so `-o json` output still parses.
- **Optional bridge for scripts.** If you no longer need the 3.x CLI, you can point an `orka3` name at the 4.0 CLI to keep existing scripts working while you migrate them. On macOS and Linux: `sudo ln -sf "$(command -v orka)" /usr/local/bin/orka3`. On Windows: copy `orka.exe` to `orka3.exe` in the same folder. This replaces the 3.x `orka3`, so don't do it if you still manage Orka 3.6 clusters. If you installed `orka3` with Homebrew, uninstall the `orka3` cask first, because Homebrew still treats `/usr/local/bin/orka3` as its own. On macOS and Linux, the symlink survives later 4.x CLI upgrades. On Windows, copy the file again after each CLI upgrade. Treat this as a bridge, not a fix: help text and error messages say `orka`, so update scripts to call `orka` directly.
- **Installing.** Download the 4.0 CLI from [Orka tools, CLI downloads, and CI/CD plugins](https://docs.macstadium.com/orka/orka-overview/tools-integrations). On macOS, the 4.0 package leaves the 3.x `orka3` binary in place. Don't suggest `brew install --cask orka` yet: until the cask is updated, the `orka` Homebrew cask installs the legacy 2.4.0 CLI.
- **Legacy Orka 2.x CLI.** The 2.x CLI was also named `orka` and installed to the same path, `/usr/local/bin/orka`, so installing the 4.0 CLI replaces it. The 2.x CLI only works with Orka 2.4.x and 3.0.x clusters, which MacStadium no longer maintains. If you still need the 2.x CLI, don't install the 4.0 CLI on the same machine.

## Essential Context

Orka runs macOS VMs on physical Mac hardware. Orka 4.0 and later run on Apple Silicon (arm64) only: M1/M2/M3/M4 Mac mini, Mac Studio. Orka 3.6 and earlier also run Intel (amd64): Mac Pro, Intel Mac mini, iMac Pro. On 3.6 the two have different command sets: ARM gets `vm push` and `imagecache`; Intel gets power operations (`start`/`stop`/`suspend`/`resume`/`revert`), ISO management, and GPU passthrough. Orka 4.0 removed the Intel set.

Apple silicon nodes run at most 2 VMs each (Apple EULA). Capacity in VM slots is 2 x Apple silicon nodes; set CI concurrency limits at or below that.

Orka 3.6 is the last release with Intel support (Intel supported through March 2028; plan migration by December 2027).

All `-o json` output from the CLI is a bare JSON array with camelCase keys (`.[0].name`, `.[]`), never `{items: [...]}`; the REST API wraps lists in `items` (see `references/commands/rest-api.md`).

User tokens expire in 1 hour. All automation and CI/CD must use service accounts (`orka sa create`, `orka sa token`), which support long-lived or non-expiring tokens.

Four execution contexts: local machine (full CLI), CI/CD (ephemeral containers: env vars injected at runtime, failed VMs often auto-deleted), an execution-capable agent (Claude Code, Gemini CLI: has CLI access, probe with `orka node list`, or `orka3 node list` on a 3.6 cluster), and a guidance-only agent or chat (no CLI access: answer from documentation only, the human runs the command). Before giving commands, find out whether the cluster is on 4.x or 3.x.

Image save, commit, push, and caching are async. Always pair with the status-check command: `orka image list <IMAGE>`, `orka imagecache info <IMAGE>`, or `orka vm get-push-status <JOB>`.

Namespace resolution (v3.5.2+, for `vm`, `node`, `imagecache`, `registrycredential`, `rolebinding`, `serviceaccount`, and on 4.0 also `emulator` and `rbac --role dev`): `--namespace` flag > `ORKA_DEFAULT_NAMESPACE` env var > `orka` kubeconfig context > `orka-default`. `orka user login` and `orka user set-token` reset the context namespace to `orka-default`, so use `ORKA_DEFAULT_NAMESPACE` for a lasting default. Some features (shared disk, namespace auto-detection, macOS Tahoe) require v3.5.2+.

Kubernetes upgrade resilience (v3.6+): Most orka commands continue working during k8s control-plane upgrades. Only `login` and `vm push` require the API server; expect failures for those two until the upgrade completes.

VM network isolation (v3.6+, Apple Silicon only): MacStadium can configure per-cluster allow/deny rules by CIDR block to restrict VM network access. Configured by support, not via CLI. Contact support@macstadium.com to set up.

Android Emulators (Apple Silicon, GA in 4.0, early access in 3.7.0-alpha): `orka emulator deploy|list|delete` runs an Android emulator on the same host node as a running macOS VM, connected over an ADB relay. `--vm` is required, plus either `--platform` and `--image-type` or, on 4.0, `--config`; `--device-profile` is optional. Orka 4.0 adds `orka emulator-config` (alias `emc`) for reusable templates, plus `--config` and `--grpc` on deploy. There is no `--device`, `--cpu`, or `--memory` flag, and `emulator list` has no `--vm` filter. Network isolation is node-level (any VM on the node can reach any emulator on it), NAT only, and ephemeral (no persistent AVD state). See `references/commands/emulator-commands.md`.

Host node macOS upgrades (3.7.0-alpha+): Orka can upgrade Apple silicon host nodes to macOS Tahoe (26) in place.

Node pod quota: on Orka 3.6 and the 3.7.0-alpha, every pod on an Apple silicon node (VMs, emulators, image-cache jobs) shares one scheduler quota, default `4`, tunable with `osx_node_orka_quota_pod`. Two VMs with paired emulators fill it, leaving no room for an image-cache job. Orka 4.0 replaces the shared cap: image-cache and push jobs get their own per-node budget (`osx_node_orka_quota_job`, default `2`), the node pod quota is `110` (the Kubernetes default), and emulators aren't capped. A 3.6 `osx_node_orka_quota_pod` override isn't needed on 4.0. See `references/workflows/upgrade-workflows.md`.

Component versions: a patch release only bumps the components it changed, so a 3.6.4 cluster reports API server and Orka Engine 3.6.3. That's not a failed upgrade. Read versions with `orka version` (API, operator) and `orka node list -o wide` (`VERSION` = Virtual Kubelet, `RUNTIME` = Orka Engine) and compare against the [component matrix](https://docs.macstadium.com/orka/orka-upgrades-and-release-notes/orka-component-versions). `orka upgrade versions` reports `unknown` until the first Upgrade Service v2 run.

macOS guests: macOS 27 Golden Gate needs Orka 3.6+, a macOS 26.6.2+ host, and more than 2 GB of RAM (4 GB recommended). macOS 27 as a host OS isn't signed off yet. In-place upgrades to macOS 15.x and 26.x inside a VM currently fail without a workaround (see `references/troubleshooting/image-issues.md`). Android emulators with `google_apis_playstore` reject ADB (`device unauthorized`), a known issue in Orka 4.0; use `google_apis`.

Upgrades are self-service, not support-ticket-only: MSDC clusters (3.6+) upgrade via the Upgrade Service (`orka upgrade run/status/history/versions`, `orka upgrade service status/agents`). Orka Anywhere (self-managed AWS or on-prem) upgrades by re-running the same Ansible install process against the target version's image, idempotent, no separate procedure. See `references/workflows/upgrade-workflows.md` for both flows.

Upgrading to Orka 4.0: the cluster must be on Orka 3.6 first (upgrade to the latest 3.6 release). A cluster with Intel worker nodes can't upgrade: the upgrade checks for Intel nodes and stops before making any changes. Contact MacStadium support to schedule a 4.0 upgrade. See `references/workflows/upgrade-workflows.md`.

VM User Data (Orka 4.0+, Apple Silicon only): `orka vm deploy --userdata <script|base64>` runs a shell script inside the VM on first boot, as root, in the background, once per VM. Needs the Orka 4.0 orka-vm-tools in the image. Track it with the `USERDATA-PHASE` column in `orka vm list -o wide`; `skipped` means the VM already ran its script on an earlier boot. Images built with the 3.7.0-alpha VM Tools skip their User Data, so update them to the 4.0 VM Tools. Orka never returns the script in API responses, but anyone with Kubernetes read access to the VM's `VirtualMachineInstance` or pod can read it, so don't put long-lived secrets in it. See `references/commands/vm-commands.md`.

RBAC subjects (Orka 4.0+): `orka rbac add-subject|list-subjects|remove-subject --role admin|dev` replaces `orka rolebinding`, which still works but prints `Command "rolebinding" is deprecated` to stderr and no longer appears in `--help`. `--role admin` isn't usable by customer admins on MacStadium-hosted clusters (`--role dev` works); ask support for the managed `orka-admin` service account instead. See `references/commands/admin-commands.md`.

Removed in Orka 4.0 (Apple Silicon only release): `orka3 vm start|stop|suspend|resume|revert`, `orka3 image generate`, the `orka3 iso` and `orka3 remote-iso` commands, the `--iso`, `--gpu`, `--system-serial`, `--disable-net-boost` and `--legacy-io` flags on `vm deploy` and `vm-config create`, and `--user`/`--password` on `vm resize`. On 4.0, `vm` and `image` reject unknown subcommands with a non-zero exit (3.6 printed help and exited `0`), so a script still calling `vm stop` now fails. The matching API routes return `404`, Intel-only request fields return `400`, and the admission webhook rejects Intel images (see `references/commands/rest-api.md`). Orka 3.6 is the last Intel release, supported through March 2028.

Deprecated in Orka 4.0, still working: NFS-hosted images. `orka image`, `orka remote-image`, `orka vm save`, and `orka vm commit` print a deprecation warning to stderr and show `(Deprecated)` in help. Use OCI images (`vm push`, `imagecache`) instead.

## Quick CLI Guide

### Setup
```bash
orka config set --api-url <ORKA_API_URL>
orka login
orka node list                            # Verify connectivity
```

### Deploy VMs
```bash
orka vm deploy --image <IMAGE>                        # Simplest form
orka vm deploy --image <IMAGE> --cpu 6 --memory 16    # With resources
orka vm deploy my-vm --image <IMAGE>                  # Named VM
orka vm deploy --image ghcr.io/org/repo/image:tag     # From OCI registry
orka vm deploy --config <TEMPLATE>                    # From VM config
orka vm deploy --config <TEMPLATE> --cpu 8            # Template + overrides
```

### Manage VMs
```bash
orka vm list                              # Basic info
orka vm list -o wide                      # Extended details
orka vm list <VM_NAME>                    # Filter by name
orka vm delete <VM_NAME>
orka vm delete <VM1> <VM2>               # Multiple
```
Connect via Screen Sharing: `vnc://<VM-IP>:<Screenshare-port>` (default creds: `admin`/`admin`)

### Save Work
```bash
orka vm push <VM> registry/image:tag      # Push to OCI (ARM only). Check: orka vm get-push-status
orka vm save <VM> <NEW_IMAGE>             # NFS image, deprecated in 4.0. New image, preserves original
orka vm commit <VM>                       # NFS image, deprecated in 4.0. Overwrites original image
# All three async. save/commit status: orka image list <IMAGE>
```

### Images (NFS-hosted, deprecated in 4.0)
```bash
orka image list                           # All images
orka image list <IMAGE>                   # Filter / check status
orka image copy <SRC> <DST>
orka image delete <IMAGE>
```

### Image Caching (ARM only)
```bash
orka imagecache add <IMAGE> --nodes <N1>,<N2>
orka imagecache add <IMAGE> --all         # All nodes in namespace
orka imagecache add <IMAGE> --tags <TAG>  # Tagged nodes
orka imagecache remove <IMAGE> --all      # Remove from all nodes (v3.6.3+)
orka imagecache remove <IMAGE> --nodes <N1>,<N2>
orka imagecache remove <IMAGE> --tags <TAG>
orka imagecache info <IMAGE>              # Check status
```

### Android Emulators (Apple Silicon, GA in v4.0, early access in v3.7.0-alpha)
```bash
orka emulator deploy --vm <VM> --platform android-36 --image-type google_apis      # All three required, no defaults
orka emulator deploy --vm <VM> --platform android-35 --image-type google_apis --device-profile pixel_8
orka emulator list                        # All emulators in namespace
orka emulator list <AVD_NAME>             # Filter by name
orka emulator delete <AVD_NAME>
# Connect using RELAY-IP/RELAY-PORT from `orka emulator list`, never a hardcoded IP:
adb connect <RELAY_IP>:<RELAY_PORT>

# Orka 4.0: emulator configurations and gRPC
orka emc create <EMULATOR_CONFIGURATION_NAME> --platform android-36 --image-type google_apis
orka emulator deploy --vm <VM> --config <EMULATOR_CONFIGURATION_NAME>
orka emulator deploy --vm <VM> --platform android-36 --image-type google_apis --grpc   # gRPC on GRPC-PORT
orka emc list
```
Plan for about 5 to 6 GB of host memory per emulator; memory, not CPU, usually limits emulators per node.

### VM Config Templates
```bash
orka vm-config create <NAME> --image <IMAGE> --cpu 6 --memory 12
orka vm-config create <NAME> --image <IMAGE> --tag <TAG> --tag-required
orka vm-config list
orka vm-config list <NAME>                # Filter by name
orka vm-config delete <NAME>
```

### Nodes
```bash
orka node list                            # All nodes
orka node list -o wide                    # With tags, capacity
orka node list <NODE>                     # Filter by name
orka node tag <NODE> <TAG>                # Tag for affinity (admin)
orka node untag <NODE> <TAG>
orka node namespace <NODE> <NS>           # Move between namespaces (admin)
```

### Namespaces & Access (Admin)
```bash
orka namespace create <NAME>
orka namespace list
orka namespace delete <NAME>              # Must be empty
orka rbac add-subject --role dev --namespace <NS> --user <EMAIL>                    # 4.0+
orka rbac add-subject --role dev --namespace <NS> --serviceaccount <SA_NS>:<SA_NAME>
orka rbac list-subjects --role dev --namespace <NS>
orka rbac remove-subject --role dev --namespace <NS> --user <EMAIL>
orka rbac add-subject --role admin --user <EMAIL>                                   # Cluster-wide; not on MSDC-hosted clusters
```
On 3.6, use `orka3 rb add-subject|list-subjects|remove-subject --namespace <NS>` (same `--user`/`--serviceaccount` flags). `rolebinding` still works on 4.0 but is deprecated.

### Service Accounts
```bash
orka sa create <NAME>
orka sa create <NAME> --namespace <NS>
orka sa token <NAME>                      # Default: 1 year
orka sa token <NAME> --duration 1h
orka sa token <NAME> --no-expiration
orka sa list
```

### Power Operations (Intel only, Orka 3.6 and earlier, removed in Orka 4.0)
```bash
orka3 vm start <VM>
orka3 vm stop <VM>
orka3 vm suspend <VM>
orka3 vm resume <VM>
orka3 vm revert <VM>                       # Revert to base image
```

### Disk Resize
```bash
orka vm resize <VM> <SIZE_GB>                                          # ARM (needs Orka VM Tools in guest)
orka3 vm resize <VM> <SIZE_GB> --user "$VM_USER" --password "$VM_PWD"   # Intel, Orka 3.6 and earlier only (needs SSH)
```
`--user` and `--password` were removed in Orka 4.0; on 4.0, pass only the VM and size.

### OCI Registry Credentials (Admin)
```bash
echo "$REGISTRY_TOKEN" | orka regcred add <SERVER> --username <USER> --password-stdin
orka regcred list
orka regcred remove <SERVER>              # SERVER includes scheme, e.g. https://ghcr.io
```

### Output & Flags
- `-o, --output`: `table` (default) | `wide` | `json`
- `-n, --namespace`: target namespace (default: resolved as described under Namespace resolution, usually `orka-default`)
- `--generate-name`: auto-generate VM name
- Aliases: `vm-config`→`vmc` `serviceaccount`→`sa` `registrycredential`→`regcred` `imagecache`→`ic` `emulator`→`emu` `emulator-config`→`emc` (4.0) `rolebinding`→`rb` (deprecated in 4.0)

## Reference Files

Most questions are answerable from this file. Load references for full flag details, complex workflows, or troubleshooting.

| Query type | File |
|------------|------|
| VM flags (deploy/save/commit/push/resize) | `references/commands/vm-commands.md` |
| Image & imagecache flags | `references/commands/image-commands.md` |
| Android emulator and emulator-config flags (GA in v4.0) | `references/commands/emulator-commands.md` |
| VM User Data, `--userdata`, `USERDATA-PHASE` (v4.0+) | `references/commands/vm-commands.md` |
| `orka rbac` role subjects (v4.0+) | `references/commands/admin-commands.md` |
| Commands and flags removed in v4.0 (Intel) | `references/commands/vm-commands.md` |
| Orka 4.0 API changes (removed routes, Intel fields rejected, webhook messages) | `references/commands/rest-api.md` |
| Emulator sizing and density, Play Store ADB known issue | `references/commands/emulator-commands.md` |
| Upgrading to 4.0, pod quota, PDBs, control plane changes | `references/workflows/upgrade-workflows.md` |
| Registry credential management | `references/commands/registry-commands.md` |
| Namespace, SA, rolebinding flags, hosted-cluster admin limits | `references/commands/admin-commands.md` |
| Node list/tag/namespace flags | `references/commands/node-commands.md` |
| CLI config, login, completion | `references/commands/config-commands.md` |
| Orka REST API (Swagger, auth, request/response shapes, emulator endpoints) | `references/commands/rest-api.md` |
| VM config template flags | `references/commands/vm-config-commands.md` |
| CI/CD pipeline setup | `references/workflows/cicd-workflows.md` |
| Custom images, OCI workflows, macOS guest compatibility | `references/workflows/image-workflows.md` |
| Multi-namespace, tagging, RBAC | `references/workflows/admin-workflows.md` |
| Scaling, load testing, disk mgmt, node disk sizing, storage usage | `references/workflows/scaling-workflows.md` |
| Intel→ARM migration, NFS-to-Harbor OCI migration, backup | `references/workflows/migration-workflows.md` |
| VM shared attached disk (v3.5.2+) | `references/workflows/shared-disk-workflows.md` |
| Cluster upgrades, component versions, Upgrade Service troubleshooting, Kubernetes upgrades, AWS upgrades | `references/workflows/upgrade-workflows.md` |
| License management, seat activation, LicenseSpring portal | `references/workflows/license-management.md` |
| Monitoring, Prometheus metrics, alerting | `references/workflows/monitoring.md` |
| Orka Burst capacity | `references/workflows/burst-workflows.md` |
| Token/permission errors | `references/troubleshooting/auth-issues.md` |
| Resource errors, VM issues, 4.0 disk-space and Intel rejection errors | `references/troubleshooting/deployment-issues.md` |
| Async ops, image caching issues, 3.6.4 fixes, in-place macOS upgrade failures | `references/troubleshooting/image-issues.md` |
| Screen Sharing, SSH, ports | `references/troubleshooting/network-issues.md` |
| GitLab Custom/Shell executor | `references/integrations/gitlab.md` |
| Packer plugin (image builds) | `references/integrations/packer.md` |
| GitHub Actions (ephemeral runners) | `references/integrations/github-actions.md` |
| Buildkite (ephemeral/permanent agents) | `references/integrations/buildkite.md` |
| TeamCity cloud agent plugin | `references/integrations/teamcity.md` |
| Jenkins (Orka by MacStadium plugin) | `references/integrations/jenkins.md` |

If you need full Orka documentation beyond what's in this skill, it's available via MCP at `https://docs.macstadium.com/mcp`. Prefer the skill contents first for CLI tasks.
