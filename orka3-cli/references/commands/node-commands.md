# Node Commands Reference

This reference provides detailed syntax and examples for node-related Orka3 CLI commands.

## orka3 node list

Show information about Orka nodes.

**Syntax:**
```bash
orka3 node list [<NAME>] [--namespace <NS>] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json
- `-n, --namespace string` - Target namespace

**Examples:**
```bash
orka3 node list
orka3 node list --output wide
orka3 node list mini-1
orka3 node list --namespace orka-test
orka3 node list mini-arm -o wide
```

## orka3 node tag (Admin)

Tag a node for targeted VM deployment (set node affinity).

**Syntax:**
```bash
orka3 node tag <NODE_NAME> <TAG> [--namespace <NS>] [flags]
```

**Tag Requirements:**
- Max 63 characters
- Alphanumeric, dashes, underscores, or periods
- Begins and ends with alphanumeric
- One tag at a time

**Examples:**
```bash
orka3 node tag mini-1 jenkins
orka3 node tag mini-1 jenkins --namespace orka-test
orka3 node list mini-1 --output wide  # Verify tag
```

## orka3 node untag (Admin)

Remove a tag from a node.

**Syntax:**
```bash
orka3 node untag <NODE_NAME> <TAG> [--namespace <NS>] [flags]
```

**Examples:**
```bash
orka3 node untag mini-1 my-tag
orka3 node untag mini-1 my-tag --namespace orka-test
```

## orka3 node namespace (Admin)

Move Orka nodes across namespaces.

**Syntax:**
```bash
orka3 node namespace <NODE> [--namespace <CURRENT_NS>] <TARGET_NS> [flags]
```

**Options:**
- `-n, --namespace string` - Current namespace (default: "orka-default")

**Examples:**
```bash
orka3 node namespace mini-1 orka-test
orka3 node namespace mini-1 --namespace orka-test orka-production
orka3 node namespace mini-1 --namespace orka-production orka-default
```
