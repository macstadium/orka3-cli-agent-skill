# Monitoring Workflows

This guide covers collecting Orka metrics with Prometheus and the alerts that matter for macOS CI. Source: [Consuming Metrics from Prometheus](https://docs.macstadium.com/orka/orka-resources/consuming-metrics-from-prometheus).

## Contents
- [What exposes metrics](#what-exposes-metrics)
- [Scrape configuration](#scrape-configuration)
- [Operator metrics](#operator-metrics)
- [Node exporter on Mac vs Linux nodes](#node-exporter-on-mac-vs-linux-nodes)
- [Alerts worth having](#alerts-worth-having)
- [Gotchas](#gotchas)

## What exposes metrics

| Source | Endpoint | Notes |
|--------|----------|-------|
| Orka server (API) | `http://<ORKA_LB_IP>/api/v1/metrics` | Go runtime and process metrics only (`go_goroutines`, `process_resident_memory_bytes`). The path is `/api/v1/metrics`, not `/metrics`. Mostly relevant if you use integrations that still rely on the legacy API server |
| Orka operator | `http://<ORKA_LB_IP>:8080/metrics` | VM lifecycle metrics. `<ORKA_LB_IP>` is usually `10.221.188.20` or `10.221.188.100`; check the IP Allocation table in My Cloud (MacStadium Portal) |
| Node exporter | `http://<NODE_IP>:9100/metrics` | Runs on every node, Intel, Apple silicon, and control plane. Mac nodes run the Homebrew darwin build of `node_exporter` |
| GitHub Actions integration | `http://<GHA_RUNNER_HOST>:8080/metrics` | Opt-in with `ENABLE_METRICS=true`. See [github-actions.md](../integrations/github-actions.md#metrics) |
| Harbor registry (3.5+) | Ask MacStadium support | Clusters using Harbor OCI storage |

Firewall and network metrics (throughput, sessions, IPsec tunnels) are a separate pipeline. See [Consuming Firewall and Network Metrics](https://docs.macstadium.com/orka/orka-resources/consuming-firewall-metrics).

Only the GitHub Actions integration exposes its own Prometheus metrics. For Jenkins, GitLab, and Buildkite, use their native metrics.

**Network:** Prometheus needs a route into the Orka private network (VPN or site-to-site), and TCP 9100 must be reachable on every node. Check each target returns `200 OK`:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://<ORKA_LB_IP>/api/v1/metrics
curl -I http://<ORKA_LB_IP>:8080/metrics
curl -I http://<NODE_IP>:9100/metrics
```

Use a GET (not `curl -I`) for the Orka server. It only answers the HTTP methods its routes register, so a HEAD request to `/api/v1/metrics` returns 404 even when the endpoint works and Prometheus can scrape it. The operator and node exporter answer HEAD.

## Scrape configuration

```yaml
scrape_configs:
  - job_name: 'orka/orka-server'
    scrape_interval: 30s
    scrape_timeout: 30s
    metrics_path: /api/v1/metrics
    scheme: http
    static_configs:
      - targets: ['10.221.188.20']
        labels:
          service: 'orka-server'

  - job_name: 'orka/orka-operator'
    scrape_interval: 30s
    scrape_timeout: 30s
    metrics_path: /metrics
    scheme: http
    static_configs:
      - targets: ['10.221.188.20:8080']
        labels:
          service: 'orka-operator'

  - job_name: 'orka/node-exporter'
    scrape_interval: 15s
    static_configs:
      - targets: ['10.221.188.5:9100', '10.221.188.6:9100', '10.221.188.7:9100']
        labels:
          group: 'master'
      - targets: ['10.221.188.34:9100']
        labels:
          group: 'arm'
```

Label node groups (`master`, `x86`, `arm`, and a separate label for burst nodes) so alerts and dashboards can split by hardware. Instead of hand-maintaining targets, generate a [file-based service discovery](https://prometheus.io/docs/guides/file-sd/) file from the cluster, once per namespace that has nodes:

```bash
orka3 node list -n <NAMESPACE> -o json \
  | jq '[.[] | {targets: ["\(.ip):9100"], labels: {node: .name, arch: .architecture}}]' \
  > <SD_DIR>/orka-nodes-<NAMESPACE>.json
```

Regenerate on a schedule so added, moved, or burst nodes are picked up.

## Operator metrics

Orka 3.6 operator metrics are cluster-wide only. There are no per-namespace or per-node labels.

| Metric | Type | Meaning |
|--------|------|---------|
| `orka_operator_virtual_machine_instances_total` | Gauge | VM instances |
| `orka_operator_virtual_machines_total` | Gauge | Virtual machines (pods) |
| `orka_operator_intel_virtual_machine_instances_total` | Gauge | Intel VM instances |
| `orka_operator_apple_silicon_virtual_machine_instances_total` | Gauge | Apple silicon VM instances |
| `orka_operator_virtual_machine_failures_total` | Counter | Failed VMs |
| `orka_operator_virtual_machine_successes_total` | Counter | Successful VMs |
| `orka_operator_virtual_machine_lifetime_errors_total` | Counter | Errors computing VM lifetime |
| `orka_operator_virtual_machine_success_deployment_duration_seconds` | Histogram | Duration of successful deployments |
| `orka_operator_virtual_machine_failed_deployment_duration_seconds` | Histogram | Duration of failed deployments |
| `orka_operator_virtual_machine_lifetime_seconds` | Histogram | VM lifetime, observed on failure or deletion |

**Orka 4.0 changes:** the operator adds a `vm_namespace` label to its metrics and reports the pending-VM queue (`orka_operator_pending_virtual_machines`, VMs requested but not yet running, and `orka_operator_virtual_machine_queue_age_seconds`, the age of the oldest one), a leading indicator of deploy backlog. The deploy-duration histograms use exponential buckets, so percentiles are meaningful, and bucket series and VM lifetime metrics are in the Prometheus allowlist. `orka-webhooks` now exposes a metrics endpoint that Prometheus scrapes. Intel instance counts only matter on 3.6.

Useful queries:

```promql
# Deploy failure ratio over the last hour
increase(orka_operator_virtual_machine_failures_total[1h])
  / (increase(orka_operator_virtual_machine_failures_total[1h]) + increase(orka_operator_virtual_machine_successes_total[1h]))

# p90 successful deploy time (rises when images aren't cached)
histogram_quantile(0.9, rate(orka_operator_virtual_machine_success_deployment_duration_seconds_bucket[30m]))

# Apple silicon slot usage, where <ARM_NODE_COUNT> is the Apple silicon node count (2 VMs per node)
orka_operator_apple_silicon_virtual_machine_instances_total / (2 * <ARM_NODE_COUNT>)
```

## Node exporter on Mac vs Linux nodes

The darwin and Linux node exporters expose different memory metrics. Write PromQL per OS:

| OS | Metrics |
|----|---------|
| macOS (Mac nodes) | `node_memory_free_bytes`, `node_memory_inactive_bytes`, `node_memory_total_bytes` |
| Linux (control plane) | `node_memory_MemAvailable_bytes`, `node_memory_MemTotal_bytes` |

```promql
# Reclaimable memory ratio on Mac nodes
(node_memory_free_bytes{group="arm"} + node_memory_inactive_bytes{group="arm"}) / node_memory_total_bytes{group="arm"}

# Available memory ratio on Linux nodes
node_memory_MemAvailable_bytes{group="master"} / node_memory_MemTotal_bytes{group="master"}
```

Check the names your exporter actually exposes with `curl http://<NODE_IP>:9100/metrics` before relying on an alert.

## Alerts worth having

- **Node disk usage.** When a node runs short of disk, deploying an uncached image evicts the oldest cached images. Nothing errors, but deploys of the evicted images go from about 5 seconds to about 4 minutes. Alert well before the disk is full:

  ```promql
  1 - node_filesystem_avail_bytes{job="orka/node-exporter",fstype!~"tmpfs|devfs|autofs|nullfs|overlay"}
    / node_filesystem_size_bytes{job="orka/node-exporter",fstype!~"tmpfs|devfs|autofs|nullfs|overlay"} > 0.85
  ```

- **Node exporter down.** `up{job="orka/node-exporter"} == 0` for 5m. Then check `orka3 node list -o wide`.
- **CI queue backlog (GitHub Actions).** Jobs waiting and no idle runner for 10 minutes means capacity is exhausted or deploys are failing:

  ```promql
  runner_scale_set_total_available_jobs > 0
    and on (runner_name) runner_scale_set_total_idle_runners == 0
  ```

- **Deploy failures.** Rising `orka_operator_virtual_machine_failures_total`. Investigate with [deployment-issues.md](../troubleshooting/deployment-issues.md).

On Apple silicon, the 2-VM-per-node limit is usually reached long before CPU saturates, so queue backlog and slot usage are better capacity signals than CPU.

## Gotchas

- **Operator metrics are cluster-wide.** You can't split them by namespace or node on 3.6. Use node exporter labels for per-node views.
- **Caching slows co-located VMs.** Each image cache job uses CPU and heavy disk I/O. Correlate disk-write spikes on a node with cache operations before blaming the build.
- **Burst nodes:** label them in your scrape config (or tag them in Orka) so dashboards can separate burst capacity from fixed capacity. See [burst-workflows.md](burst-workflows.md).
