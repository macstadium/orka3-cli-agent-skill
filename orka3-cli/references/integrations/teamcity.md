# TeamCity Plugin

Repo: https://github.com/macstadium/orka-teamcity-plugin

## Contents
- [What it does](#what-it-does)
- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration in TeamCity](#configuration-in-teamcity)
- [Gotchas](#gotchas)

## What it does

A TeamCity server plugin (Java/Gradle) that adds Orka as a cloud agent provider. Once configured, TeamCity automatically provisions ephemeral Orka VMs as build agents on demand and tears them down after jobs complete. No scripting required — all lifecycle management happens inside TeamCity.

## Requirements

- TeamCity 2023.11 or later
- Java 11, 17, or 21 on the TeamCity server
- Orka VM base image with SSH (password auth) enabled and TeamCity build agent pre-installed
- **Bidirectional network access:** TeamCity server must reach the Orka endpoint, and Orka VMs must reach the TeamCity server

## Setup

**1. Build the plugin:**
```bash
./gradlew build
# Output: macstadium-orka-server/build/distributions/*.zip
```

**2. Install in TeamCity:**
- Administration > Server Administration > Plugins List > Upload plugin zip
- Enable the plugin after upload

**3. Prepare the VM base image:**

The base image must have:
- TeamCity build agent installed and connected to the server at least once (to sync agent version)
- SSH enabled with password authentication
- Agent stopped (not running) before saving the image

```bash
# On the VM, after agent syncs and you've stopped it:
orka3 vm save <vm-name> <base-image-name>
# or commit:
orka3 vm commit <vm-name>

# Create a VM config from the image:
orka3 vmc create <config-name> --image <base-image-name>
```

**4. Configure a cloud profile** — see below.

## Configuration in TeamCity

Go to Projects > (your project) > Edit Project Settings > Cloud Profiles > Create new profile.

| Field | Value |
|-------|-------|
| Cloud type | Orka Cloud |
| Orka endpoint | Orka API URL from your IP plan |
| Orka user email | Orka user account email |
| Orka password | Orka user account password |
| VM template | VM config name created above |
| VM user | SSH user on the VM (default: `admin`) |
| VM SSH password | SSH password for the VM user |
| Maximum instances count | Cap on simultaneous agents |
| Agent Pool | TeamCity agent pool to assign agents to |
| Agent directory | Path to agent install on the VM, e.g. `/Users/admin/BuildAgent/` |

**Note:** The plugin uses Orka user credentials (email + password), not a service account token. This is the plugin's own auth model — different from all other integrations.

## Gotchas

- **Bidirectional connectivity is required.** Unlike GitLab and Buildkite, the TeamCity server initiates connections to the Orka VM (for agent management). Both sides need network access to each other.
- **"Agent Push" is not supported.** Do not attempt to push agents from TeamCity to the VM.
- **Agent must be pre-installed and synced on the base image.** If the agent version on the image doesn't match the server, TeamCity will attempt an upgrade on every VM start — slow and unreliable. Sync it once before saving the image.
- **SSH uses password auth, not key auth.** Configure `VM SSH password` in the cloud profile.
- **Auth model differs from other integrations.** The plugin uses Orka user email + password, not a service account token. Service account tokens are not applicable here.
- **Java version matters.** Build the plugin with Java 11+. If `JAVA_HOME` is wrong, set it: `export JAVA_HOME=$(/usr/libexec/java_home -v 11)`.
