# TeamCity Plugin

Repo: https://github.com/macstadium/orka-teamcity-plugin

## Contents
- [What it does](#what-it-does)
- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration in TeamCity](#configuration-in-teamcity)
- [Gotchas](#gotchas)

## What it does

A TeamCity server plugin that adds Orka as a cloud agent provider. Once a per-project cloud profile is configured, TeamCity provisions ephemeral Orka VMs as build agents on demand and tears them down after jobs complete. No scripting required: all lifecycle management happens inside TeamCity.

Current plugin release: 2.0.2 (2026-06-24), published on the [JetBrains Marketplace](https://plugins.jetbrains.com/plugin/13662-orka-by-macstadium).

## Requirements

- TeamCity 2023.11 or later
- Java 11, 17, or 21 on the TeamCity server
- Orka VM base image with SSH (password auth) enabled and TeamCity build agent pre-installed
- A service account token (see below)
- **Network access:** the TeamCity server must be connected to the Orka environment through VPN (a VPN client for temporary connectivity, or a site-to-site tunnel), and Orka VMs must reach the TeamCity server

## Setup

**1. Install the plugin** from the [JetBrains Marketplace](https://plugins.jetbrains.com/plugin/13662-orka-by-macstadium).

**2. Create a service account token.** Personal tokens expire after one hour and break agent provisioning:
```bash
orka sa create teamcity
orka sa token teamcity
```

**3. Prepare the VM base image:**

The base image must have:
- TeamCity build agent installed and connected to the server at least once (to sync agent version)
- SSH enabled with password authentication
- Agent stopped (not running) before saving the image

```bash
# On the VM, after agent syncs and you've stopped it:
orka vm save <VM_NAME> <NEW_IMAGE_NAME>
# or commit:
orka vm commit <VM_NAME>

# Create a VM config from the image:
orka vmc create <VM_CONFIGURATION_NAME> --image <NEW_IMAGE_NAME>
```

**4. Configure a cloud profile:** see below.

## Configuration in TeamCity

Go to Projects > (your project) > Edit Project Settings > Cloud Profiles > Create new profile, and set **Cloud type** to **Orka Cloud**.

| Field | Required | Value |
|-------|----------|-------|
| Orka endpoint | Yes | Orka API URL, from the IP Allocation table in My Cloud |
| Orka Token | Yes | Service account token from `orka sa token <SERVICE_ACCOUNT_NAME>` |
| VM Config | Yes | VM config name created above |
| Namespace | Yes | Namespace VMs deploy into. Must match the service account's access |
| VM user | Yes | SSH user on the deployed VM |
| VM SSH password | Yes | SSH password for that user |
| Maximum instances count | No | Cap on concurrent agents. Blank means no limit |
| Agent pool | No | TeamCity agent pool new agents join |
| Agent directory | No | Path to agent install on the VM, e.g. `/Users/admin/BuildAgent/` |
| Node mappings | No | Overrides the host address used to reach a VM. `PRIVATE_HOST;PUBLIC_HOST` pairs, one per line. Use when your network's address range overlaps with Orka's |

**Auth:** the service account token is the only auth the plugin uses. There is no username/password option.

## Gotchas

- **Bidirectional connectivity is required.** Unlike GitLab and Buildkite, the TeamCity server initiates connections to the Orka VM (for agent management). Both sides need network access to each other.
- **"Agent Push" is not supported.** Agents are only created through the cloud profile.
- **Agent must be pre-installed and synced on the base image.** If the agent version on the image doesn't match the server, TeamCity will attempt an upgrade on every VM start, which is slow and unreliable. Sync it once before saving the image.
- **SSH uses password auth, not key auth.** Configure `VM SSH password` in the cloud profile.
- **Use a service account token, not a personal token.** Personal tokens expire after one hour and break agent provisioning.
- **Known issue: first ARM deploy on a node can time out.** The first deployment of an Apple silicon agent from a VM config on a given node may time out. Subsequent deployments on that node succeed.
- **Support:** open a ticket in the [MacStadium Portal](https://portal.macstadium.com) and include the plugin's server-side logs.
