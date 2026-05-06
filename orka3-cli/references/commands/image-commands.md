# Image Commands Reference

This reference provides detailed syntax and examples for image-related Orka3 CLI commands, including image cache operations.

## Contents
- [Local Image Commands](#local-image-commands)
- [Image Cache Commands (Apple Silicon only)](#image-cache-commands-apple-silicon-only)

## Local Image Commands

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
orka3 image list --arch amd64
```

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

### orka3 image generate (Intel only)

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
- Intel-only (amd64 architecture)
- Async operation
- Used for fresh macOS installs from ISO

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
- `ready` - Available for deployment
- `caching` - Operation still active

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
