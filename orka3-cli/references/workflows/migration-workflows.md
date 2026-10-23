# Migration and Backup Workflows

This guide covers Intel to Apple Silicon migration, NFS-to-OCI (Harbor) image migration, and disaster recovery strategies.

## Contents
- [Migration from Intel to Apple Silicon](#migration-from-intel-to-apple-silicon)
- [Intel vs. Apple Silicon Feature Comparison (Orka 3.6 and earlier)](#intel-vs-apple-silicon-feature-comparison-orka-36-and-earlier)
- [Migrating NFS Images to OCI with Harbor](#migrating-nfs-images-to-oci-with-harbor)
- [Disaster Recovery and Backup Strategy](#disaster-recovery-and-backup-strategy)
- [Image Backup to OCI Registry (Apple Silicon)](#image-backup-to-oci-registry-apple-silicon)
- [Recovery Procedures](#recovery-procedures)
- [Migration Checklist](#migration-checklist)

## Migration from Intel to Apple Silicon

Orka 3.6 is the last release with Intel support. Intel is supported through March 2028; plan to finish migrating by December 2027. A cluster with Intel worker nodes can't upgrade to Orka 4.0, so do this migration on 3.6, with the 3.6 `orka3` CLI.

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

## Intel vs. Apple Silicon Feature Comparison (Orka 3.6 and earlier)

| Feature | Intel (amd64) | Apple Silicon (arm64) |
|---------|---------------|----------------------|
| Power operations | start, stop, suspend, resume, revert | Not available |
| GPU passthrough | Supported | Not supported |
| ISO installation | Supported | Not supported |
| Custom serial | Supported | Not supported |
| OCI registry push | Not supported | Supported |
| Image caching | Not supported | Supported |
| Disk resize | SSH credentials for automatic repartition, otherwise manual | Requires Orka VM Tools in the guest, on the cluster's release line |

## Migrating NFS Images to OCI with Harbor

Requires Orka 3.5+ (check with `orka version`) and a MacStadium-provisioned Harbor instance (request it from support@macstadium.com). Harbor credentials are in your firewall's Credentials section in My Cloud; the Harbor URL is usually the last IP in your Orka subnet (for example `https://10.221.189.254`) with a default project of `library`. Full guide: [Migrate NFS Orka images to OCI format with Harbor](https://docs.macstadium.com/orka/oci-images/orka-self-service-migrating-nfs-images-to-oci-with-harbor).

```bash
# 1. Add Harbor credentials (namespace-specific: repeat with --namespace for each namespace you deploy in)
echo "$HARBOR_PASSWORD" | orka regcred add <HARBOR_FQDN> --username <HARBOR_USER> --password-stdin
orka regcred list

# 2. Pick the NFS images to convert
orka image list

# 3. Deploy a temporary VM from the NFS image (--memory is a number of GB)
orka vm deploy migration-temp-vm --image <NFS_IMAGE_NAME> --cpu 4 --memory 8
orka vm list migration-temp-vm            # Wait until it's running

# 4. Push it to Harbor as an OCI image, then check the push job
orka vm push migration-temp-vm <HARBOR_FQDN>/library/<NEW_IMAGE_NAME>:<TAG>
orka vm get-push-status <JOB_NAME>

# 5. Cache the OCI image on nodes and watch progress
orka imagecache add <HARBOR_FQDN>/library/<NEW_IMAGE_NAME>:<TAG> --all
orka imagecache info <HARBOR_FQDN>/library/<NEW_IMAGE_NAME>:<TAG>

# 6. Clean up, then repeat for each image
orka vm delete migration-temp-vm
```

**Point CI/CD at the OCI image:**
- **GitHub Actions and GitLab** deploy from a VM config. Create one for the OCI image (`orka vm-config create <VM_CONFIGURATION_NAME> --image <HARBOR_FQDN>/library/<NEW_IMAGE_NAME>:<TAG>`), then set `ORKA_VM_CONFIG` (GitHub runner, restart the container) or `ORKA_CONFIG_NAME` (GitLab CI/CD variable or `.gitlab-ci.yml`) to it.
- **Jenkins** takes the image from each Orka Template (Manage Jenkins > Nodes and Clouds > Configure Clouds) and each permanent agent's node configuration, not from the Jenkinsfile. Set **Image** to the OCI reference.
- **Packer:** set `source_image` (and `image_name`) to full OCI references, and push Packer-built images to Harbor.

**Validate and roll out:** deploy a test VM from the OCI image and boot-test it, run your integration smoke tests, and watch Harbor storage. Keep the NFS images until the OCI versions are proven, migrate integrations one at a time, and pre-cache frequently used images on all nodes, ideally off-peak.

## Disaster Recovery and Backup Strategy

**Back up images and configurations:**

```bash
# 1. List all images and VM configs
orka image list -o json > images-backup-$(date +%Y%m%d).json
orka vmc list -o json > vm-configs-backup-$(date +%Y%m%d).json

# 2. For Apple Silicon: Push important images to OCI registry
orka regcred add https://ghcr.io --username "$REGISTRY_USER" --password "$REGISTRY_TOKEN"

# Deploy VM from image, then push to registry
orka vm deploy backup-vm --image important-image
orka vm push backup-vm ghcr.io/company/backups/important-image:$(date +%Y%m%d)
orka vm delete backup-vm

# 3. For Intel: Copy images to another Orka cluster
# (Use remote-image commands or manual file transfer)

# 4. Document namespace configurations
orka namespace list -o json > namespaces-backup-$(date +%Y%m%d).json
orka rbac list-subjects --role dev --namespace orka-default -o json > rbac-default-$(date +%Y%m%d).json
orka rbac list-subjects --role dev --namespace orka-prod -o json > rbac-prod-$(date +%Y%m%d).json

# 5. Document node assignments
orka node list --output wide > nodes-layout-$(date +%Y%m%d).txt
```

## Image Backup to OCI Registry (Apple Silicon)

```bash
# 1. Ensure registry credentials are configured
orka regcred list

# 2. For each important image:
#    a. Deploy a VM from the image
orka vm deploy backup-vm --image <IMAGE_NAME>

#    b. Push to registry with date tag
orka vm push backup-vm ghcr.io/company/backups/<IMAGE_NAME>:$(date +%Y%m%d)

#    c. Wait for push to complete (status Ready; push jobs live in the VM's namespace)
orka vm get-push-status -n <VM_NAMESPACE>

#    d. Clean up backup VM
orka vm delete backup-vm

# 3. Verify backup in registry
# Use external registry tools or GitHub UI to confirm
```

## Recovery Procedures

### Restore from OCI Registry

```bash
# 1. Add registry credentials (if not already configured)
echo "$REGISTRY_TOKEN" | orka regcred add https://ghcr.io --username <USER> --password-stdin

# 2. Deploy VM from backed-up image
orka vm deploy restored-vm --image ghcr.io/company/backups/<IMAGE_NAME>:<DATE>

# 3. Save as local image (optional; requires NFS image storage on the cluster)
orka vm save restored-vm <LOCAL_IMAGE_NAME>

# 4. Clean up
orka vm delete restored-vm
```

### Recreate Namespace Configuration

```bash
# Using saved backup files:

# 1. Create namespace
orka namespace create <NAMESPACE_NAME>

# 2. Move nodes (from saved node layout)
orka node namespace <NODE> <NAMESPACE_NAME>

# 3. Restore access (from saved RBAC backup)
# Review rbac-*.json files and recreate rolebindings
orka rbac add-subject --role dev --namespace <NS> --user <EMAIL>
orka rbac add-subject --role dev --namespace <NS> --serviceaccount <SA_NS>:<SA_NAME>
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
