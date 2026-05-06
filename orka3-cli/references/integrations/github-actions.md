# GitHub Actions Integration

Repo: https://github.com/macstadium/orka-github-actions-integration  
Image: `ghcr.io/macstadium/orka-github-runner:<tag>`

## Contents
- [What it does](#what-it-does) — [Prerequisites](#prerequisites) — [Configuration](#configuration) — [Multiple runners](#multiple-runners) — [Gotchas](#gotchas)

## What it does

A Docker-based controller that listens for GitHub Actions workflow runs and spins up ephemeral Orka VMs to execute them. Uses GitHub runner scale sets (similar to ARC). Each job gets a fresh VM; the VM is deleted after the job completes.

## Prerequisites

- GitHub App (not a PAT). Instructions: `docs/github-app-setup-steps.md` in the repo.
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
| `GITHUB_APP_ID` | Yes | GitHub App ID |
| `GITHUB_APP_INSTALLATION_ID` | Yes | GitHub App installation ID |
| `GITHUB_APP_PRIVATE_KEY_PATH` or `GITHUB_APP_PRIVATE_KEY` | Yes | Private key file path or contents (PKCS#1 RSA format) |
| `GITHUB_URL` | Yes | Repo or org URL, e.g. `https://github.com/myorg` |
| `ORKA_URL` | Yes | Orka API URL, e.g. `http://10.221.188.20` |
| `ORKA_TOKEN` | Yes | Service account token |
| `ORKA_VM_CONFIG` | Yes | VM config name |
| `RUNNERS` | Yes | JSON array: `[{"name":"runner-name","id":1}]` |
| `ORKA_VM_USERNAME` | No | VM SSH user, default `admin` |
| `ORKA_VM_PASSWORD` | No | VM SSH password, default `admin` |
| `ORKA_ENABLE_NODE_IP_MAPPING` | No | Enable if nodes have private IPs not reachable from container |
| `ORKA_NODE_IP_MAPPING` | No | JSON map of node internal IPs to external IPs |
| `LOG_LEVEL` | No | `info` (default), `debug`, `warning`, `error` |
| `ENABLE_METRICS` | No | Expose Prometheus metrics at `/metrics` on `METRICS_ADDR` |
| `METRICS_ADDR` | No | Default `:8080` |

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

## Private key format

GitHub App private keys must be in PKCS#1 RSA format. If needed, convert:

```bash
ssh-keygen -p -m pem -f /path/to/private-key.pem
```

## GitHub Enterprise Server (GHES)

Set `GITHUB_URL` to your GHES instance URL and add `GITHUB_API_URL` pointing to `https://<your-ghes>/api/v3`. Provide `GITHUB_TOKEN` (PAT) to avoid rate limiting when pulling the runner image from github.com.

## Multiple runners

Each container instance supports one runner scale set. To run multiple scale sets, start multiple container instances, each with a different `RUNNERS` name value.

## Workflow usage

In your GitHub Actions workflow, set `runs-on` to match the `name` in your `RUNNERS` config:

```yaml
jobs:
  build:
    runs-on: my-github-runner
```

## Gotchas

- **GitHub App, not PAT.** Authentication requires a GitHub App. A personal access token will not work.
- **ORKA_VM_CONFIG must exist before the container starts.** Create it with `orka3 vmc create`.
- **Node IP mapping.** If the container is outside the Orka network, set `ORKA_ENABLE_NODE_IP_MAPPING=true` and provide the mapping JSON.
- **VM tracker cleans up orphaned VMs** every `VM_TRACKER_INTERVAL` (default 300s). VMs without a corresponding GitHub runner for two consecutive checks are deleted.
