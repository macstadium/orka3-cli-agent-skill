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
# A service account automatically has access to the namespace it's created in
orka3 sa create sa-prod-deploy --namespace orka-prod

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

## Node Maintenance (Drain)

Orka refuses to move a node to another namespace while VMs are running on it, so drain the node before moving it. Never move first and wait afterward.

```bash
# 1. Stop scheduling new work to the node
#    Remove its tag so tag-required configs stop targeting it, or let queued jobs finish
orka3 node untag <NODE_NAME> <TAG> --namespace <CURRENT_NAMESPACE>

# 2. Wait for running VMs on the node to finish, or delete them
orka3 vm list --namespace <CURRENT_NAMESPACE> -o json | \
  jq -r --arg node "<NODE_NAME>" '.[] | select(.node == $node) | .name'
orka3 vm delete <VM_NAME> --namespace <CURRENT_NAMESPACE>

# 3. Once no VMs remain on the node, move it
orka3 node namespace <NODE_NAME> --namespace <CURRENT_NAMESPACE> <TARGET_NAMESPACE>
```

If VMs are still running, step 3 fails with `cannot move node "<NODE>" to namespace "<NS>" because the node has running VMs. Please remove the VMs before attempting to move the node`. Node tags move with the node.

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
# Service accounts already have access to the namespace they were created in.
# Bind a service account only into other namespaces:
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

# Filter by type (kind is User, Group, or ServiceAccount)
orka3 rb list-subjects --namespace orka-team -o json | jq '.[] | select(.kind=="User")'
orka3 rb list-subjects --namespace orka-team -o json | jq '.[] | select(.kind=="ServiceAccount")'
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

# Move nodes back to default (refused while VMs are still running on them)
orka3 node namespace mini-arm-1 orka-default --namespace orka-oldteam

# Delete namespace
orka3 namespace delete orka-oldteam
```
