# Upgrade Commands Reference

This reference provides syntax and examples for the `orka upgrade` commands (`orka3 upgrade` on 3.6), which drive Upgrade Service. For the upgrade process, health checks before a run, the 4.0 upgrade path, and troubleshooting, see `references/workflows/upgrade-workflows.md`.

`upgrade versions`, `upgrade status`, `upgrade run`, and `upgrade service status` print a single JSON object with `-o json`, not an array.

## orka upgrade run (Admin)

Start an upgrade by creating a run for the target release. Run names are timestamped, so retries never collide; a failed run stays in history, and a new run is the retry.

**Syntax:**
```bash
orka upgrade run --version <VERSION> [flags]
```

**Options:**
- `--version string` - Target Orka release, for example `3.6.4`, or `latest` (resolved once when the run is created)
- `-o, --output string` - Output format: table|json

**Examples:**
```bash
orka upgrade run --version 3.6.4
orka upgrade run --version latest
```

**Notes:**
- Upgrade Service doesn't perform the 3.6 to 4.0 upgrade. That upgrade is support-led; see "Upgrading to Orka 4.0" in `references/workflows/upgrade-workflows.md`

## orka upgrade versions

Show the current cluster release (from the `orka-cluster-version` ConfigMap) and any active upgrade run.

**Syntax:**
```bash
orka upgrade versions [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json

**Examples:**
```bash
orka upgrade versions
```

**Notes:**
- Reports `unknown` until the cluster completes its first successful Upgrade Service v2 run

## orka upgrade status

Show the step list and per-node counts of the latest run, or of the named run.

**Syntax:**
```bash
orka upgrade status [<RUN_NAME>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json

**Examples:**
```bash
orka upgrade status
orka upgrade status upgrade-3-6-4-20261102-140501
orka upgrade status upgrade-3-6-4-20261102-140501 -o json  # Per-node skip reasons
```

## orka upgrade history

List retained runs, newest first: target, source version, phase, duration, and age.

**Syntax:**
```bash
orka upgrade history [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json

**Examples:**
```bash
orka upgrade history
```

## orka upgrade service status

Show Upgrade Service's operator version and status.

**Syntax:**
```bash
orka upgrade service status [--namespace <NS>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|json
- `-n, --namespace string` - Namespace of the OrkaNodes to inspect (default: "orka-default")

**Examples:**
```bash
orka upgrade service status
```

**Notes:**
- `--namespace` always defaults to `orka-default`. `orka upgrade service` ignores `ORKA_DEFAULT_NAMESPACE` and the kubeconfig context

## orka upgrade service agents

List the per-node upgrade agents: name, installed version, status, and lease age. Unhealthy agents (`MISSING`, `STALE`) are listed first.

**Syntax:**
```bash
orka upgrade service agents [--namespace <NS>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json
- `-n, --namespace string` - Namespace of the OrkaNodes to inspect (default: "orka-default")

**Examples:**
```bash
orka upgrade service agents
orka upgrade service agents -n orka-test
orka upgrade service agents -o json
```

**Notes:**
- Lists one namespace at a time. Run it for every namespace that has nodes before starting a run
