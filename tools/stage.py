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
files = ['Plozz-Personal-tvOS.ipa', 'Package.resolved', 'provenance.json', 'Plozz-Advanced-source.tar.gz']
with (root / 'SHA256SUMS').open('w') as stream:
    for name in files:
        stream.write(f'{hashlib.sha256((root / name).read_bytes()).hexdigest()}  {name}\n')
notes = (f'Plozz Advanced, based on upstream {p["upstream_tag"]}.\n\n'
         'TrueHD Atmos, DTS:X and dual-layer Dolby Vision restoration applied; '
         'device build and scoped simulator checks passed. Physical playback remains hardware-dependent.\n\n'
         'Unsigned IPA: sign locally with tvsign. The existing personal bundle identity is preserved. '
         'Installation remains your choice. The complete patched source snapshot and build recipe '
         'are supplied with this release; no upstream or personal Git history is included in the snapshot.\n\n'
         f'Upstream source: https://github.com/{p["upstream_repository"]}/commit/{p["upstream_commit"]}\n\n'
         f'Build recipe: https://github.com/{p["automation_repository"]}/tree/{p["automation_commit"]}\n\n'
         + marker(p['upstream_commit'], p['automation_commit']) + '\n')
(root / 'release-notes.md').write_text(notes)
