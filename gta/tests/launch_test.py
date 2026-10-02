# SPDX-License-Identifier: Apache-2.0
import importlib.util
import json
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path

spec = importlib.util.spec_from_file_location('launch_owner', Path(__file__).resolve().parents[1] / 'tools/launch_owner.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class LaunchPreflight(unittest.TestCase):
    def test_saturated_gpu_blocks_even_below_global_process_cap(self):
        self.assertTrue(module.blockers([], 97, 'owner', 'owner'))

    def test_quiet_but_live_renderer_blocks(self):
        self.assertTrue(module.blockers([{'pid':42,'name':'unrealeditor','state':'S','command':'UE -game'}],0,'owner','owner'))

    def test_headless_import_is_allowed(self):
        self.assertFalse(module.blockers([{'pid':42,'name':'unrealeditor','state':'R','command':'UE -nullrhi -run=pythonscript'}],0,'owner','owner'))

    def test_exiting_headless_engine_still_blocks(self):
        self.assertTrue(module.blockers([{'pid':42,'name':'unrealeditor','state':'Z','command':'UE -nullrhi'}],0,'owner','owner'))

    def test_unknown_gpu_or_logged_out_desktop_blocks(self):
        self.assertTrue(module.blockers([], None, 'owner', 'owner'))
        self.assertTrue(module.blockers([], 0, 'root', 'owner'))

    def test_support_service_is_not_a_renderer(self):
        self.assertFalse(module.blockers([{'pid':42,'name':'unrealeditorservices','state':'S','command':'service'}],0,'owner','owner'))

    def test_reserved_desktop_baseline_does_not_admit_renderer(self):
        self.assertFalse(module.blockers([],21,'owner','owner',30))
        self.assertTrue(module.blockers([],30,'owner','owner',30))
        self.assertTrue(module.blockers([{'pid':42,'name':'unrealeditor','state':'R','command':'UE -game'}],21,'owner','owner',30))

    def test_native_crossover_game_blocks_exclusive_gta_without_shared_lock(self):
        # Finder-launched IW4L historically used a different perf.lock. Its
        # presence must still block GTA even with an idle utilization sample.
        for executable in ('iw4l', 'iw4l.exe', 'robloxstudio', 'robloxplayer',
                           'robloxstudiobeta.exe', 'robloxplayerbeta.exe',
                           'spider-man.exe', 'batmanak.exe'):
            with self.subTest(executable=executable):
                reasons = module.blockers([{'pid':42,'name':executable,'state':'S','command':executable}],0,'owner','owner',30)
                self.assertTrue(any('renderer' in reason for reason in reasons))

    def test_failed_process_inventory_blocks_instead_of_claiming_idle(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(module.subprocess, 'check_output', return_value='"Device Utilization %" = 0'), \
                 patch.object(module, 'processes', side_effect=PermissionError('denied')):
                result = module.preflight(Path(folder))
                self.assertTrue(result['blockers'])
                self.assertIn('Cannot inspect renderer processes', result['blockers'][0])

    def test_packaged_launcher_rejects_old_installed_candidate(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);bundle=root/'candidate';profile=root/'profile'
            bundle.mkdir();profile.mkdir()
            (bundle/'manifest.json').write_text(json.dumps({'candidate':'pose-repair','files':{'EldenLosSantos.asi':'new'}}))
            state=profile/'profile-state.json'
            state.write_text(json.dumps({'candidate':'v8','files':{'EldenLosSantos.asi':'old'}}))
            reasons=module.candidate_profile_blockers(bundle,profile)
            self.assertIn('installed=v8',reasons[0]);self.assertIn('requested=pose-repair',reasons[0])
            state.write_text(json.dumps({'candidate':'pose-repair','files':{'EldenLosSantos.asi':'new'}}))
            self.assertEqual(module.candidate_profile_blockers(bundle,profile),[])

    def test_packaged_launcher_fails_closed_when_profile_state_unavailable(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'manifest.json').write_text('{"files":{"EldenLosSantos.asi":"new"}}')
            self.assertTrue(module.candidate_profile_blockers(root,root/'missing-profile'))

    def test_unpackaged_source_helper_does_not_claim_candidate_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.assertEqual(module.candidate_profile_blockers(root,root/'missing-profile'),[])

    def test_emergency_pause_is_never_an_owner_reservation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/'PAUSED'
            self.assertFalse(module.owner_reservation(root))
            p.write_text('desktop session cannot render');self.assertFalse(module.owner_reservation(root))
            p.write_text('owner opening GTA V 14:48 - renders paused; auto-lift after GTA5.exe exits')
            self.assertTrue(module.owner_reservation(root))
            p.write_text('owner reopening GTA 15:02 - renders paused by game_watch.sh (pre-emptive)')
            self.assertTrue(module.owner_reservation(root))
            p.write_text('OWNER PAUSE 15:41: everything stopped until the owner says resume (GTA for a few hours)\n')
            self.assertTrue(module.owner_reservation(root))


if __name__ == '__main__': unittest.main()
