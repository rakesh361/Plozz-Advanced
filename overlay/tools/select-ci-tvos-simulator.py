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


def prepare_device(sdk_version):
    """Repair missing CI runtime/device provisioning without changing OS version."""
    devices = simctl_list('devices')
    try:
        return select_device(devices, sdk_version)
    except ValueError:
        pass
    runtime = 'com.apple.CoreSimulator.SimRuntime.tvOS-' + sdk_version.replace('.', '-')
    runtimes = simctl_list('runtimes')
    if not any(r.get('identifier') == runtime and r.get('isAvailable')
               for r in runtimes.get('runtimes', [])):
        print(f'Installing tvOS {sdk_version} simulator runtime', file=sys.stderr)
        subprocess.run(
            ['xcodebuild', '-downloadPlatform', 'tvOS', '-buildVersion', sdk_version],
            stdout=sys.stderr, check=True, timeout=900,
        )
        runtimes = simctl_list('runtimes')
        if not any(r.get('identifier') == runtime and r.get('isAvailable')
                   for r in runtimes.get('runtimes', [])):
            raise ValueError(f'Runtime {runtime} unavailable after installation: {runtimes}')
    # Downloading a runtime can also populate its default devices.
    try:
        return select_device(simctl_list('devices'), sdk_version)
    except ValueError:
        pass
    types = simctl_list('devicetypes').get('devicetypes', [])
    types = [t for t in types if 'Apple TV' in t.get('name', '')]
    types.sort(key=lambda t: ('1080p' not in t['name'], '4K' not in t['name'], t['name']))
    if not types:
        raise ValueError('No Apple TV simulator device type installed')
    subprocess.run(
        ['xcrun', 'simctl', 'create', 'Apple TV Plozz Advanced CI', types[0]['identifier'], runtime],
        stdout=sys.stderr, check=True, timeout=300,
    )
    return select_device(simctl_list('devices'), sdk_version)


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
                        help='Install the matching runtime and create a device if missing (CI only)')
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
