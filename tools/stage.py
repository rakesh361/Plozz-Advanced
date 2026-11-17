"""Create release checksums and record both upstream and recipe identities."""
import hashlib
import json
from pathlib import Path
from check import marker

root = Path('dist')
p = json.loads((root / 'provenance.json').read_text())
source = root / 'Plozz-Advanced-source.tar.gz'
p['source_archive_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
(root / 'provenance.json').write_text(json.dumps(p, indent=2) + '\n')
files = ['Plozz-Advanced-tvOS.ipa', 'Package.resolved', 'provenance.json', 'Plozz-Advanced-source.tar.gz']
with (root / 'SHA256SUMS').open('w') as stream:
    for name in files:
        stream.write(f'{hashlib.sha256((root / name).read_bytes()).hexdigest()}  {name}\n')
notes = (f'Plozz Advanced {p["advanced_version"]}, based on upstream {p["upstream_tag"]}.\n\n'
         'TrueHD Atmos, DTS:X and dual-layer Dolby Vision support retained. '
         'Device build and focused Advanced/version-display simulator checks passed.\n\n'
         'Playback > Advanced contains device-local Spatial audio, Rendering layout and '
         'experimental Dolby Vision FEL controls. Restart playback after changes. '
         'Spatial audio defaults on; FEL defaults off. Recheck these choices on each device '
         'when upgrading from older profile-based controls.\n\n'
         'For Profile 7 FEL videos, P7 FEL → P8.1 conversion is the master switch. '
         'With conversion on, experimental FEL on selects full reconstruction; '
         'experimental FEL off selects the official brightness approximation. '
         'Conversion off keeps HDR10 for FEL videos regardless of the experimental choice. '
         'Ordinary MEL and single-layer Dolby Vision playback remain supported. '
         'Experimental reconstruction retains its existing source/device fallback; '
         'the in-player conversion switch may be unavailable on that route. '
         'Actual Dolby Vision output and performance require device playback checks.\n\n'
         'Unsigned tvOS IPA. Matching patched source, '
         'dependency versions and checksums are included.\n\n'
         f'Upstream source: https://github.com/{p["upstream_repository"]}/commit/{p["upstream_commit"]}\n\n'
         f'Build recipe: https://github.com/{p["automation_repository"]}/tree/{p["automation_commit"]}\n\n'
         + marker(p['upstream_commit'], p['automation_commit']) + '\n')
(root / 'release-notes.md').write_text(notes)
