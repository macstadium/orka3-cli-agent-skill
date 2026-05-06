# Packer Plugin

Repo: https://github.com/macstadium/packer-plugin-macstadium-orka  
Current version: `3.1.2`

## Contents
- [What it does](#what-it-does)
- [Configuration](#configuration)
- [Key variables](#key-variables)
- [Auth](#auth)
- [OCI images](#oci-images)
- [Dev toolkit examples](#dev-toolkit-examples)
- [Gotchas](#gotchas)

## What it does

The plugin deploys an Orka VM from a source image, runs Packer provisioners (shell scripts, file uploads, etc.) inside it, saves the result as a new image, and deletes the VM. The plugin handles deploy, connect, provision, save, and delete — you write the provisioners.

## Configuration

Minimal working config:

```hcl
packer {
  required_plugins {
    macstadium-orka = {
      version = "= 3.1.2"
      source  = "github.com/macstadium/macstadium-orka"
    }
  }
}

source "macstadium-orka" "image" {
  source_image    = "ghcr.io/macstadium/orka-images/sonoma:latest"
  image_name      = "my-configured-sonoma"
  orka_endpoint   = var.orka_endpoint
  orka_auth_token = var.orka_auth_token
  ssh_username    = "admin"
  ssh_password    = "admin"
}
```

## Key variables

| Variable | Required | Description |
|----------|----------|-------------|
| `source_image` | Yes | Base image — CRD name or OCI path |
| `orka_auth_token` | Yes | Service account token (not user token) |
| `orka_endpoint` | Yes | Orka API URL, e.g. `http://10.221.188.20` |
| `image_name` | No | Output image name — CRD name or OCI path; auto-generated if omitted |
| `image_description` | No | Plain text description |
| `image_force_overwrite` | No | Overwrite existing image if it exists |
| `orka_vm_cpu_core` | No | CPU count for the builder VM |
| `ssh_username` / `ssh_password` | No | Default `admin`/`admin` on MacStadium base images |
| `packer_vm_timeout` | No | Minutes to wait for VM launch |
| `packer_push_timeout` | No | Minutes to wait for OCI push; defaults to 60 |

## Auth

`orka_auth_token` must be a service account token. The config docs are explicit on this. User tokens expire in 1 hour.

```bash
orka3 sa token <service-account-name>
```

Pass via variable, not inline in the template:

```hcl
variable "orka_auth_token" {
  default = env("ORKA_AUTH_TOKEN")
}
```

## OCI images

`source_image` and `image_name` both accept OCI registry paths. To push the output to an OCI registry, the registry credentials must be configured first:

```bash
orka3 regcred add https://ghcr.io --username "$REGISTRY_USER" --password "$REGISTRY_TOKEN"
```

Then set `image_name` to the full OCI path:

```hcl
image_name = "ghcr.io/your-org/orka-images/custom-sonoma:v1.2"
```

Push status is async — check with `orka3 vm get-push-status` if you need to confirm before proceeding.

## Dev toolkit examples

The repo includes example templates in `examples/` (Sequoia and Tahoe, 90 GB and 200 GB). These install Homebrew, Xcode CLT, Fastlane, Git, Cocoapods, and Swift.

**Known fix (PR #84, pending merge):** The examples had two bugs — Homebrew requires Xcode CLT to be installed first (the templates skipped this step), and the `brew shellenv` eval line was missing a closing `)` so PATH was never set in `.zprofile`. Both are fixed in PR #84. Until it merges, the existing example templates will fail Homebrew installation.

## Gotchas

- **VPN required.** Packer must have network connectivity to the Orka endpoint. If running locally, connect via VPN first.
- **`packer init` downloads the plugin.** Run `packer init <template>.pkr.hcl` before `packer build`.
- **`do_not_delete` and `do_not_image`** are dev-only flags. Don't set these in production — the plugin won't clean up the builder VM.
- **IP mapping:** If Orka node IPs are not directly reachable, set `enable_orka_node_ip_mapping = true` and provide `orka_node_ip_map`.
- **Intel-only flags:** `orka_enable_net_boost` and `orka_enable_legacy_io` are Intel only. Ignore on Apple Silicon clusters.
