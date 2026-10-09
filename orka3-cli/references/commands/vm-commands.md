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
- [orka3 vm start (Intel only, removed in Orka 4.0)](#orka3-vm-start-intel-only-removed-in-orka-40)
- [orka3 vm stop (Intel only, removed in Orka 4.0)](#orka3-vm-stop-intel-only-removed-in-orka-40)
- [orka3 vm suspend (Intel only, removed in Orka 4.0)](#orka3-vm-suspend-intel-only-removed-in-orka-40)
- [orka3 vm resume (Intel only, removed in Orka 4.0)](#orka3-vm-resume-intel-only-removed-in-orka-40)
- [orka3 vm revert (Intel only, removed in Orka 4.0)](#orka3-vm-revert-intel-only-removed-in-orka-40)

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
- `-m, --memory float` - RAM in gigabytes
- `--node string` - Specific node for deployment
- `--tag string` - Node affinity tag
- `--tag-required` - Require tagged nodes
- `--generate-name` - Generate unique name with suffix
- `--scheduler string` - Scheduler: 'default' or 'most-allocated'
- `--metadata stringToString` - Custom metadata (key1=value1,key2=value2)
- `-p, --ports strings` - Port mapping (NODE_PORT:VM_PORT[/tcp|/udp]); protocol defaults to TCP if omitted
- `--timeout int` - Deployment timeout in minutes (default: 10)
- `-n, --namespace string` - Target namespace
- `-o, --output string` - Output format: json|wide
- `--userdata string` - (Orka 4.0+) Bootstrap script to run inside the VM on first boot. Accepts a path to a script file, which the CLI encodes for you, or a base64-encoded string.

**Intel-only Options (removed in Orka 4.0):**
- `--iso string` - ISO name to attach
- `--gpu` - Enable GPU passthrough (requires --disable-vnc)
- `--system-serial string` - Custom serial number
- `--disable-net-boost` - Disable network performance boost
- `--disable-vnc` - Disable VNC
- `--legacy-io` - Legacy IO

Orka 4.0 is Apple Silicon only and removed every flag above. They return an unknown-flag error on 4.0. Orka 3.6 remains the last Intel-supporting release, with Intel support running through March 2028.

**User Data (`--userdata`, Orka 4.0+):**
- Requires Orka 4.0 or later and orka-vm-tools 3.7.0 or later in the image. All current MacStadium `orka-images` releases qualify.
- Apple Silicon only. Maximum 64 KiB for the base64-encoded script; for anything larger, use a small script that downloads the rest.
- Runs as root, in the background, on first boot. The VM becomes available without waiting for it.
- Runs once per VM. Orka records completion after the script finishes, succeed or fail, so a failed run does not retry on the next boot. If the VM reboots or stops mid-run, the run did not complete and the script runs again, so write scripts that are safe to re-run.
- No timeout by default. Set `ORKA_USERDATA_TIMEOUT` inside the image to add one.
- Output goes to `/var/log/orka/userdata.log` inside the VM. Keep credentials out of it, and note that anything printed there travels with an image saved or pushed from that VM.
- Changing User Data does not re-run the script on VMs that already ran it. Only newly deployed VMs pick up a new value.
- Check progress with `orka3 vm list -o wide` and the `USERDATA-PHASE` column (`userdataPhase` in API responses): `pending`, `success`, `failed`, `skipped`, `timeout`. An empty value means the VM has no User Data or isn't running. Wait for any of the four terminal phases if automation needs a ready signal.
- The phase is reported by the guest through VM Tools, so treat it as a progress signal rather than proof the work was done, and don't use it as a security control. Images with VM Tools older than 3.7.0 never report a result, which looks identical to a script still running.

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

**Note:** Stopped/suspended VMs appear as 'Running' when listed.

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
- **Apple Silicon**: Automatic - no additional steps needed
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

## orka3 vm start (Intel only, removed in Orka 4.0)

Power ON a stopped VM.

**Syntax:**
```bash
orka3 vm start <VM_NAME> [--namespace <NS>] [flags]
```

## orka3 vm stop (Intel only, removed in Orka 4.0)

Power OFF a running VM.

**Syntax:**
```bash
orka3 vm stop <VM_NAME> [--namespace <NS>] [flags]
```

## orka3 vm suspend (Intel only, removed in Orka 4.0)

Suspend a running VM (freezes processes).

**Syntax:**
```bash
orka3 vm suspend <VM_NAME> [--namespace <NS>] [flags]
```

## orka3 vm resume (Intel only, removed in Orka 4.0)

Resume a suspended VM.

**Syntax:**
```bash
orka3 vm resume <VM_NAME> [--namespace <NS>] [flags]
```

## orka3 vm revert (Intel only, removed in Orka 4.0)

Revert a VM to the latest state of its image.

**Syntax:**
```bash
orka3 vm revert <VM_NAME> [--namespace <NS>] [flags]
```

**CAUTION:** Cannot be undone. All unsaved/uncommitted data will be lost.
