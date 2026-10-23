# REST API Reference

This reference covers calling the Orka API server directly, for tools that can't shell out to the Orka3 CLI. Prefer the CLI where it's available.

## Contents
- [Swagger UI](#swagger-ui)
- [Authentication](#authentication)
- [Common Paths](#common-paths)
- [Response Shapes](#response-shapes)
- [Request Bodies](#request-bodies)
- [Push Status](#push-status)
- [Android Emulators (3.7.0-alpha, early access)](#android-emulators-370-alpha-early-access)

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
orka3 sa token <SERVICE_ACCOUNT_NAME>     # Automation and CI/CD (service account)
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

## Android Emulators (3.7.0-alpha, early access)

Apple silicon only. Same base path (`/api/v1/namespaces/{namespace}`), bearer auth, and RBAC as VMs. Source: [Android emulators on Orka](https://docs.macstadium.com/orka/orka-resources/android-emulators).

| Operation | Method and path |
|-----------|-----------------|
| Deploy an emulator on a running VM | `POST /api/v1/namespaces/{namespace}/emulators/android` |
| List emulators (optional `?vm=<VM_NAME>` filter) | `GET /api/v1/namespaces/{namespace}/emulators/android` |
| Get one emulator | `GET /api/v1/namespaces/{namespace}/emulators/android/{emulator}` |
| Delete an emulator | `DELETE /api/v1/namespaces/{namespace}/emulators/android/{emulator}` |

**Deploy body:** `vmName`, `platform`, and `imageType` are required. Optional: `deviceProfile` (`avdmanager` default if omitted), `name` (generated, starting `emu-`, if omitted), `shouldGenerateName` (bool, appends a random suffix to `name`), `timeout` (minutes, default 10).

```json
{"vmName": "my-macos-vm", "platform": "android-36", "imageType": "google_apis", "deviceProfile": "pixel_9"}
```

Deploy blocks until the emulator reaches `Running` or `Failed`, or the timeout passes. On `Failed`, Orka deletes the emulator and returns `500` with the failure message. On timeout it returns `500` but does not delete the emulator: `GET` it to see whether it reached `Running`.

**Responses:** deploy returns `name`, `status`, `nodeName`, `relayIP`, `relayPort`. `GET` returns one emulator with those fields plus `vmName`, `platform`, `imageType`, `deviceProfile`; list wraps them in `{"items": [...]}`. `errorMessage` appears only when `status` is `Failed`. `DELETE` returns `200` with no body. Note the REST key is `relayIP`, while CLI JSON uses `relayIp`.

**Errors:** `400` missing `vmName`, `platform`, or `imageType`; `403` RBAC; `404` emulator not found; `409` an emulator with that name already exists; `500` deploy failed or timed out, or an unexpected error.
