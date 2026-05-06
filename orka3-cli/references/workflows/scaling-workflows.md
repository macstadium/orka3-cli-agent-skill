# Scaling and Resource Optimization Workflows

This guide covers VM scaling, disk management, and resource optimization.

## Contents
- [Scaling VMs for Load Testing](#scaling-vms-for-load-testing)
- [VM Disk Management Workflow](#vm-disk-management-workflow)
- [Resource Optimization](#resource-optimization)
- [Scheduler Options](#scheduler-options)
- [Parallel VM Deployment Patterns](#parallel-vm-deployment-patterns)

## Scaling VMs for Load Testing

**Deploy multiple VMs for parallel workloads:**

```bash
# 1. Create VM config for load testing
orka3 vmc create load-test-vm \
  --image sonoma-configured \
  --cpu 4 \
  --memory 8 \
  --tag load-testing \
  --tag-required=false

# 2. Tag nodes that can handle load testing
orka3 node tag mini-arm-1 load-testing
orka3 node tag mini-arm-2 load-testing
orka3 node tag mini-arm-3 load-testing

# 3. Deploy multiple VMs with generated names
for i in {1..10}; do
  orka3 vm deploy load-test --config load-test-vm --generate-name
done

# 4. List all VMs
orka3 vm list --output wide

# 5. Get VM IPs for load testing script
orka3 vm list -o json | jq -r '.items[] | select(.name | startswith("load-test")) | .ip'

# 6. After load testing, clean up all VMs
orka3 vm list -o json | jq -r '.items[] | select(.name | startswith("load-test")) | .name' | \
  while read vm; do orka3 vm delete $vm; done
```

## VM Disk Management Workflow

**Resize VM disks and manage storage:**

### Apple Silicon - Simple resize

```bash
# 1. Deploy VM
orka3 vm deploy my-vm --image sonoma-90gb --cpu 4

# 2. Resize to 150GB (automatic)
orka3 vm resize my-vm 150

# 3. Verify resize (VM will restart)
orka3 vm list my-vm --output wide
```

### Intel - Resize with repartition

```bash
# 1. Deploy VM
orka3 vm deploy intel-vm --image ventura-90gb.img --cpu 6

# 2. Resize with automatic repartition (requires SSH access)
orka3 vm resize intel-vm 150 --user "$VM_USER" --password "$VM_PASSWORD"

# OR resize without automatic repartition
orka3 vm resize intel-vm 150
# Then manually repartition via Disk Utility on the VM

# 3. Save resized image for future use
orka3 vm save intel-vm ventura-150gb.img

# 4. Clean up
orka3 vm delete intel-vm

# 5. Deploy new VMs with larger disk
orka3 vm deploy --image ventura-150gb.img
```

## Resource Optimization

**Monitor and optimize cluster resource usage:**

```bash
# 1. Check overall cluster resources
orka3 node list --output wide

# 2. Identify underutilized nodes
# Look for nodes with high available CPU/memory

# 3. Check VM distribution
orka3 vm list --output wide | awk '{print $NF}' | sort | uniq -c

# 4. Identify over-provisioned VMs
orka3 vm list --output wide | sort -k3 -nr  # Sort by CPU
orka3 vm list --output wide | sort -k4 -nr  # Sort by memory

# 5. Right-size VM configs
# Create smaller configs for less demanding workloads
orka3 vmc create small-vm --image sonoma --cpu 2 --memory 4
orka3 vmc create medium-vm --image sonoma --cpu 4 --memory 8
orka3 vmc create large-vm --image sonoma --cpu 6 --memory 12

# 6. Use scheduler for better packing
orka3 vmc create packed-vm \
  --image sonoma \
  --cpu 4 \
  --scheduler most-allocated

# 7. Clean up unused images
orka3 image list --output wide
# Identify old/unused images
orka3 image delete <OLD_IMAGE>

# 8. Clean up unused VM configs
orka3 vmc list --output wide
# Identify obsolete configs
orka3 vmc delete <OLD_CONFIG>
```

## Scheduler Options

| Scheduler | Behavior | Use Case |
|-----------|----------|----------|
| `default` | Spreads VMs across nodes | General workloads, high availability |
| `most-allocated` | Packs VMs on fewest nodes | Cost optimization, power savings |

```bash
# Spread VMs (default)
orka3 vmc create spread-vm --image sonoma --cpu 4 --scheduler default

# Pack VMs
orka3 vmc create packed-vm --image sonoma --cpu 4 --scheduler most-allocated
```

## Parallel VM Deployment Patterns

### Deploy Multiple VMs Sequentially

```bash
for i in {1..5}; do
  orka3 vm deploy build-$i --image sonoma:latest --cpu 4
done
```

### Deploy Multiple VMs with Generated Names

```bash
for i in {1..5}; do
  orka3 vm deploy build --image sonoma:latest --cpu 4 --generate-name
done
```

### Get All VM IPs for Scripting

```bash
# All VMs
orka3 vm list -o json | jq -r '.items[].ip'

# Filtered by name prefix
orka3 vm list -o json | jq -r '.items[] | select(.name | startswith("build")) | .ip'

# With name and IP
orka3 vm list -o json | jq -r '.items[] | "\(.name) \(.ip)"'
```
