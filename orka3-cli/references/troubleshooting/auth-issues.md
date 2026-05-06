# Authentication Troubleshooting

This guide covers common authentication and access control issues with the Orka3 CLI.

## Contents
- [Token Expiration Reference](#token-expiration-reference)
- [Problem: "Authentication token expired"](#problem-authentication-token-expired)
- [Problem: "Unable to connect to Orka cluster"](#problem-unable-to-connect-to-orka-cluster)
- [Problem: "Forbidden" or "Insufficient permissions"](#problem-forbidden-or-insufficient-permissions)
- [Problem: Cannot create namespace / admin commands fail](#problem-cannot-create-namespace--admin-commands-fail)
- [Problem: Service account token not working](#problem-service-account-token-not-working)
- [Best Practices for Authentication](#best-practices-for-authentication)

## Token Expiration Reference

| Token Type | Default Expiration | Configurable |
|------------|-------------------|--------------|
| User login | 1 hour | No |
| Service account | 1 year (8760h) | Yes |
| Service account (no expiration) | Never | Yes |

## Problem: "Authentication token expired"

**Symptoms:**
- Commands fail with authentication error
- "Token expired" message

**Solutions:**
```bash
# 1. Re-authenticate
orka3 login

# 2. For service accounts, generate new token
orka3 sa token <SERVICE_ACCOUNT_NAME>

# 3. Set new token
orka3 user set-token <NEW_TOKEN>

# 4. Verify authentication
orka3 node list
```

**Prevention:**
- User tokens expire after 1 hour
- Service account tokens expire after their configured duration (default: 1 year)
- For long-running automation, use service accounts with long-lived tokens

## Problem: "Unable to connect to Orka cluster"

**Symptoms:**
- Connection timeout
- "Connection refused" errors
- "No route to host"

**Diagnosis:**
```bash
# 1. Check CLI configuration
orka3 config view

# 2. Verify VPN connection
# Ensure you're connected to cluster VPN

# 3. Test connectivity
curl -s -o /dev/null -w "%{http_code}" "$ORKA_API_URL/api/v1/cluster-info"

# 4. Check firewall rules
```

**Solutions:**
```bash
# 1. Verify API URL is correct
orka3 config set --api-url http://10.221.188.20  # Orka 2.1+
# OR
orka3 config set --api-url http://10.221.188.100  # Pre-2.1
# OR
orka3 config set --api-url https://company.orka.app  # Domain

# 2. Ensure VPN is connected
# Check your VPN client

# 3. Contact MacStadium support if issues persist
```

## Problem: "Forbidden" or "Insufficient permissions"

**Symptoms:**
- 403 Forbidden errors
- "User does not have permission" messages

**Diagnosis:**
```bash
# Check which namespaces you have access to
orka3 namespace list

# Try operations in orka-default (all users have access)
orka3 vm list --namespace orka-default
```

**Solutions:**
```bash
# Ask admin to grant access to required namespace
# Admin runs:
orka3 rb add-subject --namespace <TARGET_NAMESPACE> --user <YOUR_EMAIL>

# For service accounts:
orka3 rb add-subject --namespace <TARGET_NAMESPACE> \
  --serviceaccount <SA_NAMESPACE>:<SA_NAME>
```

## Problem: Cannot create namespace / admin commands fail

**Symptoms:**
- "Requires administrative privileges"
- "Forbidden" on admin operations

**Cause:**
Only admin users can perform certain operations:
- Create/delete namespaces
- Create/delete service accounts
- Manage rolebindings
- Tag/untag nodes
- Move nodes between namespaces
- Manage OCI registry credentials

**Solutions:**
```bash
# These operations require the Orka admin role.
# Admin role is assigned at the cluster level by MacStadium during provisioning.
# To check if you have admin access:
orka3 namespace list    # Admins see all namespaces; non-admins see only granted ones

# If you need admin access:
# - Contact MacStadium support (support@macstadium.com) to modify role assignments
# - Or have an existing admin delegate specific tasks via service accounts
```

## Problem: Service account token not working

**Symptoms:**
- "Invalid token"
- "Token not found"

**Diagnosis:**
```bash
# Check if service account exists
orka3 sa list --namespace <SA_NAMESPACE>

# Verify token hasn't expired
# (Check when token was generated)
```

**Solutions:**
```bash
# Generate new token
orka3 sa token <SERVICE_ACCOUNT_NAME> --namespace <SA_NAMESPACE>

# For automation, use no-expiration tokens
orka3 sa token <SA_NAME> --no-expiration

# If service account was deleted, create new one
orka3 sa create <SA_NAME> --namespace <NAMESPACE>
orka3 sa token <SA_NAME> --namespace <NAMESPACE>
```

## Best Practices for Authentication

1. **Use service accounts for automation** - Never use user credentials in CI/CD
2. **Set appropriate token durations** - Balance security vs. convenience
3. **Regularly rotate tokens** - Even long-lived tokens should be rotated periodically
4. **Use no-expiration tokens carefully** - Only for trusted, long-running automation
5. **Document service account purposes** - Track which SA is used where
