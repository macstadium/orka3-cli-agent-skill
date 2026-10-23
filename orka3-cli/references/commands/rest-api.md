# REST API Reference

This reference covers calling the Orka API server directly, for tools that can't shell out to the Orka3 CLI. Prefer the CLI where it's available.

## Contents
- [Swagger UI](#swagger-ui)
- [Authentication](#authentication)
- [Common Paths](#common-paths)
- [Response Shapes](#response-shapes)
- [Request Bodies](#request-bodies)
- [Push Status](#push-status)
- [Android Emulators (GA in 4.0)](#android-emulators-ga-in-40)
- [Orka 4.0 API Changes](#orka-40-api-changes)

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
| Save VM to new image (NFS, deprecated in 4.0) | `POST /api/v1/namespaces/{namespace}/vms/{vm}/save` |
| Commit VM to its image (NFS, deprecated in 4.0) | `POST /api/v1/namespaces/{namespace}/vms/{vm}/commit` |
| Push VM to OCI registry (Apple silicon only) | `POST /api/v1/namespaces/{namespace}/vms/{vm}/push` |
| List nodes | `GET /api/v1/namespaces/{namespace}/nodes` |
| List images (NFS, deprecated in 4.0) | `GET /api/v1/namespaces/{namespace}/images` |
| Grant, list, or revoke a role (4.0+) | `POST /api/v1/rbac/{role}/subjects/add`, `GET /api/v1/rbac/{role}/subjects`, `DELETE /api/v1/rbac/{role}/subjects/remove` |

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

Don't use the Orka 2.x `vm_metadata.items` shape; it is not part of the 3.x deploy body. Other deploy fields mirror the CLI flags: `memory`, `node`, `tag`, `tagRequired`, `scheduler`, `reservedPorts`, `shouldGenerateName`, `timeout`, `vnc`, `displayWidth`, `displayHeight`, `displayDPI`. On Orka 4.0, `userdata` takes the base64-encoded User Data script (up to 64 KiB), and VM responses include `userdataPhase`.

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

## Android Emulators (GA in 4.0)

Generally available in Orka 4.0, early access in 3.7.0-alpha. Apple silicon only. Same base path (`/api/v1/namespaces/{namespace}`), bearer auth, and RBAC as VMs. Source: [Android emulators on Orka](https://docs.macstadium.com/orka/orka-resources/android-emulators).

| Operation | Method and path |
|-----------|-----------------|
| Deploy an emulator on a running VM | `POST /api/v1/namespaces/{namespace}/emulators/android` |
| List emulators (optional `?vm=<VM_NAME>` filter) | `GET /api/v1/namespaces/{namespace}/emulators/android` |
| Get one emulator | `GET /api/v1/namespaces/{namespace}/emulators/android/{emulator}` |
| Delete an emulator | `DELETE /api/v1/namespaces/{namespace}/emulators/android/{emulator}` |
| Create an emulator configuration (4.0+) | `POST /api/v1/namespaces/orka-default/emulatorconfigs/android` |
| List emulator configurations (4.0+) | `GET /api/v1/namespaces/orka-default/emulatorconfigs/android` |
| Get one emulator configuration (4.0+) | `GET /api/v1/namespaces/orka-default/emulatorconfigs/android/{config}` |
| Delete an emulator configuration (4.0+) | `DELETE /api/v1/namespaces/orka-default/emulatorconfigs/android/{config}` |

The configuration path is `/api/v1/namespaces/{namespace}/emulatorconfigs/android`, but configurations exist only in `orka-default`; creating one in another namespace returns `400`.

**Deploy body:** `vmName` is required, plus either `config` (4.0+, the name of an emulator configuration) or both `platform` and `imageType`. Request fields override the configuration. Optional: `deviceProfile` (`avdmanager` default if omitted; an explicit empty string declines the configuration's profile), `grpc` (4.0+, bool; `false` declines a configuration that turns gRPC on), `name` (generated, starting `emu-`, if omitted), `shouldGenerateName` (bool, appends a random suffix to `name`), `timeout` (minutes, default 10).

```json
{"vmName": "my-macos-vm", "platform": "android-36", "imageType": "google_apis", "deviceProfile": "pixel_9"}
```

```json
{"vmName": "my-macos-vm", "config": "android-36-google-apis", "grpc": true}
```

**Configuration create body (4.0+):** `name`, `platform`, and `imageType` are required; `deviceProfile` and `grpc` (bool) are optional. Configuration responses return `name`, `platform`, `imageType`, and `deviceProfile` and `grpc` when the configuration sets them.

Deploy blocks until the emulator reaches `Running` or `Failed`, or the timeout passes. On `Failed`, Orka deletes the emulator and returns `500` with the failure message. On timeout it returns `500` but does not delete the emulator: `GET` it to see whether it reached `Running`.

**Responses:** deploy returns `name`, `status`, `nodeName`, `relayIP`, `relayPort`, and, for an emulator deployed with gRPC, `grpcRelayPort`. `GET` returns one emulator with those fields plus `vmName`, `platform`, `imageType`, `deviceProfile`; list wraps them in `{"items": [...]}`. `errorMessage` appears only when `status` is `Failed`. `DELETE` returns `200` with no body. Note the REST keys are `relayIP` and `grpcRelayPort`, while CLI JSON uses `relayIp` and `grpcPort`.

**Errors:** `400` missing `vmName`, or missing both `config` and `platform`/`imageType`; `403` RBAC; `404` emulator not found; `409` an emulator with that name already exists; `500` deploy failed or timed out, or an unexpected error.

## Orka 4.0 API Changes

Orka 4.0 is Apple silicon only and removes the Intel-only API surface. Full list: [Orka 4.0.0 release notes](https://docs.macstadium.com/orka/orka-upgrades-and-release-notes/orka-release-notes).

**Removed routes return `404`:**
- `POST /api/v1/namespaces/{namespace}/vms/{vm}/exec`
- `POST /api/v1/namespaces/{namespace}/images` (image generate)
- `POST /api/v1/namespaces/{namespace}/upload/image` and `GET`/`HEAD /api/v1/namespaces/{namespace}/images/{image}/download`. Apple silicon images move through OCI push and pull.
- All `/isos`, `/remoteisos`, and `POST /upload/iso` routes

**`GET /api/v1/cluster-info`** no longer returns `gpuPassthroughEnabled`. The other fields are unchanged.

**Intel-only request fields return `400`.** VM deploy and VM config create reject a request that sets `iso` or `systemSerial`, or sets `gpuPassthrough` or `legacyIO` to `true`. Resize rejects `vmUser` and `vmPassword`. The error names the field, for example `iso is not supported as of Orka 4.0, which no longer supports Intel VMs`. Values that already describe Apple silicon still pass: `false`, `""`, or `null`. `netBoost` is accepted with any value and ignored, because net boost is always on for Apple silicon (this keeps 3.6-era clients such as the Jenkins plugin working). These fields no longer appear in VM or VM config responses.

**Kubernetes resources.** The admission webhook applies the same rules to `VirtualMachineInstance` and `VirtualMachineConfig` objects created with `kubectl`. An object that references an amd64 (Intel) image is rejected with `Intel VMs are not supported as of Orka 4.0`; one that sets an Intel-only field is rejected with `<FIELD> is not supported as of Orka 4.0, which no longer supports Intel VMs`. Objects created on 3.6 can still be updated and deleted, so an upgrade doesn't leave objects you can't clean up.

**Deprecated, still working:** the `images` and `remoteimages` routes and `POST /vms/{vm}/save` and `/vms/{vm}/commit` return a `Deprecation: true` header and a `Warning` header naming the OCI replacement. The `/api/v1/namespaces/{namespace}/rolebindings/orka-dev/subjects` routes are deprecated in favor of `/api/v1/rbac/{role}/subjects`. The `cache/images` routes and VM deploy aren't affected.
