# Emulator Commands Reference (Apple Silicon only)

This reference provides detailed syntax and examples for Android emulator and emulator configuration commands.

**Generally available in Orka 4.0.** Apple Silicon nodes only. Introduced as early access in Orka 3.7.0-alpha; the flags below are the 4.0 set and differ from the alpha. Emulator configurations, `--grpc`, and `--device-profile` require Orka 4.0 or later.

If `--namespace` is not set, emulator commands operate in the `orka-default` namespace. Aliases for `orka3 emulator` are `emu`, `emus`, and `emulators`. The alias for `orka3 emulator-config` is `emc`.

## Contents
- [orka3 emulator deploy](#orka3-emulator-deploy)
- [orka3 emulator list](#orka3-emulator-list)
- [orka3 emulator delete](#orka3-emulator-delete)
- [orka3 emulator-config create](#orka3-emulator-config-create)
- [orka3 emulator-config list](#orka3-emulator-config-list)
- [orka3 emulator-config delete](#orka3-emulator-config-delete)
- [Connecting via ADB](#connecting-via-adb)
- [gRPC endpoint](#grpc-endpoint)
- [Known Limitations](#known-limitations)

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
- `-n, --namespace string` - (Optional) Namespace to deploy into (default: `orka-default`)

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

# Deploy with the gRPC endpoint enabled
orka3 emulator deploy --vm my-macos-vm --platform android-36 --image-type google_apis --grpc
```

**Notes:**
- If you don't provide an `AVD_NAME`, Orka generates a unique name starting with `emu-`. A name already in use fails unless you also pass `--generate-name`.
- The paired VM must be running. Deploying against a stopped VM fails immediately with the reason `PairedVMStopped`.
- Platform, device profile, and image type values pass straight through to the Android SDK's `avdmanager`/`sdkmanager` tooling, so any combination those tools support works on a best-effort basis. The only hard constraint is an ARM-native system image, since the emulator runs directly on the Apple Silicon host. Common values: platforms `android-35`/`android-36`/`android-37.0` (use the SDK's own name, including a minor version where it has one); device profiles `pixel_8`/`pixel_9`/`pixel_tablet`; image types `google_apis`/`google_apis_playstore`/`default`.
- Platform, system image, and device profile can't be changed after the emulator is created. Delete it and deploy a new one.
- Deploy waits until the emulator is running, or until the timeout elapses. A timeout is not necessarily a failure: the emulator may still be `Pending` while its AVD boots. Poll with `orka3 emulator list` until it settles.
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
- `-n, --namespace string` - (Optional) Namespace to list from (default: `orka-default`)

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
- Default table columns: `NAME`, `VM`, `STATUS`, `RELAY-IP`, `RELAY-PORT`, `GRPC-PORT`, `NODE`, `AGE`. `GRPC-PORT` is empty for an emulator deployed without gRPC.
- Use this to check status (`Pending`, `Running`, `Failed`) after a deploy times out. A failed emulator carries a reason in its error message.
- **There is no `--vm` filter.** Earlier versions of this reference listed one; the CLI has never had it. The API's `GET /emulators/android?vm=<name>` filter is a separate surface and does exist.
- **JSON field casing differs between the CLI and the API.** The CLI's JSON output uses `relayIp`; the API returns `relayIP`. Both are correct for their own surface. Don't normalize one to the other in a script.

## orka3 emulator delete

Delete one or more Android emulators and free their resources on the node. This cannot be undone.

**Syntax:**
```bash
orka3 emulator delete <AVD_NAME> [AVD_NAME_2 ...] [--namespace <NAMESPACE>] [flags]
```

**Options:**
- `-n, --namespace string` - (Optional) Namespace of the emulators (default: `orka-default`)

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
- **gRPC on a configuration is CLI-only.** The REST create model has no `grpc` field; `orka3 emc create --grpc` writes the resource directly. You can still request gRPC for a single emulator with `grpc` in the API deploy request.

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
- Default table columns: `NAME`, `PLATFORM`, `IMAGE-TYPE`, `DEVICE-PROFILE`, `GRPC`, `AGE`.

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
adb connect <RELAY_IP>:<RELAY_PORT>
adb devices
```

Always use the returned values rather than hardcoding an IP or port. Standard ADB operations work once connected (`adb install`, `adb shell`, `adb pull`, `adb push`) on `google_apis` and `default` images.

## gRPC endpoint

An emulator deployed with `--grpc`, or from a configuration that turns gRPC on, also starts its gRPC endpoint, so a gRPC client can drive the emulator or stream its display. Connect from the paired VM at the relay IP, on the port in the `GRPC-PORT` column (`grpcRelayPort` in the API). ADB uses `RELAY-PORT`.

Like the ADB endpoint, the gRPC endpoint speaks plaintext gRPC over HTTP/2 with no TLS and no authentication, and only VMs on the same host can reach it. To reach it from elsewhere, forward the port through the paired VM.

## Known Limitations

- `google_apis_playstore` images don't accept ADB commands. The emulator reaches `Running` and returns a relay port, but every `adb` command fails with `device unauthorized`, because Play Store images require approving each ADB key on the device and Orka emulators run headless. There is no workaround. Use `google_apis`, which includes Google Play services (Firebase Cloud Messaging, Maps, Sign-In, Location, ML Kit) but not the Play Store app or Play certification.
- Network isolation is node-level, not per-VM. Relay ports are reachable by any VM on the same physical node. Emulators are not reachable from VMs on other nodes.
- Bridged networking is not supported. The emulator relies on the host NAT network for the ADB relay, so emulators are available only on NAT-networked VMs.
- Emulators are ephemeral. There is no persistent AVD state between runs; each deploy creates a fresh emulator.
- No support yet for packaging custom AVD configurations as Orka images.
- Android SDK components download at deploy time if not already cached on the node.

**Emulator lifecycle is tied to the paired VM:**
- Deleting the VM cleans up its emulators automatically.
- If the VM stops or fails, the emulator fails with the reason `PairedVMStopped` and its ports are released for the next emulator on that node.
- The Kubernetes scheduler places the emulator on its paired VM's node. If it can't, for example because the node is cordoned, the emulator stays `Pending` with the scheduler's reason, and after 5 minutes fails with the reason `EmulatorUnschedulable`.
