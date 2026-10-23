# REST API Reference

This reference covers calling the Orka API server directly, for tools that can't shell out to the Orka3 CLI. Prefer the CLI where it's available.

## Contents
- [Swagger UI](#swagger-ui)
- [Authentication](#authentication)
- [Common Paths](#common-paths)
- [Response Shapes](#response-shapes)
- [Request Bodies](#request-bodies)
- [Push Status](#push-status)

## Swagger UI

The API server publishes its own Swagger UI, which is the source of truth for every path and field on your cluster's version:

```
<ORKA_API_URL>/api/v1/swagger
```

Connectivity check (no auth required):

```bash
curl <ORKA_API_URL>/api/v1/cluster-info
```

## Authentication

There is no login endpoint. Get a token from the CLI and pass it as a bearer token:

```bash
orka3 sa token <SA>                       # Automation and CI/CD (service account)
orka3 user get-token                      # Interactive use only (expires in 1 hour)
```

```bash
curl -H "Authorization: Bearer $ORKA_TOKEN" <ORKA_API_URL>/api/v1/namespaces/<NS>/vms
```

Keep the token in an environment variable or secret store, never inline in scripts.

## Common Paths

| Operation | Method and path |
|-----------|-----------------|
| List VMs | `GET /api/v1/namespaces/{namespace}/vms` |
| Deploy VM | `POST /api/v1/namespaces/{namespace}/vms` |
| Get VM | `GET /api/v1/namespaces/{namespace}/vms/{vm}` |
| Delete VM | `DELETE /api/v1/namespaces/{namespace}/vms/{vm}` |
| Save VM to new image | `POST /api/v1/namespaces/{namespace}/vms/{vm}/save` |
| Commit VM to its image | `POST /api/v1/namespaces/{namespace}/vms/{vm}/commit` |
| Push VM to OCI registry (Apple silicon only) | `POST /api/v1/namespaces/{namespace}/vms/{vm}/push` |
| List nodes | `GET /api/v1/namespaces/{namespace}/nodes` |
| List images | `GET /api/v1/namespaces/{namespace}/images` |

## Response Shapes

List responses wrap results in `items`:

```json
{"items": [{"name": "vm-5rjn4", "status": "Running", "owner": "system:serviceaccount:<NS>:<SA>", ...}]}
```

```bash
curl -s -H "Authorization: Bearer $ORKA_TOKEN" <ORKA_API_URL>/api/v1/namespaces/<NS>/vms | jq -r '.items[].name'
```

This differs from CLI `-o json`, which prints a bare array (`.[]`, `.[0].name`). Don't reuse `jq` filters between the two without adjusting.

## Request Bodies

**Deploy** (`image` or `vmConfig` required). Custom metadata is a flat map:

```json
{
  "name": "<VM_NAME>",
  "image": "<IMAGE>",
  "cpu": 4,
  "customMetadata": {"<KEY>": "<VALUE>"}
}
```

Don't use the Orka 2.x `vm_metadata.items` shape; it is not part of the 3.x deploy body. Other deploy fields mirror the CLI flags: `memory`, `node`, `tag`, `tagRequired`, `scheduler`, `reservedPorts`, `shouldGenerateName`, `timeout`, `vnc`, `displayWidth`, `displayHeight`, `displayDPI`.

**Save:**

```json
{"imageName": "<NEW_IMAGE>", "description": "<DESCRIPTION>"}
```

**Commit:**

```json
{"description": "<DESCRIPTION>"}
```

**Push** returns the name of the push job:

```json
{"imageReference": "<REGISTRY>/<REPO>/<IMAGE>:<TAG>"}
```

```json
{"jobName": "vm-push-qxjjf"}
```

## Push Status

There is no REST endpoint for push status. The CLI reads the push job's pods through the Kubernetes API. Check status with:

```bash
orka3 vm get-push-status <JOB_NAME> -n <NS>
```

See `vm-commands.md` for status values.
