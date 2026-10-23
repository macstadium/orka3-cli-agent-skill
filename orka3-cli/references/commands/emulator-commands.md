# Emulator Commands Reference (Apple Silicon only)

This reference provides detailed syntax and examples for Android emulator and emulator configuration commands.

**Generally available in Orka 4.0.** Apple Silicon nodes only. Introduced as early access in Orka 3.7.0-alpha. Emulator configurations, `--config`, and `--grpc` require Orka 4.0 or later. `--vm`, `--platform`, `--image-type`, and `--device-profile` were already in the alpha; in 4.0, `--platform` and `--image-type` aren't required when `--config` is set.

Emulator commands resolve the namespace the same way as `vm`: the `--namespace` flag, then the `ORKA_DEFAULT_NAMESPACE` environment variable, then the namespace in the `orka` kubeconfig context, then `orka-default`. `orka3 user login` resets the context namespace to `orka-default`, so use `ORKA_DEFAULT_NAMESPACE` for a lasting default. Emulator configurations always live in `orka-default`, whatever your default namespace is.

Aliases for `orka3 emulator` are `emu`, `emus`, and `emulators`. Aliases for `orka3 emulator-config` are `emc`, `emuconfig`, `emuconfigs`, and `emulator-configs`.

## Contents
- [orka3 emulator deploy](#orka3-emulator-deploy)
- [orka3 emulator list](#orka3-emulator-list)
- [orka3 emulator delete](#orka3-emulator-delete)
- [orka3 emulator-config create](#orka3-emulator-config-create)
- [orka3 emulator-config list](#orka3-emulator-config-list)
- [orka3 emulator-config delete](#orka3-emulator-config-delete)
- [Connecting via ADB](#connecting-via-adb)
- [gRPC endpoint](#grpc-endpoint)
- [Sizing and density](#sizing-and-density)
- [REST API](#rest-api)
- [Known Issues and Limitations](#known-issues-and-limitations)

## orka3 emulator deploy

Deploy an Android emulator paired with a running Orka VM. The emulator runs directly on the same physical host node as the VM (Apple Silicon does not support nested virtualization, so the emulator cannot run inside the VM itself) and connects to it over an ADB relay bridge.

Describe the emulator either with `--platform` and `--image-type`, or with `--config` to take those settings from an emulator configuration.

**Syntax:**
```bash
orka3 emulator deploy [AVD_NAME] --vm <VM_NAME> (--platform <PLATFORM> --image-type <IMAGE_TYPE> | --config <CONFIG_NAME>) [flags]
```

**Options:**
- `--vm string` - (Required) Name of the running Orka VM to pair the emulator with
- `--platform string` - (Required unless `--config` is set) Android platform level, as the Android SDK names it, for example `android-35`, `android-36`, `android-37.0`
- `--image-type string` - (Required unless `--config` is set) System image type, for example `google_apis`
- `--config string` - (Optional) Name of the emulator configuration to deploy from
- `--device-profile string` - (Optional) AVD device profile, for example `pixel_8`. If omitted, uses the configuration's profile, or the `avdmanager` default. Set to `""` to force the `avdmanager` default even when the configuration sets one.
- `--grpc` - (Optional) Start the emulator's gRPC endpoint alongside ADB. If omitted, uses the configuration's setting, or gRPC stays off. Set to `false` to keep gRPC off even when the configuration turns it on.
- `--generate-name` - (Optional) Generate a unique name starting with the provided `AVD_NAME`
- `--timeout int` - (Optional) Minutes to wait for the deployment to complete (default: `5`)
- `-o, --output string` - (Optional) Output format: `json`|`wide`
- `-n, --namespace string` - (Optional) Namespace to deploy into (default: your default namespace, see above)

**Examples:**
```bash
# Deploy an emulator paired with a running VM
orka3 emulator deploy --vm my-macos-vm --platform android-36 --image-type google_apis

# Deploy a named emulator
orka3 emulator deploy my-emulator --vm my-macos-vm --platform android-36 --image-type google_apis

# Deploy with a specific device profile
orka3 emulator deploy --vm my-macos-vm --platform android-35 --image-type google_apis --device-profile pixel_8

# Deploy from an emulator configuration
orka3 emulator deploy --vm my-macos-vm --config android-36-google-apis

# Deploy from a configuration, overriding its device profile
orka3 emulator deploy --vm my-macos-vm --config android-36-google-apis --device-profile pixel_tablet

# Deploy from a configuration, ignoring the device profile it sets (avdmanager default)
orka3 emulator deploy --vm my-macos-vm --config android-36-google-apis --device-profile ""

# Deploy with the gRPC endpoint enabled
orka3 emulator deploy --vm my-macos-vm --platform android-36 --image-type google_apis --grpc

# Deploy from a configuration that turns gRPC on, but keep it off for this emulator
orka3 emulator deploy --vm my-macos-vm --config android-36-grpc --grpc=false
```

**Notes:**
- If you don't provide an `AVD_NAME`, Orka generates a unique name starting with `emu-`. A name already in use fails unless you also pass `--generate-name`.
- The paired VM must be running. Deploying against a stopped VM fails immediately with the reason `PairedVMStopped`.
- Platform, device profile, and image type values pass straight through to the Android SDK's `avdmanager`/`sdkmanager` tooling, so any combination those tools support works on a best-effort basis. The only hard constraint is an ARM-native system image, since the emulator runs directly on the Apple Silicon host. Common values: platforms `android-35`/`android-36`/`android-37.0` (use the SDK's own name, including a minor version where it has one); device profiles `pixel_8`/`pixel_9`/`pixel_tablet`; image types `google_apis`/`google_apis_playstore`/`default`.
- Platform, system image, and device profile can't be changed after the emulator is created. Delete it and deploy a new one.
- Any of `--platform`, `--image-type`, and `--device-profile` set alongside `--config` override the configuration.
- Deploy waits until the emulator is running, or until the timeout elapses. A timeout is not necessarily a failure: the emulator may still be `Pending` while its AVD boots. Poll with `orka3 emulator list <AVD_NAME>` until it settles. If the emulator reaches `Failed`, the CLI prints the error and deletes the emulator.
- First deploy on a node may be slow: Android SDK components (roughly 2-4GB per platform and image type pair) download at deploy time if not already cached on the host.

**There is no `--device`, `--cpu`, or `--memory` flag.** Earlier versions of this reference listed them; the CLI has never accepted them, including in 3.7.0-alpha. Use `--device-profile` for the device.

## orka3 emulator list

Show basic or extended information about Android emulators. With no names, lists every emulator in the namespace.

**Syntax:**
```bash
orka3 emulator list [AVD_NAME_1 [AVD_NAME_2 ...]] [--namespace <NAMESPACE>] [--output wide|json] [flags]
```

**Options:**
- `-o, --output string` - (Optional) Output format: `table` (default)|`wide`|`json`
- `-n, --namespace string` - (Optional) Namespace to list from (default: your default namespace, see above)

**Examples:**
```bash
# List all emulators in the default namespace
orka3 emulator list

# List emulators in another namespace with extended information
orka3 emulator list --namespace orka-test --output wide

# Show a specific emulator as JSON
orka3 emulator list my-emulator --output json
```

**Notes:**
- Default table columns: `NAME`, `VM`, `STATUS`, `RELAY-IP`, `RELAY-PORT`, `GRPC-PORT`, `NODE`, `AGE`. `GRPC-PORT` is empty for an emulator deployed without gRPC. `-o wide` adds `PLATFORM`, `IMAGE-TYPE`, `DEVICE-PROFILE`, and `OWNER`.
- Use this to check status (`Pending`, `Running`, `Failed`) after a deploy times out. A failed emulator carries a reason in its error message.
- **There is no `--vm` filter.** Earlier versions of this reference listed one; the CLI has never had it. Pass AVD names, or filter JSON on the `vm` field: `orka3 emulator list -o json | jq -r '.[] | select(.vm == "<VM_NAME>") | .name'`. The API's `GET /emulators/android?vm=<VM_NAME>` filter is a separate surface and does exist.
- **JSON field names differ between the CLI and the API.** CLI JSON keys are the column names in camelCase: `relayIp`, `relayPort`, `grpcPort`. The API returns `relayIP`, `relayPort`, and `grpcRelayPort`. Both are correct for their own surface. Don't normalize one to the other in a script.

## orka3 emulator delete

Delete one or more Android emulators and free their resources on the node. This cannot be undone.

**Syntax:**
```bash
orka3 emulator delete <AVD_NAME> [AVD_NAME_2 ...] [--namespace <NAMESPACE>] [flags]
```

**Options:**
- `-n, --namespace string` - (Optional) Namespace of the emulators (default: your default namespace, see above)

**Examples:**
```bash
orka3 emulator delete my-emulator
orka3 emulator delete my-emulator my-other-emulator --namespace orka-test
```

**Notes:**
- Manual delete is only needed to remove an emulator before its paired VM is deleted. Deleting the VM cleans up its emulators automatically.

## orka3 emulator-config create

Create an emulator configuration: a template storing a platform, system image type, and optionally a device profile and gRPC setting, so pipelines deploy with `--config` instead of repeating flags. Requires Orka 4.0 or later.

**Syntax:**
```bash
orka3 emulator-config create <CONFIG_NAME> --platform <PLATFORM> --image-type <IMAGE_TYPE> [flags]
```

**Options:**
- `--platform string` - (Required) Android platform level, as the Android SDK names it, for example `android-35`, `android-36`, `android-37.0`
- `--image-type string` - (Required) System image type, for example `google_apis`
- `--device-profile string` - (Optional) AVD device profile, for example `pixel_8`
- `--grpc` - (Optional) Emulators deployed from this configuration start the gRPC endpoint

**Examples:**
```bash
orka3 emc create android-36-google-apis --platform android-36 --image-type google_apis
orka3 emc create pixel-8 --platform android-35 --image-type google_apis --device-profile pixel_8
orka3 emc create android-36-grpc --platform android-36 --image-type google_apis --grpc
```

**Notes:**
- The configuration name must not exceed 63 characters, must consist of lowercase alphanumerics, dashes, or dots, must start and end with a lowercase alphanumeric, and must be unique in the cluster.
- All emulator configurations reside in `orka-default` and are available to every user and service account with access to it.
- Orka copies the configuration's settings into the emulator at deploy time, so changing or deleting a configuration never affects emulators already running.
- `--grpc` on a configuration turns gRPC on for every emulator deployed from it. A single deploy can still turn it off with `--grpc=false`. The REST API accepts `grpc` (bool) on configuration create and returns it in configuration responses when the configuration sets it.

## orka3 emulator-config list

Show basic or extended information about emulator configurations. With no names, lists every configuration. Requires Orka 4.0 or later.

**Syntax:**
```bash
orka3 emulator-config list [CONFIG_1 [CONFIG_2 ...]] [--output wide|json] [flags]
```

**Options:**
- `-o, --output string` - (Optional) Output format: `table` (default)|`wide`|`json`

**Examples:**
```bash
orka3 emc list
orka3 emc list --output wide
orka3 emc list android-36-google-apis pixel-8
```

**Notes:**
- Default table columns: `NAME`, `PLATFORM`, `IMAGE-TYPE`, `DEVICE-PROFILE`, `GRPC`, `AGE`. `-o wide` adds `OWNER`.

## orka3 emulator-config delete

Delete one or more emulator configurations. Requires Orka 4.0 or later.

**Syntax:**
```bash
orka3 emulator-config delete <CONFIG_NAME> [CONFIG_2 ...] [flags]
```

**Notes:**
- You can delete only configurations you created. Orka administrators can delete any configuration.
- Emulators already deployed from a configuration are not affected.

## Connecting via ADB

Once the emulator is `Running`, get its relay IP and relay port from `orka3 emulator list` (the `RELAY-IP` and `RELAY-PORT` columns) or from the API response. From inside the paired macOS VM:

```bash
orka3 emulator list <AVD_NAME> -o json | jq -r '.[0] | "\(.relayIp):\(.relayPort)"'   # Run where the CLI is configured
adb connect <RELAY_IP>:<RELAY_PORT>                                                   # Run inside the paired VM
adb devices
```

Always use the returned values rather than hardcoding an IP or port. Standard ADB operations work once connected (`adb install`, `adb shell`, `adb pull`, `adb push`) on `google_apis` and `default` images.

## gRPC endpoint

An emulator deployed with `--grpc`, or from a configuration that turns gRPC on, also starts its gRPC endpoint, so a gRPC client can drive the emulator or stream its display. Connect from the paired VM at the relay IP, on the port in the `GRPC-PORT` column (`grpcRelayPort` in the API). ADB uses `RELAY-PORT`.

Like the ADB endpoint, the gRPC endpoint speaks plaintext gRPC over HTTP/2 with no TLS and no authentication, and only VMs on the same host can reach it. To reach it from elsewhere, forward the port through the paired VM.

If the deploy prints `Warning: gRPC was requested but the emulator reports no gRPC port.`, the emulator is running and usable over ADB, but the node's Orka components predate gRPC. Check that the node is on Orka 4.0.

## Sizing and density

Each emulator runs on the host next to the VMs, so it uses host memory and CPU on top of theirs. An emulator's CPU and memory come from its device profile; you can't set them at deploy time.

- **Plan for about 5 to 6 GB of host memory per emulator.** In MacStadium's capacity testing, a default `pixel_9` emulator (4 cores and about 2.5 GB of guest RAM) used about 5.7 GB of host memory.
- **Memory usually limits how many emulators a node can run.** Add the emulators' memory to the memory of the VMs on the node, and leave room for the host itself. Four emulators use about 23 GB of host memory, which leaves little room for VMs on a 32 GB node.
- **Emulators slow down first when a node runs short of memory.** UI and screenshot tests can then become flaky, for example with small pixel shifts between runs. Try fewer emulators per node.
- Orka 4.0 doesn't cap emulators per node in the scheduler (see the pod quota notes in `references/workflows/upgrade-workflows.md`), so this sizing is on you.

For UI and screenshot tests, turn off animations in the emulator after you connect:

```bash
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0
```

Source: [Android emulators on Orka](https://docs.macstadium.com/orka/orka-resources/android-emulators).

## REST API

Emulators: `/api/v1/namespaces/{namespace}/emulators/android`. Emulator configurations: `/api/v1/namespaces/{namespace}/emulatorconfigs/android` (Orka 4.0+, `orka-default` only; other namespaces return `400`). The deploy request accepts `config` and `grpc`, and responses include `grpcRelayPort` for an emulator deployed with gRPC. Full request and response shapes are in `references/commands/rest-api.md`.

## Known Issues and Limitations

- **Known issue in Orka 4.0: Google Play Store system images don't accept ADB.** An emulator deployed with `--image-type google_apis_playstore` reaches `Running` and returns a relay port, but every `adb` command from the paired VM fails with `device unauthorized`. Play Store images require each ADB key to be authorized on the device, and Orka emulators run headless, so there's no way to approve it. Use `google_apis` instead. It includes Google Play services (Firebase Cloud Messaging, Maps, Sign-In, Location, ML Kit), but not the Play Store app or Play certification, so you can't test Play Store install and update flows, Play Billing or in-app purchases, or install referrer, and Play Integrity checks behave differently. The CLI's own help still shows `google_apis_playstore` examples; don't copy them for ADB workflows.
- Network isolation is node-level, not per-VM. Relay ports are reachable by any VM on the same physical node. Emulators are not reachable from VMs on other nodes.
- Bridged networking is not supported. The emulator relies on the host NAT network for the ADB relay, so emulators are available only on NAT-networked VMs.
- Emulators are ephemeral. There is no persistent AVD state between runs; each deploy creates a fresh emulator.
- No support yet for packaging custom AVD configurations as Orka images.
- Android SDK components download at deploy time if not already cached on the node.

**Emulator lifecycle is tied to the paired VM:**
- Deleting the VM cleans up its emulators automatically.
- If the VM stops or fails, the emulator fails with the reason `PairedVMStopped` and its ports are released for the next emulator on that node.
- The Kubernetes scheduler places the emulator on its paired VM's node. If it can't, for example because the node is cordoned, the emulator stays `Pending` with the scheduler's reason, and after 5 minutes fails with the reason `EmulatorUnschedulable`.
