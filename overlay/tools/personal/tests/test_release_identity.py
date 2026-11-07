"""Guard against showing a newer release than the accepted personal source."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('personal_identity', ROOT / 'tools/personal/release_identity.py')
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)


class ReleaseIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'personal').mkdir()
        (self.root / 'App/Resources').mkdir(parents=True)
        self.source = self.root / 'personal/source.json'
        self.source.write_text(json.dumps({'upstream_tag': 'release/069.2'}))
        self.catalog = self.root / 'App/Resources/ReleaseNotes.json'
        self.entries = [
            {'id': 'release/070', 'version': '2026.11.4', 'build': 70},
            {'id': 'release/069.2', 'version': '2026.11.3', 'build': '69.2'},
        ]
        self.save_catalog()

    def save_catalog(self):
        self.catalog.write_text(json.dumps({'releases': self.entries}))

    def test_accepted_source_wins_over_newest_catalog_entry(self):
        self.assertEqual(identity.release_identity(self.root), ('2026.11.3', '69.2'))

    def test_source_update_automatically_changes_display(self):
        self.source.write_text(json.dumps({'upstream_tag': 'release/070'}))
        self.assertEqual(identity.release_identity(self.root), ('2026.11.4', '70'))

    def test_missing_or_mismatched_release_stops_build(self):
        self.entries[1]['build'] = '69.1'
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            identity.release_identity(self.root)
        self.entries.pop()
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            identity.release_identity(self.root)

    def test_packaging_rejects_missing_or_stale_display_identity(self):
        for info in [{}, {'PlozzPersonalUpstreamVersion': '2026.11.4', 'PlozzPersonalUpstreamBuild': '70'}]:
            info['CFBundleDisplayName'] = 'Plozz Advanced'
            with self.assertRaisesRegex(ValueError, 'does not display'):
                identity.verify_bundle(info, self.root)
        self.assertEqual(identity.verify_bundle({
            'CFBundleDisplayName': 'Plozz Advanced',
            'PlozzPersonalUpstreamVersion': '2026.11.3', 'PlozzPersonalUpstreamBuild': '69.2',
            'CFBundleVersion': '4900.1',
        }, self.root), ('2026.11.3', '69.2'))

    def test_packaging_rejects_old_or_missing_app_name(self):
        for name in [None, 'Plozz Personal', 'Plozz']:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, 'must be named Plozz Advanced'):
                    identity.verify_bundle({
                        'CFBundleDisplayName': name,
                        'PlozzPersonalUpstreamVersion': '2026.11.3',
                        'PlozzPersonalUpstreamBuild': '69.2',
                    }, self.root)


if __name__ == '__main__':
    unittest.main()
