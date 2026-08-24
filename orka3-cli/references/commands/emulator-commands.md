# Emulator Commands Reference (Apple Silicon only, Early Access — v3.7.0-alpha+)

This reference provides detailed syntax and examples for Android emulator commands.

**Early access.** Requires Orka 3.7.0-alpha or later. Apple Silicon nodes only. Commands, defaults, and behavior may change before general availability. Not recommended for production workloads. Contact support@macstadium.com with questions or feedback.

## Contents
- [orka3 emulator deploy](#orka3-emulator-deploy)
- [orka3 emulator list](#orka3-emulator-list)
- [orka3 emulator delete](#orka3-emulator-delete)
- [Connecting via ADB](#connecting-via-adb)
- [Known Limitations](#known-limitations)

## orka3 emulator deploy

Deploy an Android emulator attached to a running macOS VM. The emulator runs directly on the same physical host node as the VM (Apple Silicon does not support nested virtualization, so the emulator cannot run inside the VM itself) and connects to it over an ADB relay bridge.

**Syntax:**
```bash
orka3 emulator deploy --vm <VM> [--platform <PLATFORM>] [--device <DEVICE>] [--image-type <TYPE>] [--cpu <N>] [--memory <MB>] [--timeout <MIN>] [flags]
```

**Options:**
- `--vm string` - Name of the running macOS VM to attach the emulator to (required)
- `--platform string` - Android platform level (default: `android-36`)
- `--device string` - Device profile (default: `pixel_9`)
- `--image-type string` - System image type (default: `google_apis`)
- `--cpu int` - CPU cores to allocate to the emulator
- `--memory int` - Memory in MB to allocate to the emulator
- `--timeout int` - Deploy timeout in minutes (default: `5`)

**Examples:**
```bash
orka3 emulator deploy --vm my-macos-vm
orka3 emulator deploy --vm my-macos-vm --platform android-35 --device pixel_8
orka3 emulator deploy --vm my-macos-vm --image-type google_apis_playstore --cpu 4 --memory 4096
orka3 emulator deploy --vm my-macos-vm --device pixel_tablet --timeout 10
```

**Notes:**
- Parent VM must be `Running`, or deploy fails with a `409`.
- Platform, device, and image-type values pass straight through to the Android SDK's `avdmanager`/`sdkmanager` tooling. Any combination those tools support works on a best-effort basis — the only hard constraint is an ARM-native system image, since the emulator runs directly on the Apple Silicon host. Common values: platforms `android-35`/`android-36`; devices `pixel_8`/`pixel_9`/`pixel_tablet`; image types `google_apis`/`google_apis_playstore`/`default`.
- Deploy blocks until the emulator reaches `Running` or `Failed`, or until the timeout elapses — whichever comes first. A timeout is not necessarily a failure: the emulator may still be `Pending` while its AVD boots. Poll with `orka3 emulator list` until it settles.
- Response includes `adbRelayIP` and `adbRelayPort` — always use these values to connect (see [Connecting via ADB](#connecting-via-adb)), never hardcode an IP or port.
- First deploy on a node may be slow: Android SDK components (roughly 2-4GB per platform/image-type pair) download at deploy time if not already cached on the host. There is no pre-caching in early access.
- Emulator lifecycle is tied to the parent VM — deleting the VM automatically cleans up its emulator(s).

## orka3 emulator list

List Android emulators.

**Syntax:**
```bash
orka3 emulator list [<EMULATOR>] [--vm <VM>] [--output <FORMAT>] [flags]
```

**Options:**
- `--vm string` - Filter by parent VM name
- `-o, --output string` - Output format: table|wide|json

**Examples:**
```bash
orka3 emulator list
orka3 emulator list --vm my-macos-vm
orka3 emulator list my-macos-vm-avd-0 --output json
```

**Notes:**
- Use this to poll emulator status (`Pending`/`Running`/`Failed`) after a deploy call times out.
- When `phase` is `Failed`, the response includes an `errorMessage` explaining why.

## orka3 emulator delete

Delete an Android emulator.

**Syntax:**
```bash
orka3 emulator delete <EMULATOR> [flags]
```

**Examples:**
```bash
orka3 emulator delete my-macos-vm-avd-0
```

**Notes:**
- Manual delete is only needed to remove an emulator before its parent VM is deleted — deleting the VM cleans up its emulator(s) automatically.

## Connecting via ADB

From inside the macOS VM, connect using the `adbRelayIP`/`adbRelayPort` returned by `deploy` or `list`:

```bash
adb connect <adbRelayIP>:<adbRelayPort>
adb devices
```

Standard ADB operations work once connected: `adb install`, `adb shell`, `adb pull`, `adb push`. The relay IP is currently always the host's NAT gateway address (`192.168.64.1`), but treat `adbRelayIP`/`adbRelayPort` as opaque values from the API response rather than hardcoding them — they are the source of truth, not the underlying network detail.

## Known Limitations

- **Node-level network isolation only.** Relay ports are reachable by any VM running on the same physical node, not just the VM the emulator is attached to. Emulators are unreachable from VMs on other nodes. Per-VM isolation is planned for a future release.
- **NAT only.** Bridged networking is not supported — the ADB relay requires the host's NAT network, so emulators are only available on NAT-networked VMs.
- **Ephemeral.** No persistent AVD state between deploys; each deploy creates a fresh emulator. No support yet for packaging custom AVD configurations as Orka images.
- **No pre-caching.** SDK components download at deploy time if not already on the host node; expect slower first deploys per node.
