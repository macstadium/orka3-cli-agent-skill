# Buildkite Integration

Repo: https://github.com/macstadium/orka-integrations/tree/master/Buildkite

## Contents
- [Ephemeral agent (proxy pattern)](#ephemeral-agent-proxy-pattern) — [Permanent agent](#permanent-agent) — [Auth](#auth) — [Env vars](#environment-variables) — [Gotchas](#gotchas)

## Ephemeral agent (proxy pattern)

A Docker container (the proxy agent) intercepts Buildkite jobs and, instead of running them locally, spins up an Orka VM, delegates the job to the VM via SSH, then deletes the VM after completion. The Buildkite agent is installed on both the proxy container and the VM.

**Setup summary:**
1. Create a base image with:
   - SSH enabled with private key (no passphrase)
   - Buildkite agent installed (`brew install buildkite/buildkite/buildkite-agent`)
2. Save the image: `orka3 vm save <vm> <image-name>`
3. Create a VM config from it: `orka3 vmc create <name> --image <image-name>`
4. Build the Docker image from the [Dockerfile](https://github.com/macstadium/orka-integrations/blob/master/Buildkite/Dockerfile)
5. Run the container with SSH keys mounted and Buildkite agent token:

```bash
docker run \
  -v /path/to/ssh-keys:/buildkite-secrets \
  -e BUILDKITE_AGENT_TOKEN="<your-token>" \
  -e ORKA_TOKEN="<service-account-token>" \
  -e ORKA_ENDPOINT="http://10.221.188.20" \
  -e ORKA_CONFIG_NAME="<vm-config-name>" \
  orka-buildkite
```

The `buildkite-secrets` folder must contain:
- The private SSH key for connecting to ephemeral Orka VMs
- Any SSH keys needed for code repository access

## Permanent agent

Install the Buildkite agent directly on a long-lived Orka VM. No proxy container or custom scripts needed. Follow the standard [Buildkite agent installation](https://buildkite.com/docs/agent/v3/installation) instructions on the VM.

## Auth

`ORKA_TOKEN` must be a service account token. User tokens expire in 1 hour.

```bash
orka3 sa token <service-account-name>
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ORKA_TOKEN` | Yes | Service account token |
| `ORKA_ENDPOINT` | Yes | Orka API URL, e.g. `http://10.221.188.20` |
| `ORKA_CONFIG_NAME` | Yes | VM config name |
| `BUILDKITE_AGENT_TOKEN` | Yes | Buildkite agent token |
| `ORKA_VM_NAME_PREFIX` | No | VM name prefix, default `buildkite-agent` |
| `ORKA_VM_USER` | No | SSH user, default `admin` |

Optional Buildkite sub-agent overrides (append `_SUBAGENT` suffix to standard Buildkite env vars, e.g. `BUILDKITE_AGENT_DEBUG_SUBAGENT`).

## Connectivity

- **Ephemeral agent to Buildkite server:** one-way, initiated from the agent. Orka environment needs outbound access to Buildkite.
- **Proxy agent to Orka:** the container must have network access to the Orka endpoint. Use VPN if running outside the MacStadium network.

## Gotchas

- **Buildkite agent must be installed on the VM image,** not just the proxy container. The proxy delegates the actual job to the VM.
- **SSH keys must have no passphrase.** The proxy agent cannot handle passphrase-protected keys.
- **Mount all SSH keys in one volume** at `/buildkite-secrets`. This includes both the Orka VM key and any repo access keys.
- **VM config must exist before the container starts.** Create it with `orka3 vmc create`.
- **No VPN required for the Buildkite server to reach Orka** — traffic is initiated from the agent side. VPN is only needed for the proxy container to reach the Orka endpoint.
