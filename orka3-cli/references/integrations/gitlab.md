# GitLab Integration

Repo: https://github.com/macstadium/orka-integrations/tree/master/GitLab  
Current release: `v2.0.1`

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
1. Create a base image with SSH enabled (private key, no passphrase) and the `gitlab-runner` binary installed. Without the binary, cache and artifacts are disabled (job log: `Missing gitlab-runner. Extracting cache is disabled.`)
2. Create a VM config from that image: `orka vmc create <VM_CONFIGURATION_NAME> --image <IMAGE_NAME>`
3. Build and run the Docker container from the [Dockerfile](https://github.com/macstadium/orka-integrations/blob/master/GitLab/Dockerfile)
4. Register the runner inside the container using `TOKEN=${REGISTRATION_TOKEN}`
5. Set `concurrent` (and per-runner `limit`) in `config.toml` at or below VM slot capacity (2 x Apple silicon nodes in the target namespace). The template ships with `concurrent = 1`.

## Shell executor (permanent)

The Shell executor runs jobs directly on the machine where the GitLab Runner is installed, a long-lived Orka VM. No scripting or Docker involved. Install the Runner on the VM and register it with `--executor shell`.

## Auth

Use a service account token for `ORKA_TOKEN`. User tokens expire in 1 hour and will not work reliably in CI/CD.

```bash
orka sa token <SERVICE_ACCOUNT_NAME>
```

Where the control plane caps token lifetime (EKS), use a non-expiring token:

```bash
orka sa token <SERVICE_ACCOUNT_NAME> --no-expiration
```

**Note:** The custom-executor.md doc lists `orka3 user get-token` as an option. That is wrong for CI/CD. Service account tokens only.

## Environment variables

| Variable | Required | Where to set | Description |
|----------|----------|-------------|-------------|
| `ORKA_TOKEN` | Yes | GitLab CI/CD Variables | Service account token |
| `ORKA_ENDPOINT` | Yes | Docker container env | Orka API URL, e.g. `http://10.221.188.20` (no trailing slash) |
| `ORKA_CONFIG_NAME` | Yes | GitLab CI/CD Variables | VM config name |
| `ORKA_SSH_KEY_FILE` | Yes | GitLab CI/CD Variables only | Private key contents (not a path), no passphrase |
| `ORKA_VM_USER` | No | GitLab CI/CD Variables | SSH user, default `admin` |
| `ORKA_VM_NAME_PREFIX` | No | GitLab CI/CD Variables | VM name prefix, default `gl-runner` |
| `VM_DEPLOYMENT_ATTEMPTS` | No | GitLab CI/CD Variables | Deploy attempts per job, default `1`. Adds to GitLab's own 3 retries |

**Two scopes:** Variables like `ORKA_ENDPOINT` that are needed at container startup go in the Docker `--env` flag. Variables like `ORKA_TOKEN` that are needed during job execution go in GitLab CI/CD Variables (Settings > CI/CD > Variables). Mark `ORKA_TOKEN` as Masked. Every `ORKA_*` variable except `ORKA_SSH_KEY_FILE` works in either place; if both are set, the container env wins.

**SSH key:** The scripts read the key only from the GitLab CI/CD variable `ORKA_SSH_KEY_FILE` and write its contents to `~/.ssh/orka_deployment_key`. A key file mounted into the container, or a container env var, is ignored (and the key file at that path is overwritten). Store the private key contents in a CI/CD variable named `ORKA_SSH_KEY_FILE` of type Variable (a File-type variable passes a path, not the contents). GitLab can't mask values containing whitespace, so a multi-line key can't be masked: limit who can view CI/CD settings instead.

## Connectivity

Runner initiates connection to GitLab, one-way. The GitLab server does not need visibility to Orka. The runner container must have network access to both the Orka endpoint and the GitLab server.

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
- **Failed VMs are auto-deleted by the runner.** To debug SSH issues, deploy a VM manually: `orka vm deploy test-debug --config $ORKA_CONFIG_NAME -o json`, troubleshoot, then `orka vm delete test-debug`.
- **SSH key must have no passphrase.** The runner cannot handle passphrase-protected keys.
- **ORKA_ENDPOINT must include the protocol and no trailing slash.** `http://10.221.188.20` is correct; `10.221.188.20` and `http://10.221.188.20/` are not.
- **Don't use grep or pipes for CLI output.** Use `orka vmc list <VM_CONFIGURATION_NAME>` to check if a config exists.
- **VM config must exist before the runner starts.** Create it with `orka vmc create <VM_CONFIGURATION_NAME> --image <IMAGE_NAME> --cpu <CPU>`.
- **Failures exit with `$SYSTEM_FAILURE_EXIT_CODE`.** Deploy, IP, and SSH failures in the prepare stage are reported to GitLab as system failures, not build failures.
- **Debug:** run the runner with `gitlab-runner --debug run`.
- **Integration error strings** (`Invalid ip`, `Waited 30 seconds for sshd to start`, and others) come from the integration's own scripts. Its [troubleshooting.md](https://github.com/macstadium/orka-integrations/blob/master/GitLab/troubleshooting.md) covers them, but it exists only on `master` (not in v2.0.1), and its advice to mount the SSH key file into the container (Option B) doesn't work: `GitLab/scripts/base.sh` always overwrites `~/.ssh/orka_deployment_key` with the `ORKA_SSH_KEY_FILE` CI/CD variable. Use the CI/CD variable as described above.
