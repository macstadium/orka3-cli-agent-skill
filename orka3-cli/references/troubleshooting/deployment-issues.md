# VM Deployment Troubleshooting

This guide covers common VM deployment issues with the Orka CLI.

## Contents
- [Quick Triage Checklist](#quick-triage-checklist)
- [Problem: VM deployment fails for lack of CPU or memory](#problem-vm-deployment-fails-for-lack-of-cpu-or-memory)
- [Problem: Apple silicon VM limit reached](#problem-apple-silicon-vm-limit-reached)
- [Problem: Deploys fail on a node that shows READY with free capacity](#problem-deploys-fail-on-a-node-that-shows-ready-with-free-capacity)
- [Problem: VM deployment succeeds but VM is unresponsive](#problem-vm-deployment-succeeds-but-vm-is-unresponsive)
- [Problem: VM deployment fails with "Image not found"](#problem-vm-deployment-fails-with-image-not-found)
- [Problem: VM name already exists](#problem-vm-name-already-exists)
- [Problem: VM or config name is rejected](#problem-vm-or-config-name-is-rejected)
- [Problem: "Namespace has no nodes"](#problem-namespace-has-no-nodes)
- [Problem: Tag required but no tagged nodes available](#problem-tag-required-but-no-tagged-nodes-available)
- [Problem: Node can't be moved to another namespace](#problem-node-cant-be-moved-to-another-namespace)
- [Problem: "Not enough disk space on node" (Orka 4.0)](#problem-not-enough-disk-space-on-node-orka-40)
- [Problem: Intel image or setting rejected (Orka 4.0)](#problem-intel-image-or-setting-rejected-orka-40)
- [VM Start Diagnostics (v3.6+)](#vm-start-diagnostics-v36)
- [Log Sources for Deep Troubleshooting (v3.4+)](#log-sources-for-deep-troubleshooting-v34)

## Quick Triage Checklist

```bash
# 1. Check node resources
orka node list --output wide

# Look for:
# - Available CPU/memory
# - Node status
# - Existing VM count

# 2. Check if image exists and is ready
orka image list <IMAGE_NAME> --output wide

# For OCI images, verify caching status
orka ic info <OCI_IMAGE>

# 3. Verify namespace has resources
orka node list --namespace <YOUR_NAMESPACE>

# 4. Check for VM name conflicts
orka vm list <VM_NAME>

# 5. Try deployment with longer timeout
orka vm deploy --image <IMAGE> --timeout 20

# 6. Try deployment on specific node
orka vm deploy --image <IMAGE> --node <NODE_NAME>

# 7. Check if VM config exists
orka vmc list <CONFIG_NAME> --output wide

# 8. If tag-required is set, verify tagged nodes exist
orka node list -o wide              # Check Tags column for <TAG>

# 9. Try with JSON output for detailed error messages
orka vm deploy --image <IMAGE> -o json
```

## Problem: VM deployment fails for lack of CPU or memory

**Symptoms:**
- `Requested CPU is not available in the cluster`
- `No available nodes with sufficient memory`
- `The provided memory or CPU is greater than the maximum allowed.`
- Deployment times out

**Diagnosis:**
```bash
# 1. Check node resources
orka node list --output wide

# Look for available CPU and memory

# 2. Check current VM usage
orka vm list --output wide

# 3. Check if namespace has any nodes
orka node list --namespace <YOUR_NAMESPACE>
```

**Solutions:**
```bash
# Option 1: Reduce VM resource requirements
orka vm deploy --image <IMAGE> --cpu 3 --memory 6  # Smaller resources

# Option 2: Deploy to specific node with resources
orka node list --output wide  # Find node with resources
orka vm deploy --image <IMAGE> --node <NODE_WITH_RESOURCES>

# Option 3: Remove tag-required if using tagged deployment
orka vm deploy --image <IMAGE> --tag <TAG> --tag-required=false

# Option 4: Wait for resources to free up
orka vm delete <UNUSED_VM>  # Clean up unused VMs

# Option 5: Add more nodes to namespace (requires admin role)
orka node namespace <ADDITIONAL_NODE> <YOUR_NAMESPACE>
```

**Memory caps:** `--memory` can't exceed 32GB on 32GB nodes or 60GB on 64GB and 128GB nodes. Requests above the cap fail with `The provided memory or CPU is greater than the maximum allowed.`

## Problem: Apple silicon VM limit reached

**Symptoms:**
- `The maximum supported number of Apple silicon VMs has been reached.`
- `orka node list -o wide` shows free CPU and memory on the node, but the deploy still fails

**Cause:** Apple's macOS EULA limits each Apple silicon node to 2 running VMs, regardless of free CPU or memory. Apple silicon capacity is counted in VM slots: 2 x the number of Apple silicon nodes in the namespace.

**Solutions:**
```bash
# Count running VMs per node in the namespace
orka vm list -n <NAMESPACE> -o wide

# Free a slot by deleting finished or leaked VMs
orka vm delete <UNUSED_VM> -n <NAMESPACE>

# Add Apple silicon nodes to the namespace (requires admin role)
orka node namespace <ADDITIONAL_NODE> <NAMESPACE>
```

Set CI concurrency limits at or below 2 x the Apple silicon nodes in the target namespace, so jobs queue in the CI system instead of failing at deploy.

## Problem: Deploys fail on a node that shows READY with free capacity

**Symptoms:**
- `Cannot deploy to requested node "<NODE>". Make sure that the node is accessible and has sufficient available resources.`
- `Cannot deploy with required tag "<TAG>". Verify that there are nodes with the tag that have enough available resources or deploy the VM without the required tag.`
- `orka node list` shows the node as `READY` with free CPU and memory

**Cause:** The node is cordoned in Kubernetes (`SchedulingDisabled`). `orka node list` doesn't show cordons, and the deploy error is generic. The real reason only appears in Kubernetes events as `N node(s) were unschedulable`.

**Diagnosis (admins with kubectl access):**
```bash
# Cordoned nodes show SchedulingDisabled in the STATUS column
kubectl get nodes

# Scheduling failures for the namespace
kubectl get events -n <NAMESPACE> --field-selector reason=FailedScheduling
```

**Solution:** Find out why the node was cordoned before reversing it. When it's safe, `kubectl uncordon <NODE_NAME>`.

## Problem: VM deployment succeeds but VM is unresponsive

**Symptoms:**
- VM appears as "Running"
- Cannot connect via Screen Sharing or SSH
- Timeout connecting

**Diagnosis:**
```bash
# 1. Check VM status
orka vm list <VM_NAME> --output wide

# 2. Verify IP and ports are assigned
# Look for IP address, SSH port, Screen Sharing port

# 3. Check if this is an Intel VM that needs power on (Orka 3.6 and earlier)
# Intel VMs may need explicit start command
```

**Solutions:**
```bash
# For Intel VMs on Orka 3.6 and earlier - try power operations (removed in Orka 4.0)
orka3 vm start <VM_NAME>

# For Apple Silicon VMs - wait a few minutes for boot
# macOS takes time to boot, especially on first launch

# Check if Screen Sharing is enabled on the VM
# Some images require manual enablement

# Verify image has connectivity tools installed
# MacStadium base images (ghcr.io/macstadium/orka-images/*)
# come pre-configured with SSH and Screen Sharing

# If VM is still unresponsive:
orka vm delete <VM_NAME>
orka vm deploy --image <VERIFIED_IMAGE>  # Use known-good image
```

## Problem: VM deployment fails with "Image not found"

**Symptoms:**
- `Failed to pull image due to image not found, is the name correct?` (OCI images)
- `Failed to pull image due to being unauthorized (on some OCI registries/providers this may also mean image not found).`
- "Image <IMAGE_NAME> not found" (local images)

**Diagnosis:**
```bash
# 1. List available local images
orka image list

# 2. Check if it's an OCI image
orka ic list  # Check cached OCI images

# 3. Verify image name spelling
```

**Solutions:**
```bash
# For local images - verify exact name
orka image list <IMAGE_NAME>

# For OCI images - ensure full path with registry
orka vm deploy --image ghcr.io/macstadium/orka-images/sonoma:latest

# Check if image needs to be cached (Apple Silicon)
orka ic add <OCI_IMAGE> --all
orka ic info <OCI_IMAGE>  # Wait for 'Ready' status

# For Intel - check if deprecated remote-image command was used
# Use OCI registries instead
```

## Problem: VM name already exists

**Symptoms:**
- "VM with name <VM_NAME> already exists"
- Name conflict error

**Solutions:**
```bash
# Use --generate-name for a unique suffix (recommended)
orka vm deploy my-vm --image <IMAGE> --generate-name

# Or delete the existing VM first
orka vm delete <VM_NAME>
orka vm deploy <VM_NAME> --image <IMAGE>
```

## Problem: VM or config name is rejected

Orka 3.6 returns one of two messages, depending on which check the name fails first:

- `a lowercase RFC 1123 subdomain must consist of ...`: the Kubernetes object-name check. Triggered by uppercase letters or `_`.
- `VM name must consist of lower case alphanumeric characters or ' - ', start with an alphabetic character, ...` or `VM config name must be a valid DNS-1035 label. ...`: Orka's DNS-1035 check. Triggered by names that pass the first check but start with a digit, contain `.`, or exceed the length limit (63 characters for VMs, 50 for VM configs).

**Solution:** Use lowercase letters, digits, and `-` only, start with a letter, and end with a letter or digit.

```bash
orka vm deploy ci-build --image <IMAGE> --generate-name
```

## Problem: "Namespace has no nodes"

**Symptoms:**
- Cannot deploy VMs in namespace
- ``No node in `READY` state is available to deploy to. Run `orka nodes list --namespace <NAMESPACE>` to check nodes state``

**Diagnosis:**
```bash
# Check nodes in namespace
orka node list --namespace <NAMESPACE>
```

**Solutions:**
```bash
# Move nodes to namespace (requires admin role)
orka node namespace <NODE_NAME> <TARGET_NAMESPACE>

# Verify nodes appear
orka node list --namespace <TARGET_NAMESPACE>
```

## Problem: Tag required but no tagged nodes available

**Symptoms:**
- `Required Tag "<TAG>" is not available. Verify that there are nodes with the tag that have enough available resources or deploy the VM without the required tag.`
- `Cannot deploy with required tag "<TAG>". Verify that there are nodes with the tag that have enough available resources or deploy the VM without the required tag.`

**Solutions:**
```bash
# Check if tagged nodes exist
orka node list -o wide              # Check Tags column for <TAG>

# Option 1: Tag a node (requires admin role)
orka node tag <NODE> <TAG>

# Option 2: Deploy without strict tag requirement
orka vm deploy --image <IMAGE> --tag <TAG> --tag-required=false

# Option 3: Deploy without tag
orka vm deploy --image <IMAGE>
```

If the tagged nodes show `READY` with free capacity, check for a cordoned node (see [Deploys fail on a node that shows READY with free capacity](#problem-deploys-fail-on-a-node-that-shows-ready-with-free-capacity)).

## Problem: Node can't be moved to another namespace

**Symptoms:**
- `cannot move node "<NODE>" to namespace "<NS>" because the node has running VMs. Please remove the VMs before attempting to move the node`

**Solution:** Drain the node first: stop scheduling new work to it, wait for its VMs to finish or delete them, then run `orka node namespace`. See [node-commands.md](../commands/node-commands.md).

## Problem: "Not enough disk space on node" (Orka 4.0)

**Symptoms:**
- Deploy fails with `Not enough disk space on node <NODE> to deploy the VM`, followed by the space the VM needs and the space available
- The VM's pod records a `FailedCreate` event with the same error

**Cause:** the node doesn't have room for the VM's disk. On 3.6 the same condition surfaced as `Unable to deploy the VM as the underlying VM process has crashed.` From 4.0, concurrent deploys and image pulls on a node also reserve the space they still need, so a node no longer runs out of disk mid-pull.

**Solutions:**
```bash
# Deploy to another node, or let the scheduler pick one
orka vm deploy --image <IMAGE> --node <OTHER_NODE>

# Free disk on the node by removing cached images you no longer deploy
orka ic remove <OLD_IMAGE> --nodes <NODE_NAME>
```

See node disk sizing in [scaling-workflows.md](../workflows/scaling-workflows.md).

## Problem: Intel image or setting rejected (Orka 4.0)

**Symptoms (Orka 4.0 and later):**
- `Intel VMs are not supported as of Orka 4.0` when creating a VM or VM config, including with `kubectl apply`
- `<FIELD> is not supported as of Orka 4.0, which no longer supports Intel VMs` (for `iso`, `systemSerial`, `gpuPassthrough`, or `legacyIO`), with HTTP `400` from the API
- `Error: unknown flag: --iso` (or `--gpu`, `--system-serial`, `--disable-net-boost`, `--legacy-io`) from the CLI

**Cause:** Orka 4.0 runs on Apple silicon only. The API and the admission webhook reject new objects that reference an amd64 image or turn on an Intel-only setting. `netBoost` is accepted with any value and ignored. Objects created on 3.6 can still be updated and deleted.

**Solution:** Use an Apple silicon (arm64) image and drop the Intel-only setting. If you still need Intel VMs, keep that cluster on Orka 3.6 (supported through March 2028). See `references/commands/rest-api.md`.

## VM Start Diagnostics (v3.6+)

In Orka 3.6+, VM start failures surface actionable error messages. Earlier versions returned empty messages for the same failures.

**Common error types:**
- **VZErrorDomain**: macOS Virtualization framework error, usually a hardware/image compatibility issue or resource exhaustion at the host level. Check `/opt/orka/logs/vm/` for the full error code.
- **Configuration validation failures**: invalid disk size, unsupported CPU/memory combination, or missing image.

If you're on an older version and getting empty error messages on VM start failures, upgrading to 3.6 will surface the actual cause.

### On-prem node diagnosis

On Orka Anywhere on-prem clusters, a failed deploy often surfaces only as `Unable to deploy the VM as the underlying VM process has crashed.` The root cause is on the Mac node.

```bash
# 1. Find the failed VMI name in the operator logs
kubectl logs -n default deployment/orka-operator --since=1h

# 2. Find the node it landed on: look for "Successfully assigned <NS>/<VMI_NAME> to <NODE>"
kubectl events -n <NAMESPACE>
```

Failed VMs are cleaned up automatically, so they won't appear in `orka vm list`. To troubleshoot, deploy manually to the suspect node with `orka vm deploy --image <IMAGE> --node <NODE_NAME>` and read the node logs (see the table below).

**Node log signatures:**
- `VZErrorDomain Code=-9 "The virtual machine encountered a security error."`: the VM user's login keychain is locked because a different user holds the foreground GUI session on the node. Check `ORKA_ENGINE_VIRTUAL_MACHINE_USER` in `/Library/LaunchDaemons/com.macstadium.orka-engine.server.managed.plist` and make sure that user is logged into the GUI.
- `VM ... exited with code 9`: SIGKILL from the Virtual Kubelet. It appears on every VM delete, so it isn't a problem on its own. Read the log lines before it.

**Raise the Virtual Kubelet log level** (default `error`): set `LOG_LEVEL` to `info` in `/Library/LaunchDaemons/orka.virtual.kubeletd.plist`, then reload the service:

```bash
sudo launchctl bootout system /Library/LaunchDaemons/orka.virtual.kubeletd.plist
sudo launchctl bootstrap system /Library/LaunchDaemons/orka.virtual.kubeletd.plist
```

## Log Sources for Deep Troubleshooting (v3.4+)

When CLI diagnostics aren't sufficient, check the underlying logs:

| Log Type | Location | Access Method | Purpose |
|----------|----------|---------------|---------|
| Virtual Kubelet Logs | Mac Node | Via promtail: `/var/log/virtual-kubelet/vk.log` | Interactions between k8s and worker node for managing virtualization |
| Orka VM Logs | Mac Node | Via promtail: `/opt/orka/logs/vm/` | Logs pertaining to the lifecycle of a specific VM |
| Orka Engine Logs | Engine Node | `/opt/orka/logs/com.macstadium.orka-engine.server.managed.log` | Logs pertaining to Orka Engine |
| Pod Logs | Kubernetes | Kubernetes Client, Dashboard, or Helm Chart exposing to secondary service | All Kubernetes-level behavior |

**When to check each log:**
- **VM won't start / lifecycle issues** → Orka VM Logs (`/opt/orka/logs/vm/`)
- **Node not responding / scheduling issues** → Virtual Kubelet Logs (`/var/log/virtual-kubelet/vk.log`)
- **Engine-level errors** → Orka Engine Logs
- **Kubernetes orchestration issues** → Pod Logs via kubectl or dashboard
