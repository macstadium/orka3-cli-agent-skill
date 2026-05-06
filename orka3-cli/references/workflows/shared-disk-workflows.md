# VM Shared Attached Disk Workflows

This guide covers configuring and managing VM shared attached disks in Orka 3.5.2+.

## Contents
- [Overview](#overview)
- [AWS Deployment Workflow](#aws-deployment-workflow)
- [On-Premises / MSDC Deployment Workflow](#on-premises--msdc-deployment-workflow)
- [First-Time Per-Host Disk Initialization](#first-time-per-host-disk-initialization)
- [Requirements Checklist](#requirements-checklist)
- [Troubleshooting](#troubleshooting)

## Overview

The Orka AMI supports automatic setup of VM shared attached disks during instance initialization. This feature provides standardized storage configuration across your infrastructure.

**Key Benefits:**
- Consistent VM storage across deployments
- Automatic disk provisioning (no manual storage setup)
- Flexible sizing per instance

**Critical Limitations:**
- **Apple Silicon:** When shared attached disk is enabled, only ONE VM may run per Apple silicon node
- Feature is disabled by default and requires explicit enablement

## AWS Deployment Workflow

Setting up shared attached disks on AWS requires a two-step process.

### Step 1: Enable Globally via CodeBuild/Ansible

Configure your Ansible variables to enable the feature cluster-wide:

```yaml
vm_shared_disk_enabled: true
```

Run your CodeBuild project to apply the configuration.

### Step 2: Configure Each EC2 Mac Instance

Add the following to your EC2 Mac instance user data script:

```bash
#!/bin/bash
export VM_SHARED_DISK_SIZE=500
/usr/local/bin/bootstrap-orka <eks-cluster-name> <aws-region> <orka-engine-license-key>
```

Replace:
- `<eks-cluster-name>` with your EKS cluster name
- `<aws-region>` with your AWS region (e.g., `us-east-1`)
- `<orka-engine-license-key>` with your Orka license key
- `500` with your desired disk size in GB

### Verification

After instance bootstrap completes:
1. VMs deployed on the instance will automatically use the shared attached disk
2. Verify by deploying a test VM and checking storage configuration

### Disabling the Feature

To disable shared attached disks on AWS:

1. Update Ansible configuration:
   ```yaml
   vm_shared_disk_enabled: false
   ```

2. Re-run your CodeBuild project

3. Terminate existing EC2 Mac instances

4. Re-create EC2 Mac instances (without the `VM_SHARED_DISK_SIZE` variable)

## On-Premises / MSDC Deployment Workflow

### Enable and Configure via Ansible

Set the following variables in your Ansible configuration:

```yaml
# Enable the feature globally
vm_shared_disk_enabled: true

# Optional: Set disk size (in GB)
osx_node_orka_vm_shared_disk_size: 500
```

Run your Ansible playbook to apply the configuration.

### Disabling the Feature

```yaml
vm_shared_disk_enabled: false
```

Re-run Ansible to apply changes.

## First-Time Per-Host Disk Initialization

After enabling shared disk and provisioning a host, the guest-visible shared disk arrives **unformatted**. You must format it once per host — subsequent VMs on that host auto-mount at `/Volumes/shared` with no additional setup.

This applies to **both AWS and on-prem** deployments.

```bash
# 1. Deploy a VM on the host
orka3 vm deploy init-vm --image <IMAGE> --node <HOST_NODE>

# 2. In the guest, find the unformatted disk
diskutil list internal physical
# Look for an unformatted disk (no partition scheme) — note its identifier (e.g., disk1)

# 3. Format the disk (JHFS+ for macOS compatibility)
diskutil eraseDisk -noEFI JHFS+ shared /dev/<disk-identifier>

# 4. Verify mount
ls /Volumes/shared

# 5. Clean up init VM
orka3 vm delete init-vm
```

Once formatted, the disk **persists across host reboots** — this is a one-time operation per host. All future VMs deployed on that host will auto-mount the shared disk at `/Volumes/shared`.

## Requirements Checklist

Before enabling shared attached disks, verify:

- [ ] Orka cluster is upgraded to v3.5.2 or later
- [ ] Cluster was upgraded from Orka 3.4+ / k8s v1.33+
- [ ] Understand the Apple Silicon limitation (1 VM per node when enabled)
- [ ] Have determined appropriate disk sizes for your workloads

## Troubleshooting

### VMs Not Using Shared Disk

1. Verify `vm_shared_disk_enabled: true` is set in Ansible
2. For AWS: Confirm `VM_SHARED_DISK_SIZE` was set in instance user data
3. For AWS: Instance may need to be terminated and re-created after enabling

### Apple Silicon Node Running Multiple VMs

If shared disk is enabled, only one VM can run per Apple Silicon node. To run multiple VMs:
- Disable the shared disk feature, OR
- Use Intel nodes for multi-VM scenarios

### Configuration Changes Not Taking Effect

1. Re-run CodeBuild/Ansible after configuration changes
2. Terminate and re-create affected EC2 Mac instances (AWS)
3. Verify the bootstrap script completed successfully
