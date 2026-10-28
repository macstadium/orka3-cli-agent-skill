# Administrative Workflows

This guide covers namespace management, RBAC configuration, and node organization.

## Contents
- [Multi-Namespace Team Setup](#multi-namespace-team-setup)
- [Node Affinity and Tagging Strategy](#node-affinity-and-tagging-strategy)
- [Node Maintenance (Drain)](#node-maintenance-drain)
- [Access Control Patterns](#access-control-patterns)
- [Namespace Lifecycle](#namespace-lifecycle)

## Multi-Namespace Team Setup

**Set up isolated namespaces for different teams:**

```bash
# As admin:

# 1. Create namespaces for teams
orka namespace create orka-dev-team
orka namespace create orka-qa-team
orka namespace create orka-prod

# 2. Dedicate nodes to each namespace
# Dev team gets 2 nodes
orka node namespace mini-arm-1 orka-dev-team
orka node namespace mini-arm-2 orka-dev-team

# QA team gets 2 nodes
orka node namespace mini-arm-3 orka-qa-team
orka node namespace mini-arm-4 orka-qa-team

# Production gets 4 nodes
orka node namespace mini-arm-5 orka-prod
orka node namespace mini-arm-6 orka-prod
orka node namespace mini-arm-7 orka-prod
orka node namespace mini-arm-8 orka-prod

# 3. Grant team members access
# Dev team
orka rbac add-subject --role dev --namespace orka-dev-team \
  --user dev1@company.com,dev2@company.com,dev3@company.com

# QA team
orka rbac add-subject --role dev --namespace orka-qa-team \
  --user qa1@company.com,qa2@company.com

# Production (admin only, plus service accounts)
# A service account automatically has access to the namespace it's created in
orka sa create sa-prod-deploy --namespace orka-prod

# 4. Verify setup
orka namespace list
orka rbac list-subjects --role dev --namespace orka-dev-team
orka rbac list-subjects --role dev --namespace orka-qa-team
orka rbac list-subjects --role dev --namespace orka-prod

# 5. Verify resources
orka node list --namespace orka-dev-team
orka node list --namespace orka-qa-team
orka node list --namespace orka-prod
```

## Node Affinity and Tagging Strategy

**Organize nodes for workload isolation:**

```bash
# 1. Tag nodes by hardware capability
orka node tag mac-studio-1 high-performance
orka node tag mac-studio-2 high-performance
orka node tag mini-m1-1 standard
orka node tag mini-m1-2 standard

# 2. Tag nodes by workload type
orka node tag mini-m1-3 ci-builds
orka node tag mini-m1-4 ci-builds
orka node tag mac-studio-1 rendering
orka node tag mac-studio-2 rendering

# 3. Create VM configs with node affinity
# Flexible affinity (will use tagged nodes if available, otherwise any node)
orka vmc create ci-vm \
  --image sonoma-ci \
  --cpu 4 \
  --tag ci-builds \
  --tag-required=false

# Strict affinity (ONLY uses tagged nodes)
orka vmc create render-vm \
  --image sonoma-render \
  --cpu 8 \
  --memory 16 \
  --tag rendering \
  --tag-required=true

# 4. Deploy and verify placement
orka vm deploy --config ci-vm
orka vm deploy --config render-vm

# 5. Check which nodes VMs landed on
orka vm list --output wide

# 6. View all node tags
orka node list --output wide

# 7. Remove tags when reconfiguring
orka node untag mini-m1-3 ci-builds
orka node untag mini-m1-4 ci-builds
```

## Node Maintenance (Drain)

Orka refuses to move a node to another namespace while VMs are running on it, so drain the node before moving it. Never move first and wait afterward.

```bash
# 1. Stop scheduling new work to the node
#    Remove its tag so tag-required configs stop targeting it, or let queued jobs finish
orka node untag <NODE_NAME> <TAG> --namespace <CURRENT_NAMESPACE>

# 2. Wait for running VMs on the node to finish, or delete them
orka vm list --namespace <CURRENT_NAMESPACE> -o json | \
  jq -r --arg node "<NODE_NAME>" '.[] | select(.node == $node) | .name'
orka vm delete <VM_NAME> --namespace <CURRENT_NAMESPACE>

# 3. Once no VMs remain on the node, move it
orka node namespace <NODE_NAME> --namespace <CURRENT_NAMESPACE> <TARGET_NAMESPACE>
```

If VMs are still running, step 3 fails with `cannot move node "<NODE>" to namespace "<NS>" because the node has running VMs. Please remove the VMs before attempting to move the node`. Node tags move with the node.

## Access Control Patterns

These examples use `orka rbac ... --role dev` (Orka 4.0+), which modifies the `orka-dev` rolebinding in one namespace. On Orka 3.6, use `orka3 rb add-subject|remove-subject|list-subjects --namespace <NS>` with the same `--user` and `--serviceaccount` flags and no `--role`. `rolebinding` still works on 4.0, but it's deprecated and hidden from `--help`.

### Grant User Access

```bash
# Single user
orka rbac add-subject --role dev --namespace orka-team --user user@company.com

# Multiple users
orka rbac add-subject --role dev --namespace orka-team --user user1@company.com,user2@company.com
```

### Grant Service Account Access

```bash
# Service accounts already have access to the namespace they were created in.
# Bind a service account only into other namespaces:
orka rbac add-subject --role dev --namespace orka-prod --serviceaccount orka-ci:sa-deploy
```

### Revoke Access

```bash
# Revoke user access
orka rbac remove-subject --role dev --namespace orka-team --user user@company.com

# Revoke service account access
orka rbac remove-subject --role dev --namespace orka-team --serviceaccount orka-ci:sa-deploy
```

### Audit Access

```bash
# List all subjects in namespace
orka rbac list-subjects --role dev --namespace orka-team

# Filter by type (kind is User, Group, or ServiceAccount)
orka rbac list-subjects --role dev --namespace orka-team -o json | jq '.[] | select(.kind=="User")'
orka rbac list-subjects --role dev --namespace orka-team -o json | jq '.[] | select(.kind=="ServiceAccount")'
```

## Namespace Lifecycle

### Creating Namespaces

```bash
# Standard namespace for VMs
orka namespace create orka-newteam

# Namespace for custom Kubernetes pods (no VMs)
orka namespace create orka-custom --enable-custom-pods
```

### Deleting Namespaces

Prerequisites before deletion:
1. Delete all VMs in namespace
2. Move all nodes to another namespace

```bash
# Check what's in namespace
orka vm list --namespace orka-oldteam
orka node list --namespace orka-oldteam

# Clean up VMs
orka vm delete <VM1> <VM2> --namespace orka-oldteam

# Move nodes back to default (refused while VMs are still running on them)
orka node namespace mini-arm-1 orka-default --namespace orka-oldteam

# Delete namespace
orka namespace delete orka-oldteam
```
