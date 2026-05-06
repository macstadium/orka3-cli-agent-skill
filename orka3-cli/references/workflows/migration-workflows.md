# Migration and Backup Workflows

This guide covers Intel to Apple Silicon migration and disaster recovery strategies.

## Contents
- [Migration from Intel to Apple Silicon](#migration-from-intel-to-apple-silicon)
- [Intel vs. Apple Silicon Feature Comparison](#intel-vs-apple-silicon-feature-comparison)
- [Disaster Recovery and Backup Strategy](#disaster-recovery-and-backup-strategy)
- [Image Backup to OCI Registry (Apple Silicon)](#image-backup-to-oci-registry-apple-silicon)
- [Recovery Procedures](#recovery-procedures)
- [Migration Checklist](#migration-checklist)

## Migration from Intel to Apple Silicon

**Plan and execute architecture migration:**

```bash
# 1. Audit current Intel VMs
orka3 vm list --output wide              # Check Arch column for amd64 VMs

# 2. Identify Intel-specific features in use
# - GPU passthrough
# - Custom serial numbers
# - ISO installations
# - Power operations (start/stop/suspend/resume)

# 3. For each Intel VM:
#    a. Document configuration
orka3 vm list <INTEL_VM> --output wide

#    b. Create ARM equivalent image
#       Deploy Intel VM, configure, save as new image
orka3 vm save <INTEL_VM> intel-configured-image

#    c. Manually recreate on ARM (no direct conversion)
#       Deploy ARM VM, manually configure with same settings
orka3 vm deploy arm-vm --image ghcr.io/macstadium/orka-images/sonoma:latest

#    d. Test ARM VM thoroughly
#    e. Create VM config for ARM version
orka3 vmc create arm-version \
  --image arm-configured-image \
  --cpu 4 \
  --memory 8

# 4. Update CI/CD pipelines to use ARM configs
# 5. Monitor performance and adjust resources as needed
# 6. Decommission Intel VMs after validation
```

## Intel vs. Apple Silicon Feature Comparison

| Feature | Intel (amd64) | Apple Silicon (arm64) |
|---------|---------------|----------------------|
| Power operations | start, stop, suspend, resume, revert | Not available |
| GPU passthrough | Supported | Not supported |
| ISO installation | Supported | Not supported |
| Custom serial | Supported | Not supported |
| OCI registry push | Not supported | Supported |
| Image caching | Not supported | Supported |
| Disk resize | Requires SSH credentials | Automatic |

## Disaster Recovery and Backup Strategy

**Back up images and configurations:**

```bash
# 1. List all images and VM configs
orka3 image list -o json > images-backup-$(date +%Y%m%d).json
orka3 vmc list -o json > vm-configs-backup-$(date +%Y%m%d).json

# 2. For Apple Silicon: Push important images to OCI registry
orka3 regcred add https://ghcr.io --username "$REGISTRY_USER" --password "$REGISTRY_TOKEN"

# Deploy VM from image, then push to registry
orka3 vm deploy backup-vm --image important-image
orka3 vm push backup-vm ghcr.io/company/backups/important-image:$(date +%Y%m%d)
orka3 vm delete backup-vm

# 3. For Intel: Copy images to another Orka cluster
# (Use remote-image commands or manual file transfer)

# 4. Document namespace configurations
orka3 namespace list -o json > namespaces-backup-$(date +%Y%m%d).json
orka3 rb list-subjects --namespace orka-default -o json > rbac-default-$(date +%Y%m%d).json
orka3 rb list-subjects --namespace orka-prod -o json > rbac-prod-$(date +%Y%m%d).json

# 5. Document node assignments
orka3 node list --output wide > nodes-layout-$(date +%Y%m%d).txt
```

## Image Backup to OCI Registry (Apple Silicon)

```bash
# 1. Ensure registry credentials are configured
orka3 regcred list

# 2. For each important image:
#    a. Deploy a VM from the image
orka3 vm deploy backup-vm --image <IMAGE_NAME>

#    b. Push to registry with date tag
orka3 vm push backup-vm ghcr.io/company/backups/<IMAGE_NAME>:$(date +%Y%m%d)

#    c. Wait for push to complete
orka3 vm get-push-status

#    d. Clean up backup VM
orka3 vm delete backup-vm

# 3. Verify backup in registry
# Use external registry tools or GitHub UI to confirm
```

## Recovery Procedures

### Restore from OCI Registry

```bash
# 1. Add registry credentials (if not already configured)
orka3 regcred add https://ghcr.io --username <USER> --password <TOKEN>

# 2. Deploy VM from backed-up image
orka3 vm deploy restored-vm --image ghcr.io/company/backups/<IMAGE_NAME>:<DATE>

# 3. Save as local image (optional)
orka3 vm save restored-vm <LOCAL_IMAGE_NAME>

# 4. Clean up
orka3 vm delete restored-vm
```

### Recreate Namespace Configuration

```bash
# Using saved backup files:

# 1. Create namespace
orka3 namespace create <NAMESPACE_NAME>

# 2. Move nodes (from saved node layout)
orka3 node namespace <NODE> <NAMESPACE_NAME>

# 3. Restore access (from saved RBAC backup)
# Review rbac-*.json files and recreate rolebindings
orka3 rb add-subject --namespace <NS> --user <EMAIL>
orka3 rb add-subject --namespace <NS> --serviceaccount <SA_NS>:<SA_NAME>
```

## Migration Checklist

- [ ] Document all current Intel VM configurations
- [ ] Identify Intel-only features in use
- [ ] Plan workarounds for unavailable features
- [ ] Create ARM-compatible images
- [ ] Test ARM VMs thoroughly
- [ ] Update CI/CD pipelines
- [ ] Train team on ARM-specific workflows
- [ ] Set migration date and cutover plan
- [ ] Back up all Intel images before decommissioning
- [ ] Monitor ARM VMs post-migration
