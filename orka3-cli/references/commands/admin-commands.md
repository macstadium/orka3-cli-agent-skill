# Admin Commands Reference

This reference provides detailed syntax and examples for administrative Orka3 CLI commands including namespace management, RBAC, and service accounts.

## Contents
- [Namespace Commands](#namespace-commands)
- [Service Account Commands](#service-account-commands)
- [RBAC Commands (orka3 rbac, Orka 4.0+)](#rbac-commands-orka3-rbac-orka-40)
- [RBAC Commands (Rolebinding, deprecated in Orka 4.0)](#rbac-commands-rolebinding-deprecated-in-orka-40)

## Namespace Commands

### orka3 namespace create

Create a new namespace.

**Syntax:**
```bash
orka3 namespace create <NAME> [--enable-custom-pods] [flags]
```

**Options:**
- `--enable-custom-pods` - Configure for custom K8s resources (cannot run Orka VMs)

**Name Requirements:**
- Begins with `orka-` prefix
- Max 63 characters (including prefix)
- Lowercase alphanumeric or dashes
- Ends with alphanumeric
- Unique to cluster

**Post-Creation Steps:**
1. Move nodes: `orka3 node namespace <NODE> <NAMESPACE>` (the command's help text points to `orka3 tag namespace`, which doesn't exist)
2. Grant access: `orka3 rb add-subject --namespace <NS> --user <EMAIL>`. New namespaces bind only the admin group; developers have no access until added

**Custom pods namespaces (`--enable-custom-pods`):**
- Each pod needs the toleration `{"key":"orka.macstadium.com/namespace-reserved","value":"<NS>"}`
- Custom pods can't run in `orka-default`
- Apple silicon nodes can't be moved into these namespaces

**Examples:**
```bash
orka3 namespace create orka-test
orka3 namespace create orka-cp --enable-custom-pods
```

**Note (fixed in 3.6.4):** On `--enable-custom-pods` namespaces created before 3.6.4, users added via `rb add-subject` may be missing the `orka-dev` role binding. See `references/troubleshooting/auth-issues.md`.

### orka3 namespace list

List all namespaces. Admin only.

**Syntax:**
```bash
orka3 namespace list [<NAME>] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json

### orka3 namespace delete

Delete specified namespaces.

**Syntax:**
```bash
orka3 namespace delete <NAME> [<NAME2> ...] [--timeout <DURATION>] [flags]
```

**Options:**
- `-t, --timeout duration` - Time to wait before giving up (default: 1h0m0s)

**Prerequisites:**
- All VMs/pods must be removed
- All nodes must be moved out

**CAUTION:** Destructive operation - cannot be undone.

## Service Account Commands

### orka3 serviceaccount create (alias: sa)

Create a service account in the specified namespace.

**Syntax:**
```bash
orka3 serviceaccount create <NAME> [--namespace <NS>] [flags]
```

**Options:**
- `-n, --namespace string` - Target namespace (default: "orka-default")
- `-h, --help` - Display help

**Name Requirements:**
- Max 253 characters
- Lowercase alphanumeric, dashes, or periods
- Begins and ends with lowercase alphanumeric
- Unique to namespace

### orka3 serviceaccount token (alias: sa)

Obtain an authentication token for a service account.

**Syntax:**
```bash
orka3 serviceaccount token <NAME> [--duration <DURATION>] [--namespace <NS>] [flags]
```

**Options:**
- `--duration duration` - Token lifetime (default: 8760h = 1 year)
- `--no-expiration` - Create token with no expiration
- `-n, --namespace string` - Target namespace (default: "orka-default")

**Examples:**
```bash
orka3 sa token sa-jenkins
orka3 sa token sa-jenkins --duration 1h
orka3 sa token sa-jenkins --no-expiration
```

**Notes:**
- The returned token's lifetime may be shorter or longer than `--duration`
- `--duration` and `--no-expiration` are mutually exclusive. Use `--no-expiration` on EKS, where the control plane caps token lifetime
- A service account automatically has access to the namespace it was created in, and can't be moved to another namespace
- Individual tokens can't be revoked; only `sa delete` revokes, and it revokes all of that account's tokens. Use one service account per consumer, and rotate by minting a new token on the same account
- `sa list` doesn't show token expiry
- New service accounts get developer (`orka-dev`) permissions in their namespace, not admin. There is no `orka3` command to add a user or service account to the `orka-admin` RoleBinding.

**Admin-privileged service accounts:**
- **Self-managed and Orka Anywhere on-prem:** you have cluster-level RBAC rights. Elevate a service account by editing the `orka-admin` RoleBinding directly with `kubectl`. Elevate a user by adding them to the admin OIDC group or editing the same RoleBinding.
- **MacStadium-hosted clusters:** customer admins can't modify the `orka-admin` RoleBinding or anything else in the `default` namespace. This is expected. For an admin service account (for example, to automate custom TLS certificate uploads to `/api/v1/upload/cert`), ask MacStadium support to enable the managed `orka-admin` service account. After that, any of your admins can mint a token with `orka3 sa token orka-admin`. No credentials are handed over.
- An `orka-admin` token can also create and delete service accounts, mint their tokens, and read or update registry credentials. Store it like any admin credential. If it's exposed, invalidate it by deleting and recreating the service account.

### orka3 serviceaccount list (alias: sa)

List service accounts in the specified namespace.

**Syntax:**
```bash
orka3 serviceaccount list [<NAME>] [--namespace <NS>] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json
- `-n, --namespace string` - Target namespace

### orka3 serviceaccount delete (alias: sa)

Delete one or more service accounts.

**Syntax:**
```bash
orka3 serviceaccount delete <NAME> [<NAME2> ...] [--namespace <NS>] [flags]
```

**CAUTION:** Deleting a service account invalidates all associated tokens.

## RBAC Commands (orka3 rbac, Orka 4.0+)

Requires Orka 4.0 or later. On earlier versions use the `orka3 rolebinding` commands below, which are deprecated as of 4.0 but still work.

Every `orka3 rbac` command requires administrative privileges and a `--role`:

- `--role dev` modifies the `orka-dev` rolebinding in a single namespace. Use `--namespace` to choose it; defaults to your default namespace.
- `--role admin` is cluster-wide. Subjects are added to or removed from every rolebinding and cluster rolebinding granting the admin role to its OIDC group, so `--namespace` is not valid with `--role admin`.

### orka3 rbac add-subject

Grant a role to one or more users and/or service accounts.

**Syntax:**
```bash
orka3 rbac add-subject --role admin|dev [--namespace <NS>] --user <EMAIL>[,<EMAIL2>,...] AND/OR --serviceaccount <SA_NS>:<SA_NAME>[,...] [flags]
```

**Options:**
- `-r, --role string` - The role to grant: `admin` or `dev`
- `-n, --namespace string` - (Optional) With `--role dev`, the namespace whose `orka-dev` rolebinding is modified. Not valid with `--role admin`.
- `-u, --user strings` - Users (email addresses, comma-separated)
- `-s, --serviceaccount strings` - Service accounts (`NAMESPACE:SERVICE_ACCOUNT`, comma-separated)

**Examples:**
```bash
orka3 rbac add-subject --role admin --serviceaccount orka-default:sa-jenkins
orka3 rbac add-subject --role admin --user user@company.com
orka3 rbac add-subject --role dev --namespace orka-test --user user@company.com
orka3 rbac add-subject --role admin --user user1@company.com,user2@company.com --serviceaccount orka-default:sa-jenkins
```

**Notes:**
- Admin grants apply only to the admin bindings that exist at grant time. Bindings created later, for example when you create a namespace, start without the granted subjects. Re-run after creating namespaces. Safe to run more than once.

### orka3 rbac list-subjects

List the subjects currently granted a role. With `--role admin`, the list combines subjects from every binding granting the admin role, without duplicates.

**Syntax:**
```bash
orka3 rbac list-subjects --role admin|dev [--namespace <NS>] [--output wide|json] [flags]
```

**Examples:**
```bash
orka3 rbac list-subjects --role admin
orka3 rbac list-subjects --role dev --namespace orka-test
```

### orka3 rbac remove-subject

Revoke a role from one or more users and/or service accounts. Same flags as `add-subject`.

**Examples:**
```bash
orka3 rbac remove-subject --role admin --user user@company.com
orka3 rbac remove-subject --role dev --namespace orka-test --serviceaccount orka-default:sa-jenkins
```

## RBAC Commands (Rolebinding, deprecated in Orka 4.0)

Deprecated as of Orka 4.0 in favour of `orka3 rbac ... --role dev`. They still work and behave the same. The `/api/v1/namespaces/{namespace}/rolebindings/orka-dev/subjects` routes are deprecated alongside them, replaced by `/api/v1/rbac`.

| Deprecated | Replacement |
|---|---|
| `orka3 rolebinding add-subject` | `orka3 rbac add-subject --role dev` |
| `orka3 rolebinding list-subjects` | `orka3 rbac list-subjects --role dev` |
| `orka3 rolebinding remove-subject` | `orka3 rbac remove-subject --role dev` |


### orka3 rolebinding add-subject (alias: rb)

Add a subject to a namespace rolebinding (grant access).

**Syntax:**
```bash
orka3 rolebinding add-subject --namespace <NS> --user <EMAIL>[,<EMAIL2>,...] AND/OR --serviceaccount <SA_NS>:<SA_NAME>[,<SA_NS2>:<SA_NAME2>,...] [flags]
```

**Options:**
- `-u, --user strings` - Users (email addresses, comma-separated)
- `-s, --serviceaccount strings` - Service accounts (NAMESPACE:NAME format, comma-separated)
- `-n, --namespace string` - Target namespace (default: "orka-default")

**Examples:**
```bash
orka3 rb add-subject --namespace orka-test --user user@company.com
orka3 rb add-subject --namespace orka-test --user user1@company.com,user2@company.com
orka3 rb add-subject --namespace orka-test --serviceaccount orka-default:sa-jenkins
orka3 rb add-subject --namespace orka-test --serviceaccount orka-default:sa-jenkins,orka-production:sa-release
orka3 rb add-subject --namespace orka-test --user user@company.com --serviceaccount orka-default:sa-jenkins
```

### orka3 rolebinding list-subjects (alias: rb)

List all rolebinding subjects in a namespace.

**Syntax:**
```bash
orka3 rolebinding list-subjects [--namespace <NS>] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json
- `-n, --namespace string` - Target namespace (default: "orka-default")

**Examples:**
```bash
orka3 rb list-subjects
orka3 rb list-subjects --namespace orka-test
orka3 rb list-subjects -o json | jq '.[] | select(.kind=="ServiceAccount")'
```

**Notes:**
- `-o json` returns `[{"kind": "User"|"Group"|"ServiceAccount", "name": ...}]`. Service account subjects are named `<NS>:<SA>`
- `orka-default` carries the groups `oidc:Administrator` and `oidc:Technical` by default

### orka3 rolebinding remove-subject (alias: rb)

Remove a subject from a namespace rolebinding (revoke access).

**Syntax:**
```bash
orka3 rolebinding remove-subject --user <EMAIL>[,<EMAIL2>,...] AND/OR --serviceaccount <SA_NS>:<SA_NAME>[,<SA_NS2>:<SA_NAME2>,...] [--namespace <NS>] [flags]
```

**Options:**
- `-u, --user strings` - Users to remove (email addresses, comma-separated)
- `-s, --serviceaccount strings` - Service accounts to remove (NAMESPACE:NAME format, comma-separated)
- `-n, --namespace string` - Target namespace (default: "orka-default")

**Examples:**
```bash
orka3 rb remove-subject --namespace orka-test --user user@company.com
orka3 rb remove-subject --namespace orka-test --user user1@company.com,user2@company.com
orka3 rb remove-subject --namespace orka-test --serviceaccount orka-default:sa-jenkins
orka3 rb remove-subject --namespace orka-test --user user@company.com --serviceaccount orka-default:sa-jenkins
```
