"""Regression checks: feature loss must stop an update, never produce a release."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('preservation', ROOT / 'tools/personal/verify-source.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for relative in ['Package.swift', 'Package.resolved', 'project.yml', 'personal/source.json',
                         'Sources/CoreModels/AdvancedPlaybackSettings.swift',
                         'Sources/EnginePlozzigen/PlozzigenVideoEngine.swift',
                         'Sources/EnginePlozzigen/AdvancedPlaybackOptions.swift',
                         'Sources/FeatureSettings/AdvancedPlaybackControls.swift',
                         'Sources/FeatureSettings/ExternalPlayerSettingsView.swift',
                         'Tests/EnginePlozzigenTests/AdvancedPlaybackTests.swift']:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)

    def tearDown(self):
        self.temp.cleanup()

    def test_preserved_baseline_is_accepted(self):
        guard.verify(self.root)

    def test_downloaded_upstream_workflows_are_not_active_recipe_workflows(self):
        path = self.root / '.github/workflows/unexpected.yml'
        path.parent.mkdir(parents=True)
        path.write_text('name: Downloaded upstream specification\n')
        guard.verify(self.root)

    def test_each_missing_trait_is_rejected(self):
        manifest = (ROOT / 'Package.swift').read_text()
        for trait in ['TrueHDObjectAudio', 'DTSXObjectAudio', 'DualLayerDolbyVision',
                      'DolbyVisionStillReshaping']:
            with self.subTest(trait=trait):
                (self.root / 'Package.swift').write_text(manifest.replace(f'"{trait}"', ''))
                with self.assertRaisesRegex(ValueError, 'traits missing'):
                    guard.verify(self.root)

    def test_ui_toggle_without_runtime_wiring_is_rejected(self):
        path = self.root / 'Sources/EnginePlozzigen/PlozzigenVideoEngine.swift'
        path.write_text(path.read_text().replace(
            'AdvancedPlaybackOptions.apply(advanced, policy: outputPolicy, to: &options)',
            '// Advanced hookup removed'))
        with self.assertRaisesRegex(ValueError, 'Playback preservation check failed'):
            guard.verify(self.root)

    def test_stale_lock_is_rejected(self):
        path = self.root / 'Package.resolved'
        lock = json.loads(path.read_text())
        for pin in lock['pins']:
            if pin['identity'] == 'aetherengine':
                pin['state']['revision'] = '0' * 40
        path.write_text(json.dumps(lock))
        with self.assertRaisesRegex(ValueError, 'manifest/lock mismatch'):
            guard.verify(self.root)

    def test_missing_decoder_dependency_is_rejected(self):
        path = self.root / 'Package.resolved'
        lock = json.loads(path.read_text())
        lock['pins'] = [p for p in lock['pins'] if p['identity'] != 'libtruehd']
        path.write_text(json.dumps(lock))
        with self.assertRaises(KeyError):
            guard.verify(self.root)


if __name__ == '__main__':
    unittest.main()
