#!/usr/bin/env python3
"""Fail closed if an update drops traits, locked dependencies or runtime wiring.

These are source guards. The existing AetherReleaseIntegrationTests assert the
linked OptionalComponent values at runtime; only playback can prove rendering.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify(root=ROOT):
    config = json.loads((root / 'personal/source.json').read_text())
    package = (root / 'Package.swift').read_text()
    match = re.search(
        r'\.package\(\s*url:\s*"https://github.com/([^"\s]+/AetherEngine)"'
        r',\s*revision:\s*"([a-f0-9]{40})",\s*traits:\s*\[([^]]*)\]', package)
    if not match:
        raise ValueError('Expected SHA-pinned AetherEngine dependency with explicit traits')
    repository, revision, traits = match.groups()
    required = set(config['required_traits'])
    if not required <= set(re.findall(r'"([A-Za-z0-9]+)"', traits)):
        raise ValueError('Advanced playback traits missing from Package.swift')
    if repository != config['engine_repository'] or revision != config['engine_commit']:
        raise ValueError('Engine changed: review it and update personal/source.json explicitly')
    pins = json.loads((root / 'Package.resolved').read_text())['pins']
    pins = {pin['identity']: pin for pin in pins}
    if pins['aetherengine']['state']['revision'] != revision:
        raise ValueError('Engine manifest/lock mismatch')
    for identity in ('libtruehd', 'ffmpegbuild', 'libdovi'):
        if not re.fullmatch('[a-f0-9]{40}', pins[identity]['state']['revision']):
            raise ValueError(f'{identity} must have an exact locked revision')
    checks = {
        'Sources/CoreModels/AdvancedPlaybackSettings.swift':
            ['com.plozz.advanced.device.spatialAudio', 'com.plozz.advanced.device.dolbyVisionFEL'],
        'Sources/EnginePlozzigen/PlozzigenVideoEngine.swift':
            ['advanced: advancedPlaybackPreference()',
             'AdvancedPlaybackSettingsStore().load()',
             'AdvancedPlaybackOptions.apply(advanced, policy: outputPolicy, to: &options)'],
        'Sources/EnginePlozzigen/AdvancedPlaybackOptions.swift':
            ['options.preferDualLayerDolbyVision = true',
             'options.objectAudioRendering = .render',
             '!options.isLive, policy.isAudible, !policy.sharesAudioSession'],
        'Sources/FeatureSettings/AdvancedPlaybackControls.swift':
            ['advanced-spatial-audio', 'advanced-dolby-vision-fel', 'advanced-spatial-layout',
             '@AppStorage(AdvancedPlaybackSettingsStore.spatialKey)',
             '@AppStorage(AdvancedPlaybackSettingsStore.felKey)'],
        'Sources/FeatureSettings/ExternalPlayerSettingsView.swift': ['+ AdvancedPlaybackControls.rows'],
        'Tests/EnginePlozzigenTests/AdvancedPlaybackTests.swift':
            ['testDeviceChoicesReachActualEngineRequests', 'testRestrictedOutputsStayDisabled'],
    }
    for path, needles in checks.items():
        source = (root / path).read_text()
        for needle in needles:
            if needle not in source:
                raise ValueError(f'Playback preservation check failed: {path}: {needle}')
    project = (root / 'project.yml').read_text()
    if not re.search(r'packages:\s+Plozz:\s+path: \.', project):
        raise ValueError('Local package bridge changed; review Xcode trait propagation')
    return config


if __name__ == '__main__':
    try:
        result = verify()
    except (ValueError, KeyError, FileNotFoundError) as error:
        sys.exit(str(error))
    print(f"Source checks passed: {result['upstream_tag']}, engine {result['engine_commit']}")
