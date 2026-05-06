# VM Deployment Troubleshooting

This guide covers common VM deployment issues with the Orka3 CLI.

## Contents
- [Quick Triage Checklist](#quick-triage-checklist)
- [Problem: VM deployment fails with "Insufficient resources"](#problem-vm-deployment-fails-with-insufficient-resources)
- [Problem: VM deployment succeeds but VM is unresponsive](#problem-vm-deployment-succeeds-but-vm-is-unresponsive)
- [Problem: VM deployment fails with "Image not found"](#problem-vm-deployment-fails-with-image-not-found)
- [Problem: VM name already exists](#problem-vm-name-already-exists)
- [Problem: "Namespace has no nodes"](#problem-namespace-has-no-nodes)
- [Problem: "Tag required but no tagged nodes available"](#problem-tag-required-but-no-tagged-nodes-available)
- [Log Sources for Deep Troubleshooting (v3.4+)](#log-sources-for-deep-troubleshooting-v34)

## Quick Triage Checklist

```bash
# 1. Check node resources
orka3 node list --output wide

# Look for:
# - Available CPU/memory
# - Node status
# - Existing VM count

# 2. Check if image exists and is ready
orka3 image list <IMAGE_NAME> --output wide

# For OCI images, verify caching status
orka3 ic info <OCI_IMAGE>

# 3. Verify namespace has resources
orka3 node list --namespace <YOUR_NAMESPACE>

# 4. Check for VM name conflicts
orka3 vm list <VM_NAME>

# 5. Try deployment with longer timeout
orka3 vm deploy --image <IMAGE> --timeout 20

# 6. Try deployment on specific node
orka3 vm deploy --image <IMAGE> --node <NODE_NAME>

# 7. Check if VM config exists
orka3 vmc list <CONFIG_NAME> --output wide

# 8. If tag-required is set, verify tagged nodes exist
orka3 node list -o wide              # Check Tags column for <TAG>

# 9. Try with JSON output for detailed error messages
orka3 vm deploy --image <IMAGE> -o json
```

## Problem: VM deployment fails with "Insufficient resources"

**Symptoms:**
- "Not enough CPU available"
- "Not enough memory available"
- Deployment times out

**Diagnosis:**
```bash
# 1. Check node resources
orka3 node list --output wide

# Look for available CPU and memory

# 2. Check current VM usage
orka3 vm list --output wide

# 3. Check if namespace has any nodes
orka3 node list --namespace <YOUR_NAMESPACE>
```

**Solutions:**
```bash
# Option 1: Reduce VM resource requirements
orka3 vm deploy --image <IMAGE> --cpu 3 --memory 6  # Smaller resources

# Option 2: Deploy to specific node with resources
orka3 node list --output wide  # Find node with resources
orka3 vm deploy --image <IMAGE> --node <NODE_WITH_RESOURCES>

# Option 3: Remove tag-required if using tagged deployment
orka3 vm deploy --image <IMAGE> --tag <TAG> --tag-required=false

# Option 4: Wait for resources to free up
orka3 vm delete <UNUSED_VM>  # Clean up unused VMs

# Option 5: Add more nodes to namespace (requires admin role)
orka3 node namespace <ADDITIONAL_NODE> <YOUR_NAMESPACE>
```

## Problem: VM deployment succeeds but VM is unresponsive

**Symptoms:**
- VM appears as "Running"
- Cannot connect via Screen Sharing or SSH
- Timeout connecting

**Diagnosis:**
```bash
# 1. Check VM status
orka3 vm list <VM_NAME> --output wide

# 2. Verify IP and ports are assigned
# Look for IP address, SSH port, Screen Sharing port

# 3. Check if this is an Intel VM that needs power on
# Intel VMs may need explicit start command
```

**Solutions:**
```bash
# For Intel VMs - try power operations
orka3 vm start <VM_NAME>

# For Apple Silicon VMs - wait a few minutes for boot
# macOS takes time to boot, especially on first launch

# Check if Screen Sharing is enabled on the VM
# Some images require manual enablement

# Verify image has connectivity tools installed
# MacStadium base images (ghcr.io/macstadium/orka-images/*)
# come pre-configured with SSH and Screen Sharing

# If VM is still unresponsive:
orka3 vm delete <VM_NAME>
orka3 vm deploy --image <VERIFIED_IMAGE>  # Use known-good image
```

## Problem: VM deployment fails with "Image not found"

**Symptoms:**
- "Image <n> not found"
- "No such image"

**Diagnosis:**
```bash
# 1. List available local images
orka3 image list

# 2. Check if it's an OCI image
orka3 ic list  # Check cached OCI images

# 3. Verify image name spelling
```

**Solutions:**
```bash
# For local images - verify exact name
orka3 image list <IMAGE_NAME>

# For OCI images - ensure full path with registry
orka3 vm deploy --image ghcr.io/macstadium/orka-images/sonoma:latest

# Check if image needs to be cached (Apple Silicon)
orka3 ic add <OCI_IMAGE> --all
orka3 ic info <OCI_IMAGE>  # Wait for 'ready' status

# For Intel - check if deprecated remote-image command was used
# Use OCI registries instead
```

## Problem: VM name already exists

**Symptoms:**
- "VM with name <n> already exists"
- Name conflict error

**Solutions:**
```bash
# Use --generate-name for a unique suffix (recommended)
orka3 vm deploy my-vm --image <IMAGE> --generate-name

# Or delete the existing VM first
orka3 vm delete <VM_NAME>
orka3 vm deploy <VM_NAME> --image <IMAGE>
```

## Problem: "Namespace has no nodes"

**Symptoms:**
- Cannot deploy VMs in namespace
- "No nodes available in namespace"

**Diagnosis:**
```bash
# Check nodes in namespace
orka3 node list --namespace <NAMESPACE>
```

**Solutions:**
```bash
# Move nodes to namespace (requires admin role)
orka3 node namespace <NODE_NAME> <TARGET_NAMESPACE>

# Verify nodes appear
orka3 node list --namespace <TARGET_NAMESPACE>
```

## Problem: "Tag required but no tagged nodes available"

**Symptoms:**
- Deployment fails with tag requirement error

**Solutions:**
```bash
# Check if tagged nodes exist
orka3 node list -o wide              # Check Tags column for <TAG>

# Option 1: Tag a node (requires admin role)
orka3 node tag <NODE> <TAG>

# Option 2: Deploy without strict tag requirement
orka3 vm deploy --image <IMAGE> --tag <TAG> --tag-required=false

# Option 3: Deploy without tag
orka3 vm deploy --image <IMAGE>
```

## VM Start Diagnostics (v3.6+)

In Orka 3.6+, VM start failures surface actionable error messages. Earlier versions returned empty messages for the same failures.

**Common error types:**
- **VZErrorDomain** — macOS Virtualization framework error, usually a hardware/image compatibility issue or resource exhaustion at the host level. Check `/opt/orka/logs/vm/` for the full error code.
- **Configuration validation failures** — invalid disk size, unsupported CPU/memory combination, or missing image.

If you're on an older version and getting empty error messages on VM start failures, upgrading to 3.6 will surface the actual cause.

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
