# Node Commands Reference

This reference provides detailed syntax and examples for node-related Orka CLI commands.

## orka node list

Show information about Orka nodes.

**Syntax:**
```bash
orka node list [<NAME>] [--namespace <NS>] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json
- `-n, --namespace string` - Target namespace

**Examples:**
```bash
orka node list
orka node list --output wide
orka node list mini-1
orka node list --namespace orka-test
orka node list mini-arm -o wide
```

**Notes:**
- JSON keys: `name`, `ip`, `status` (`READY`/`NOT READY`), `architecture`, `tags`, `allocatableCpu`, `availableCpu`, `allocatableMemory`, `availableMemory`, `runtime`, `version`. Capacity used = allocatable - available
- A node cordoned in Kubernetes (`SchedulingDisabled`) still shows `READY` with free capacity here, and deploys to it fail with generic errors (see `references/troubleshooting/deployment-issues.md`). Admins with kubectl access can see it in `kubectl get nodes`

```bash
orka node list -o json | jq -r '.[] | "\(.name) \(.allocatableCpu - .availableCpu)/\(.allocatableCpu) CPU used"'
```

## orka node tag (Admin)

Tag a node for targeted VM deployment (set node affinity).

**Syntax:**
```bash
orka node tag <NODE_NAME> <TAG> [--namespace <NS>] [flags]
```

**Tag Requirements:**
- Max 63 characters
- Alphanumeric, dashes, underscores, or periods
- Begins and ends with alphanumeric
- One tag at a time

**Examples:**
```bash
orka node tag mini-1 jenkins
orka node tag mini-1 jenkins --namespace orka-test
orka node list mini-1 --output wide  # Verify tag
```

## orka node untag (Admin)

Remove a tag from a node.

**Syntax:**
```bash
orka node untag <NODE_NAME> <TAG> [--namespace <NS>] [flags]
```

**Examples:**
```bash
orka node untag mini-1 my-tag
orka node untag mini-1 my-tag --namespace orka-test
```

## orka node namespace (Admin)

Move Orka nodes across namespaces.

**Syntax:**
```bash
orka node namespace <NODE> [--namespace <CURRENT_NS>] <TARGET_NS> [flags]
```

**Options:**
- `-n, --namespace string` - Current namespace (default: "orka-default")

**Examples:**
```bash
orka node namespace mini-1 orka-test
orka node namespace mini-1 --namespace orka-test orka-production
orka node namespace mini-1 --namespace orka-production orka-default
```

**Notes:**
- Refused while VMs are running on the node: `cannot move node "<NODE>" to namespace "<NS>" because the node has running VMs. Please remove the VMs before attempting to move the node`. Drain first (wait for or delete the VMs), then move
- Apple silicon nodes can't be moved into a namespace created with `--enable-custom-pods` (`arm nodes cannot be moved to namespaces with custom pods enabled`)
- Node tags travel with the node
