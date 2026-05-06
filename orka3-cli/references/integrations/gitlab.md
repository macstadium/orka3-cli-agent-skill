# GitLab Integration

## Contents
- [Custom executor (ephemeral)](#custom-executor-ephemeral)
- [Shell executor (permanent)](#shell-executor-permanent)
- [Auth](#auth)
- [Environment variables](#environment-variables)
- [Connectivity](#connectivity)
- [IP mapping](#ip-mapping)
- [Gotchas](#gotchas)

## Custom executor (ephemeral)

The Custom executor runs each CI/CD job inside a fresh Orka VM, then deletes it after. The runner is a Docker container running MacStadium-provided scripts that handle VM lifecycle.

**Setup summary:**
1. Create a base image with SSH enabled (private key, no passphrase)
2. Create a VM config from that image: `orka3 vmc create <name> --image <image>`
3. Build and run the Docker container from the [Dockerfile](https://github.com/macstadium/orka-integrations/blob/master/GitLab/Dockerfile)
4. Register the runner inside the container using `TOKEN=${REGISTRATION_TOKEN}`

## Shell executor (permanent)

The Shell executor runs jobs directly on the machine where the GitLab Runner is installed — a long-lived Orka VM. No scripting or Docker involved. Install the Runner on the VM and register it with `--executor shell`.

## Auth

Use a service account token for `ORKA_TOKEN`. User tokens expire in 1 hour and will not work reliably in CI/CD.

```bash
orka3 sa token <service-account-name>
```

**Note:** The custom-executor.md doc lists `orka3 user get-token` as an option — that is wrong for CI/CD. Service account tokens only.

## Environment variables

| Variable | Required | Where to set | Description |
|----------|----------|-------------|-------------|
| `ORKA_TOKEN` | Yes | GitLab CI/CD Variables | Service account token |
| `ORKA_ENDPOINT` | Yes | Docker container env | Orka API URL, e.g. `http://10.221.188.20` (no trailing slash) |
| `ORKA_CONFIG_NAME` | Yes | GitLab CI/CD Variables | VM config name |
| `ORKA_SSH_KEY_FILE` | Yes | Mount into container | Private key contents — no passphrase |
| `ORKA_VM_USER` | No | GitLab CI/CD Variables | SSH user, default `admin` |
| `ORKA_VM_NAME_PREFIX` | No | GitLab CI/CD Variables | VM name prefix, default `gl-runner` |
| `VM_DEPLOYMENT_ATTEMPTS` | No | GitLab CI/CD Variables | Retry attempts, default `1` |

**Two scopes:** Variables like `ORKA_ENDPOINT` that are needed at container startup go in the Docker `--env` flag. Variables like `ORKA_TOKEN` that are needed during job execution go in GitLab CI/CD Variables (Settings > CI/CD > Variables). Mark sensitive variables as Masked.

**SSH key:** Prefer mounting the key file into the container (`-v /path/to/keys:/keys`) over storing key contents as a GitLab variable.

## Connectivity

Runner initiates connection to GitLab — one-way. The GitLab server does not need visibility to Orka. The runner container must have network access to both the Orka endpoint and the GitLab server.

## IP mapping

If Orka node IPs are private and the runner connects over a public IP, configure IP mapping in `/var/custom-executor/settings.json` on the container:

```json
{
  "mappings": [
    { "private_host": "10.221.188.100", "public_host": "203.0.113.100" }
  ]
}
```

## Gotchas

- **Tokens are not available for manual verification inside the container.** They are injected at job run time by GitLab. Don't suggest `export ORKA_TOKEN=...` or inline verification steps.
- **Failed VMs are auto-deleted by the runner.** To debug SSH issues, deploy a VM manually: `orka3 vm deploy test-debug --config $ORKA_CONFIG_NAME -o json`, troubleshoot, then `orka3 vm delete test-debug`.
- **SSH key must have no passphrase.** The runner cannot handle passphrase-protected keys.
- **ORKA_ENDPOINT must include the protocol and no trailing slash.** `http://10.221.188.20` is correct; `10.221.188.20` and `http://10.221.188.20/` are not.
- **Don't use grep or pipes for CLI output.** Use `orka3 vmc list <name>` to check if a config exists.
- **VM config must exist before the runner starts.** Create it with `orka3 vmc create <name> --image <image> --cpu <n>`.
