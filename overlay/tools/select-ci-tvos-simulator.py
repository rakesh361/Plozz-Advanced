#!/usr/bin/env python3
"""Select an available tvOS simulator matching the CI build SDK."""

import argparse
import json
import subprocess
import sys


def simctl_list(kind):
    return json.loads(subprocess.check_output(
        ['xcrun', 'simctl', 'list', kind, '--json'],
        text=True, timeout=300,
    ))


def boot_device(identifier):
    subprocess.run(['xcrun', 'simctl', 'bootstatus', identifier, '-b'],
                   stdout=sys.stderr, check=True, timeout=300)


def prepare_device(sdk_version):
    """Return a bootable CI device, provisioning the matching runtime if needed."""
    runtime = 'com.apple.CoreSimulator.SimRuntime.tvOS-' + sdk_version.replace('.', '-')
    try:
        device = select_device(simctl_list('devices'), sdk_version)
    except ValueError:
        device = None
    if device is not None:
        try:
            boot_device(device[0])
            return device
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            print(f'Boot failed for {device[0]}; provisioning a fresh device: {error}', file=sys.stderr)

    def runtime_available():
        return any(r.get('identifier') == runtime and r.get('isAvailable')
                   for r in simctl_list('runtimes').get('runtimes', []))

    if not runtime_available():
        print(f'Installing tvOS {sdk_version} simulator runtime', file=sys.stderr)
        subprocess.run(
            ['xcodebuild', '-downloadPlatform', 'tvOS', '-buildVersion', sdk_version],
            stdout=sys.stderr, check=True, timeout=900,
        )
        if not runtime_available():
            raise ValueError(f'Runtime {runtime} unavailable after installation')
    types = simctl_list('devicetypes').get('devicetypes', [])
    types = [t for t in types if 'Apple TV' in t.get('name', '')]
    types.sort(key=lambda t: ('1080p' not in t['name'], '4K' not in t['name'], t['name']))
    if not types:
        raise ValueError('No Apple TV simulator device type installed')
    name = 'Apple TV Plozz Advanced CI'
    identifier = subprocess.check_output(
        ['xcrun', 'simctl', 'create', name, types[0]['identifier'], runtime],
        text=True, timeout=300,
    ).strip()
    boot_device(identifier)
    return identifier, name


def select_device(devices: dict, sdk_version: str) -> tuple[str, str]:
    runtime = "com.apple.CoreSimulator.SimRuntime.tvOS-" + sdk_version.replace(".", "-")
    candidates = [
        device for device in devices.get("devices", {}).get(runtime, [])
        if device.get("isAvailable") and "Apple TV" in device.get("name", "")
    ]
    if not candidates:
        raise ValueError(f"No available Apple TV simulator for {runtime}")
    candidates.sort(key=lambda device: (
        "1080p" not in device["name"],
        "4K" not in device["name"],
        device["name"],
        device["udid"],
    ))
    return candidates[0]["udid"], candidates[0]["name"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-version", required=True)
    parser.add_argument('--prepare', action='store_true',
                        help='Boot a matching device and provision it if needed (CI only)')
    args = parser.parse_args()
    try:
        if args.prepare:
            identifier, name = prepare_device(args.sdk_version)
        else:
            identifier, name = select_device(simctl_list('devices'), args.sdk_version)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"CI simulator selection failed: {error}", file=sys.stderr)
        return 1
    print(f"Selected tvOS {args.sdk_version}: {name} ({identifier})", file=sys.stderr)
    print(identifier)
    return 0


if __name__ == "__main__":
    sys.exit(main())
