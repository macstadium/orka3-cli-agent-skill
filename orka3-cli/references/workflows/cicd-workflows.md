# CI/CD Pipeline Workflows

This guide covers setting up service accounts and CI/CD pipelines with Orka3.

## Contents
- [CI/CD Pipeline Setup](#cicd-pipeline-setup)
- [CI/CD Pipeline Commands](#cicd-pipeline-commands)
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
orka3 vmc create ci-build \
  --image ghcr.io/macstadium/orka-images/sonoma:latest \
  --cpu 4 \
  --memory 8 \
  --namespace orka-ci

# 7. Tag nodes for specific workload types (optional)
orka3 node tag mini-arm-10 fast-builds --namespace orka-ci
orka3 node tag mini-arm-11 integration-tests --namespace orka-ci

# 8. Create tagged VM configs
orka3 vmc create fast-build \
  --image sonoma:latest \
  --cpu 6 \
  --tag fast-builds \
  --tag-required \
  --namespace orka-ci
```

## CI/CD Pipeline Commands

**In your CI script:**

```bash
# Authenticate with service account token
orka3 user set-token $SA_TOKEN

# Deploy VM for build
VM_NAME=$(orka3 vm deploy --config ci-build --namespace orka-ci --generate-name -o json | jq -r '.name')

# Get VM connection info
VM_INFO=$(orka3 vm list $VM_NAME --namespace orka-ci -o json)
VM_IP=$(echo $VM_INFO | jq -r '.[0].ip')
VM_SSH_PORT=$(echo $VM_INFO | jq -r '.[0].ssh')

# Run your build (via SSH)
ssh -p $VM_SSH_PORT admin@$VM_IP 'cd /path/to/project && make test'

# Clean up
orka3 vm delete $VM_NAME --namespace orka-ci
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

# Grant access to each
orka3 rb add-subject --namespace orka-ci --serviceaccount orka-ci:sa-jenkins
orka3 rb add-subject --namespace orka-ci --serviceaccount orka-ci:sa-github-actions
orka3 rb add-subject --namespace orka-ci --serviceaccount orka-ci:sa-gitlab-runner

# Create different VM configs per workload type
orka3 vmc create unit-tests --image sonoma:latest --cpu 4 --memory 8
orka3 vmc create integration-tests --image sonoma:latest --cpu 6 --memory 12
orka3 vmc create ui-tests --image sonoma:latest --cpu 4 --memory 16
```
