"""Check that routine engine updates do not require feature-hook rebases."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from features import TRAITS, enable_manifest, replace_once, decoder_pin


class FeatureHookTests(unittest.TestCase):
    def test_engine_revisions_comments_and_existing_traits_are_preserved(self):
        for revision in ['a' * 40, 'b' * 40]:
            source = ('// Newly added disc support\n.package(\n'
                      '    url: "https://github.com/brandomoore/AetherEngine",\n'
                      f'    revision: "{revision}",\n'
                      '    traits: ["ExistingFeature"]\n),\n// Other packages follow\n')
            result, repo, selected = enable_manifest(source)
            self.assertEqual(repo, 'brandomoore/AetherEngine')
            self.assertEqual(selected, revision)
            self.assertEqual(result.replace(
                '["ExistingFeature", ' + ', '.join(f'"{x}"' for x in TRAITS) + ']',
                '["ExistingFeature"]'), source)
            self.assertEqual(enable_manifest(result)[0], result)

    def test_unknown_or_ambiguous_package_interface_stops_instead_of_guessing(self):
        entry = '.package(url: "https://github.com/brandomoore/AetherEngine", revision: "' + 'a'*40 + '", traits: [])'
        for source in [entry.replace('revision:', 'branch:'), entry + entry, '']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                enable_manifest(source)

    def test_missing_or_duplicate_runtime_hook_stops_instead_of_releasing(self):
        for source in ['removed', 'hook hook']:
            with self.assertRaises(ValueError):
                replace_once(source, 'hook', 'enabled')


class DecoderPinTests(unittest.TestCase):
    def test_existing_engine_decoder_lock_is_preserved(self):
        pin = {'identity': 'libtruehd', 'state': {'revision': 'a' * 40}}
        self.assertEqual(decoder_pin({'pins': [pin]}, '', None), pin)

    def test_disabled_trait_uses_declared_minor_floor_and_immutable_revision(self):
        manifest = '.package(url: "https://github.com/owner/LibTrueHD", .upToNextMinor(from: "3.2.0"))'
        calls = []
        def resolve(repo, version):
            calls.append((repo, version))
            return 'b' * 40
        pin = decoder_pin({'pins': []}, manifest, resolve)
        self.assertEqual(calls, [('owner/LibTrueHD', '3.2.0')])
        self.assertEqual(pin['state'], {'revision': 'b' * 40, 'version': '3.2.0'})
        for source in ['', manifest + manifest, manifest.replace('upToNextMinor', 'upToNextMajor')]:
            with self.assertRaises(ValueError):
                decoder_pin({'pins': []}, source, resolve)
        with self.assertRaises(ValueError):
            decoder_pin({'pins': []}, manifest, lambda *args: 'main')
