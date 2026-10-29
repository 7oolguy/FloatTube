import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('updater', Path(__file__).resolve().parents[1] / 'scripts/update.py')
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)

class SignatureVerificationTests(unittest.TestCase):
    def test_wrong_identity_stops_before_system_commands(self):
        with patch.object(updater, 'read_info', return_value={'CFBundleIdentifier': 'wrong', 'CFBundleShortVersionString': '1.0.0'}), patch.object(updater.subprocess, 'run') as run:
            with self.assertRaises(ValueError): updater.verify(Path('candidate.app'), 'ABCDEFGHIJ', '1.0.0')
            run.assert_not_called()

    def test_signature_failure_stops_before_gatekeeper(self):
        info = {'CFBundleIdentifier': updater.BUNDLE_ID, 'CFBundleShortVersionString': '1.0.0'}
        with patch.object(updater, 'read_info', return_value=info), patch.object(updater.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'codesign')) as run:
            with self.assertRaises(subprocess.CalledProcessError): updater.verify(Path('candidate.app'), 'ABCDEFGHIJ', '1.0.0')
            self.assertEqual(run.call_count, 1)
            self.assertIn('ABCDEFGHIJ', run.call_args.args[0][-2])

    def test_all_verifiers_are_required(self):
        info = {'CFBundleIdentifier': updater.BUNDLE_ID, 'CFBundleShortVersionString': '1.0.0'}
        with patch.object(updater, 'read_info', return_value=info), patch.object(updater.subprocess, 'run') as run:
            updater.verify(Path('candidate.app'), 'ABCDEFGHIJ', '1.0.0')
            self.assertEqual([call.args[0][0] for call in run.call_args_list], ['codesign', 'spctl', 'xcrun'])
            self.assertTrue(all(call.kwargs['check'] for call in run.call_args_list))
