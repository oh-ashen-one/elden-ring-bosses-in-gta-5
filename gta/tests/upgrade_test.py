# SPDX-License-Identifier: Apache-2.0
"""Exercise upgrades and rollback on tiny synthetic payloads, never real games."""
import copy
import fcntl
import json
import shutil
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import upgrade_profile as u

class UpgradeTests(unittest.TestCase):
    def fixture(self,base):
        root=base/'profile';profile=root/'Game';retail=root/'Retail';install=base/'Steam/Game'
        bundle=base/'bundle';candidate=base/'candidate'
        exe=b'MZ'+b'\0'*30+struct.pack('<6I',0xfeef04bd,0x10000,1<<16,3889<<16,0,0)
        for path in [profile,retail]:path.mkdir(parents=True);(path/'GTA5.exe').write_bytes(exe)
        install.parent.mkdir();install.symlink_to(profile,target_is_directory=True)
        for package,kind in [(bundle,'old'),(candidate,'new')]:
            files={}
            for name in u.REQUIRED:
                path=package/'payload'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(kind+name);files[name]=u.digest(path)
            (package/'manifest.json').write_text(json.dumps({'candidate':kind,'files':files,'expected_game_version':'1.0.3889.0'}))
            (package/'Tools').mkdir()
            for name in u.TOOLS:(package/'Tools'/name).write_text(kind+name)
            for name in ['START-HERE.md','VERIFICATION.json']:(package/name).write_text(kind)
        manifest=json.loads((bundle/'manifest.json').read_text())
        for name in manifest['files']:
            dst=profile/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(bundle/'payload'/name,dst)
        state={'phase':'active','candidate':'old','profile':str(profile),'retail':str(retail),'install':str(install),
               'original_exe_sha256':u.digest(retail/'GTA5.exe'),'files':manifest['files'],'previous_dinput8':None}
        (root/'profile-state.json').write_text(json.dumps(state))
        return candidate,bundle,root,state

    def test_success_is_repeatable_and_preserves_retail(self):
        with tempfile.TemporaryDirectory() as t,patch.object(u,'ensure_game_stopped'):
            c,b,r,old=self.fixture(Path(t));result=u.upgrade(c,b,r)
            self.assertEqual(result['status'],'installed');self.assertTrue(u.verify(b,r)['ok'])
            self.assertEqual(u.digest(r/'Retail/GTA5.exe'),old['original_exe_sha256'])
            self.assertEqual(u.upgrade(c,b,r)['status'],'already_installed')

    def test_failed_replace_restores_payload_helpers_and_state(self):
        with tempfile.TemporaryDirectory() as t,patch.object(u,'ensure_game_stopped'):
            c,b,r,old=self.fixture(Path(t));replace=u.os.replace;count=0
            def fail_once(src,dst):
                nonlocal count
                if '.upgrade-' in str(src):
                    count+=1
                    if count==3:raise OSError('injected file replacement failure')
                return replace(src,dst)
            with patch.object(u.os,'replace',side_effect=fail_once):
                with self.assertRaisesRegex(OSError,'injected'):u.upgrade(c,b,r)
            self.assertEqual(json.loads((r/'profile-state.json').read_text()),old)
            self.assertTrue(u.verify(b,r)['ok']);self.assertEqual((b/'Tools/launch_owner.py').read_text(),'oldlaunch_owner.py')
            self.assertFalse(list(b.rglob('*.upgrade-*')))

    def test_running_game_or_drift_blocks_before_mutation(self):
        with tempfile.TemporaryDirectory() as t:
            c,b,r,old=self.fixture(Path(t))
            with patch.object(u,'ensure_game_stopped',side_effect=RuntimeError('running')):
                with self.assertRaisesRegex(RuntimeError,'running'):u.upgrade(c,b,r)
            (c/'payload/EldenLosSantos.asi').write_text('bad')
            with patch.object(u,'ensure_game_stopped'):
                with self.assertRaisesRegex(RuntimeError,'checksum mismatch'):u.upgrade(c,b,r)
            self.assertEqual(json.loads((r/'profile-state.json').read_text()),old)

    def test_same_payload_repairs_stale_helpers(self):
        with tempfile.TemporaryDirectory() as t,patch.object(u,'ensure_game_stopped'):
            c,b,r,_=self.fixture(Path(t));u.upgrade(c,b,r)
            (b/'Tools/launch_owner.py').write_text('stale helper')
            result=u.upgrade(c,b,r)
            self.assertEqual(result['status'],'installed')
            self.assertEqual((b/'Tools/launch_owner.py').read_text(),'newlaunch_owner.py')

    def test_another_profile_mutation_blocks(self):
        with tempfile.TemporaryDirectory() as t,patch.object(u,'ensure_game_stopped'):
            c,b,r,_=self.fixture(Path(t))
            with (r/'profile.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):u.upgrade(c,b,r)

if __name__=='__main__':unittest.main()
