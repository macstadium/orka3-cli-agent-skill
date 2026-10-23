# Upgrade Workflows Reference

## Orka Cluster Upgrades (MSDC — MacStadium Data Centers)

Self-service as of Orka 3.6+ via the Upgrade Service (v2), started and monitored from the `orka3` CLI. See [Upgrade Service (self-service, 3.6+)](#upgrade-service-self-service-36) below for the full command flow. Only fall back to a MacStadium support ticket if the cluster hasn't completed its v1→v2 migration yet, or for anything the Upgrade Service doesn't cover (Kubernetes control-plane version changes, hardware changes).

### Process
1. Review release notes for the target version
2. Confirm Upgrade Service and node agents are healthy: `orka3 upgrade versions`, `orka3 upgrade service status`, `orka3 upgrade service agents`
3. Start the run: `orka3 upgrade run --version <VERSION>` (admin access required)
4. Monitor: `orka3 upgrade status <run-name>`
5. After upgrade: download the new CLI version and regenerate service account tokens if this was a full version upgrade (or if the release notes require it)
6. Update Orka VM Tools in custom golden images to the new cluster version and republish them. A VM Tools mismatch breaks disk resize and shared storage on Apple silicon.

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

**To minimize disruption:** Increase API Server and Operator replica counts, then add PodDisruptionBudgets (`minAvailable: 1`) selecting `app: orka-apiserver` and `app: orka-operator`. A PDB requires at least 2 replicas: a single-replica deployment with a PDB blocks the drain and the upgrade.

**Webhooks PDB depends on the Orka version:**
- **Orka 3.6 and earlier:** Orka doesn't create a Webhooks PDB. Add your own if you need the Webhooks available through the drain.
- **Orka 4.0 and later:** Orka creates its own `orka-webhooks` PDB during install and upgrade. Don't add another. Two PDBs selecting the same pods make Kubernetes refuse to evict them, and the node drain hangs.
- **Before upgrading from 3.6 to 4.0:** your own Webhooks PDB stays in the cluster through the upgrade and collides with the one 4.0 adds. Find it and delete any PDB whose selector matches `app: orka-webhooks`:
  ```bash
  kubectl get pdb -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,SELECTOR:.spec.selector.matchLabels'
  ```

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

## Upgrade Service (self-service, 3.6+)

Orka 3.6.0 introduced Upgrade Service v1, which let MacStadium push upgrades to a cluster. As of the v1→v2 migration, Upgrade Service is self-service: you start, monitor, and review upgrades yourself from the `orka3` CLI, for both MSDC and Orka Anywhere clusters. It is not a scheduler or an auto-updater; it replaces manually sequencing service, agent, and node-component upgrades one at a time for a single planned run you start yourself.

**Before starting a run:**
```bash
orka3 upgrade versions              # Current version + available releases
orka3 upgrade service status        # Eligible nodes vs. live/seen agents
orka3 upgrade service agents        # Per-node agent version, status, lease age
```
Resolve any node reporting `STALE` or `MISSING` before starting. `orka3 upgrade service agents` only lists nodes in one namespace (default `orka-default`), so run it with `-n <NAMESPACE>` for every namespace that has nodes.

If these commands fail with `no matches for kind "ClusterUpgrade"`, the Upgrade Service isn't installed on the cluster. This is common on AWS-hosted Anywhere (see [AWS-hosted Anywhere](#orka-anywhere-upgrades-self-service-aws-hosted-or-on-premises) below).

**Starting and monitoring a run:**
```bash
orka3 upgrade run --version <VERSION>     # Admin access required
orka3 upgrade run --version latest        # Resolves once at run creation, fixed for that run
orka3 upgrade status                      # Most recent run
orka3 upgrade status <run-name>
orka3 upgrade history                     # Retained runs, newest first (10 max)
```
All four commands support `-o json` for scripting.

Pin an explicit version (`orka3 upgrade run --version <VERSION>`) in change tickets and runbooks rather than `latest`, so the ticket records exactly what was applied.

**How a run behaves:** validates the target release, upgrades Upgrade Service itself if needed, upgrades per-node agents, upgrades node components (canary node first, then a bounded rolling window), upgrades core control-plane components, then remaining Orka services. If a node upgrade fails, no new node work is released, in-flight work finishes, and the run is marked failed with the control plane left on its previous version, every node ends as succeeded/failed/skipped with a reason. Retrying a failed run means creating a new run at the same target; already-converged components are idempotent. There is no full-cluster rollback, and deleting a run does not cancel in-flight work.

**Until a cluster completes its first successful v2 run**, `orka3 upgrade versions` reports its version as `unknown`. To check component versions before then, use `orka3 version` and `orka3 node list -o wide`.

**Who can run what:** starting a run requires administrator access. `upgrade status`, `upgrade history`, and `upgrade versions` only need read access.

**Availability by deployment:**
- **MSDC:** all 3.6+ clusters already have Upgrade Service v2 installed. No action needed.
- **Orka Anywhere on-prem:** requires Orka 3.6.2+. Runs v1 until migrated (see the migration script below).
- **Orka Anywhere AWS-hosted:** requires Orka 3.6+. Not installed by default; install it with the `ghcr.io/macstadium/orka-ansible-aws:3.6.4` image (see below).

### Troubleshooting Upgrade Service runs

- **Run stays `Pending`, then fails:** a run has up to 30 minutes to be admitted. Exceeding that usually means the target couldn't be resolved or another run was still active. Check `orka3 upgrade history`.
- **Requested version not found or unavailable:** the release may be missing from the release index or temporarily quarantined. Check `orka3 upgrade versions`, then pick an available release or use `--version latest`.
- **Cluster already on the requested version:** not an error. Repeated run requests are safe because run names are timestamped and never collide.
- **A node didn't upgrade:** run `orka3 upgrade service status`, then `orka3 upgrade service agents`. An agent that hasn't renewed its lease in 90 seconds reports `STALE`; one that has never been seen reports `MISSING`. Recover the agent, then start a new run.
- **A node was skipped or its deadline expired:** read the skip reason in `orka3 upgrade status <RUN_NAME> -o json`. Common causes: no live agent, node already on the target version, node drained, or the node roster changed during the run.
- **Failed runs can't be resumed.** Fix the cause and start a new run at the same target.
- **Only the 10 most recent completed runs are retained.** Export `orka3 upgrade history` or a run's status first if you need long-term records.
- **Escalating to support:** include the run name, target release, and the output of `orka3 upgrade status <RUN_NAME> -o json` and `orka3 upgrade service agents -o json`.

## Orka Anywhere upgrades (self-service, AWS-hosted or on-premises)

Orka Anywhere is any deployment you run and manage yourself (AWS-hosted or fully on-prem), as opposed to MSDC. Upgrades reuse the same Ansible-based process used to install the cluster, pointed at the Ansible image tagged for your target release, there is no separate upgrade procedure to learn.

**AWS-hosted:** see the [AWS Upgrades](#aws-upgrades) section above (CodeBuild + SSH/SSM ARM node tooling).

**On-premises:** reuses the exact `ghcr.io/macstadium/orka-ansible-onprem` container and the same `cluster.yml`/`nodes.yml`/`hosts` files used at install. Playbooks are idempotent, re-running them re-converges the cluster to the target version. The upgrade is the same container-then-playbook flow as install, just with the target version's tag on the image:

```bash
# Services upgrade — enter the container built for your target version, then run the playbook inside it
docker run -it -v <kube_config_location>:/root/.kube/config -v ./cluster.yml:/ansible/group_vars/all/cluster.yml ghcr.io/macstadium/orka-ansible-onprem:<version_tag> bash
# inside the container, in /ansible:
ansible-playbook site.yml

# ARM node tooling upgrade — same pattern, with the node-specific mounts
docker run -it -v <kube_config_location>:/root/.kube/config -v ./cluster.yml:/ansible/group_vars/all/cluster.yml -v ./nodes.yml:/ansible/group_vars/arm-nodes/nodes.yml -v ./hosts:/ansible/hosts -v <mac_ssh_key_location>:/root/.ssh/id_rsa ghcr.io/macstadium/orka-ansible-onprem:<version_tag> bash
# inside the container, in /ansible:
ansible-playbook configure-arm.yml -i hosts --ask-become-pass
```
`<version_tag>` is the target Orka version (e.g. `3.6.4`), the same variable named in the install docs, not a new upgrade-specific flag. Node tooling (Virtual Kubelet, Orka Engine) is version-gated, not blindly replaced: the playbook compares installed vs. target version and only updates on a mismatch, so re-running against nodes already on the target is a no-op. You normally don't need to set `osx_node_orka_engine_version` or `osx_node_orka_vk_version` in `nodes.yml` for a routine upgrade: the `orka-ansible` package ships with its own default pin for the node tooling version. Set them only if MacStadium has given you a specific custom build.

**Don't pin these to the release version.** Orka Engine and Virtual Kubelet aren't always on the same version as the release. Orka 3.6.4 uses Orka Engine 3.6.3 and no Engine 3.6.4 build exists, so `osx_node_orka_engine_version: official/3.6.4` makes the configuration playbook fail with HTTP 403 on every node.

**Hybrid (EKS control plane + on-prem Mac nodes):** upgrade each part with its own workflow above.

**Migrating Orka Anywhere's own Upgrade Service from v1 to v2 (on-prem only):** on-prem clusters already run Upgrade Service as v1; a dedicated `kubectl`-only script migrates it, separate from the cluster/node-tooling upgrade above:
```bash
curl -fsSLO https://distribution.macstadium.com/orka-releases/helpers/migrate-upgrade-service.sh
chmod +x migrate-upgrade-service.sh
./migrate-upgrade-service.sh          # latest release, or pass a version as the first arg
```
Requires `kubectl` (admin context) and `jq`, plus outbound HTTPS to distribution.macstadium.com. Installs v2 CRDs, applies updated permissions, removes v1 leftovers, and waits up to 7 minutes for every node's upgrade agent to check in ("waiting for agent leases" messages during that window are expected). If your cluster's Mac node labels don't expose a standard `arm64` architecture label, set `ORKA_EXPECTED_AGENTS` to the actual node count first. Before running it, confirm the cluster's own v1→v2 self-upgrade already completed (`orka3 upgrade service status` should show an operator version starting `2.0.0-`), the script doesn't perform that step itself.

**AWS-hosted Anywhere: fresh v2 install, not a migration.** Upgrade Service isn't present by default on AWS-hosted Anywhere, there's no v1 to migrate from. Install it via CodeBuild the same way as ARM node tooling, using the Ansible image tagged for your current version:
```bash
AWS_DEFAULT_REGION=<region> ansible-playbook -i arm.ssh.aws_ec2.yml /ansible/deploy-upgrade-service.yml --private-key ~/.ssh/id_rsa
```

## Host node macOS upgrades (3.7.0-alpha+)

Orka can upgrade existing Apple silicon host nodes to macOS Tahoe (26) as of 3.7.0-alpha; earlier 3.7.0-alpha builds only recognized Sequoia as an upgrade target. This is the physical host's OS, not a guest VM's OS, and is unrelated to the Orka version upgrades above.

Multi-node host OS upgrades are throttled to avoid overloading the control plane on large clusters, and transient node-tooling failures during an upgrade now retry automatically instead of failing the whole run.

**Per-node pod quota (3.7.0-alpha+):** each Apple silicon node advertises a pod quota to the Kubernetes scheduler, how many VM, emulator, and image-cache job pods it can run at once. Default is `4`, tunable via the `osx_node_orka_quota_pod` Ansible variable. If running Android emulators, plan for headroom: a node running two VMs and their two paired emulators is already at the default quota, leaving no room for an image-cache job until one finishes. Contact MacStadium support to have the quota raised for a cluster.
