# Administrative Workflows

This guide covers namespace management, RBAC configuration, and node organization.

## Contents
- [Multi-Namespace Team Setup](#multi-namespace-team-setup)
- [Node Affinity and Tagging Strategy](#node-affinity-and-tagging-strategy)
- [Access Control Patterns](#access-control-patterns)
- [Namespace Lifecycle](#namespace-lifecycle)

## Multi-Namespace Team Setup

**Set up isolated namespaces for different teams:**

```bash
# As admin:

# 1. Create namespaces for teams
orka3 namespace create orka-dev-team
orka3 namespace create orka-qa-team
orka3 namespace create orka-prod

# 2. Dedicate nodes to each namespace
# Dev team gets 2 nodes
orka3 node namespace mini-arm-1 orka-dev-team
orka3 node namespace mini-arm-2 orka-dev-team

# QA team gets 2 nodes
orka3 node namespace mini-arm-3 orka-qa-team
orka3 node namespace mini-arm-4 orka-qa-team

# Production gets 4 nodes
orka3 node namespace mini-arm-5 orka-prod
orka3 node namespace mini-arm-6 orka-prod
orka3 node namespace mini-arm-7 orka-prod
orka3 node namespace mini-arm-8 orka-prod

# 3. Grant team members access
# Dev team
orka3 rb add-subject --namespace orka-dev-team \
  --user dev1@company.com,dev2@company.com,dev3@company.com

# QA team
orka3 rb add-subject --namespace orka-qa-team \
  --user qa1@company.com,qa2@company.com

# Production (admin only, plus service accounts)
orka3 sa create sa-prod-deploy --namespace orka-prod
orka3 rb add-subject --namespace orka-prod \
  --serviceaccount orka-prod:sa-prod-deploy

# 4. Verify setup
orka3 namespace list
orka3 rb list-subjects --namespace orka-dev-team
orka3 rb list-subjects --namespace orka-qa-team
orka3 rb list-subjects --namespace orka-prod

# 5. Verify resources
orka3 node list --namespace orka-dev-team
orka3 node list --namespace orka-qa-team
orka3 node list --namespace orka-prod
```

## Node Affinity and Tagging Strategy

**Organize nodes for workload isolation:**

```bash
# 1. Tag nodes by hardware capability
orka3 node tag mac-studio-1 high-performance
orka3 node tag mac-studio-2 high-performance
orka3 node tag mini-m1-1 standard
orka3 node tag mini-m1-2 standard

# 2. Tag nodes by workload type
orka3 node tag mini-m1-3 ci-builds
orka3 node tag mini-m1-4 ci-builds
orka3 node tag mac-studio-1 rendering
orka3 node tag mac-studio-2 rendering

# 3. Create VM configs with node affinity
# Flexible affinity (will use tagged nodes if available, otherwise any node)
orka3 vmc create ci-vm \
  --image sonoma-ci \
  --cpu 4 \
  --tag ci-builds \
  --tag-required=false

# Strict affinity (ONLY uses tagged nodes)
orka3 vmc create render-vm \
  --image sonoma-render \
  --cpu 8 \
  --memory 16 \
  --tag rendering \
  --tag-required=true

# 4. Deploy and verify placement
orka3 vm deploy --config ci-vm
orka3 vm deploy --config render-vm

# 5. Check which nodes VMs landed on
orka3 vm list --output wide

# 6. View all node tags
orka3 node list --output wide

# 7. Remove tags when reconfiguring
orka3 node untag mini-m1-3 ci-builds
orka3 node untag mini-m1-4 ci-builds
```

## Access Control Patterns

### Grant User Access

```bash
# Single user
orka3 rb add-subject --namespace orka-team --user user@company.com

# Multiple users
orka3 rb add-subject --namespace orka-team --user user1@company.com,user2@company.com
```

### Grant Service Account Access

```bash
# Service account from same namespace
orka3 rb add-subject --namespace orka-team --serviceaccount orka-team:sa-builds

# Service account from different namespace
orka3 rb add-subject --namespace orka-prod --serviceaccount orka-ci:sa-deploy
```

### Revoke Access

```bash
# Revoke user access
orka3 rb remove-subject --namespace orka-team --user user@company.com

# Revoke service account access
orka3 rb remove-subject --namespace orka-team --serviceaccount orka-ci:sa-deploy
```

### Audit Access

```bash
# List all subjects in namespace
orka3 rb list-subjects --namespace orka-team

# Filter by type
orka3 rb list-subjects --namespace orka-team | grep 'User'
orka3 rb list-subjects --namespace orka-team | grep 'ServiceAccount'
```

## Namespace Lifecycle

### Creating Namespaces

```bash
# Standard namespace for VMs
orka3 namespace create orka-newteam

# Namespace for custom Kubernetes pods (no VMs)
orka3 namespace create orka-custom --enable-custom-pods
```

### Deleting Namespaces

Prerequisites before deletion:
1. Delete all VMs in namespace
2. Move all nodes to another namespace

```bash
# Check what's in namespace
orka3 vm list --namespace orka-oldteam
orka3 node list --namespace orka-oldteam

# Clean up VMs
orka3 vm delete <VM1> <VM2> --namespace orka-oldteam

# Move nodes back to default
orka3 node namespace mini-arm-1 orka-default --namespace orka-oldteam

# Delete namespace
orka3 namespace delete orka-oldteam
```
