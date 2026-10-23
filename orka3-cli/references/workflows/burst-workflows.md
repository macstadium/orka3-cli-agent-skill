# Orka Burst Workflows

This guide covers enabling, draining, and disabling Orka Burst capacity, and automating it through the MacStadium Portal API. Source: [Orka Burst](https://docs.macstadium.com/orka/orka-resources/burst).

## Contents
- [Overview](#overview)
- [Portal API token](#portal-api-token)
- [Find the cluster ID and check status](#find-the-cluster-id-and-check-status)
- [Enable burst](#enable-burst)
- [Drain and disable burst](#drain-and-disable-burst)
- [Automation patterns](#automation-patterns)
- [Gotchas](#gotchas)

## Overview

Orka Burst (Orka 3.3+) adds contracted, on-demand nodes to a cluster, billed only while enabled. MacStadium sets it up once in a maintenance window (contact your sales team). After that, admins toggle it from the MacStadium Admin Portal or the Portal GraphQL API. Burst nodes are typically ready within about 15 minutes of enabling.

- Only portal admins can enable or disable burst.
- Burst nodes can't be managed directly in Kubernetes, but you can tag them and move them between Orka namespaces with `orka`.
- Burst has no knowledge of running workloads. Disabling it while VMs run on burst nodes kills those jobs.

## Portal API token

The Portal GraphQL API is at `https://portal.macstadium.com/graphql`. Create a token in the Admin Portal: account menu > **Users** > **Tokens** tab, with read/write permissions.

This is a Portal token, separate from Orka service account tokens: it authenticates against `portal.macstadium.com`, not the cluster. Store it as a CI/CD secret and reference it as `$PORTAL_TOKEN`; never write it inline.

## Find the cluster ID and check status

Mutations need the opaque cluster `id`, not the human-readable `displayId`. Look it up once:

```bash
curl -X POST https://portal.macstadium.com/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PORTAL_TOKEN" \
  -d '{"query":"{ viewer { account { orkaServices(pagination:{offset:0,limit:50}) { edges { node { id displayId } } } } } }"}'
```

Check burst status:

```bash
curl -X POST https://portal.macstadium.com/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PORTAL_TOKEN" \
  -d '{
    "query": "query GetOrkaServiceById($id: ID!) { node(id: $id) { ... on OrkaService { id displayId name status hasBurst burstEnabled burstLastTime actions { canUpdate cannotUpdateReasons } } } }",
    "variables": { "id": "<ORKA_SERVICE_ID>" }
  }'
```

| Field | Meaning |
|-------|---------|
| `hasBurst` | Cluster is provisioned with burst nodes |
| `burstEnabled` | Current burst state |
| `burstLastTime` | Last burst state change |
| `canUpdate` | Burst can be toggled right now |
| `cannotUpdateReasons` | Why not, when `canUpdate` is false |

Always check `canUpdate` before a mutation. A cluster mid-transition or in an error state returns `canUpdate: false` and the mutation fails.

## Enable burst

```bash
curl -X POST https://portal.macstadium.com/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PORTAL_TOKEN" \
  -d '{
    "query": "mutation UpdateOrkaBurst($input: UpdateOrkaBurstInput!) { updateOrkaBurst(input: $input) { service { id displayId burstEnabled burstLastTime } } }",
    "variables": { "input": { "id": "<ORKA_SERVICE_ID>", "state": true } }
  }'
```

Then wait for the burst nodes to show `READY`:

```bash
orka node list -n <BURST_NAMESPACE> -o wide
```

Tag burst nodes so monitoring can separate them from fixed capacity (tags appear as Kubernetes node labels, visible through the `kube_node_labels` metric if you run kube-state-metrics) and so you can route burst-tolerant jobs to them:

```bash
orka node tag <BURST_NODE> burst -n <BURST_NAMESPACE>
```

## Drain and disable burst

Drain first, always. Plan disables for low-utilization windows and tell the teams that use the cluster.

1. **Stop scheduling new work to the burst nodes.** Point burst-only CI at permanent capacity, lower CI concurrency limits back to permanent slot capacity, or repoint CI at VM configs that don't target the `burst` tag (VM configs can't be edited, only recreated). Keeping burst nodes in their own namespace makes this step simple: stop the CI integrations that deploy into it.
2. **Wait for or delete the VMs on the burst nodes.** Check by node in the namespace the burst nodes are in:

   ```bash
   orka vm list -n <BURST_NAMESPACE> -o json \
     | jq -r --arg node "<BURST_NODE>" '.[] | select(.node == $node) | .name'
   ```

   Repeat until the output is empty for every burst node. Let jobs finish, or delete their VMs deliberately.
3. **Then move or release the nodes.** If burst nodes share a namespace with permanent nodes, move them to a separate namespace (`orka node namespace` is refused while VMs run on the node, which is why draining comes first):

   ```bash
   orka node namespace <BURST_NODE> --namespace <CURRENT_NAMESPACE> <HOLDING_NAMESPACE>
   ```

4. **Disable burst** after confirming `canUpdate: true`:

   ```bash
   curl -X POST https://portal.macstadium.com/graphql \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $PORTAL_TOKEN" \
     -d '{
       "query": "mutation UpdateOrkaBurst($input: UpdateOrkaBurstInput!) { updateOrkaBurst(input: $input) { service { id displayId burstEnabled burstLastTime } } }",
       "variables": { "input": { "id": "<ORKA_SERVICE_ID>", "state": false } }
     }'
   ```

Never move the nodes first and wait afterwards: the move is refused while VMs run, and disabling before the drain fails whatever is still running.

## Automation patterns

| Pattern | Trigger | Guardrail |
|---------|---------|-----------|
| Pipeline bookend | Enable at the start of a heavy workflow, disable in a final cleanup job | Cleanup job drains and confirms no VMs on burst nodes before disabling |
| Off-peak schedule | Cron: enable before peak hours, disable at night | Check `canUpdate` each run and skip if false |
| Queue-depth scaler | GitHub Actions integration metric `runner_scale_set_total_available_jobs` (with `ENABLE_METRICS=true`) stays above a threshold | Enable on sustained backlog; disable only after the backlog is gone and the burst nodes are drained |

See [monitoring.md](monitoring.md) for the backlog alert and burst node labeling.

## Gotchas

- **Two different tokens.** The Portal token toggles burst; Orka service account tokens drive `orka`. Neither works in place of the other.
- **`id`, not `displayId`.** Mutations fail with the human-readable name.
- **Consumption data isn't in the API.** `burstLastTime` shows when the state last changed. For usage against prepaid credit, ask your CSM (support@macstadium.com).
- **API stability.** These operations are stable and supported, but the broader Portal API has no formal versioning commitment yet. Keep the queries in one place.
- **Shared namespaces.** Don't put burst nodes in the same namespace as permanent nodes unless you plan to drain and move them out before every disable.
