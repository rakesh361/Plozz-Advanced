"""Check upstream and skip macOS when the same recipe/release is published."""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

UPSTREAM = 'brandomoore/Plozz'
ASSETS = {'Plozz-Personal-tvOS.ipa', 'Plozz-Personal-tvOS.ipa.sha256',
          'provenance.json', 'Package.resolved', 'SHA256SUMS', 'Plozz-Advanced-source.tar.gz'}


def api(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Plozz-Advanced'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    request = urllib.request.Request('https://api.github.com/' + path, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def select_release(releases):
    candidates = [r for r in releases if not r['draft'] and
                  re.fullmatch(r'release/\d{3,4}(?:\.\d{1,2}){0,2}', r['tag_name'])]
    if not candidates:
        raise ValueError('No published numbered Plozz release found')
    return max(candidates, key=lambda r: tuple(map(int, r['tag_name'].split('/')[1].split('.'))))


def marker(upstream_commit, recipe_commit):
    return f'<!-- plozz-advanced upstream={upstream_commit} recipe={recipe_commit} -->'


def already_published(releases, upstream_commit, recipe_commit):
    expected = marker(upstream_commit, recipe_commit)
    return any(not r['draft'] and expected in (r.get('body') or '') and
               ASSETS <= {a['name'] for a in r.get('assets', [])} for r in releases)


def main():
    release = select_release(api(f'repos/{UPSTREAM}/releases?per_page=100'))
    tag = release['tag_name']
    sha = api(f'repos/{UPSTREAM}/commits/{urllib.parse.quote(tag, safe="")}')['sha']
    recipe = os.environ['GITHUB_SHA']
    if not re.fullmatch('[a-f0-9]{40}', sha) or not re.fullmatch('[a-f0-9]{40}', recipe):
        raise ValueError('Expected immutable commit IDs')
    own = api(f'repos/{os.environ["GITHUB_REPOSITORY"]}/releases?per_page=100')
    build = not already_published(own, sha, recipe)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
        stream.write(f'build={str(build).lower()}\ntag={tag}\ncommit={sha}\n')
    print(f'{tag}: ' + ('build required' if build else 'already published; no macOS build'))


if __name__ == '__main__':
    main()
