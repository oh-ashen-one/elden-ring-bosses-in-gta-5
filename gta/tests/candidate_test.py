# SPDX-License-Identifier: Apache-2.0
import hashlib
import importlib.util
import json
import sys
import struct
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location('verify_candidate', TOOLS / 'verify_candidate.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CandidateChecks(unittest.TestCase):
    def fixture(self, folder):
        bundle = Path(folder) / 'candidate'
        files = {}
        for name in module.REQUIRED:
            target = bundle / 'payload' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(('fixture:' + name).encode())
            files[name] = hashlib.sha256(target.read_bytes()).hexdigest()
        manifest = {'files': files, 'expected_game_version': '1.0.3889.0', 'source_commit': 'a' * 40,
                    'candidate': 'fixture'}
        (bundle / 'manifest.json').write_text(json.dumps(manifest))
        return bundle, manifest

    def test_intact_candidate_passes_without_executing_payloads(self):
        with tempfile.TemporaryDirectory() as folder:
            bundle, _ = self.fixture(folder)
            report = module.verify(bundle)
            self.assertTrue(report['ok'])
            self.assertFalse(report['gameplay_verified_by_this_check'])

    def test_changed_plugin_and_missing_dlc_are_distinguished(self):
        with tempfile.TemporaryDirectory() as folder:
            bundle, _ = self.fixture(folder)
            (bundle / 'payload/EldenLosSantos.asi').write_bytes(b'other build')
            (bundle / 'payload/newmods/dlcpacks/ergt/dlc.rpf').unlink()
            report = module.verify(bundle)
            self.assertFalse(report['ok'])
            self.assertTrue(any('checksum mismatch: EldenLosSantos.asi' in x for x in report['issues']))
            self.assertTrue(any('unavailable: newmods/dlcpacks/ergt/dlc.rpf' in x for x in report['issues']))

    def test_no_checksum_list_can_omit_the_creatures(self):
        with tempfile.TemporaryDirectory() as folder:
            bundle, manifest = self.fixture(folder)
            del manifest['files']['newmods/dlcpacks/ergt/dlc.rpf']
            (bundle / 'manifest.json').write_text(json.dumps(manifest))
            self.assertFalse(module.verify(bundle)['ok'])

    def test_overlapping_plugin_and_queued_diagnostic_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            bundle, _ = self.fixture(folder)
            (bundle / 'payload/EldenLosSantosProbe.asi').write_bytes(b'probe')
            (bundle / 'payload/EldenLosSantos.import-check.request').write_text('CHECK_IMPORTS_ONCE\n')
            report = module.verify(bundle)
            self.assertFalse(report['ok'])
            self.assertTrue(report['package_automatic_import_request_queued'])
            self.assertTrue(any('hotkeys overlap' in x for x in report['issues']))

    def test_manifest_cannot_read_outside_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            bundle, manifest = self.fixture(folder)
            manifest['files']['newmods/../../outside'] = 'a' * 64
            (bundle / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                module.verify(bundle)

    def test_active_profile_detects_stale_manifest_and_changed_game_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            bundle, manifest = self.fixture(folder)
            root = Path(folder) / 'profile-root'
            profile, retail, install = root / 'Game', root / 'Retail', Path(folder) / 'SteamGame'
            profile.mkdir(parents=True)
            retail.mkdir()
            exe = b'MZ' + b'\0' * 30 + struct.pack('<6I', 0xfeef04bd, 0x10000, 1 << 16, 3889 << 16, 0, 0)
            for directory in (profile, retail):
                (directory / 'GTA5.exe').write_bytes(exe)
            for name in manifest['files']:
                target = profile / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((bundle / 'payload' / name).read_bytes())
            install.symlink_to(profile, target_is_directory=True)
            state = {'phase': 'active', 'profile': str(profile), 'retail': str(retail), 'install': str(install),
                     'files': manifest['files'], 'original_exe_sha256': hashlib.sha256(exe).hexdigest()}
            state_path = root / 'profile-state.json'
            state_path.write_text(json.dumps(state))
            self.assertTrue(module.verify(bundle, root)['ok'])
            state['files'] = {'EldenLosSantos.asi': 'b' * 64}
            state_path.write_text(json.dumps(state))
            (profile / 'GTA5.exe').write_bytes(exe + b'changed')
            report = module.verify(bundle, root)
            self.assertFalse(report['ok'])
            self.assertTrue(any('profile manifest differs' in x for x in report['issues']))
            self.assertTrue(any('profile game executable differs' in x for x in report['issues']))

    def test_symlinked_external_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            bundle, _ = self.fixture(folder)
            target = bundle / 'payload/EldenLosSantos.asi'
            external = Path(folder) / 'external.asi'
            external.write_bytes(target.read_bytes())
            target.unlink()
            target.symlink_to(external)
            with self.assertRaises(ValueError):
                module.verify(bundle)


if __name__ == '__main__':
    unittest.main()
