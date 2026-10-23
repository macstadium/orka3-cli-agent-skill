# Image Management Troubleshooting

This guide covers common image-related issues with the Orka CLI.

## Contents
- [Problem: Async image operations stuck in progress](#problem-async-image-operations-stuck-in-progress)
- [Problem: Cannot delete image (in use)](#problem-cannot-delete-image-in-use)
- [Problem: Image cache not working (Apple Silicon)](#problem-image-cache-not-working-apple-silicon)
- [Problem: Deploys that used to be fast are slow again (cache eviction)](#problem-deploys-that-used-to-be-fast-are-slow-again-cache-eviction)
- [Fixed in Orka 3.6.4: caching jobs could stall indefinitely](#fixed-in-orka-364-caching-jobs-could-stall-indefinitely)
- [Problem: `imagecache remove` fails or isn't recognized despite an up-to-date CLI](#problem-imagecache-remove-fails-or-isnt-recognized-despite-an-up-to-date-cli)
- [Fixed in Orka 4.0: re-caching an image committed under the same name (v3.6.3+)](#fixed-in-orka-40-re-caching-an-image-committed-under-the-same-name-v363)
- [Known Issue: in-place macOS 15.x and 26.x upgrades inside a VM fail](#known-issue-in-place-macos-15x-and-26x-upgrades-inside-a-vm-fail)
- [Problem: "Invalid image format"](#problem-invalid-image-format)
- [Problem: Image push fails (Apple Silicon)](#problem-image-push-fails-apple-silicon)
- [Problem: `vm save` or `vm commit` fails with "image storage is not supported"](#problem-vm-save-or-vm-commit-fails-with-image-storage-is-not-supported)
- [Problem: Image is missing recent changes](#problem-image-is-missing-recent-changes)
- [Problem: Image copy operation slow or failing](#problem-image-copy-operation-slow-or-failing)
- [Image Operation Timing Reference](#image-operation-timing-reference)
- [Best Practices for Image Operations](#best-practices-for-image-operations)

## Problem: Async image operations stuck in progress

**Symptoms:**
- `orka image list` shows image but with errors
- Image save/commit/copy not completing
- "Operation in progress" for extended time

**Diagnosis:**
```bash
# Check image status with extended output
orka image list <IMAGE_NAME> --output wide

# Look for error messages or status indicators
```

**Solutions:**
```bash
# 1. Wait longer - large images take time
# 90GB+ images can take 10-30+ minutes

# 2. If stuck for hours, contact MacStadium support

# 3. For save/commit operations - ensure source VM is stable
orka vm list <SOURCE_VM> --output wide

# 4. Avoid concurrent operations on same image
# Wait for one operation to complete before starting another
```

## Problem: Cannot delete image (in use)

**Symptoms:**
- "Image is in use by VM"
- "Cannot delete image"

**Diagnosis:**
```bash
# Find VMs using the image
orka vm list --output wide              # Check Image column for <IMAGE_NAME>

# Find VM configs using the image
orka vmc list --output wide             # Check Image column for <IMAGE_NAME>
```

**Solutions:**
```bash
# Option 1: Delete VMs using the image
orka vm delete <VM_NAME>

# Option 2: Delete or update VM configs
orka vmc delete <CONFIG_NAME>
# OR update config to use different image

# Then try deletion again
orka image delete <IMAGE_NAME>

# For Intel: Ensure image is not in use by ANY VM
# For Apple Silicon: Image can be deleted if only used by one VM
```

## Problem: Image cache not working (Apple Silicon)

**Symptoms:**
- `imagecache add` succeeds but deployments still slow
- `imagecache info` stays in `Caching` indefinitely, or shows `Failed`

Cache states are `Ready`, `Caching`, `Failed`, `Removing`, and `RemoveFailed`.

**Diagnosis:**
```bash
# Check caching status
orka ic info <IMAGE>

# Verify nodes have the image cached
orka ic list --output wide
```

**Solutions:**
```bash
# 1. Wait for caching to complete (can take time for large images)
watch -n 30 'orka ic info <IMAGE>'

# 2. Verify registry credentials exist for OCI images, in the same namespace
#    you're caching into (caching private images needs them, not only push)
orka regcred list -n <NAMESPACE>

# For private registries (server URL must include the scheme, e.g. https://):
echo "$REGISTRY_TOKEN" | orka regcred add <REGISTRY_URL> --username <USER> --password-stdin -n <NAMESPACE>

# 3. Try caching on specific nodes
orka ic add <IMAGE> --nodes <NODE_NAME>

# 4. Check node storage capacity
orka node list --output wide

# 5. If cache fails persistently, contact MacStadium support
```

**`imagecache add` into a custom namespace does nothing (clusters before 3.5.1):** on clusters older than 3.5.1, `imagecache add` with `--namespace` set to a custom namespace silently did nothing. Upgrade the cluster to 3.5.1 or later, then run `imagecache add` again.

## Problem: Deploys that used to be fast are slow again (cache eviction)

**Symptoms:**
- Deploys of an image that were taking about 5 seconds now take about 4 minutes on some nodes
- `orka ic info <IMAGE>` no longer lists the image on those nodes

**Cause:** When a node is short on disk, deploying an uncached image there evicts the oldest cached images. Nothing reports the eviction; the next deploy of an evicted image is a cold pull.

**Orka 4.0 changes:** eviction frees only the shortfall instead of the full required size, rejects the operation up front when evicting can't help (on 3.6 it could empty the cache and still reject), skips images an in-progress deployment is using (on 3.6 that failed the deploy with `The file "disk.img" couldn't be opened`), and counts space macOS reports late. Evicted images no longer linger as `Ready` in `imagecache` output. On 4.0 you should see far fewer surprise cold pulls, but re-cache the same way if you do.

**Solutions:**
```bash
# Re-cache the image on the affected nodes
orka ic add <IMAGE> --nodes <NODE_NAME>

# Remove cached images you no longer deploy, to free disk (cluster 3.6.3+)
orka ic remove <OLD_IMAGE> --nodes <NODE_NAME>
```

Alert on node disk usage so you catch this before deploys slow down. See [monitoring.md](../workflows/monitoring.md).

## Fixed in Orka 3.6.4: caching jobs could stall indefinitely

Three caching-related bugs were fixed in Orka 3.6.4. If you're on an earlier version and hitting these symptoms, upgrading resolves them.

**Caching jobs that couldn't schedule, or got stuck mid-import, never failed or released resources.** If 4 or more caching jobs on the same node were stuck this way, no new VMs could deploy on that node.
- **Fixed:** Caching jobs now fail after a bounded deadline (3 hours by default). The deadline is tunable via the `cache_job_active_deadline_seconds` Ansible variable — this is a cluster-admin/Ansible-level setting, not an `orka` CLI flag. If a caching job fails after ~3 hours with no other explanation, this deadline is the cause, not a new bug.

**Cached images could be evicted unexpectedly** (a regression introduced in 3.6.3).
- **Fixed:** Orka now retains cached images as expected. No workaround was available pre-3.6.4 other than re-caching (`orka imagecache add <IMAGE> --all`).

**Namespaces created with `orka namespace create --enable-custom-pods` didn't grant the `orka-dev` role binding to users added to the namespace afterward,** leaving them without dev-level access.
- **Fixed:** Namespaces created on 3.6.4+ are unaffected. Existing custom-pods namespaces created before upgrading do **not** resolve automatically — contact [MacStadium support](mailto:support@macstadium.com) to have the missing role binding applied. See also `references/troubleshooting/auth-issues.md`.

## Problem: `imagecache remove` fails or isn't recognized despite an up-to-date CLI

**Symptoms:**
- `orka imagecache remove` errors out or behaves as if the command doesn't exist
- CLI is confirmed current (3.6.3+), but the command still doesn't work

**Cause:** `imagecache remove` is a server-side feature gate, not a CLI feature gate. It requires the Orka **cluster** to be running 3.6.3 or later (early access in 3.6.2), separate from the `orka` CLI version. Updating only the local CLI does not enable it, a common point of confusion: several customers have hit this assuming a CLI update alone was sufficient.

**Solution:** confirm the cluster's version, not just the CLI's:
```bash
orka version             # API Version, Operator Version
orka node list -o wide   # VERSION = Virtual Kubelet, RUNTIME = Orka Engine
```
Compare these against the [component version matrix](https://docs.macstadium.com/orka/orka-upgrades-and-release-notes/orka-component-versions). A patch release only bumps the components it changed, so some components report an earlier number than the release (a 3.6.4 cluster runs the API server at 3.6.3). Don't rely on `orka upgrade versions` for this: it reports `unknown` until the cluster completes its first Upgrade Service v2 run.

If the cluster is on an earlier version, it needs a cluster upgrade (see `upgrade-workflows.md`), not a CLI reinstall.

## Fixed in Orka 4.0: re-caching an image committed under the same name (v3.6.3+)

**Status:** Fixed in Orka 4.0, where `imagecache add` re-caches the updated image on those nodes. Still affects Orka 3.6.3 and later 3.6 releases; use the workaround below on 3.6.

**Symptoms:**
- You commit changes to an existing image while keeping the same name/tag
- A subsequent `orka imagecache add <IMAGE>` reports the image as already cached on some nodes and skips re-caching the updated content
- Affects both OCI and NFS images

**Impact:** VMs still deploy from the updated image — the first VM deployment from that image on an affected node re-caches it automatically. That first deployment is just slower, since the cache rebuilds at deploy time instead of ahead of time.

**Workaround:**
```bash
# Option 1: Force a re-cache explicitly
orka imagecache remove <IMAGE> --all      # or --nodes / --tags
orka imagecache add <IMAGE> --all

# Option 2: Deploy a VM from the image once to force the re-cache
orka vm deploy --image <IMAGE>
```

## Known Issue: in-place macOS 15.x and 26.x upgrades inside a VM fail

**Status:** Open. Workaround below. Source: [compatibility matrix](https://docs.macstadium.com/orka/orka-overview/compatibility-matrix).

**Symptoms** (Software Update or `startosinstall`):
- **macOS 26.x** (for example 26.6 to 26.6.2, or to 26.7): the VM never finishes its first boot after the upgrade restart. Staying below 26.7 doesn't avoid it.
- **macOS 15.x** (for example 15.7.6 to 15.8.1): the VM boots, but macOS can use only about 1.75 GiB of memory, however much the VM has.
- In-place upgrades to macOS 27 are not affected.

**Cause:** since macOS 27.0 shipped (September 14, 2026), an in-place update inside a VM installs the requested macOS version but downloads the newest firmware/recovery bundle Apple serves for virtual Macs (macOS 27's). This affects any Apple Virtualization.framework guest, not only Orka, and the host's macOS version doesn't matter (it fails on a 26.6.2 host too).

**Check a 15.x VM after an upgrade** (both values in bytes):
```bash
sysctl hw.memsize hw.memsize_usable
```
`hw.memsize_usable` should be close to `hw.memsize`. Around `1879031808` (about 1.75 GiB) on a larger VM means it got the newer firmware.

**An affected VM can't be repaired in place.** Recreate it, then apply the workaround to the new VM before upgrading. Same for a 26.x VM that never finished its first boot.

**Workaround** (inside the guest, before starting the upgrade). Run the code blocks exactly as written, without leading indentation, so the heredoc terminator works.

**Step 1. Download the full installer** while Apple's servers are reachable. Replace `<MACOS_VERSION>` with the target, for example `26.7` or `15.8.1`:
```bash
softwareupdate --fetch-full-installer --full-installer-version <MACOS_VERSION>
```

**Step 2. Block the firmware download:**
```bash
sudo tee -a /etc/hosts >/dev/null <<'EOF'
127.0.0.1 gdmf.apple.com
127.0.0.1 mesu.apple.com
127.0.0.1 updates.cdn-apple.com
127.0.0.1 updates-http.cdn-apple.com
127.0.0.1 swcdn.apple.com
127.0.0.1 swdist.apple.com
EOF
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

**Step 3. Run the installer** for the target version. `<ADMIN_USER>` is an administrator account on the VM; `--stdinpass` reads its password from standard input.
```bash
# macOS 26.x
"/Applications/Install macOS Tahoe.app/Contents/Resources/startosinstall" --agreetolicense --nointeraction --forcequitapps --user <ADMIN_USER> --stdinpass
# macOS 15.x
"/Applications/Install macOS Sequoia.app/Contents/Resources/startosinstall" --agreetolicense --nointeraction --forcequitapps --user <ADMIN_USER> --stdinpass
```
Check `/var/log/install.log` for `No SFR update was found on the server, using bundled SFR` to confirm the fallback worked. The VM reboots into the new version in about 15 to 20 minutes.

**Step 4. Verify and unblock.** On 15.x, rerun `sysctl hw.memsize hw.memsize_usable` and confirm the values are close. Then remove the six lines added to `/etc/hosts`, or Software Update and other Apple downloads in the guest stay blocked.

Contact MacStadium support if the workaround doesn't resolve it.

## Problem: "Invalid image format"

**Cause:** Incorrect OCI image path

**Solution:**
```bash
# Use full OCI path with registry
orka vm deploy --image ghcr.io/org/repo/image:tag

# Verify registry credentials exist
orka regcred list
```

## Problem: Image push fails (Apple Silicon)

**Symptoms:**
- `orka vm push` command fails
- Push job stuck or errored

**Diagnosis:**
```bash
# Check push status (push jobs live in the VM's namespace)
orka vm get-push-status -n <VM_NAMESPACE>

# Check a specific job
orka vm get-push-status <JOB_NAME> -n <VM_NAMESPACE> --output wide
```

A finished push shows `Ready`. A failed push shows `Failed` with a message. Otherwise the status is `Pending` or `Running`. Job records are cleaned up one hour after the push finishes; if the job is gone, check the registry for the tag.

**`vm push` returns `Unauthorized` while other commands work:** push goes through the Orka API server, so it needs an Orka token. A kubeconfig with certificate-only auth (common on AWS and on-prem clusters) isn't enough. For CI, set a service-account token (minted by an admin with `orka sa token <SA_NAME>` and stored as a CI secret):

```bash
orka user set-token "$ORKA_TOKEN"
```

**Solutions:**
```bash
# 1. Verify registry credentials
orka regcred list

# 2. Ensure credentials are in the same namespace as the VM
echo "$REGISTRY_TOKEN" | orka regcred add <REGISTRY_URL> --username <USER> --password-stdin --namespace <VM_NAMESPACE>

# 3. Verify image format is correct
# Format: server.com/repository/image:tag
orka vm push <VM_NAME> ghcr.io/org/repo/image:tag

# 4. Check VM is running and stable
orka vm list <VM_NAME> --output wide

# 5. Try with different tag
orka vm push <VM_NAME> ghcr.io/org/repo/image:new-tag
```

## Problem: `vm save` or `vm commit` fails with "image storage is not supported"

**Symptoms:**
- `image storage is not supported. You cannot run save or commit image commands`

**Cause:** `vm save` and `vm commit` need NFS image storage on the cluster. Clusters that use only Harbor or another OCI registry (Harbor is the default for new deployments since 3.5) don't have it.

**Solution:** Use `vm push` to an OCI registry instead:
```bash
orka vm push <VM_NAME> <REGISTRY>/<REPOSITORY>/<IMAGE>:<TAG> -n <VM_NAMESPACE>
```

## Problem: Image is missing recent changes

**Symptoms:**
- A VM deployed from a newly pushed, saved, or committed image is missing files or settings that were in the source VM

**Cause:** The host copies the running VM's disk without flushing the guest. Writes still in the guest's page cache can be missing from the image.

**Solution:** Run `sync` inside the guest right before `vm push`, `vm save`, or `vm commit`:
```bash
ssh -p <SSH_PORT> <USER>@<NODE_IP> sync
orka vm push <VM_NAME> <REGISTRY>/<REPOSITORY>/<IMAGE>:<TAG> -n <VM_NAMESPACE>
```

See [vm-commands.md](../commands/vm-commands.md).

## Problem: Image copy operation slow or failing

**Symptoms:**
- `orka image copy` taking very long
- Copy operation stuck

**Solutions:**
```bash
# 1. Check image size (large images take longer)
orka image list <SOURCE_IMAGE> --output wide

# 2. Monitor copy progress
orka image list <DESTINATION_IMAGE> --output wide

# 3. Avoid starting multiple copy operations simultaneously

# 4. For very large images, expect 30+ minutes
```

## Image Operation Timing Reference

| Operation | Typical Duration | Factors |
|-----------|-----------------|---------|
| image list | Instant | - |
| image copy | 5-30+ minutes | Image size |
| image delete | Instant | - |
| vm save | 5-30+ minutes | Image size, VM disk usage |
| vm commit | 5-30+ minutes | Image size, VM disk usage |
| vm push | 10-60+ minutes | Image size, network speed |
| imagecache add | 5-30+ minutes | Image size, number of nodes |

## Best Practices for Image Operations

1. **Check status of async operations** - Don't assume completion
2. **Avoid concurrent operations** - One operation per image at a time
3. **Use descriptive names** - Include version or date in names
4. **Test images before deployment** - Verify with single VM first
5. **Clean up unused images** - Regularly remove old images
6. **Cache images before mass deployment** - Improves consistency
