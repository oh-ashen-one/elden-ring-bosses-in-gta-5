# SPDX-License-Identifier: Apache-2.0
import importlib.util
import unittest
import tempfile
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

    def test_emergency_pause_is_never_an_owner_reservation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/'PAUSED'
            self.assertFalse(module.owner_reservation(root))
            p.write_text('desktop session cannot render');self.assertFalse(module.owner_reservation(root))
            p.write_text('owner opening GTA V 14:48 - renders paused; auto-lift after GTA5.exe exits')
            self.assertTrue(module.owner_reservation(root))
            p.write_text('owner reopening GTA 15:02 - renders paused by game_watch.sh (pre-emptive)')
            self.assertTrue(module.owner_reservation(root))


if __name__ == '__main__': unittest.main()
