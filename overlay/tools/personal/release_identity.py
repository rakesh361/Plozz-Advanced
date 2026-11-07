"""Display the accepted upstream release, independently of installation numbering."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def release_identity(root=ROOT):
    config = json.loads((root / 'personal/source.json').read_text())
    tag = config['upstream_tag']
    if not re.fullmatch(r'release/\d{3,4}(?:\.\d{1,2}){0,2}', tag):
        raise ValueError('Invalid personal upstream release tag')
    catalog = json.loads((root / 'App/Resources/ReleaseNotes.json').read_text())
    entries = [entry for entry in catalog['releases'] if entry['id'] == tag]
    if len(entries) != 1:
        raise ValueError(f'Expected exactly one catalog entry for {tag}')
    entry = entries[0]
    version, build = entry['version'], str(entry['build'])
    expected_build = '.'.join(str(int(part)) for part in tag.split('/')[1].split('.'))
    if build != expected_build:
        raise ValueError(f'Upstream release tag/build mismatch: {tag}, {build}')
    if not re.fullmatch(r'\d{4}\.\d{1,2}\.\d{1,2}', version):
        raise ValueError('Unexpected upstream display version')
    return version, build


def verify_bundle(info, root=ROOT):
    version, build = release_identity(root)
    if info.get('PlozzPersonalBuild') is not True:
        raise ValueError('Built personal app is missing its signing-independent identity marker')
    if info.get('CFBundleDisplayName') != 'Plozz Advanced':
        raise ValueError('Built personal app must be named Plozz Advanced')
    if (info.get('PlozzPersonalUpstreamVersion'), info.get('PlozzPersonalUpstreamBuild')) != (version, build):
        raise ValueError('Built personal app does not display the accepted upstream release')
    return version, build


if __name__ == '__main__':
    print(*release_identity())
