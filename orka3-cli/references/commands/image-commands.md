# Image Commands Reference

This reference provides detailed syntax and examples for image-related Orka3 CLI commands, including image cache operations.

## Contents
- [Local Image Commands](#local-image-commands)
- [Image Cache Commands (Apple Silicon only)](#image-cache-commands-apple-silicon-only)

## Local Image Commands

**Deprecated in Orka 4.0.** NFS-hosted images are deprecated and will be removed in a future release; no removal release has been set. On 4.0, every `orka3 image` and `orka3 remote-image` command (`list`, `pull`) prints ``Warning: NFS-hosted images are deprecated and will be removed in a future Orka release. Use OCI images (`orka vm push`) instead.`` to stderr and shows `(Deprecated)` in its help. Standard output is unchanged. Use OCI images instead, created with `orka3 vm push`, and `orka3 imagecache` to load them onto nodes. `orka3 vm save` and `orka3 vm commit` are deprecated alongside them. The `orka3 imagecache` commands are not affected.

`orka3 image generate`, the `orka3 iso` commands and the `orka3 remote-iso` commands were Intel-only and are removed in Orka 4.0.

### orka3 image list

List locally stored images in your Orka cluster.

**Syntax:**
```bash
orka3 image list [<NAME>] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json

**Examples:**
```bash
orka3 image list
orka3 image list sonoma-90gb-orka3-arm
orka3 image list --output json
```

**Notes:**
- `-o json` includes `state` (`Ready`, `Updating`, `Failed`) and `error`
- Image names: up to 63 characters, lowercase alphanumerics, `-` or `.`

### orka3 image copy

Copy an image and set a new name for the copy.

**Syntax:**
```bash
orka3 image copy <SOURCE> <DESTINATION> [--description '<DESC>'] [flags]
```

**Options:**
- `-d, --description string` - Custom description for the copy

**Notes:**
- Async operation - check status with `orka3 image list <NAME>`
- Copies description from source by default

### orka3 image generate (Intel only, removed in Orka 4.0)

Generate a new empty image with the specified size.

**Syntax:**
```bash
orka3 image generate <NAME> <SIZE> [--description '<DESC>'] [flags]
```

**Options:**
- `-d, --description string` - Custom description

**Examples:**
```bash
orka3 image generate 120gbemptyimage 120G
```

**Notes:**
- Intel-only (amd64 architecture), Orka 3.6 and earlier
- Async operation
- Used for fresh macOS installs from ISO
- Removed in Orka 4.0; the API route returns `404`

### orka3 image set-description

Set a custom description for an image.

**Syntax:**
```bash
orka3 image set-description <NAME> <DESCRIPTION> [flags]
```

**CAUTION:** Overrides existing description (cannot be undone).

### orka3 image delete

Delete the specified locally stored images.

**Syntax:**
```bash
orka3 image delete <NAME> [<NAME2> ...] [flags]
```

**CAUTION:** Cannot be undone. Affects VMs/configs using this image.

## Image Cache Commands (Apple Silicon only)

### orka3 imagecache add (alias: ic)

Cache an image on specified node(s).

**Syntax:**
```bash
orka3 imagecache add <IMAGE> {--nodes|--tags|--all} [--namespace <NS>] [flags]
```

**Options:**
- `--nodes string` - Specific nodes (comma-separated)
- `--tags string` - Node tags to filter by (comma-separated)
- `--all` - Cache on all nodes in namespace
- `-n, --namespace string` - Target namespace

**Examples:**
```bash
orka3 ic add ghcr.io/macstadium/orka-images/sequoia:latest --nodes mini-arm-10
orka3 ic add sonoma-90gb-orka3-arm --nodes mini-arm-10,mini-arm-11
orka3 ic add sequoia:latest --all
orka3 ic add sonoma:latest --tags jenkins-builds
```

**Notes:**
- Async operation
- Image must be pulled first (or be an OCI image)
- `--nodes`, `--tags`, and `--all` are mutually exclusive
- An OCI reference without a tag means `:latest`
- Before 3.5.1, `imagecache add` into a custom namespace silently did nothing
- Each cache job uses about 0.5 CPU and heavy disk I/O, which slows running VMs and the scheduler. Caching several images at once is faster than one after another

**Cache behavior:**
- First deploy of an uncached image on a node takes about 4 minutes; a cached deploy takes about 5 seconds
- When node disk is short, deploying an uncached image evicts the oldest cached images
- Orka 4.0 eviction fixes: eviction frees only the shortfall (3.6 could evict several images to make room for one), rejects up front when evicting can't help, skips images an in-progress deployment is using, and the node's image list refreshes after evictions, so evicted images no longer show `Ready`
- Re-caching an image committed under the same name and tag: on 3.6.3 and later 3.6 releases, `imagecache add` could report it as already cached on nodes where a deploy had cached it and skip it. Fixed in Orka 4.0 (see `references/troubleshooting/image-issues.md`)

### orka3 imagecache remove (alias: ic), v3.6.3+

Selectively remove a cached image from Apple Silicon nodes without support intervention.

**Syntax:**
```bash
orka3 imagecache remove <IMAGE> {--nodes|--tags|--all} [--namespace <NS>] [flags]
```

**Options:**
- `--nodes string` - Specific nodes (comma-separated)
- `--tags string` - Node tags to filter by (comma-separated)
- `--all` - Remove from all nodes in namespace
- `-n, --namespace string` - Target namespace

**Examples:**
```bash
orka3 ic remove sonoma-90gb-orka3-arm --all
orka3 ic remove sequoia:latest --nodes mini-arm-10,mini-arm-11
orka3 ic remove sonoma:latest --tags jenkins-builds
```

**Removal states:**

| State | Meaning |
|-------|---------|
| `Removing` | Remove job is running on the target node |
| `RemoveFailed` | Remove job failed; image stays cached. Retry with the same command. |

**Notes:**
- Async: check status with `orka3 imagecache info <IMAGE>`
- `--nodes`, `--tags`, and `--all` are mutually exclusive; exactly one is required
- `--tags` matches nodes that have ALL listed tags
- With `--all` or `--tags`, nodes that don't have the image cached are skipped. On Orka 4.0 they report a per-node status of `202`; on 3.6 they returned `404`. With `--nodes`, a listed node that holds no cache record for the image still reports `404` for that node
- Orka 4.0 also cleans up orphaned `Failed` and `RemoveFailed` cache entries, and a remove whose tag an earlier timed-out call already deleted reports not found and clears the record instead of staying `RemoveFailed`
- If a targeted node no longer exists, the cache entry is cleaned up immediately
- Images cached implicitly by a deploy can be removed the same way
- Never remove an image while VMs are deploying from it on that node. Removal between pull and clone fails the deploy with a generic error
- API: `POST /api/v1/namespaces/{namespace}/cache/images/{image}/remove` (207 Multi-Status, with a status per node)

### orka3 imagecache info (alias: ic)

Display the caching status of an image across nodes.

**Syntax:**
```bash
orka3 imagecache info <IMAGE> [--namespace <NS>] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json
- `-n, --namespace string` - Target namespace

**Status Values:**
- `Ready` - Available for deployment
- `Caching` - Cache job still running
- `Failed` - Cache job failed
- `Removing` - Remove job running (v3.6.3+)
- `RemoveFailed` - Remove job failed; image stays cached (v3.6.3+)

### orka3 imagecache list (alias: ic)

List cached images across nodes.

**Syntax:**
```bash
orka3 imagecache list [<IMAGE>] [--namespace <NS>] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json
- `-n, --namespace string` - Target namespace

**Examples:**
```bash
orka3 ic list
orka3 ic list sonoma-90gb-orka3-arm
orka3 ic list ghcr.io/macstadium/orka-images/sequoia
orka3 ic list ghcr.io/macstadium/orka-images/sonoma:14.0
```
