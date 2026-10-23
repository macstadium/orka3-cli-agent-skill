# Jenkins Plugin

Repo: https://github.com/jenkinsci/macstadium-orka-plugin  
Plugin: **Orka by MacStadium** (`macstadium-orka`)  
Current version: `2.10` (2026-06-04). Orka 3.x requires plugin 2.0+. On Orka 2.x, use plugin 1.35.

## Contents
- [What it does](#what-it-does)
- [Requirements](#requirements)
- [Auth](#auth)
- [Ephemeral agents (Orka Cloud)](#ephemeral-agents-orka-cloud)
- [Agent template fields](#agent-template-fields)
- [Retention strategies](#retention-strategies)
- [Permanent agents](#permanent-agents)
- [Logging](#logging)
- [Orka 4.0](#orka-40)
- [Gotchas](#gotchas)

## What it does

A Jenkins plugin that adds Orka as a cloud provider and as a permanent agent type. The plugin deploys an Orka VM through the Orka API, then the Jenkins controller connects to it over SSH. Ephemeral agents are created when the build queue needs executors and deleted when their retention strategy says so. No scripting required.

## Requirements

- Orka 3.0+ (plugin 2.0+)
- Jenkins controller with network access to the Orka endpoint. Each Orka environment is behind a firewall, so connect through a VPN client or a site-to-site VPN tunnel.
- A base image with SSH (Remote Login) enabled and credentials that match the Jenkins VM Credentials
- Install from Manage Jenkins > Plugins > Available plugins > "Orka by MacStadium"

## Auth

The Orka Token field takes a Jenkins credential (Secret text) holding a **service account token**. Never use a user token; user tokens expire after 1 hour.

```bash
orka3 sa create <SA_NAME> -n <NAMESPACE>
orka3 sa token <SA_NAME> -n <NAMESPACE>
```

The VM Credentials field is a separate Jenkins credential (username and password, or SSH username with private key) used by the controller to SSH into the VM.

## Ephemeral agents (Orka Cloud)

Manage Jenkins > Nodes and Clouds > Configure Clouds > Add a new cloud > **Orka Cloud**.

| Field | Default | Notes |
|-------|---------|-------|
| Name of this Cloud | | |
| Orka Token | | Service account token credential |
| Orka Endpoint | | Orka API URL, e.g. `http://10.221.188.20` |
| Max Jenkins Agents Limit (Advanced) | No limit | Maximum Orka VMs this cloud creates. Set at or below VM slot capacity (2 x Apple silicon nodes in the template's namespace) so builds queue instead of failing at deploy |
| Deployment Timeout (sec) (Advanced) | `600` | Wait for a VM deploy |
| HTTP Timeout (sec) (Advanced) | `300` | All other Orka API calls |
| Node Mappings (Advanced) | | Map private node IPs to public host addresses (public addresses come from MacStadium) |
| Use Jenkins HTTP Proxy Settings (Advanced) | Off | Route Orka API calls through the Jenkins proxy |
| Ignore SSL Errors (Advanced) | Off | Avoid; fix the certificate instead |
| No Delay Provisioning (Advanced) | Off | Skip Jenkins' provisioning delay so agents are created as soon as needed. Can overprovision |

Use **Test Connection** to check the endpoint and token. Then click **Add Orka Template**.

## Agent template fields

With **Orka 3.x Deployment** selected, choose one input mode:

- **Specify values directly:** Image (an image name from cluster storage, such as `sequoia-90gb-orka3-arm`, or an OCI reference, such as `ghcr.io/macstadium/orka-images/sequoia:latest`), # of CPUs (default `2`), Memory in G (default `auto`, calculated from CPUs), Tag, Tag Required, Scheduler, plus under Advanced the Intel-only Use Net Boost, Use Legacy IO, and Use GPU Passthrough (GPU must be enabled for the cluster), and Display Settings (width, height, DPI).
- **Use a VM Config:** select an existing Orka VM config. All VM parameters come from the config, so you can change them in Orka without touching Jenkins.

Common fields:

| Field | Notes |
|-------|-------|
| Namespace | Default `orka-default`. The service account must have access to it |
| Name Prefix | VM and Jenkins agent name become `<PREFIX>-<random>`. Use a unique prefix per controller so leaked VMs are attributable |
| VM Credentials | SSH credentials for the VM |
| Scheduler | `default` spreads VMs across nodes; `most-allocated` fills a node before using the next |
| Tag / Tag Required | Node affinity. Tag Required deploys only to nodes with the tag |
| # of executors, Remote FS root, Labels | Standard Jenkins agent fields. Labels are what pipelines target |

Templates migrated from Orka 2.x show an **Orka 2.x Deployment** option that is read-only. Switch to Orka 3.x Deployment to make changes.

## Retention strategies

| Strategy | Behavior |
|----------|----------|
| Terminate immediately after use (help text calls it "Use agent only once") | One job per VM, then the VM is deleted. Requires **# of executors = 1**. Idle time (default 1 minute) cleans up after unexpected failures |
| Keep until idle time expires | Reuses the VM for multiple jobs; deleted after the idle time. Default and recommended minimum idle time: 30 minutes |

## Permanent agents

Manage Jenkins > Nodes and Clouds > New Node > **Agent running under Orka by MacStadium**. Fields: Orka Token, Orka Endpoint, Namespace, Node (the Orka node to deploy on), Public Host (optional, from MacStadium), Image, # of CPUs, Memory, Tag, Tag Required, the Intel-only options, VM Credentials, Name Prefix. The VM stays up until you delete the agent.

## Orka 4.0

Plugin 2.10 works with Orka 4.0. The plugin sends the Use Net Boost checkbox on every deploy, so an unchecked box sends `"netBoost": false`. Orka 4.0 accepts that and sets net boost on, as 3.6 did for Apple silicon (OK-6467). Leave Use Legacy IO and Use GPU Passthrough unchecked: 4.0 rejects both when they're turned on.

## Logging

Manage Jenkins > System Log > Add new log recorder > Loggers > Add:

```
io.jenkins.plugins.orka
```

Set the level to **All**. This is verbose and can slow a busy controller. For lighter logging, use `io.jenkins.plugins.orka.OrkaCloud` at All instead.

## Gotchas

- **Service account token only.** A user token works at first, then fails after 1 hour.
- **Set Max Jenkins Agents Limit.** Left empty there is no limit, and jobs beyond slot capacity fail at deploy instead of waiting in the queue.
- **First Apple silicon deploy is slow.** The first boot of an uncached image on an Apple silicon node takes minutes. Raise the agent connection timeout before the first deploy.
- **"Terminate immediately after use" needs one executor.** More than one executor defeats the one-job-per-VM model.
- **Intel-only options.** Net Boost, Legacy IO, and GPU Passthrough apply only to Intel nodes. Leave Legacy IO and GPU Passthrough unchecked; Orka 4.0 rejects them. See [Orka 4.0](#orka-40).
- **VPN or site-to-site connection required.** The controller initiates the API calls and the SSH connection, so it must reach both the Orka endpoint and the node IPs (or mapped public hosts).
