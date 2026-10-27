# VM Commands Reference

This reference provides detailed syntax and examples for VM-related Orka3 CLI commands.

## Contents
- [orka3 vm deploy](#orka3-vm-deploy)
- [orka3 vm list](#orka3-vm-list)
- [orka3 vm delete](#orka3-vm-delete)
- [orka3 vm save](#orka3-vm-save)
- [orka3 vm commit](#orka3-vm-commit)
- [orka3 vm push (Apple Silicon only)](#orka3-vm-push-apple-silicon-only)
- [orka3 vm get-push-status (Apple Silicon only)](#orka3-vm-get-push-status-apple-silicon-only)
- [orka3 vm resize](#orka3-vm-resize)
- [orka3 vm start (Intel only)](#orka3-vm-start-intel-only)
- [orka3 vm stop (Intel only)](#orka3-vm-stop-intel-only)
- [orka3 vm suspend (Intel only)](#orka3-vm-suspend-intel-only)
- [orka3 vm resume (Intel only)](#orka3-vm-resume-intel-only)
- [orka3 vm revert (Intel only)](#orka3-vm-revert-intel-only)

## orka3 vm deploy

Deploy a VM with specified configuration.

**Syntax:**
```bash
orka3 vm deploy [<NAME>] --image <IMAGE> [flags]
orka3 vm deploy [<NAME>] --config <TEMPLATE> [flags]
```

**Options:**
- `-i, --image string` - (Required if no --config) Base image (local or OCI)
- `--config string` - VM configuration template
- `-c, --cpu int` - Number of CPU cores (default: 3)
- `-m, --memory float` - RAM in gigabytes. Max 32GB on 32GB nodes, 60GB on 64GB and 128GB nodes. If unset, defaults to a value based on the node with the least memory
- `--node string` - Specific node for deployment
- `--tag string` - Node affinity tag
- `--tag-required` - Require tagged nodes
- `--generate-name` - Generate unique name with suffix
- `--scheduler string` - Scheduler: 'default' or 'most-allocated'
- `--metadata stringToString` - Custom metadata (key1=value1,key2=value2). Keys and values can't contain `,` or `=`; six keys are reserved: `orka_vm_id`, `orka_vm_name`, `orka_base_image`, `orka_cpu`, `orka_memory`, `orka_node_name` (other `orka_*` keys are accepted). See [VM metadata](#vm-metadata)
- `-p, --ports strings` - Port mapping (NODE_PORT:VM_PORT[/tcp|/udp]); protocol defaults to TCP if omitted. Maps the node port to the VM port but does not open the port inside macOS
- `--display-width int` - Virtual display width, 320-3840 (3.4+)
- `--display-height int` - Virtual display height, 480-2160 (3.4+)
- `--display-dpi int` - Virtual display DPI, 60-320 (3.4+)
- `--disable-vnc` - Disable VNC. Locks you out unless the image has SSH or Screen Sharing enabled
- `--timeout int` - Deployment timeout in minutes (default: 10)
- `-n, --namespace string` - Target namespace
- `-o, --output string` - Output format: json|wide

**Intel-only Options:**
- `--iso string` - ISO name to attach
- `--gpu` - Enable GPU passthrough (requires --disable-vnc)
- `--system-serial string` - Custom serial number
- `--disable-net-boost` - Disable network performance boost
- `--legacy-io` - Legacy IO, required for High Sierra and Mojave VMs

**VM Name Requirements:**
- Max 63 characters (including generated suffix)
- Lowercase alphanumeric or dashes
- Starts with alphabetic, ends with alphanumeric
- Unique to namespace

**Examples:**
```bash
# Basic deployments
orka3 vm deploy --image ghcr.io/macstadium/orka-images/sonoma:latest
orka3 vm deploy my-vm --image sonoma-90gb-orka3-arm --cpu 4
orka3 vm deploy --image sonoma:latest --memory 10
orka3 vm deploy --image sonoma:latest --generate-name

# Targeted deployments
orka3 vm deploy --image sonoma:latest --node mini-arm-14
orka3 vm deploy --image sonoma:latest --tag jenkins-builds --tag-required
orka3 vm deploy --image sonoma:latest --namespace orka-test

# Advanced deployments
orka3 vm deploy --image sonoma:latest --metadata 'foo=1,baz=https://example.com'
orka3 vm deploy --image sonoma:latest --ports 9000:4000,9001:4001
orka3 vm deploy --image sonoma:latest --ports 9000:4000/udp,9001:4001/tcp

# Intel-only deployments
orka3 vm deploy --image emptydisk.img --iso ventura.iso
orka3 vm deploy --image ventura.img --gpu=true --disable-vnc
orka3 vm deploy --image ventura.img --system-serial A00BC123D4

# Template deployments
orka3 vm deploy --config small-ventura-config
orka3 vm deploy my-vm --config small-ventura-config
orka3 vm deploy --config small-ventura-config --cpu 6 --memory 16
```

**Notes:**
- Deploy returns when the VM reaches `Running`, not when macOS has finished booting. Wait for SSH (poll the SSH port) before using the VM.

### VM metadata

Custom metadata is set at deploy time only and is readable from inside the VM through the metadata server:

```bash
curl http://169.254.169.254/metadata/            # All metadata, JSON
curl http://169.254.169.254/metadata/<KEY>       # One key
curl http://169.254.169.254/metadata/my%20key    # URL-encode keys with spaces
```

- Built-in keys: `orka_vm_id`, `orka_vm_name`, `orka_node_name`, `orka_base_image`, `orka_cpu`, `orka_memory`
- Unauthenticated: never put secrets in metadata
- The server can time out right after boot. Gate startup scripts on readiness:
  ```bash
  until curl -fs --max-time 2 http://169.254.169.254/metadata/ >/dev/null; do sleep 1; done
  ```
- Apple silicon: requires Orka VM Tools in the image (check with `sudo launchctl list com.orka.vm.tools`)
- Custom metadata does not appear in `vm list` output

## orka3 vm list

Show information about VMs.

**Syntax:**
```bash
orka3 vm list [<NAME>] [--namespace <NS>] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json
- `-n, --namespace string` - Target namespace

**Examples:**
```bash
orka3 vm list
orka3 vm list --output wide
orka3 vm list my-vm
orka3 vm list --namespace orka-test
orka3 vm list mini-arm-14 -o wide
```

**Notes:**
- Stopped/suspended VMs appear as 'Running' when listed.
- `-o json` includes `owner`, the identity that deployed the VM (for example `system:serviceaccount:<NS>:<SA>` or a user). With one service account per integration, use it to attribute leaked VMs:
  ```bash
  orka3 vm list -n <NS> -o json | jq -r '.[] | select(.owner == "system:serviceaccount:<NS>:<SA>") | .name'
  ```

## orka3 vm delete

Delete specified VMs.

**Syntax:**
```bash
orka3 vm delete <NAME> [<NAME2> ...] [--namespace <NS>] [flags]
```

**CAUTION:** Cannot be undone. Unsaved/uncommitted data will be lost.

## orka3 vm save

Save a new image from a running VM.

**Syntax:**
```bash
orka3 vm save <VM_NAME> <NEW_IMAGE_NAME> [--description '<DESC>'] [--namespace <NS>] [flags]
```

**Options:**
- `-d, --description string` - Custom description for new image
- `-n, --namespace string` - Target namespace

**Notes:**
- Preserves original image
- Async operation (check with `orka3 image list <NAME>`)
- Restarts the VM
- Requires NFS image storage on the cluster. On Harbor/OCI-only clusters (the default for new deployments since 3.5) it fails with "image storage is not supported. You cannot run save or commit image commands"; use `vm push`
- Run `sync` inside the guest first (see [Flush the guest before capturing](#flush-the-guest-before-capturing))

## orka3 vm commit

Update an existing image from a running VM.

**Syntax:**
```bash
orka3 vm commit <VM_NAME> [--description '<DESC>'] [--namespace <NS>] [flags]
```

**Options:**
- `-d, --description string` - New description for original image
- `-n, --namespace string` - Target namespace

**Notes:**
- Modifies original image
- Intel: image must not be in use by other VMs
- Async operation
- Restarts the VM
- Requires NFS image storage on the cluster (same error as `vm save` on Harbor/OCI-only clusters); use `vm push` there
- Run `sync` inside the guest first (see [Flush the guest before capturing](#flush-the-guest-before-capturing))

## orka3 vm push (Apple Silicon only)

Push VM state to an OCI-compatible registry.

**Syntax:**
```bash
orka3 vm push <VM_NAME> <IMAGE[:TAG]> [--namespace <NS>] [flags]
```

**Notes:**
- Image format: `server.com/repository/image:tag`
- Tag defaults to `latest` if not provided
- Registry credentials required in same namespace
- Async operation (check with `orka3 vm get-push-status`)
- Does not restart the VM (`save` and `commit` do)
- One push per VM at a time. A second push while one is running fails with `vm push operation already in progress for "<VM>"`
- Run `sync` inside the guest first (see [Flush the guest before capturing](#flush-the-guest-before-capturing))

**Examples:**
```bash
orka3 vm push vm-5rjn4 ghcr.io/myorg/orka-images/base:latest
orka3 vm push vm-fxwj5 ghcr.io/myorg/orka-images/base:1.0 --namespace orka-test
```

## orka3 vm get-push-status (Apple Silicon only)

View status of image push to OCI registry.

**Syntax:**
```bash
orka3 vm get-push-status [<JOB_NAME>] [--namespace <NS>] [--output <FORMAT>] [flags]
```

**Notes:**
- Job name from push operation
- Status viewable for 1 hour after completion
- Lists all pushes if no job name provided
- Push jobs live in the VM's namespace: pass `-n <NS>` for VMs outside `orka-default`
- Status values: `Ready` when finished, `Failed` (with a message) on failure, otherwise the job pod phase (`Pending`/`Running`). Poll until `Ready` or `Failed`
- JSON keys: `name`, `status`, `message`

```bash
orka3 vm get-push-status <JOB_NAME> -n <NS> -o json | jq -r '.[0].status'
```

### Flush the guest before capturing

The host copies the running VM's disk without flushing the guest, so writes still in the guest page cache can be missing from the image. Run `sync` inside the guest right before `vm push`, `vm save`, or `vm commit`:

```bash
ssh <VM_USER>@<VM_IP> -p <SSH_PORT> sync
orka3 vm push <VM> <IMAGE[:TAG]> -n <NS>
```

The Packer plugin does this automatically.

## orka3 vm resize

Resize the disk of a running VM (increase only).

**Syntax:**
```bash
orka3 vm resize <VM_NAME> <NEW_SIZE_GB> [--user <SSH_USER>] [--password <SSH_PASS>] [--namespace <NS>] [flags]
```

**Options:**
- `-u, --user string` - (Intel-only) SSH user for automatic repartition
- `-p, --password string` - (Intel-only) SSH password for automatic repartition
- `-n, --namespace string` - Target namespace

**Architecture Behavior:**
- **Apple Silicon**: Requires Orka VM Tools 3.6.0 or later installed in the guest (3.6 and 4.0 VM Tools both work on 3.6 and 4.0 clusters). With VM Tools present, Orka resizes and repartitions automatically
- **Intel**: Provide SSH credentials for automatic repartition, or manually complete

**Notes:**
- Size always in GB
- Restarts the VM
- Can only increase size

**Examples:**
```bash
orka3 vm resize my-vm 100
orka3 vm resize intel-vm 100 --user admin --password admin
```

## orka3 vm start (Intel only)

Power ON a stopped VM.

**Syntax:**
```bash
orka3 vm start <VM_NAME> [--namespace <NS>] [flags]
```

## orka3 vm stop (Intel only)

Power OFF a running VM.

**Syntax:**
```bash
orka3 vm stop <VM_NAME> [--namespace <NS>] [flags]
```

## orka3 vm suspend (Intel only)

Suspend a running VM (freezes processes).

**Syntax:**
```bash
orka3 vm suspend <VM_NAME> [--namespace <NS>] [flags]
```

## orka3 vm resume (Intel only)

Resume a suspended VM.

**Syntax:**
```bash
orka3 vm resume <VM_NAME> [--namespace <NS>] [flags]
```

## orka3 vm revert (Intel only)

Revert a VM to the latest state of its image.

**Syntax:**
```bash
orka3 vm revert <VM_NAME> [--namespace <NS>] [flags]
```

**CAUTION:** Cannot be undone. All unsaved/uncommitted data will be lost.
