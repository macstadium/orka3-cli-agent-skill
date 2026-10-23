# VM Configuration Commands Reference

This reference provides detailed syntax and examples for VM configuration template commands in Orka3 CLI.

**Scope:** VM configs always live in `orka-default` and are visible to every user and service account with access to it. `vm-config` has no `--namespace` flag; pass `-n` on `vm deploy` instead.

**No update command:** there is no `vm-config update`. To change a config, delete and recreate it, or create it under a new name. Deleting a config that CI references breaks queued jobs, so roll changes blue/green: create the new name, repoint CI, then delete the old one. VMs don't record which config they were deployed from.

**Sizing (Apple silicon):** nodes run at most 2 VMs each, so size configs at about half a node's allocatable CPU and memory. Larger configs strand the second slot.

## orka3 vm-config create (alias: vmc)

Create a VM configuration template.

**Syntax:**
```bash
orka3 vm-config create <NAME> [flags]
```

**Options:**
- `-i, --image string` - (Required) Base image (local or OCI)
- `-c, --cpu int` - Number of CPU cores (default: 3)
- `-m, --memory float` - RAM in gigabytes. Max 32GB on 32GB nodes, 60GB on 64GB and 128GB nodes. If unset, defaults to a value based on the node with the least memory
- `--node string` - Specific node for deployment
- `--scheduler string` - Scheduler: 'default' or 'most-allocated'
- `--tag string` - Node affinity tag
- `--tag-required` - Require tagged nodes
- `--disable-vnc` - Disable VNC. Locks you out unless the image has SSH or Screen Sharing enabled
- `--display-width int` - Virtual display width, 320-3840 (3.4+)
- `--display-height int` - Virtual display height, 480-2160 (3.4+)
- `--display-dpi int` - Virtual display DPI, 60-320 (3.4+)

**Intel-only Options:**
- `--iso string` - ISO name to attach
- `--gpu` - Enable GPU passthrough
- `--system-serial string` - Custom serial number
- `--disable-net-boost` - Disable network boost
- `--legacy-io` - Legacy IO, required for High Sierra and Mojave VMs

**Config Name Requirements:**
- Max 50 characters
- Lowercase alphanumeric or dashes
- Starts with alphabetic, ends with alphanumeric
- Unique to cluster

**Examples:**
```bash
orka3 vmc create medium-ventura-vm --image 90gbventurassh.img --cpu 6
orka3 vmc create small-arm-vm -i ghcr.io/org/orka-images/orka-arm:latest --cpu 4
orka3 vmc create medium-vm --image sonoma.orkasi --memory 5
orka3 vmc create build-vm --image sonoma.orkasi --tag jenkins-builds --tag-required
orka3 vmc create wide-display-vm --image sonoma.orkasi --display-width 2920 --display-height 1380 --display-dpi 100
```

## orka3 vm-config list (alias: vmc)

Show information about VM configurations.

**Syntax:**
```bash
orka3 vm-config list [<NAME>] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json

**Examples:**
```bash
orka3 vmc list
orka3 vmc list --output wide
orka3 vmc list small-ventura-vm
orka3 vmc list -o json | jq -r '.[] | select(.image | startswith("ghcr.io/")) | .name'
```

## orka3 vm-config delete (alias: vmc)

Delete VM configuration templates.

**Syntax:**
```bash
orka3 vm-config delete <NAME> [<NAME2> ...] [flags]
```
