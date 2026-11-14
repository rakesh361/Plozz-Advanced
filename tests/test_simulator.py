"""Exercise missing runner runtime/device recovery without touching local Xcode."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'simulator', ROOT / 'overlay/tools/select-ci-tvos-simulator.py')
simulator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simulator)
RUNTIME = 'com.apple.CoreSimulator.SimRuntime.tvOS-27-0'
EMPTY = {'devices': {}}
READY = {'devices': {RUNTIME: [
    {'name': 'Apple TV Plozz Advanced CI', 'udid': 'fixture', 'isAvailable': True}]}}
RUNTIMES = {'runtimes': [{'identifier': RUNTIME, 'isAvailable': True}]}
TYPES = {'devicetypes': [{'name': 'Apple TV 4K (at 1080p)', 'identifier': 'tv-type'}]}


class SimulatorTests(unittest.TestCase):
    def test_workflow_prepares_source_device_and_exports_identifier(self):
        workflow = (ROOT / '.github/workflows/build.yml').read_text()
        step = workflow.split('      - name: Prepare matching Apple TV simulator\n')[1]
        block = step.split('        run: |\n')[1].split('      - name:')[0]
        script = '\n'.join(line[10:] for line in block.splitlines())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            personal = root / 'work/source/tools/personal'
            personal.mkdir(parents=True)
            (personal / 'environment.sh').write_text('test -d tools/personal || return 1\n')
            (personal.parent / 'select-ci-tvos-simulator.py').write_text(
                'import sys\nassert sys.argv[1:] == ["--sdk-version", "27.0", "--prepare"]\nprint("fixture")\n')
            (root / 'xcrun').write_text('#!/bin/sh\necho 27.0\n')
            (root / 'xcrun').chmod(0o755)
            envfile = root / 'github-env'
            result = subprocess.run(['bash', '-c', script], cwd=root, capture_output=True,
                env={**os.environ, 'PATH': str(root) + os.pathsep + os.environ['PATH'],
                     'GITHUB_ENV': str(envfile)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(envfile.read_text(), 'PLOZZ_SIM_ID=fixture\n')

    @patch.object(simulator.subprocess, 'run')
    @patch.object(simulator, 'simctl_list', return_value=READY)
    def test_existing_device_needs_no_mutation(self, listing, run):
        self.assertEqual(simulator.prepare_device('27.0')[0], 'fixture')
        run.assert_not_called()

    @patch.object(simulator.subprocess, 'run')
    @patch.object(simulator, 'simctl_list', side_effect=[EMPTY, RUNTIMES, EMPTY, TYPES, READY])
    def test_installed_runtime_with_no_device_creates_one(self, listing, run):
        self.assertEqual(simulator.prepare_device('27.0')[0], 'fixture')
        self.assertEqual(run.call_args.args[0], [
            'xcrun', 'simctl', 'create', 'Apple TV Plozz Advanced CI', 'tv-type', RUNTIME])

    @patch.object(simulator.subprocess, 'run')
    @patch.object(simulator, 'simctl_list', side_effect=[EMPTY, {}, RUNTIMES, EMPTY, TYPES, READY])
    def test_missing_runtime_downloads_exact_sdk_before_creating_device(self, listing, run):
        self.assertEqual(simulator.prepare_device('27.0')[0], 'fixture')
        self.assertEqual(run.call_args_list[0].args[0], [
            'xcodebuild', '-downloadPlatform', 'tvOS', '-buildVersion', '27.0'])
        self.assertEqual(run.call_count, 2)

    @patch.object(simulator.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'download'))
    @patch.object(simulator, 'simctl_list', side_effect=[EMPTY, {}])
    def test_failed_download_stops_setup(self, listing, run):
        with self.assertRaises(subprocess.CalledProcessError):
            simulator.prepare_device('27.0')

    @patch.object(simulator.subprocess, 'run')
    @patch.object(simulator, 'simctl_list', side_effect=[EMPTY, {}, {}])
    def test_unavailable_runtime_after_download_stops_setup(self, listing, run):
        with self.assertRaisesRegex(ValueError, 'unavailable after installation'):
            simulator.prepare_device('27.0')
        self.assertEqual(run.call_count, 1)

    def test_other_os_and_unavailable_devices_cannot_satisfy_selection(self):
        for devices in [
            {'devices': {RUNTIME.replace('27-0', '27-2'): READY['devices'][RUNTIME]}},
            {'devices': {RUNTIME: [dict(READY['devices'][RUNTIME][0], isAvailable=False)]}},
        ]:
            with self.assertRaises(ValueError):
                simulator.select_device(devices, '27.0')
