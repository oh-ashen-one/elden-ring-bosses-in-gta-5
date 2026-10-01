# SPDX-License-Identifier: Apache-2.0
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('dlc_manifest',Path(__file__).resolve().parents[1]/'asset-tools/dlc_manifest.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class PropRegistration(unittest.TestCase):
    def check(self, contents, enabled=True):
        with tempfile.TemporaryDirectory() as folder:
            setup=Path(folder)/'setup.xml';content=Path(folder)/'content.xml'
            setup.write_text('<SSetupData><contentChangeSetGroups><Item><NameHash>GROUP_STARTUP</NameHash><ContentChangeSets><Item>start</Item></ContentChangeSets></Item></contentChangeSetGroups></SSetupData>')
            content.write_text('<CDataFileMgr__ContentsOfDataFileXml><dataFiles><Item><filename>dlc_ergt:/ergt.ityp</filename><fileType>DLC_ITYP_REQUEST</fileType><disabled value="true"/>'+contents+'</Item></dataFiles><contentChangeSets><Item><changeSetName>start</changeSetName><filesToEnable>'+('<Item>dlc_ergt:/ergt.ityp</Item>' if enabled else '')+'</filesToEnable></Item></contentChangeSets></CDataFileMgr__ContentsOfDataFileXml>')
            return module.validate_registration(setup,content)

    def test_original_missing_prop_classification_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'CONTENTS_PROPS'):self.check('')

    def test_prop_registration_and_startup_enable_are_both_required(self):
        prop='<contents>CONTENTS_PROPS</contents>'
        self.assertEqual(self.check(prop),1)
        with self.assertRaisesRegex(ValueError,'never enabled'):self.check(prop,False)


if __name__=='__main__':unittest.main()
