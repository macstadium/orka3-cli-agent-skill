# GitHub Actions Integration

Repo: https://github.com/macstadium/orka-github-actions-integration  
Image: `ghcr.io/macstadium/orka-github-runner:<tag>`

## Contents
- [What it does](#what-it-does)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Key variables](#key-variables)
- [Auth](#auth)
- [Multiple runners](#multiple-runners)
- [Metrics](#metrics)
- [Gotchas](#gotchas)

## What it does

A Docker-based controller that listens for GitHub Actions workflow runs and spins up ephemeral Orka VMs to execute them. Uses GitHub runner scale sets (similar to ARC). Each job gets a fresh VM; the VM is deleted after the job completes.

The integration tracks in-flight VM deployments to prevent over-provisioning when multiple jobs start simultaneously. On restart, it reconciles existing VMs (adopting running ones, cleaning up failed/finished ones) and reuses the existing runner scale set so in-progress jobs continue uninterrupted.

## Prerequisites

- GitHub App for repo- or org-level runners. Instructions: `docs/github-app-setup-steps.md` in the repo. Alternatively, a classic PAT via `GITHUB_PAT` (v1.1.15+), which is required for enterprise-level runners (see [Auth](#auth)).
- An Orka VM config created from a suitable base image: `orka3 vmc create <name> --image <image>`
- A service account token: `orka3 sa token <service-account-name>`
- A machine with Docker and network access to the Orka cluster

## Configuration

Run the container with env vars directly or via a `.env` file:

```bash
docker run \
  -e GITHUB_APP_ID=<id> \
  -e GITHUB_APP_INSTALLATION_ID=<install-id> \
  -e GITHUB_APP_PRIVATE_KEY_PATH=/keys/private-key.pem \
  -e GITHUB_URL=https://github.com/<org-or-repo> \
  -e ORKA_URL=http://10.221.188.20 \
  -e ORKA_TOKEN=<service-account-token> \
  -e ORKA_VM_CONFIG=my-orka-runner \
  -e RUNNERS='[{"name":"my-github-runner"}]' \
  -v /path/to/keys:/keys \
  ghcr.io/macstadium/orka-github-runner:<tag>
```

Or mount a `.env` file:

```bash
docker run -v /path/to/.env:/.env ghcr.io/macstadium/orka-github-runner:<tag>
```

## Key variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_APP_ID` | Yes, unless `GITHUB_PAT` is set | GitHub App ID |
| `GITHUB_APP_INSTALLATION_ID` | Yes, unless `GITHUB_PAT` is set | GitHub App installation ID |
| `GITHUB_APP_PRIVATE_KEY_PATH` or `GITHUB_APP_PRIVATE_KEY` | Yes, unless `GITHUB_PAT` is set | Private key file path or contents (PKCS#1 RSA only) |
| `GITHUB_PAT` | No | Classic PAT used instead of the GitHub App (v1.1.15+). Takes precedence over the App vars. Required for enterprise-level runners |
| `GITHUB_URL` | Yes | Repo, org, or enterprise URL, e.g. `https://github.com/myorg` |
| `ORKA_URL` | Yes | Orka API URL, e.g. `http://10.221.188.20` |
| `ORKA_NAMESPACE` | No | Namespace VMs are deployed in, default `orka-default` |
| `ORKA_TOKEN` | Yes | Service account token |
| `ORKA_VM_CONFIG` | Yes | VM config name |
| `RUNNERS` | Yes | JSON array: `[{"name":"runner-name","id":1}]` |
| `ORKA_VM_USERNAME` | No | VM SSH user, default `admin` |
| `ORKA_VM_PASSWORD` | No | VM SSH password, default `admin` |
| `ORKA_ENABLE_NODE_IP_MAPPING` | No | Enable if nodes have private IPs not reachable from container |
| `ORKA_NODE_IP_MAPPING` | No | JSON map of node internal IPs to external IPs |
| `LOG_LEVEL` | No | `info` (default), `debug`, `warning`, `error` |
| `ORKA_VM_METADATA` | No | Custom VM metadata passed to the VM, as `key=value` comma-separated pairs |
| `ENABLE_METRICS` | No | Expose Prometheus metrics at `/metrics` on `METRICS_ADDR` (default: `false`) |
| `METRICS_ADDR` | No | Address for Prometheus metrics endpoint (default: `:8080`) |
| `METRICS_POLL_INTERVAL` | No | How often runner scale set stats are polled for metrics (default: `30s`) |
| `ENABLE_RECONCILIATION` | No | Reconcile existing VMs on restart: adopt running VMs, clean up failed/finished ones (default: `true`) |
| `MANAGE_RUNNER_SCALE_SETS` | No | `true` = delete existing scale set on startup and exit; `false` = reuse if found (default: `false`) |
| `MAX_RUNNERS` | No | Maximum runners the scale set reports to GitHub (default: `9000`). Set at or below VM slot capacity (2 x Apple silicon nodes in `ORKA_NAMESPACE`) so jobs queue instead of failing at deploy |
| `VM_TRACKER_INTERVAL` | No | Orphaned-VM check interval (default: `300s`). A VM is deleted after two consecutive checks with no matching runner |
| `RUNNER_DEREGISTRATION_TIMEOUT` | No | Wait for a runner to de-register before force-deleting it (default: `30s`) |
| `RUNNER_DEREGISTRATION_POLL_INTERVAL` | No | Poll interval while waiting for de-registration (default: `2s`) |
| `GITHUB_RUNNER_VERSION` | No | Pin the Actions runner version installed on each VM, e.g. `2.336.0` (no leading `v`). If unset, the latest release is looked up on github.com at startup |
| `GITHUB_TOKEN` | No | github.com token used only for the runner release lookup (always a github.com token, even on GHES; unrelated to `GITHUB_PAT`). Unauthenticated lookups are limited to 60/hour per IP and exceeding that fails startup with `403 Forbidden`. Not needed if `GITHUB_RUNNER_VERSION` is set |

## Auth

`ORKA_TOKEN` must be a service account token, not a user token. User tokens expire in 1 hour.

```bash
orka3 sa token <service-account-name>
```

For long-lived or non-expiring tokens:

```bash
orka3 sa token <name> --duration 8760h   # 1 year
orka3 sa token <name> --no-expiration
```

### GitHub credentials: App or PAT

- **GitHub App:** the default for repo- and org-level runners.
- **Classic PAT (`GITHUB_PAT`, v1.1.15+):** takes precedence over the App vars; the App vars are not required when it is set. Required for enterprise-level runners (`GITHUB_URL=https://<GHES_OR_GITHUB_HOST>/enterprises/<ENTERPRISE>`): GitHub does not grant `manage_runners:enterprise` to App installations, so App auth fails with `403 Resource not accessible by integration`. Use a classic token with the `admin:enterprise` scope, owned by an enterprise owner. Fine-grained PATs don't expose enterprise scopes and don't work. The runner refuses to start with an enterprise `GITHUB_URL` and no `GITHUB_PAT`.

## Private key format

GitHub App private keys must be in PKCS#1 RSA format. If needed, convert the key:

```bash
ssh-keygen -p -m pem -f /path/to/private-key.pem
```

## GitHub Enterprise Server (GHES)

Set `GITHUB_URL` to your org or repo on the GHES instance. The API URL is derived from `GITHUB_URL` and logged on startup. `GITHUB_API_URL` is accepted but ignored, and logs a warning when set.

The runner release is still looked up on github.com: provide a github.com `GITHUB_TOKEN` to avoid the unauthenticated rate limit, or pin `GITHUB_RUNNER_VERSION` to skip the lookup entirely.

## Multiple runners

Each container instance supports one runner scale set. To run multiple scale sets, start multiple container instances, each with a different `RUNNERS` name value.

## Metrics

With `ENABLE_METRICS=true`, the integration exposes Prometheus gauges at `<METRICS_ADDR>/metrics`, each labeled `runner_name`, refreshed every `METRICS_POLL_INTERVAL`:

| Metric | Meaning |
|--------|---------|
| `runner_scale_set_total_available_jobs` | Jobs waiting for a runner |
| `runner_scale_set_total_acquired_jobs` | Jobs acquired by the scale set |
| `runner_scale_set_total_assigned_jobs` | Jobs assigned to a runner |
| `runner_scale_set_total_running_jobs` | Jobs running |
| `runner_scale_set_total_registered_runners` | Registered runners |
| `runner_scale_set_total_busy_runners` | Runners executing a job |
| `runner_scale_set_total_idle_runners` | Runners registered but idle |

See [monitoring.md](../workflows/monitoring.md) for a backlog alert built on these.

## Workflow usage

In your GitHub Actions workflow, set `runs-on` to match the `name` in your `RUNNERS` config:

```yaml
jobs:
  build:
    runs-on: my-github-runner
```

## Gotchas

- **App or classic PAT.** Use a GitHub App for repo/org runners, or a classic `GITHUB_PAT` (v1.1.15+, required for enterprise-level runners). Fine-grained PATs don't work.
- **ORKA_VM_CONFIG must exist before the container starts.** Create it with `orka3 vmc create`.
- **Node IP mapping.** If the container is outside the Orka network, set `ORKA_ENABLE_NODE_IP_MAPPING=true` and provide the mapping JSON.
- **Orphaned VMs are cleaned up automatically.** VMs without a corresponding GitHub runner for two consecutive checks (`VM_TRACKER_INTERVAL`, default 300s) are deleted. Runner deregistration uses exponential backoff on failure.
- **VM names are `<RUNNERS[].name>-<random>`.** There is no name prefix setting, so give scale sets a recognizable name if you filter or clean up VMs by name.
- **Debug logging:** set `LOG_LEVEL=debug`.
