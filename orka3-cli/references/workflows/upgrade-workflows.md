# Upgrade Workflows Reference

## Orka Cluster Upgrades (MSDC, MacStadium Data Centers)

Self-service as of Orka 3.6+ via the Upgrade Service (v2), started and monitored from the `orka` CLI. See [Upgrade Service (self-service, 3.6+)](#upgrade-service-self-service-36) below for the full command flow. Only fall back to a MacStadium support ticket if the cluster hasn't completed its v1→v2 migration yet, or for anything the Upgrade Service doesn't cover (Kubernetes control-plane version changes, hardware changes).

**Upgrading to Orka 4.0 is support-led.** The Upgrade Service can't perform a 3.6 to 4.0 upgrade yet, so don't start an `upgrade run` for it. See [Upgrading to Orka 4.0](#upgrading-to-orka-40).

### Process
1. Review release notes for the target version
2. Confirm Upgrade Service and node agents are healthy: `orka upgrade versions`, `orka upgrade service status`, `orka upgrade service agents`
3. Start the run: `orka upgrade run --version <VERSION>` (admin access required)
4. Monitor: `orka upgrade status <RUN_NAME>`
5. After upgrade: download the new CLI version
6. Check Orka VM Tools in custom golden images. Any VM Tools 3.6.0 or later work on both 3.6 and 4.0 clusters; VM Tools 4.0 is required only for 4.0's User Data feature. To update, run `brew upgrade orka-vm-tools` in the image and republish it. VM Tools is versioned separately from the cluster: on the 3.6 line it stays at 3.6.0 for every patch release.

### Upgrading to Orka 4.0

- **Orka 3.6 first.** Upgrading to 4.0.0 requires Orka 3.6. If the cluster runs an earlier version, upgrade to the latest 3.6 release first.
- **No Intel worker nodes.** Orka 4.0 runs on Apple silicon only. The upgrade checks for Intel worker nodes and stops before making any changes (the pre-check reports `Orka 4.0 does not support Intel worker nodes. Remove these nodes from the cluster first:` followed by the node names). Remove the Intel nodes first, or keep the cluster on Orka 3.6, which MacStadium supports through March 2028.
- **Schedule it with support.** The upgrade to 4.0 is support-led: the Upgrade Service can't perform it yet. Contact [MacStadium support](mailto:support@macstadium.com) to schedule it.
- **Before the upgrade:** delete any PodDisruptionBudget of your own that selects `app: orka-webhooks` (4.0 creates its own; see [Kubernetes Upgrades](#kubernetes-upgrades)). Check scripts and pipelines for the removed Intel commands and flags and the deprecated NFS image commands (`references/commands/vm-commands.md`, `references/commands/image-commands.md`).
- **After the upgrade:** install the 4.0 `orka` CLI (see the CLI section in `SKILL.md`), and update Orka VM Tools in golden images to 4.0 before relying on VM User Data. Per-node limits change in 4.0 (see [Per-node pod quota](#per-node-pod-quota-apple-silicon)).

Full list of changes: [Orka 4.0.0 release notes](https://docs.macstadium.com/orka/orka-upgrades-and-release-notes/orka-release-notes).

### Checking component versions

A cluster's version is the release version, but its components are versioned separately, and a patch release only publishes new builds of the components it changed. Some components keep an earlier number. Example: a 3.6.4 cluster runs the API server and Orka Engine at 3.6.3, because neither changed in 3.6.4. That is not a failed upgrade.

```bash
orka version             # API Version (API server), Operator Version (operator, webhooks, CRDs)
orka node list -o wide   # VERSION = Virtual Kubelet, RUNTIME = Orka Engine, per node
orka version --client    # Local CLI only, no cluster call
```

Compare the version number only, against the [component version matrix](https://docs.macstadium.com/orka/orka-upgrades-and-release-notes/orka-component-versions). The suffix after the version (`-c8fe8aed`) is a build ID and can differ between clusters on the same release. On 3.4 the Engine version itself ends in `-oc` (`orka-engine://3.4.2-oc-<BUILD>`), and that `-oc` is part of the version.

- A 3.6.4 cluster is on 3.6.4 when the operator and every node's Virtual Kubelet report 3.6.4.
- If one node reports an earlier Virtual Kubelet or Engine than the matrix, that node's tooling wasn't upgraded. Send `orka node list -o wide` output to MacStadium support.
- Use the CLI version the matrix lists for the release. A newer CLI can include commands the cluster doesn't support yet (for example `imagecache remove` needs a 3.6.3+ cluster).
- VM Tools and CI/CD integrations are versioned independently of the release (on the 3.6 line, VM Tools stays at 3.6.0).

**On-prem 3.6.4 installer re-pull:** the `ghcr.io/macstadium/orka-ansible-onprem:3.6.4` image published before October 1, 2026 deployed the operator, CRDs, and Virtual Kubelet at 3.6.3. If an Orka Anywhere on-prem cluster reports operator 3.6.3 after a 3.6.4 upgrade, re-pull the `3.6.4` installer image and run the upgrade again.

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

### Patch version upgrades (x.y.Z)
Zero-downtime. No maintenance window required. Running VMs and image cache are preserved.

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
- **Orka 4.0 also protects its HA control-plane components with PDBs.** On every cluster it reserves kubelet resources on control-plane nodes. On MacStadium-hosted clusters only, it also caps memory for login sessions on control-plane hosts, runs Orka components under dedicated PriorityClass tiers (kube-vip at `system-node-critical`), and sets per-component resource requests and limits. On AWS and on-prem clusters, Orka creates no priority classes (they're cluster-wide and could preempt your workloads) and leaves requests and limits empty for you to size.
- **Before upgrading from 3.6 to 4.0:** your own Webhooks PDB stays in the cluster through the upgrade and collides with the one 4.0 adds. Find it and delete any PDB whose selector matches `app: orka-webhooks`:
  ```bash
  kubectl get pdb -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,SELECTOR:.spec.selector.matchLabels'
  ```

**Post-upgrade verification:**
```bash
kubectl get nodes
orka node list
kubectl get pods
orka vm deploy --image <IMAGE_NAME>
curl <ORKA_API_URL>/api/v1/cluster-info   # Expect HTTP 200
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

### ARM node tooling upgrade: SSH method (preferred)

```yaml
# buildspec.yml
version: 0.2
env:
  shell: bash
  secrets-manager:
    SSH_PRIVATE_KEY: "<SECRET_NAME>"
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

### ARM node tooling upgrade: SSM method (fallback, up to 4 hours)

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
  --private-key ~/.ssh/id_rsa -e override_orka_engine_license_key=<LICENSE_KEY>
```

### Multi-region deployments

```bash
aws codebuild start-build --project-name <PROJECT_NAME> \
  --environment-variables-override name=AWS_DEFAULT_REGION,value=us-west-2,type=PLAINTEXT
```

### Key changes in 3.5 → 3.6 (AWS)
- ARM tooling updates now in-place via Ansible; no longer requires AMI replacement (~2 hours previously)
- AWS credentials no longer needed for artifact distribution (CloudFront public access)
- cert-manager no longer auto-installed if already present in cluster

### Post-upgrade (AWS, 3.5 to 3.6)
- Download and install the Orka 3.6 CLI (`orka3`)
- If your cluster uses a public NAT IP, update your API URL to use HTTPS:
  ```bash
  orka3 config set --api-url https://<YOUR_PUBLIC_URL>
  ```
  (3.6.2 change: CLI now determines TLS from an API feature flag rather than IP detection)

---

## Upgrade Service (self-service, 3.6+)

Orka 3.6.0 introduced Upgrade Service v1, which let MacStadium push upgrades to a cluster. As of the v1→v2 migration, Upgrade Service is self-service: you start, monitor, and review upgrades yourself from the `orka` CLI, for both MSDC and Orka Anywhere clusters. It is not a scheduler or an auto-updater; it replaces manually sequencing service, agent, and node-component upgrades one at a time for a single planned run you start yourself.

**Before starting a run:**
```bash
orka upgrade versions              # Current version + available releases
orka upgrade service status        # Eligible nodes vs. live/seen agents
orka upgrade service agents        # Per-node agent version, status, lease age
```
Resolve any node reporting `STALE` or `MISSING` before starting. `orka upgrade service agents` only lists nodes in one namespace (default `orka-default`), so run it with `-n <NAMESPACE>` for every namespace that has nodes.

If these commands fail with `no matches for kind "ClusterUpgrade"`, the Upgrade Service isn't installed on the cluster. This is common on AWS-hosted Anywhere (see [AWS-hosted Anywhere](#orka-anywhere-upgrades-self-service-aws-hosted-or-on-premises) below).

**Starting and monitoring a run:**
```bash
orka upgrade run --version <VERSION>     # Admin access required
orka upgrade run --version latest        # Resolves once at run creation, fixed for that run
orka upgrade status                      # Most recent run
orka upgrade status <RUN_NAME>
orka upgrade history                     # Retained runs, newest first (10 max)
```
All four commands support `-o json` for scripting.

Pin an explicit version (`orka upgrade run --version <VERSION>`) in change tickets and runbooks rather than `latest`, so the ticket records exactly what was applied.

**How a run behaves:** validates the target release, upgrades Upgrade Service itself if needed, upgrades per-node agents, upgrades node components (canary node first, then a bounded rolling window), upgrades core control-plane components, then remaining Orka services. If a node upgrade fails, no new node work is released, in-flight work finishes, and the run is marked failed with the control plane left on its previous version, every node ends as succeeded/failed/skipped with a reason. Retrying a failed run means creating a new run at the same target; already-converged components are idempotent. There is no full-cluster rollback, and deleting a run does not cancel in-flight work.

**Until a cluster completes its first successful v2 run**, `orka upgrade versions` reports its version as `unknown`. To check component versions before then, use `orka version` and `orka node list -o wide`.

**Who can run what:** starting a run requires administrator access. `upgrade status`, `upgrade history`, and `upgrade versions` only need read access.

**Availability by deployment:**
- **MSDC:** all 3.6+ clusters already have Upgrade Service v2 installed. No action needed.
- **Orka Anywhere on-prem:** requires Orka 3.6.2+. Runs v1 until migrated (see the migration script below).
- **Orka Anywhere AWS-hosted:** requires Orka 3.6+. Not installed by default; install it with the `ghcr.io/macstadium/orka-ansible-aws:3.6.4` image (see below).

### Troubleshooting Upgrade Service runs

- **Run stays `Pending`, then fails:** a run has up to 30 minutes to be admitted. Exceeding that usually means the target couldn't be resolved or another run was still active. Check `orka upgrade history`.
- **Requested version not found or unavailable:** the release may be missing from the release index or temporarily quarantined. Check `orka upgrade versions`, then pick an available release or use `--version latest`.
- **Cluster already on the requested version:** not an error. Repeated run requests are safe because run names are timestamped and never collide.
- **A node didn't upgrade:** run `orka upgrade service status`, then `orka upgrade service agents`. An agent that hasn't renewed its lease in 90 seconds reports `STALE`; one that has never been seen reports `MISSING`. Recover the agent, then start a new run.
- **A node was skipped or its deadline expired:** read the skip reason in `orka upgrade status <RUN_NAME> -o json`. Common causes: no live agent, node already on the target version, node drained, or the node roster changed during the run.
- **Failed runs can't be resumed.** Fix the cause and start a new run at the same target.
- **Only the 10 most recent completed runs are retained.** Export `orka upgrade history` or a run's status first if you need long-term records.
- **Escalating to support:** include the run name, target release, and the output of `orka upgrade status <RUN_NAME> -o json` and `orka upgrade service agents -o json`.

## Orka Anywhere upgrades (self-service, AWS-hosted or on-premises)

Orka Anywhere is any deployment you run and manage yourself (AWS-hosted or fully on-prem), as opposed to MSDC. Upgrades reuse the same Ansible-based process used to install the cluster, pointed at the Ansible image tagged for your target release, there is no separate upgrade procedure to learn.

**AWS-hosted:** see the [AWS Upgrades](#aws-upgrades) section above (CodeBuild + SSH/SSM ARM node tooling).

**On-premises:** reuses the exact `ghcr.io/macstadium/orka-ansible-onprem` container and the same `cluster.yml`/`nodes.yml`/`hosts` files used at install. Playbooks are idempotent, re-running them re-converges the cluster to the target version. The upgrade is the same container-then-playbook flow as install, just with the target version's tag on the image:

```bash
# Services upgrade: enter the container built for your target version, then run the playbook inside it
docker run -it -v <KUBECONFIG_PATH>:/root/.kube/config -v ./cluster.yml:/ansible/group_vars/all/cluster.yml ghcr.io/macstadium/orka-ansible-onprem:<VERSION_TAG> bash
# inside the container, in /ansible:
ansible-playbook site.yml

# ARM node tooling upgrade: same pattern, with the node-specific mounts
docker run -it -v <KUBECONFIG_PATH>:/root/.kube/config -v ./cluster.yml:/ansible/group_vars/all/cluster.yml -v ./nodes.yml:/ansible/group_vars/arm-nodes/nodes.yml -v ./hosts:/ansible/hosts -v <MAC_SSH_KEY_PATH>:/root/.ssh/id_rsa ghcr.io/macstadium/orka-ansible-onprem:<VERSION_TAG> bash
# inside the container, in /ansible:
ansible-playbook configure-arm.yml -i hosts --ask-become-pass
```
`<VERSION_TAG>` is the target Orka version (e.g. `3.6.4`), the same image tag variable used at install, not a new upgrade-specific flag. Node tooling (Virtual Kubelet, Orka Engine) is version-gated, not blindly replaced: the playbook compares installed vs. target version and only updates on a mismatch, so re-running against nodes already on the target is a no-op. You normally don't need to set `osx_node_orka_engine_version` or `osx_node_orka_vk_version` in `nodes.yml` for a routine upgrade: the `orka-ansible` package ships with its own default pin for the node tooling version. Set them only if MacStadium has given you a specific custom build.

**Don't pin these to the release version.** Orka Engine and Virtual Kubelet aren't always on the same version as the release. Orka 3.6.4 uses Orka Engine 3.6.3 and no Engine 3.6.4 build exists, so `osx_node_orka_engine_version: official/3.6.4` makes the configuration playbook fail with HTTP 403 on every node.

**Hybrid (EKS control plane + on-prem Mac nodes):** upgrade each part with its own workflow above.

**Migrating Orka Anywhere's own Upgrade Service from v1 to v2 (on-prem only):** on-prem clusters already run Upgrade Service as v1; a dedicated `kubectl`-only script migrates it, separate from the cluster/node-tooling upgrade above:
```bash
curl -fsSLO https://distribution.macstadium.com/orka-releases/helpers/migrate-upgrade-service.sh
chmod +x migrate-upgrade-service.sh
./migrate-upgrade-service.sh          # latest release, or pass a version as the first arg
```
Requires `kubectl` (admin context) and `jq`, plus outbound HTTPS to distribution.macstadium.com. Installs v2 CRDs, applies updated permissions, removes v1 leftovers, and waits up to 7 minutes for every node's upgrade agent to check in ("waiting for agent leases" messages during that window are expected). If your cluster's Mac node labels don't expose a standard `arm64` architecture label, set `ORKA_EXPECTED_AGENTS` to the actual node count first. Before running it, confirm the cluster's own v1→v2 self-upgrade already completed (`orka upgrade service status` should show an operator version starting `2.0.0-`), the script doesn't perform that step itself.

**AWS-hosted Anywhere: fresh v2 install, not a migration.** Upgrade Service isn't present by default on AWS-hosted Anywhere, there's no v1 to migrate from. Install it via CodeBuild the same way as ARM node tooling, using the Ansible image tagged for your current version:
```bash
AWS_DEFAULT_REGION=<AWS_REGION> ansible-playbook -i arm.ssh.aws_ec2.yml /ansible/deploy-upgrade-service.yml --private-key ~/.ssh/id_rsa
```

## Per-node pod quota (Apple silicon)

Each Apple silicon node advertises a pod quota to the Kubernetes scheduler. What it limits depends on the Orka version:

- **Orka 3.6:** the Virtual Kubelet's built-in default (`ORKA_QUOTA_POD`) is `4` pods per node. The 3.6 Ansible has no variable for it.
- **Orka 3.7.0-alpha:** default `4`, now tunable with the `osx_node_orka_quota_pod` Ansible variable, and it counts VM, emulator, and image-cache job pods together. If running Android emulators, plan for headroom: a node running two VMs and their two paired emulators is already at the default, leaving no room for an image-cache job until one finishes. Contact MacStadium support to have the quota raised for a cluster.
- **Orka 4.0:** the shared cap is gone.
  - Image-cache, cache-remove, and registry-push jobs have their own per-node budget, `osx_node_orka_quota_job` (default `2`). Surplus jobs wait `Pending` rather than fail. They no longer compete with VMs or emulators.
  - `osx_node_orka_quota_pod` is `110`, the Kubernetes default, and is sized never to bind, so it no longer limits VMs, emulators, and jobs together. VMs keep their own limit, `osx_node_orka_quota_vm` (2 per Apple silicon node, 1 with shared disk).
  - Emulators aren't capped. They're counted per node, so `kubectl describe node` shows how many are running. Memory is the practical limit (see emulator sizing in `references/commands/emulator-commands.md`).
  - The Kubernetes scheduler places emulators on their paired VM's node. If it can't, for example because the node is cordoned, the emulator stays `Pending` with the scheduler's reason, and fails with `EmulatorUnschedulable` after 5 minutes.

If you raised `osx_node_orka_quota_pod` on the 3.7.0-alpha to make room for emulators or cache jobs, you don't need that override on 4.0.
