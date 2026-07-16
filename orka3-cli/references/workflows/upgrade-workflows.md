# Upgrade Workflows Reference

## Orka Cluster Upgrades (On-Prem / Hosted)

Upgrades are initiated through MacStadium support, not the CLI directly.

### Process
1. Review release notes for the target version
2. Submit a support ticket via the MacStadium portal
3. Schedule a maintenance window (Mon–Thu, 9am or 1pm EST; up to 3 hours)
4. After upgrade: download the new CLI version and regenerate service account tokens

### What persists across a full version upgrade
- Orka users
- Custom service accounts
- VM configs
- Images and ISOs
- Custom namespaces and permissions

### What does NOT persist
- Running VMs (deleted; redeploy from configs)
- Image cache on Apple Silicon nodes (cleared)
- Registry credentials (Virtualization/Orchestration layer upgrades only)
- Custom Kubernetes Pods and services (Virtualization/Orchestration layer upgrades only)

**Critical:** Service account tokens must be regenerated after a full version upgrade. Any automated workflows using SA tokens will fail until regenerated.

### Patch version upgrades (x.y.Z)
Zero-downtime. No maintenance window required. Running VMs, SA tokens, and image cache all preserved.

**Note:** Adding Mac compute nodes requires the latest patch version. Node additions will fail on older patch versions.

---

## Kubernetes Upgrades

Orka does not change how you upgrade Kubernetes. Follow standard upgrade practices for your provider.

**Service impact during node drain:**
- API Server (1 replica default): API calls may fail temporarily; most integrations auto-retry
- Operator (1 replica default): Resource changes pause; queued on restart
- Webhooks (3 replicas default): Requests blocked during downtime
- Virtual Kubelet: Node cannot manage VMs; marked Not Ready after extended downtime
- **Running VMs are unaffected by all of the above**

**To minimize disruption:** Increase API Server and Operator replica counts; add PodDisruptionBudgets (requires minimum 2 replicas — a single-replica deployment with a PDB blocks upgrades).

**Post-upgrade verification:**
```bash
kubectl get nodes
orka3 node list
kubectl get pods
orka3 vm deploy --image <image>
curl <api-endpoint>/api/v1/cluster-info   # Expect HTTP 200
```

Orka 3.6 is validated against Kubernetes 1.35. The Virtual Kubelet requires no upgrade and is forward-compatible with new Kubernetes versions.

---

## AWS Upgrades

Upgrades on AWS consist of two parts: EKS Kubernetes services and ARM Mac node tooling (via Ansible/CodeBuild).

### Requirements
- All ARM EC2 Mac instances must have EC2 tag `role=orka-arm` (instances without this tag are skipped)
- SSH on port 22 for `ec2-user` with key-based auth (preferred; completes in under 10 minutes)

### Services upgrade
Run the CodeBuild project pointed at the Orka 3.6 Ansible image (same method used during installation).

### ARM node tooling upgrade — SSH method (preferred)

```yaml
# buildspec.yml
version: 0.2
env:
  shell: bash
  secrets-manager:
    SSH_PRIVATE_KEY: "<your-secret-name>"
phases:
  install:
    commands:
      - apt-get update && apt-get install -y openssh-client
      - mkdir -p ~/.ssh
      - printf "%s\n" "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
      - chmod 600 ~/.ssh/id_rsa
  build:
    commands:
      - ansible-playbook -i arm.ssh.aws_ec2.yml configure-arm.yml --private-key ~/.ssh/id_rsa
```

### ARM node tooling upgrade — SSM method (fallback, up to 4 hours)

```bash
ansible-playbook -i arm.ssm.aws_ec2.yml configure-arm.yml
```

Requires `AmazonSSMManagedInstanceCore` policy and an S3 bucket in the same region (`ANSIBLE_AWS_SSM_BUCKET` env var).

### Modifying node values without a full upgrade

```bash
# Change hostname
ansible-playbook -i arm.ssh.aws_ec2.yml configure-arm.yml \
  --private-key ~/.ssh/id_rsa -e override_node_hostname=arm-node-1

# Change license key
ansible-playbook -i arm.ssh.aws_ec2.yml configure-arm.yml \
  --private-key ~/.ssh/id_rsa -e override_orka_engine_license_key=<key>
```

### Multi-region deployments

```bash
aws codebuild start-build --project-name <project-name> \
  --environment-variables-override name=AWS_DEFAULT_REGION,value=us-west-2,type=PLAINTEXT
```

### Key changes in 3.5 → 3.6 (AWS)
- ARM tooling updates now in-place via Ansible; no longer requires AMI replacement (~2 hours previously)
- AWS credentials no longer needed for artifact distribution (CloudFront public access)
- cert-manager no longer auto-installed if already present in cluster

### Post-upgrade (AWS)
- Download and install the Orka 3.6 CLI
- If your cluster uses a public NAT IP, update your API URL to use HTTPS:
  ```bash
  orka3 config set --api-url https://<YOUR_PUBLIC_URL>
  ```
  (3.6.2 change: CLI now determines TLS from an API feature flag rather than IP detection)

---

## Upgrade Service (3.6+)

The Upgrade Service is a Kubernetes-native update mechanism deployed automatically in 3.6.0. It enables MacStadium to push cluster upgrades to your environment.

```bash
orka3 version                      # Shows Upgrade Service operator version
kubectl get orkanodes -o wide      # Shows Upgrade Service agent version per node
```
