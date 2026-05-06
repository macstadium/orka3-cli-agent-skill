# Network and Connectivity Troubleshooting

This guide covers common network and connectivity issues with Orka3 VMs.

## Contents
- [Problem: Cannot connect to VM via Screen Sharing](#problem-cannot-connect-to-vm-via-screen-sharing)
- [Problem: Cannot connect via SSH](#problem-cannot-connect-via-ssh)
- [Problem: Port conflicts](#problem-port-conflicts)
- [Problem: VM is slow/unresponsive during use](#problem-vm-is-slowunresponsive-during-use)
- [Problem: VM deployments are very slow](#problem-vm-deployments-are-very-slow)
- [Default Credentials](#default-credentials)
- [Common Ports](#common-ports)
- [Getting Help](#getting-help)

## Problem: Cannot connect to VM via Screen Sharing

**Symptoms:**
- Connection timeout
- "Connection refused"
- Authentication fails

**Diagnosis:**
```bash
# 1. Get VM connection info
orka3 vm list <VM_NAME> --output wide

# Note the IP and Screenshare port

# 2. Verify VM is running
# Intel VMs may need explicit start

# 3. Check if it's a fresh OS install
# Screen Sharing may not be enabled by default
```

**Solutions:**
```bash
# 1. Ensure you're using the correct format
# vnc://<VM_IP>:<Screenshare_port>

# 2. For Intel VMs - ensure VM is powered on
orka3 vm start <VM_NAME>

# 3. Try SSH first if available
ssh -p <SSH_PORT> admin@<VM_IP>

# Then enable Screen Sharing from command line:
sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart \
  -activate -configure -access -on \
  -restart -agent -privs -all

# 4. Use MacStadium base images which have Screen Sharing pre-enabled
orka3 vm deploy --image ghcr.io/macstadium/orka-images/sonoma:latest

# 5. Wait longer - VM may still be booting
# First boot can take 5-10 minutes
```

## Problem: Cannot connect via SSH

**Symptoms:**
- SSH connection timeout
- "Connection refused" on SSH port
- Authentication failures

**Diagnosis:**
```bash
# 1. Get VM connection info
orka3 vm list <VM_NAME> --output wide

# Note the IP and SSH port

# 2. Verify SSH is listening
# Connect via Screen Sharing and check System Settings > Sharing > Remote Login
```

**Solutions:**
```bash
# 1. Use correct port (not 22)
ssh -p <SSH_PORT> admin@<VM_IP>

# 2. If SSH is disabled, enable via Screen Sharing:
# System Settings > Sharing > Remote Login > Enable

# 3. Or enable via command line (if you have another way in):
sudo systemsetup -setremotelogin on

# 4. Use MacStadium base images (SSH pre-enabled)
orka3 vm deploy --image ghcr.io/macstadium/orka-images/sonoma:latest

# 5. Check firewall on VM
# System Settings > Network > Firewall
```

## Problem: Port conflicts

**Symptoms:**
- "Port already in use"
- Custom port mapping fails

**Diagnosis:**
```bash
# Check which ports are in use
orka3 vm list --output wide              # Check Node column for port usage
```

**Solutions:**
```bash
# Let Orka assign ports automatically (recommended)
orka3 vm deploy --image <IMAGE>  # No --ports flag

# Or specify different available ports
orka3 vm deploy --image <IMAGE> --ports 9100:4000,9101:5000
```

## Problem: VM is slow/unresponsive during use

**Symptoms:**
- Laggy Screen Sharing
- Slow application performance
- Builds taking too long

**Diagnosis:**
```bash
# 1. Check VM resource allocation
orka3 vm list <VM_NAME> --output wide

# Look at CPU and memory allocated

# 2. Check node load
orka3 node list --output wide

# Look at available resources on host node

# 3. Check if too many VMs on one node
orka3 vm list --output wide | awk '{print $NF}' | sort | uniq -c
```

**Solutions:**
```bash
# Option 1: Increase VM resources
# Create new config with more resources
orka3 vmc create larger-vm --image <IMAGE> --cpu 6 --memory 16

# Delete old VM and redeploy
orka3 vm delete <VM_NAME>
orka3 vm deploy <VM_NAME> --config larger-vm

# Option 2: Reduce load on node
# Delete unnecessary VMs
orka3 vm delete <UNUSED_VM>

# Option 3: Use node affinity to spread VMs
# Tag less loaded nodes
orka3 node tag <UNDERUTILIZED_NODE> low-load

# Deploy new VMs to those nodes
orka3 vm deploy --image <IMAGE> --tag low-load

# Option 4: Use most-allocated scheduler for better packing
orka3 vmc create packed-vm --image <IMAGE> --scheduler most-allocated
```

## Problem: VM deployments are very slow

**Symptoms:**
- Deployments take 15+ minutes
- Inconsistent deployment times
- Timeout errors

**Diagnosis:**
```bash
# 1. Check if images are cached (Apple Silicon)
orka3 ic list

# 2. Check node load
orka3 node list --output wide

# 3. Verify image size
orka3 image list <IMAGE> --output wide
```

**Solutions:**
```bash
# For Apple Silicon: Pre-cache images
orka3 ic add <IMAGE> --all

# Wait for caching to complete
orka3 ic info <IMAGE>

# Then deploy (should be much faster)
orka3 vm deploy --image <IMAGE>

# Use smaller images if possible
# Consider creating optimized base images

# Deploy to less loaded nodes
orka3 node list --output wide  # Find node with fewer VMs
orka3 vm deploy --image <IMAGE> --node <LESS_LOADED_NODE>

# Increase deployment timeout
orka3 vm deploy --image <IMAGE> --timeout 20
```

## Default Credentials

For MacStadium base images (ghcr.io/macstadium/orka-images/*):
- **Username:** admin
- **Password:** admin

**Important:** Change the password after first login for security.

## Common Ports

| Service | Default Port | Notes |
|---------|-------------|-------|
| SSH | Varies (not 22) | Check `orka3 vm list --output wide` |
| Screen Sharing (VNC) | Varies | Check `orka3 vm list --output wide` |
| Custom ports | User-defined | Use `--ports` flag |

## Getting Help

If you cannot resolve an issue:

1. **Get Verbose Output:**
   ```bash
   orka3 <command> --output json
   ```

2. **Collect Diagnostic Information:**
   ```bash
   orka3 version
   orka3 config view
   orka3 node list --output wide
   orka3 vm list --output wide
   ```

3. **Contact MacStadium Support:**
   - Provide CLI version, cluster version, and error messages
   - Include diagnostic output
   - Describe what you were trying to accomplish
