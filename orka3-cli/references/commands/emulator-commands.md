# Emulator Commands Reference (Apple Silicon only, Early Access, v3.7.0-alpha+)

This reference provides detailed syntax and examples for Android emulator commands.

**Early access.** Requires Orka 3.7.0-alpha or later. Apple Silicon nodes only. Commands, flags, and behavior may change before general availability. Not recommended for production workloads. Contact support@macstadium.com with questions or feedback.

## Contents
- [orka3 emulator deploy](#orka3-emulator-deploy)
- [orka3 emulator list](#orka3-emulator-list)
- [orka3 emulator delete](#orka3-emulator-delete)
- [Connecting via ADB](#connecting-via-adb)
- [Known Limitations](#known-limitations)

## orka3 emulator deploy

Deploy an Android emulator paired with a running macOS VM. The emulator runs directly on the same physical host node as the VM (Apple Silicon does not support nested virtualization, so the emulator cannot run inside the VM itself) and connects to it over an ADB relay bridge.

**Syntax:**
```bash
orka3 emulator deploy [<AVD_NAME>] --vm <VM> --platform <PLATFORM> --image-type <TYPE> [--device-profile <PROFILE>] [--generate-name] [--timeout <MIN>] [flags]
```

**Options:**
- `--vm string` - Name of the running macOS VM to pair the emulator with (required)
- `--platform string` - Android platform level, e.g. `android-35`, `android-36` (required, no default)
- `--image-type string` - System image type, e.g. `google_apis`, `google_apis_playstore`, `default` (required, no default)
- `--device-profile string` - AVD device profile, e.g. `pixel_8`, `pixel_9`, `pixel_tablet` (optional; `avdmanager` default if omitted)
- `--generate-name` - Generate a unique name starting with `AVD_NAME`
- `--timeout int` - Minutes to wait for the deploy to complete (default: `5`)
- `-o, --output string` - Output format: json|wide
- `-n, --namespace string` - Target namespace

**Examples:**
```bash
orka3 emulator deploy --vm my-macos-vm --platform android-36 --image-type google_apis
orka3 emulator deploy my-emulator --vm my-macos-vm --platform android-36 --image-type google_apis --generate-name
orka3 emulator deploy --vm my-macos-vm --platform android-35 --image-type google_apis_playstore --device-profile pixel_8
orka3 emulator deploy --vm my-macos-vm --platform android-36 --image-type google_apis --timeout 10 -o json
```

**Notes:**
- Parent VM must be `Running`, or deploy fails with a `409`.
- Without `AVD_NAME`, Orka generates a name starting with `emu-`.
- Platform, image type, and device profile can't be changed after the emulator is created; delete and redeploy to change them.
- Values pass straight through to the Android SDK's `avdmanager`/`sdkmanager` tooling. Any combination those tools support works on a best-effort basis. The only hard constraint is an ARM-native system image, since the emulator runs directly on the Apple Silicon host.
- Deploy blocks until the emulator reaches `Running` or `Failed`, or until the timeout elapses. A timeout is not necessarily a failure: the emulator may still be `Pending` while its AVD boots. Poll with `orka3 emulator list <AVD_NAME>` until it settles. On `Failed`, the CLI prints the error and deletes the emulator.
- First deploy on a node may be slow: Android SDK components (roughly 2-4GB per platform/image-type pair) download at deploy time if not already cached on the host. There is no pre-caching in early access.
- Emulator lifecycle is tied to the parent VM. Deleting the VM automatically cleans up its emulator(s).

## orka3 emulator list

List Android emulators in the namespace.

**Syntax:**
```bash
orka3 emulator list [<AVD_NAME> ...] [--output <FORMAT>] [flags]
```

**Options:**
- `-o, --output string` - Output format: table|wide|json
- `-n, --namespace string` - Target namespace

**Examples:**
```bash
orka3 emulator list
orka3 emulator list --namespace orka-test --output wide
orka3 emulator list my-emulator my-other-emulator --output json
```

**Notes:**
- There is no `--vm` filter. Pass AVD names, or filter JSON by the `vm` field: `orka3 emulator list -o json | jq -r '.[] | select(.vm == "<VM>") | .name'`
- Table columns: `NAME`, `VM`, `STATUS`, `AGE`, `RELAY-IP`, `RELAY-PORT`, `NODE`; `-o wide` adds `PLATFORM`, `IMAGE-TYPE`, `DEVICE-PROFILE`. JSON keys are camelCase (`relayIp`, `relayPort`).
- Use this to poll emulator `status` (`Pending`/`Running`/`Failed`) after a deploy call times out.
- In the REST API, a `Failed` emulator includes an `errorMessage` explaining why.

## orka3 emulator delete

Delete one or more Android emulators.

**Syntax:**
```bash
orka3 emulator delete <AVD_NAME> [<AVD_NAME_2> ...] [flags]
```

**Examples:**
```bash
orka3 emulator delete my-emulator
orka3 emulator delete my-emulator my-other-emulator --namespace orka-test
```

**Notes:**
- Cannot be undone.
- Manual delete is only needed to remove an emulator before its parent VM is deleted. Deleting the VM cleans up its emulator(s) automatically.

## Connecting via ADB

From inside the macOS VM, connect using the relay IP and port from `orka3 emulator list` (`RELAY-IP`/`RELAY-PORT` columns; `relayIp`/`relayPort` in CLI JSON; `relayIP`/`relayPort` in the REST API):

```bash
orka3 emulator list <AVD_NAME> -o json | jq -r '.[0] | "\(.relayIp):\(.relayPort)"'   # Run where the CLI is configured
adb connect <RELAY_IP>:<RELAY_PORT>                                                   # Run inside the VM
adb devices
```

Standard ADB operations work once connected: `adb install`, `adb shell`, `adb pull`, `adb push`. The relay IP is currently the host's NAT gateway address (`192.168.64.1`), but treat the listed relay IP and port as opaque values rather than hardcoding them.

## Known Limitations

- **Node-level network isolation only.** Relay ports are reachable by any VM running on the same physical node, not just the VM the emulator is attached to. Emulators are unreachable from VMs on other nodes. Per-VM isolation is planned for a future release.
- **NAT only.** Bridged networking is not supported: the ADB relay requires the host's NAT network, so emulators are only available on NAT-networked VMs.
- **Ephemeral.** No persistent AVD state between deploys; each deploy creates a fresh emulator. No support yet for packaging custom AVD configurations as Orka images.
- **No pre-caching.** SDK components download at deploy time if not already on the host node; expect slower first deploys per node.
