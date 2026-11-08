"""Fetch upstream source and apply the build patches."""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
from features import enable, TRAITS
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[1]
UPSTREAM = 'https://github.com/brandomoore/Plozz.git'



def installation_build(run_number, attempt):
    number, attempt = int(run_number) + 6000, int(attempt)
    if not 6001 <= number <= 9999 or not 1 <= attempt <= 99:
        raise ValueError('Installation numbering needs review; refusing a downgrade/invalid version')
    return f'{number}.{attempt}'


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'release/\d{3,4}(?:\.\d{1,2}){0,2}', args.tag):
        raise ValueError('Unexpected upstream tag')
    if not re.fullmatch('[a-f0-9]{40}', args.commit):
        raise ValueError('Expected upstream commit SHA')
    root = args.source.resolve()
    root.mkdir(parents=True, exist_ok=False)
    git(root, 'init', '-b', 'upstream-source')
    git(root, 'remote', 'add', 'origin', UPSTREAM)
    git(root, 'fetch', '--depth=1', 'origin', f'refs/tags/{args.tag}')
    git(root, 'checkout', '--detach', 'FETCH_HEAD')
    if git(root, 'rev-parse', 'HEAD') != args.commit:
        raise ValueError('Upstream tag moved after the release check')
    enable(root)
    patch_hashes = {}
    for patch in sorted((RECIPE / 'patches').glob('*.patch'), key=lambda p: p.name):
        patch_hashes[patch.name] = hashlib.sha256(patch.read_bytes()).hexdigest()
        git(root, 'apply', '--3way', '--check', str(patch))
        git(root, 'apply', '--3way', '--index', str(patch))
    shutil.copytree(RECIPE / 'overlay', root, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('.DS_Store', '__pycache__'))
    package = (root / 'Package.swift').read_text()
    engine = re.search(r'url: "https://github.com/([^"\s]+/AetherEngine)",\s*revision: "([a-f0-9]{40})"', package)
    if not engine:
        raise ValueError('Engine integration changed; recipe needs review')
    config = {'upstream_repository': 'brandomoore/Plozz', 'upstream_tag': args.tag,
              'upstream_commit': args.commit, 'engine_repository': engine[1],
              'engine_commit': engine[2], 'required_traits': sorted(TRAITS),
              'bundle_identifier': 'com.thatcube.Plozz.personal-advanced'}
    personal = root / 'personal'
    personal.mkdir(exist_ok=True)
    (personal / 'source.json').write_text(json.dumps(config, indent=2) + '\n')
    recipe = {'automation_repository': os.environ.get('GITHUB_REPOSITORY', 'local-validation'),
              'automation_commit': os.environ['GITHUB_SHA'], 'patches_sha256': patch_hashes,
              'source_history_included': False,
              'feature_hooks_sha256': hashlib.sha256((RECIPE / 'tools/features.py').read_bytes()).hexdigest()}
    (personal / 'recipe.json').write_text(json.dumps(recipe, indent=2) + '\n')
    load('source_guard', root / 'tools/personal/verify-source.py').verify(root)
    load('release_identity', root / 'tools/personal/release_identity.py').release_identity(root)
    print(f'Prepared {args.tag} with TrueHD Atmos, DTS:X and dual-layer Dolby Vision enabled.')


if __name__ == '__main__':
    main()
