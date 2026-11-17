"""Check upstream and skip macOS when the same recipe/release is published."""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

UPSTREAM = 'brandomoore/Plozz'
ASSETS = {'Plozz-Advanced-tvOS.ipa', 'Plozz-Advanced-tvOS.ipa.sha256',
          'provenance.json', 'Package.resolved', 'SHA256SUMS', 'Plozz-Advanced-source.tar.gz'}


def api(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Plozz-Advanced'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    request = urllib.request.Request('https://api.github.com/' + path, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def select_release(releases, tag=None):
    candidates = [r for r in releases if not r['draft'] and
                  re.fullmatch(r'release/\d{3,4}(?:\.\d{1,2}){0,2}', r['tag_name'])]
    if tag:
        candidates = [r for r in candidates if r['tag_name'] == tag]
    if not candidates:
        raise ValueError('No published numbered Plozz release found')
    return max(candidates, key=lambda r: tuple(map(int, r['tag_name'].split('/')[1].split('.'))))


def marker(upstream_commit, recipe_commit):
    return f'<!-- plozz-advanced upstream={upstream_commit} recipe={recipe_commit} -->'


def advanced_version(tag, requested=''):
    base = tag.removeprefix('release/')
    if not re.fullmatch(r'\d{3,4}(?:\.\d{1,2}){0,2}', base):
        raise ValueError('Invalid upstream version')
    if requested and not re.fullmatch(re.escape(base) + r'(?:\.[1-9]\d?)?', requested):
        raise ValueError('Advanced version must match upstream or append a positive patch number')
    return requested or base


def already_published(releases, upstream_commit, recipe_commit, version=None):
    expected = marker(upstream_commit, recipe_commit)
    return any(not r['draft'] and expected in (r.get('body') or '') and
               (version is None or r.get('name') == f'Plozz Advanced {version}') and
               ASSETS <= {a['name'] for a in r.get('assets', [])} for r in releases)


def main():
    release = select_release(api(f'repos/{UPSTREAM}/releases?per_page=100'),
                             os.environ.get('UPSTREAM_TAG', '').strip())
    tag = release['tag_name']
    requested = os.environ.get('ADVANCED_VERSION', '').strip()
    version = advanced_version(tag, requested)
    sha = api(f'repos/{UPSTREAM}/commits/{urllib.parse.quote(tag, safe="")}')['sha']
    recipe = os.environ['GITHUB_SHA']
    if not re.fullmatch('[a-f0-9]{40}', sha) or not re.fullmatch('[a-f0-9]{40}', recipe):
        raise ValueError('Expected immutable commit IDs')
    own = api(f'repos/{os.environ["GITHUB_REPOSITORY"]}/releases?per_page=100')
    build = not already_published(own, sha, recipe, version if requested else None)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
        stream.write(f'build={str(build).lower()}\ntag={tag}\ncommit={sha}\nversion={version}\n')
    print(f'{tag}: ' + ('build required' if build else 'already published; no macOS build'))


if __name__ == '__main__':
    main()
