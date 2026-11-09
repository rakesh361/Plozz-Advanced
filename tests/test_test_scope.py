"""Verify the release executes only its own target and preserves failure handling."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

RECIPE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RECIPE / 'tools'))
from materialize import add_focused_tests


class FocusedTestScopeTests(unittest.TestCase):
    def test_dedicated_target_keeps_upstream_targets_and_copies_version_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = 'let package = Package(\n    targets: [\n        .testTarget(name: "CoreModelsTests"),\n    ]\n)\n'
            (root / 'Package.swift').write_text(original)
            upstream = root / 'Tests/CoreModelsTests/AppVersionIdentityTests.swift'
            upstream.parent.mkdir(parents=True)
            upstream.write_text('version-display regression tests\n')
            (root / 'Tests/PlozzAdvancedTests').mkdir()
            add_focused_tests(root)
            result = (root / 'Package.swift').read_text()
            self.assertEqual(result.count('name: "PlozzAdvancedTests"'), 1)
            self.assertIn('.testTarget(name: "CoreModelsTests")', result)
            self.assertEqual((root / 'Tests/PlozzAdvancedTests/AppVersionIdentityTests.swift').read_bytes(), upstream.read_bytes())
            with self.assertRaises(ValueError):
                add_focused_tests(root)

    def test_runner_selects_only_advanced_target_and_propagates_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            personal = root / 'tools/personal'
            personal.mkdir(parents=True)
            shutil.copy2(RECIPE / 'overlay/tools/personal/test-tv.sh', personal / 'test-tv.sh')
            (personal / 'environment.sh').write_text('export PLOZZ_SIM_ID=fixture\n')
            runner = root / 'tools/run-tests.sh'
            runner.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@" > selected-targets\nexit "${FOCUSED_TEST_EXIT:-0}"\n')
            runner.chmod(0o755)
            for status in [0, 1]:
                result = subprocess.run(['bash', str(personal / 'test-tv.sh')],
                    cwd=root, env={**os.environ, 'FOCUSED_TEST_EXIT': str(status)}, capture_output=True)
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertEqual((root / 'selected-targets').read_text(), 'PlozzAdvancedTests\n')
