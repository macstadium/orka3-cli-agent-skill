# VM Configuration Commands Reference

This reference provides detailed syntax and examples for VM configuration template commands in Orka3 CLI.

## orka3 vm-config create (alias: vmc)

Create a VM configuration template.

**Syntax:**
```bash
orka3 vm-config create <NAME> [flags]
```

**Options:**
- `-i, --image string` - (Required) Base image (local or OCI)
- `-c, --cpu int` - Number of CPU cores (default: 3)
- `-m, --memory float` - RAM in gigabytes
- `--scheduler string` - Scheduler: 'default' or 'most-allocated'
- `--tag string` - Node affinity tag
- `--tag-required` - Require tagged nodes
- `--disable-vnc` - Disable VNC

**Intel-only Options:**
- `--iso string` - ISO name to attach
- `--gpu` - Enable GPU passthrough
- `--system-serial string` - Custom serial number
- `--disable-net-boost` - Disable network boost

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
orka3 vmc list --output wide | grep 'user@company.com'
```

## orka3 vm-config delete (alias: vmc)

Delete VM configuration templates.

**Syntax:**
```bash
orka3 vm-config delete <NAME> [<NAME2> ...] [flags]
```
