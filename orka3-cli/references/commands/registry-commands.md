# OCI Registry Commands Reference

This reference provides detailed syntax and examples for OCI registry credential management in Orka3. These are admin-only operations.

## orka3 registrycredential add (alias: regcred)

Add credentials for an OCI registry server.

**Syntax:**
```bash
orka3 registrycredential add <SERVER> --username <USER> {--password <PASS>|--password-stdin} [--replace] [--allow-insecure] [--namespace <NS>] [flags]
```

**Options:**
- `-u, --username string` - (Required) Username
- `-p, --password string` - Password
- `--password-stdin` - Read password from stdin
- `--replace` - Replace existing credentials
- `--allow-insecure` - Fall back to HTTP if HTTPS unavailable
- `-n, --namespace string` - Target namespace

**Server Address Requirements:**
- Must include scheme and hostname (and optionally port)
- Examples: `https://ghcr.io`, `https://10.221.188.5:30080`

**Examples:**
```bash
orka3 regcred add https://ghcr.io --username "$REGISTRY_USER" --password "$REGISTRY_TOKEN"
echo -n "$REGISTRY_TOKEN" | orka3 regcred add https://ghcr.io --username "$REGISTRY_USER" --password-stdin
orka3 regcred add --allow-insecure http://10.221.188.5:30080 --username "$REGISTRY_USER" --password "$REGISTRY_TOKEN"
orka3 regcred add --replace https://ghcr.io --username "$REGISTRY_USER" --password "$REGISTRY_TOKEN"
```

## orka3 registrycredential list (alias: regcred)

List OCI registry servers with stored credentials.

**Syntax:**
```bash
orka3 registrycredential list [--namespace <NS>] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json
- `-n, --namespace string` - Target namespace

## orka3 registrycredential remove (alias: regcred)

Remove authentication credentials for a registry server.

**Syntax:**
```bash
orka3 registrycredential remove <SERVER> [--namespace <NS>] [flags]
```

**Options:**
- `-n, --namespace string` - Target namespace
