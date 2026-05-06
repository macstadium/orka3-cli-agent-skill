# Configuration and Utility Commands Reference

This reference provides detailed syntax and examples for configuration, authentication, and utility Orka3 CLI commands.

## Contents
- [Configuration Commands](#configuration-commands)
- [Default Namespace Detection (v3.5.2+)](#default-namespace-detection-v352)
- [Authentication Commands](#authentication-commands)
- [Utility Commands](#utility-commands)

## Configuration Commands

### orka3 config set

Set the Orka service URL for your environment.

**Syntax:**
```bash
orka3 config set --api-url <URL> [flags]
```

**Options:**
- `-a, --api-url string` - (Required) The Orka service URL
- `-h, --help` - Display help

**Examples:**
```bash
orka3 config set --api-url http://10.221.188.20
orka3 config set --api-url https://company.orka.app
```

**Common API URLs:**
- `http://10.221.188.20` — Standard Orka 2.1+ on-premises / MSDC
- `https://company.orka.app` — Domain-based access (replace `company` with your org)
- Check with your MacStadium team or support@macstadium.com if you don't know your API URL

### orka3 config view

View the current local Orka CLI configuration.

**Syntax:**
```bash
orka3 config view [flags]
```

## Default Namespace Detection (v3.5.2+)

The Orka CLI now automatically reads the default namespace from your orka kubeconfig context, eliminating the need to repeatedly specify namespaces in commands.

**Namespace Resolution Hierarchy (highest to lowest priority):**
1. `--namespace` / `-n` flag on command
2. `ORKA_DEFAULT_NAMESPACE` environment variable
3. Namespace from orka kubeconfig context
4. Falls back to `orka-default`

**Setting a Custom Default Namespace:**
```bash
# Option 1: Environment variable (session or persistent)
export ORKA_DEFAULT_NAMESPACE=my-team-namespace
orka3 vm list  # Uses my-team-namespace

# Option 2: kubectl context (persistent)
kubectl config set-context orka --namespace=orka-default
```

**Requirements:**
- Orka CLI version 3.5.2 or later
- Valid orka kubeconfig file with configured context

## Authentication Commands

### orka3 login

Log in to your Orka cluster with MacStadium Customer Portal credentials.

**Syntax:**
```bash
orka3 login [flags]
```

**Notes:**
- Opens browser for authentication
- Token stored in `~/.kube/config`
- Token valid for 1 hour

### orka3 user get-token

Print your authentication token from ~/.kube/config.

**Syntax:**
```bash
orka3 user get-token [flags]
```

### orka3 user set-token

Log in with a valid authentication token.

**Syntax:**
```bash
orka3 user set-token <TOKEN> [flags]
```

## Utility Commands

### orka3 completion

Generate shell autocompletion scripts.

**Syntax:**
```bash
orka3 completion {bash|fish|powershell|zsh} [flags]
```

**Examples:**
```bash
# Bash (load current session)
source <(orka3 completion bash)

# Bash (persist - Linux)
orka3 completion bash > /etc/bash_completion.d/orka3

# Bash (persist - macOS)
orka3 completion bash > $(brew --prefix)/etc/bash_completion.d/orka3

# Zsh (load current session)
source <(orka3 completion zsh)

# Zsh (persist - Linux)
orka3 completion zsh > "${fpath[1]}/_orka3"

# Zsh (persist - macOS)
orka3 completion zsh > $(brew --prefix)/share/zsh/site-functions/_orka3
```

### orka3 version

Print the current version of the Orka CLI.

**Syntax:**
```bash
orka3 version [flags]
```

**Output Includes:**
- CLI build information
- Compatibility with Orka cluster
