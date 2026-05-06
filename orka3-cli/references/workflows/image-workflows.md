# Image Management Workflows

This guide covers custom image preparation, caching, and OCI registry integration.

## Contents
- [Custom Image Preparation Workflow](#custom-image-preparation-workflow)
- [Image Caching for Fast Deployments (Apple Silicon)](#image-caching-for-fast-deployments-apple-silicon)
- [OCI Registry Integration Workflow](#oci-registry-integration-workflow)
- [VM save vs. VM commit](#vm-save-vs-vm-commit)
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
#      Note: Base images from ghcr.io/macstadium/orka-images (3.6+) already include
#      the current VM Tools version. Skip this step if using a current base image.

# 5. Save as new image (preserves original)
orka3 vm save base-config my-configured-sonoma

# OR commit to original image (modifies original)
orka3 vm commit base-config --description 'Configured with build tools'

# 6. Wait for async operation to complete
orka3 image list my-configured-sonoma --output wide

# 7. Clean up base VM
orka3 vm delete base-config

# 8. Test the new image
orka3 vm deploy test-vm --image my-configured-sonoma

# 9. Verify configuration persists
# Connect via Screen Sharing and verify changes

# 10. Clean up test VM
orka3 vm delete test-vm

# 11. Deploy production VMs with configured image
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

# Wait until status shows 'ready' on all nodes

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

# 5. Push customized VM back to registry (Apple Silicon only)
orka3 vm push <VM_NAME> ghcr.io/your-org/orka-images/custom-sonoma:v1.3

# 6. Check push status
orka3 vm get-push-status

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

## Image Management Best Practices

1. **Test images before deployment** - Always verify new images work correctly
2. **Use descriptive names** - Include version or date in image names
3. **Cache images for CI/CD** - Pre-cache on dedicated CI nodes
4. **Use OCI registries** - Modern approach for image distribution
5. **Document image configurations** - Track what's installed in each image
6. **Clean up unused images** - Regularly remove old/unused images
