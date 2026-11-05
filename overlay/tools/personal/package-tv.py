#!/usr/bin/env python3
"""Validate the built device bundle, retain provenance, and package for re-signing."""
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path
from release_identity import verify_bundle

ROOT = Path(__file__).resolve().parents[2]


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def package(app, output):
    config = json.loads((ROOT / 'personal/source.json').read_text())
    compiled_traits = set()
    for line in (output / 'build.log').open():
        if 'builtin-SwiftDriver' in line and '-module-name AetherEngine ' in line:
            compiled_traits.update(re.findall(r'-D\s*([A-Za-z0-9_]+)', line))
    if not set(config['required_traits']) <= compiled_traits:
        raise ValueError('Build log does not prove all required engine compile conditions')
    with (app / 'Info.plist').open('rb') as stream:
        info = plistlib.load(stream)
    if info['CFBundleIdentifier'] != config['bundle_identifier']:
        raise ValueError('Refusing canonical or unexpected app identifier')
    upstream_version, upstream_build = verify_bundle(info)
    if info.get('CFBundleSupportedPlatforms') != ['AppleTVOS']:
        raise ValueError('Expected a tvOS device bundle, not a simulator app')
    credential_fields = ('AniListClientID', 'AniListClientSecret', 'LastFmAPIKey',
                         'LastFmSharedSecret', 'MALClientID', 'OMDBAPIKey', 'SimklClientID',
                         'TMDBBearerToken', 'TVDBAPIKey', 'TraktClientID', 'WetrakrClientID')
    if any(info.get(key, '') for key in credential_fields):
        raise ValueError('Embedded service configuration is not empty; refusing publication')
    if any(path.suffix.lower() in {'.p12', '.pfx', '.p8', '.key', '.mobileprovision'}
           for path in app.rglob('*') if path.is_file()):
        raise ValueError('Unexpected signing file in app bundle')
    executable = app / info['CFBundleExecutable']
    if run('lipo', '-archs', str(executable)) != 'arm64':
        raise ValueError('Expected an arm64 executable')
    # SPM owns embedding. Check every Mach-O load command for a missing embedded
    # framework rather than producing an IPA that only works on the build host.
    engine = app / 'Frameworks/AetherEngine.framework/AetherEngine'
    if not engine.is_file():
        raise ValueError('Missing dynamic AetherEngine framework')
    binaries = [executable]
    for directory in app.rglob('*.framework'):
        binary = directory / directory.stem
        if binary.is_file():
            binaries.append(binary)
    for binary in binaries:
        loads = run('otool', '-L', str(binary))
        for line in loads.splitlines()[1:]:
            name = line.strip().split(' (', 1)[0]
            if name.startswith('@rpath/') and '.framework/' in name:
                framework = name.removeprefix('@rpath/').split('/', 1)[0]
                if not (app / 'Frameworks' / framework).is_dir():
                    raise ValueError(f'Missing embedded framework: {framework}')
    payload = output / 'Payload'
    payload.mkdir()
    subprocess.run(['ditto', str(app), str(payload / app.name)], check=True)
    ipa = output / 'Plozz-Personal-tvOS.ipa'
    subprocess.run(['ditto', '-c', '-k', '--keepParent', str(payload), str(ipa)], check=True)
    shutil.copy2(ROOT / 'Package.resolved', output / 'Package.resolved')
    recipe = json.loads((ROOT / 'personal/recipe.json').read_text())
    provenance = {
        **config, **recipe,
        'upstream_checkout_commit': run('git', 'rev-parse', 'HEAD'),
        'xcode': run('xcodebuild', '-version'),
        'tvos_sdk': run('xcrun', '--sdk', 'appletvos', '--show-sdk-version'),
        'xcodegen': run('xcodegen', '--version'),
        'build_number': info['CFBundleVersion'], 'signed': False,
        'upstream_display_version': upstream_version, 'upstream_display_build': upstream_build,
        'playback_validated': False,
        'package_lock_sha256': hashlib.sha256((ROOT / 'Package.resolved').read_bytes()).hexdigest(),
        'ipa_sha256': hashlib.sha256(ipa.read_bytes()).hexdigest(),
        'compiled_traits': sorted(set(config['required_traits']) & compiled_traits),
    }
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    # Keep a checksum sidecar alongside the IPA.
    (output / (ipa.name + '.sha256')).write_text(provenance['ipa_sha256'] + '\n')
    with (output / 'SHA256SUMS').open('w') as stream:
        for filename in ('Plozz-Personal-tvOS.ipa', 'Package.resolved', 'provenance.json'):
            digest = hashlib.sha256((output / filename).read_bytes()).hexdigest()
            stream.write(f'{digest}  {filename}\n')


if __name__ == '__main__':
    package(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
