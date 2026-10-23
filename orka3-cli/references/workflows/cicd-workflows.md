# CI/CD Pipeline Workflows

This guide covers setting up service accounts and CI/CD pipelines with Orka3.

## Contents
- [CI/CD Pipeline Setup](#cicd-pipeline-setup)
- [CI/CD Pipeline Commands](#cicd-pipeline-commands)
- [Capacity and Concurrency Limits](#capacity-and-concurrency-limits)
- [Cleaning Up Leaked VMs](#cleaning-up-leaked-vms)
- [Smoke Test a New Integration](#smoke-test-a-new-integration)
- [Service Account Token Options](#service-account-token-options)
- [Best Practices for CI/CD](#best-practices-for-cicd)
- [Multiple Pipeline Setup](#multiple-pipeline-setup)

## CI/CD Pipeline Setup

**Set up service account for Jenkins/GitHub Actions/GitLab:**

```bash
# 1. Create service account (admin)
orka3 sa create sa-ci-pipeline

# 2. Get long-lived token (1 year)
orka3 sa token sa-ci-pipeline

# 3. (Optional) Create namespace for CI workloads
orka3 namespace create orka-ci

# 4. Move dedicated nodes to CI namespace
orka3 node namespace mini-arm-10 orka-ci
orka3 node namespace mini-arm-11 orka-ci

# 5. Grant service account access to CI namespace
orka3 rb add-subject --namespace orka-ci --serviceaccount orka-default:sa-ci-pipeline

# 6. Create VM config for consistent builds
#    (VM configs always live in orka-default and have no --namespace flag;
#    the namespace is chosen at deploy time)
orka3 vmc create ci-build \
  --image ghcr.io/macstadium/orka-images/sonoma:latest \
  --cpu 4 \
  --memory 8

# 7. Tag nodes for specific workload types (optional)
orka3 node tag mini-arm-10 fast-builds --namespace orka-ci
orka3 node tag mini-arm-11 integration-tests --namespace orka-ci

# 8. Create tagged VM configs
orka3 vmc create fast-build \
  --image sonoma:latest \
  --cpu 6 \
  --tag fast-builds \
  --tag-required
```

## CI/CD Pipeline Commands

**In your CI script:**

```bash
# Authenticate with service account token (stored as a CI secret)
orka3 user set-token "$SA_TOKEN"

NS=orka-ci

# Pick the VM name before deploying and arm cleanup first, so an interrupted
# or failed deploy still gets deleted
VM="ci-build-$(date +%s)-$RANDOM"
trap 'orka3 vm delete "$VM" -n "$NS"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Deploy VM for build (-o json returns an array)
orka3 vm deploy "$VM" --config ci-build -n "$NS" -o json > vm.json
VM_IP=$(jq -r '.[0].ip' vm.json)
VM_SSH_PORT=$(jq -r '.[0].ssh' vm.json)

# vm deploy returns when the VM is Running, not when macOS has booted: wait for SSH
for i in $(seq 1 60); do nc -z "$VM_IP" "$VM_SSH_PORT" && break; sleep 5; done

# Run your build (via SSH)
ssh -p "$VM_SSH_PORT" admin@"$VM_IP" 'cd /path/to/project && make test'

# Cleanup runs from the EXIT trap
```

**Retries:** retry a failed deploy only for capacity or timeout errors (for example `The maximum supported number of Apple silicon VMs has been reached.` or a deploy timeout). Never retry auth, naming, or image-not-found errors: they fail the same way every time.

**Traps aren't enough on their own.** SIGKILL and lost network connections skip the trap, so run a periodic cleanup as a backstop (see [Cleaning Up Leaked VMs](#cleaning-up-leaked-vms)).

## Capacity and Concurrency Limits

Apple silicon nodes run at most 2 VMs each. Set the integration's concurrency limit at or below 2 x the Apple silicon nodes in the target namespace, otherwise extra jobs fail at deploy instead of queueing in the CI system:

| Integration | Setting |
|-------------|---------|
| GitHub Actions | `MAX_RUNNERS` |
| Jenkins | Max Jenkins Agents Limit |
| GitLab | `concurrent` / `limit` in `config.toml` |
| Buildkite | Number of proxy agent containers |

## Cleaning Up Leaked VMs

`orka3 vm list <NAME>` matches exact names only, so select leaked VMs by name prefix or `owner` and age with `-o json | jq`:

```bash
# VMs older than 4 hours whose names start with the integration's prefix
orka3 vm list -n <NAMESPACE> -o json | jq -r --arg prefix "<PREFIX>" --argjson max_age 14400 \
  '.[] | select(.name | startswith($prefix))
       | select((now - (.deployDate | fromdateiso8601)) > $max_age) | .name'

# Or select by the deploying identity (one service account per integration)
orka3 vm list -n <NAMESPACE> -o json | jq -r \
  '.[] | select(.owner == "system:serviceaccount:<NAMESPACE>:<SA_NAME>") | .name'

# Delete each VM the query returned
orka3 vm delete <VM_NAME> -n <NAMESPACE>
```

**Rules for cleanup jobs:**
- Set the age threshold to at least 2x the longest job and at least 2x the integration's own reconciliation interval. Never delete ahead of the integration's own cleanup.
- Exclude permanent agents and long-lived VMs.
- Always pass `-n`.

**VM names by integration:**

| Integration | VM name |
|-------------|---------|
| GitLab | `gl-runner` prefix (`ORKA_VM_NAME_PREFIX`) |
| Buildkite | `buildkite-agent` prefix |
| Packer | `packer-<TIMESTAMP>` unless `orka_vm_builder_prefix` is set |
| GitHub Actions | `<RUNNERS[].name>-<RANDOM>`. There's no prefix setting, so give your runner scale sets a recognizable name prefix |

## Smoke Test a New Integration

After wiring up an integration, run a one-step job that prints the macOS and Xcode versions:

```bash
sw_vers && xcodebuild -version
```

While the job runs and after it finishes, watch the namespace to confirm the VM appeared and was then deleted:

```bash
orka3 vm list -n <NAMESPACE> -o wide
```

## Service Account Token Options

```bash
# Default: 1 year expiration
orka3 sa token sa-jenkins

# Custom duration
orka3 sa token sa-jenkins --duration 1h
orka3 sa token sa-jenkins --duration 24h
orka3 sa token sa-jenkins --duration 8760h  # 1 year

# No expiration (for long-lived automation)
orka3 sa token sa-jenkins --no-expiration
```

## Best Practices for CI/CD

1. **Use service accounts, not user credentials** - User tokens expire in 1 hour
2. **Create dedicated namespaces** - Isolate CI workloads from other environments
3. **Use VM configs** - Ensure consistent build environments
4. **Tag nodes** - Route different workloads to appropriate hardware
5. **Generate unique names** - Use `--generate-name` to avoid conflicts
6. **Clean up after builds** - Always delete VMs when done
7. **Cache images** - Pre-cache images on CI nodes for faster deployments

## Multiple Pipeline Setup

For organizations with multiple CI/CD pipelines:

```bash
# Create service accounts per pipeline
orka3 sa create sa-jenkins --namespace orka-ci
orka3 sa create sa-github-actions --namespace orka-ci
orka3 sa create sa-gitlab-runner --namespace orka-ci

# Service accounts get access to the namespace they were created in automatically.
# Bind them only into other namespaces they need, for example:
orka3 rb add-subject --namespace <OTHER_NAMESPACE> --serviceaccount orka-ci:sa-jenkins

# Create different VM configs per workload type
orka3 vmc create unit-tests --image sonoma:latest --cpu 4 --memory 8
orka3 vmc create integration-tests --image sonoma:latest --cpu 6 --memory 12
orka3 vmc create ui-tests --image sonoma:latest --cpu 4 --memory 16
```
