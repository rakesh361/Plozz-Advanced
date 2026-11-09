"""Small, checked hooks for Advanced playback; no engine revision is hardcoded.

Each replacement must match once. Upstream interface changes stop publication.
Owned settings, controls, policy and regression tests live in overlay/.
"""
import json
import re
import urllib.request

TRAITS = ('TrueHDObjectAudio', 'DTSXObjectAudio', 'DualLayerDolbyVision',
          'DolbyVisionStillReshaping')


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f'Advanced hook changed upstream: {old[:100]}')
    return source.replace(old, new, 1)


def edit(root, path, changes):
    target = root / path
    source = target.read_text()
    for old, new in changes:
        source = replace_once(source, old, new)
    target.write_text(source)


def enable_manifest(source):
    pattern = (r'(\.package\(\s*url: "https://github.com/([^"\s]+/AetherEngine)",'
               r'\s*revision: "([a-f0-9]{40})",\s*traits: )\[([^]]*)\]')
    matches = list(re.finditer(pattern, source))
    if len(matches) != 1:
        raise ValueError('Aether package interface changed; review Advanced integration')
    match = matches[0]
    traits = list(dict.fromkeys(re.findall(r'"([A-Za-z0-9]+)"', match[4]) + list(TRAITS)))
    source = source[:match.start()] + match[1] + '[' + ', '.join(map(json.dumps, traits)) + ']' + source[match.end():]
    return source, match[2], match[3]


def enable(root, engine_lock=None):
    manifest = root / 'Package.swift'
    source, repository, revision = enable_manifest(manifest.read_text())
    manifest.write_text(source)
    # Use the decoder lock belonging to Plozz's chosen engine, not an old recipe pin.
    if engine_lock is None:
        url = f'https://raw.githubusercontent.com/{repository}/{revision}/Package.resolved'
        with urllib.request.urlopen(url, timeout=30) as response:
            engine_lock = json.load(response)
    decoder = next(pin for pin in engine_lock['pins'] if pin['identity'] == 'libtruehd')
    if not re.fullmatch('[a-f0-9]{40}', decoder['state']['revision']):
        raise ValueError('Expected an immutable LibTrueHD revision')
    lock_path = root / 'Package.resolved'
    lock = json.loads(lock_path.read_text())
    existing = next((pin for pin in lock['pins'] if pin['identity'] == 'libtruehd'), None)
    if existing is not None and existing != decoder:
        raise ValueError('Upstream/engine LibTrueHD locks disagree')
    if existing is None:
        lock['pins'].append(decoder)
    lock['pins'].sort(key=lambda pin: pin['identity'])
    lock_path.write_text(json.dumps(lock, indent=2) + '\n')

    edit(root, 'Sources/EnginePlozzigen/PlozzigenVideoEngine.swift', [
        ('    private let losslessAudioPreference: @MainActor () -> Bool',
         '    private let advancedPlaybackPreference: @MainActor () -> AdvancedPlaybackSettings\n    private let losslessAudioPreference: @MainActor () -> Bool'),
        ('losslessAudioPreference: @escaping @MainActor () -> Bool = { LosslessAudioSettingsStore().load() }',
         'losslessAudioPreference: @escaping @MainActor () -> Bool = { LosslessAudioSettingsStore().load() },\n        advancedPlaybackPreference: @escaping @MainActor () -> AdvancedPlaybackSettings = { AdvancedPlaybackSettingsStore().load() }'),
        ('        self.losslessAudioPreference = losslessAudioPreference',
         '        self.advancedPlaybackPreference = advancedPlaybackPreference\n        self.losslessAudioPreference = losslessAudioPreference'),
        ('            losslessAudioEnabled: losslessAudioPreference(),',
         '            advanced: advancedPlaybackPreference(),\n            losslessAudioEnabled: losslessAudioPreference(),'),
        ('    nonisolated static func onDemandLoadOptions(\n',
         '    nonisolated static func onDemandLoadOptions(\n        advanced: AdvancedPlaybackSettings = .disabled,\n'),
        ('        options.sessionCacheByteBudget = readAhead == .automatic ? nil : Int.max',
         '        options.sessionCacheByteBudget = readAhead == .automatic ? nil : Int.max\n        AdvancedPlaybackOptions.apply(advanced, policy: outputPolicy, to: &options)'),
    ])
    edit(root, 'Sources/FeatureSettings/ExternalPlayerSettingsView.swift', [
        ('        ExternalPlayerSettingsRows.advanced(model: model)',
         '        ExternalPlayerSettingsRows.advanced(model: model) + AdvancedPlaybackControls.rows'),
        ('                .accessibilityIdentifier("playback-external-player")\n            }',
         '                .accessibilityIdentifier("playback-external-player")\n            }\n            SettingsSectionGroup("Advanced playback") { AdvancedPlaybackControls() }'),
    ])
    # Keep included library notices truthful without rewriting upstream documentation.
    edit(root, 'Sources/CoreModels/PlozzAttributions.swift', [
        ('LibTrueHD 3.1.0 supported optional spatial audio rendering in earlier builds ',
         'LibTrueHD 3.1.0 supports optional spatial audio rendering '),
        ('and is not linked in this build. ', 'and is linked in this Advanced build. '),
    ])
    notice = root / 'NOTICE.md'
    notice_source = re.sub(r'(`github.com/[^`]+/AetherEngine` @ `)[a-f0-9]{40}',
                           lambda m: m[1] + revision, notice.read_text())
    notice.write_text(notice_source + '\n## Plozz Advanced build\n\n'
        'This variant enables TrueHDObjectAudio, DTSXObjectAudio, DualLayerDolbyVision '
        'and DolbyVisionStillReshaping. LibTrueHD is linked; its exact source is pinned '
        'in Package.resolved and its MIT/Apache-2.0 notices are bundled. '
        'Statements above describing these components as disabled apply to upstream Plozz.\n')

    return repository, revision
