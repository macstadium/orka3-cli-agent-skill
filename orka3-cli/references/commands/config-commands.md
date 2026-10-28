# Configuration and Utility Commands Reference

This reference provides detailed syntax and examples for configuration, authentication, and utility Orka CLI commands.

## Contents
- [Configuration Commands](#configuration-commands)
- [Default Namespace Detection (v3.5.2+)](#default-namespace-detection-v352)
- [Authentication Commands](#authentication-commands)
- [Utility Commands](#utility-commands)

## Configuration Commands

### orka config set

Set the Orka service URL for your environment. `orka` (4.x) and `orka3` (3.x) share this setting and the `orka` kubeconfig context, so switching between a 3.6 and a 4.0 cluster means running `config set --api-url` and logging in again with either CLI. See "Which CLI" in `SKILL.md`.

**Syntax:**
```bash
orka config set --api-url <URL> [flags]
```

**Options:**
- `-a, --api-url string` - (Required) The Orka service URL
- `-h, --help` - Display help

**Examples:**
```bash
orka config set --api-url http://10.221.188.20
orka config set --api-url https://company.orka.app
```

**Common API URLs:**
- `http://10.221.188.20`: environments first deployed with Orka 2.1 or later
- `http://10.221.188.100`: environments first deployed before Orka 2.1
- `https://company.orka.app`: built-in Orka domain (replace `company` with your org), or your external custom domain
- If the cluster has public NAT IPs or a custom domain for the Orka API, use the public URL. The internal IP times out on those clusters.
- Find your API URL in the IP Allocation table in My Cloud (MacStadium Portal), or ask support@macstadium.com

**`--api-url` does not change kubeconfig.** It sets only the Orka API URL the CLI uses. The cluster's `server` entry in `~/.kube/config` points to the Kubernetes API server, a separate endpoint (for example `10.221.188.19` on TCP 6443, while the Orka API is at `10.221.188.20`). So `kubectl config view` can still show an IP address after you set `--api-url` to a hostname. That's expected, not a failed config change.

### orka config view

View the current local Orka CLI configuration.

**Syntax:**
```bash
orka config view [flags]
```

## Default Namespace Detection (v3.5.2+)

The Orka CLI reads the default namespace from your `orka` kubeconfig context, so you don't need to pass a namespace on every command.

**Namespace Resolution Hierarchy (highest to lowest priority):**
1. `--namespace` / `-n` flag on command
2. `ORKA_DEFAULT_NAMESPACE` environment variable
3. Namespace set on the `orka` context in your kubeconfig
4. Falls back to `orka-default`

**Scope:** this order applies only to the `vm`, `node`, `imagecache`, `registrycredential`, `rolebinding`, and `serviceaccount` commands, plus on Orka 4.0 `emulator` and `rbac --role dev`, for every user, not only admins. `vm-config` and `emulator-config` always use `orka-default`. `orka upgrade service` doesn't follow it: its `--namespace` flag always defaults to `orka-default` and ignores both the environment variable and the kubeconfig context.

**Setting a lasting default namespace:** use the environment variable, for example in your shell profile:
```bash
export ORKA_DEFAULT_NAMESPACE=<NAMESPACE>
```

Setting the namespace on the context (`kubectl config set-context orka --namespace=<NAMESPACE>`) works only until the next `orka user login` or `orka user set-token`: both reset the `orka` context namespace to `orka-default` every time they run. Don't recommend the context as a persistent default.

**Commands land in an unexpected namespace:** the environment variable beats the kubeconfig context, so check for and unset a stale `ORKA_DEFAULT_NAMESPACE`:
```bash
unset ORKA_DEFAULT_NAMESPACE
```

**Requirements:**
- Orka CLI version 3.5.2 or later
- Valid orka kubeconfig file with configured context

## Authentication Commands

### orka login

Log in to your Orka cluster with MacStadium Customer Portal credentials.

**Syntax:**
```bash
orka login [flags]
```

**Notes:**
- Opens browser for authentication
- Token stored in `~/.kube/config`
- Token valid for 1 hour

### orka user get-token

Print your authentication token from ~/.kube/config.

**Syntax:**
```bash
orka user get-token [flags]
```

### orka user set-token

Log in with a valid authentication token.

**Syntax:**
```bash
orka user set-token <TOKEN> [flags]
```

## Utility Commands

### orka completion

Generate shell autocompletion scripts.

**Syntax:**
```bash
orka completion {bash|fish|powershell|zsh} [flags]
```

**Examples:**
```bash
# Bash (load current session)
source <(orka completion bash)

# Bash (persist - Linux)
orka completion bash > /etc/bash_completion.d/orka

# Bash (persist - macOS)
orka completion bash > $(brew --prefix)/etc/bash_completion.d/orka

# Zsh (load current session)
source <(orka completion zsh)

# Zsh (persist - Linux)
orka completion zsh > "${fpath[1]}/_orka"

# Zsh (persist - macOS)
orka completion zsh > $(brew --prefix)/share/zsh/site-functions/_orka
```

### orka version

Print the local CLI version and the versions of the Orka API server and operator on the cluster.

**Syntax:**
```bash
orka version [--client] [flags]
```

**Options:**
- `--client` - Print only the local CLI version, without contacting the cluster

**Output fields:**
- `Client Version`: your local CLI (`v4.x` for `orka`, `v3.x` for `orka3`)
- `API Version`: Orka API server
- `Operator Version`: Orka operator (webhooks and CRDs ship with it and match its version)
- `Upgrade Service Operator Version`, `Upgrade Service Cluster Agent Version`: only when Upgrade Service is installed

Per-node Virtual Kubelet and Orka Engine versions come from `orka node list -o wide` (`VERSION` and `RUNTIME`). Components can report different numbers on the same cluster because a patch release only bumps what it changed. See "Checking component versions" in `references/workflows/upgrade-workflows.md`.
