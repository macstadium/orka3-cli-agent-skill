# Image Management Workflows

This guide covers custom image preparation, caching, and OCI registry integration.

## Contents
- [Custom Image Preparation Workflow](#custom-image-preparation-workflow)
- [Image Caching for Fast Deployments (Apple Silicon)](#image-caching-for-fast-deployments-apple-silicon)
- [OCI Registry Integration Workflow](#oci-registry-integration-workflow)
- [VM save vs. VM commit](#vm-save-vs-vm-commit)
- [Image Versioning and Promotion](#image-versioning-and-promotion)
- [Apple Silicon Image Known Issues](#apple-silicon-image-known-issues)
- [Image Management Best Practices](#image-management-best-practices)

## Custom Image Preparation Workflow

**Create a custom configured image from a base image:**

```bash
# 1. Deploy base VM
orka3 vm deploy base-config --image ghcr.io/macstadium/orka-images/sonoma:latest

# 2. Get connection info
orka3 vm list base-config --output wide

# 3. Connect via Screen Sharing
# vnc://<VM_IP>:<Screenshare_port>
# Credentials: admin/admin

# 4. On the VM:
#    - Change password (System Settings > Users & Groups)
#    - Install software (brew install xcode-select git node)
#    - Apply OS updates
#    - Configure settings
#    - Install/upgrade Orka VM Tools:
#      brew install orka-vm-tools  # or brew upgrade orka-vm-tools
#      Note: Base images from ghcr.io/macstadium/orka-images are automatically kept
#      current with VM Tools on each Orka release (3.6+). Skip this step if using a
#      current GHCR base image. Only needed for custom images not derived from one.
#    - Install MDM/EDR/DLP agents if required, but don't enroll them here:
#      every VM cloned from this image would share one device identity.
#      Enroll per VM at deploy time instead.

# 5. Flush the guest's disk writes (required). The host copies the running VM's
#    disk without flushing the guest, so unsynced writes can be missing from the image.
ssh -p <SSH_PORT> admin@<VM_IP> sync

# 6. Save as new image (preserves original)
#    save and commit need NFS image storage; on Harbor/OCI-only clusters use vm push
orka3 vm save base-config my-configured-sonoma

# OR commit to original image (modifies original)
orka3 vm commit base-config --description 'Configured with build tools'

# 7. Wait for async operation to complete
orka3 image list my-configured-sonoma --output wide

# 8. Clean up base VM
orka3 vm delete base-config

# 9. Boot-test the published image, not the builder VM
orka3 vm deploy test-vm --image my-configured-sonoma

# 10. Verify configuration persists
# Connect via Screen Sharing and verify changes

# 11. Clean up test VM
orka3 vm delete test-vm

# 12. Deploy production VMs with configured image
orka3 vm deploy prod-vm-1 --image my-configured-sonoma --cpu 6 --memory 12
```

## Image Caching for Fast Deployments (Apple Silicon)

**Pre-cache images on nodes for consistent deployment times:**

```bash
# 1. Check current node image cache
orka3 ic list

# 2. Cache base images on all nodes
orka3 ic add ghcr.io/macstadium/orka-images/sonoma:latest --all

# 3. Check caching progress
orka3 ic info ghcr.io/macstadium/orka-images/sonoma:latest

# Wait until status shows 'Ready' on all nodes

# 4. Cache additional images on specific nodes
orka3 ic add my-configured-image --nodes mini-arm-1,mini-arm-2,mini-arm-3

# 5. Cache by node tags
# First, tag nodes
orka3 node tag mini-arm-4 xcode-15
orka3 node tag mini-arm-5 xcode-15

# Then cache image on tagged nodes
orka3 ic add xcode-15-image --tags xcode-15

# 6. Verify all images are cached
orka3 ic list --output wide

# 7. Deploy VMs (will use cached images - fast!)
orka3 vm deploy --image ghcr.io/macstadium/orka-images/sonoma:latest
```

## OCI Registry Integration Workflow

**Set up and use private OCI registry for images:**

```bash
# As admin:

# 1. Add registry credentials
orka3 regcred add https://ghcr.io \
  --username "$REGISTRY_USER" \
  --password "$REGISTRY_TOKEN"

# OR read password from stdin
echo -n "$REGISTRY_TOKEN" | orka3 regcred add https://ghcr.io \
  --username "$REGISTRY_USER" \
  --password-stdin

# 2. Verify credentials
orka3 regcred list

# 3. Deploy VM from OCI image
orka3 vm deploy --image ghcr.io/your-org/orka-images/custom-sonoma:v1.2

# 4. Customize VM (connect via Screen Sharing)
# Install software, configure settings, etc.

# 5. Flush guest disk writes, then push customized VM back to registry (Apple Silicon only)
ssh -p <SSH_PORT> admin@<VM_IP> sync
orka3 vm push <VM_NAME> ghcr.io/your-org/orka-images/custom-sonoma:v1.3

# 6. Check push status (pass the VM's namespace; finished pushes show Ready)
orka3 vm get-push-status -n <VM_NAMESPACE>

# 7. Deploy new VMs from updated image
orka3 vm deploy --image ghcr.io/your-org/orka-images/custom-sonoma:v1.3

# 8. (Optional) Cache OCI images on nodes
orka3 ic add ghcr.io/your-org/orka-images/custom-sonoma:v1.3 --all
```

## VM save vs. VM commit

| Operation | Behavior | Use Case |
|-----------|----------|----------|
| `vm save` | Creates new image, preserves original | Creating variants of a base image |
| `vm commit` | Updates original image | Iterative development on single image |
| `vm push` | Pushes to an OCI registry, doesn't restart the VM | Distributing images (Apple Silicon); the only option on Harbor/OCI-only clusters |

`vm save` and `vm commit` require NFS image storage on the cluster. On clusters that use only Harbor or another OCI registry (Harbor is the default for new deployments since 3.5), they fail with `image storage is not supported`; use `vm push`.

## Image Versioning and Promotion

- Push every build under an immutable version tag (for example `:1.4.2`) and never re-push a version tag.
- Use channel tags (for example `:stable`) to mark which version is promoted.
- Promote and roll back by repointing the VM config CI uses at a version tag. VM configs can't be updated in place, so create a config for the new version, repoint CI, then delete the old config (see [vm-config-commands.md](../commands/vm-config-commands.md)).

## Apple Silicon Image Known Issues

- **Use Orka VM Tools 3.6.0 or later.** Any VM Tools from 3.6.0 on work on both 3.6 and 4.0 clusters, and `brew upgrade orka-vm-tools` (which now installs 4.0.0) is safe on a 3.6 cluster. VM Tools 4.0 is required only for 4.0's User Data feature. VM Tools is versioned separately from the cluster: on the 3.6 line it stays at 3.6.0 for every patch release, so don't expect the VM Tools version to equal the cluster version.
- **Upgrade macOS before resizing the disk.** A macOS upgrade can fail on a resized VM. Upgrade first and resize last. If you've already resized, start from an unresized image.
- **Provisioning UDID isn't stable across deploys on Sequoia.** If signing needs a stable Provisioning UDID, build from a Sonoma base image, upgrade the guest to Sequoia in place, then save the image.

## Image Management Best Practices

1. **Test images before deployment** - Boot-test the published image, not the builder VM
2. **Run `sync` before push, save, or commit** - Otherwise recent writes can be missing
3. **Use descriptive names** - Include version or date in image names
4. **Cache images for CI/CD** - Pre-cache on dedicated CI nodes
5. **Use OCI registries** - Standard approach for image distribution
6. **Document image configurations** - Track what's installed in each image
7. **Clean up unused images** - Regularly remove old/unused images
