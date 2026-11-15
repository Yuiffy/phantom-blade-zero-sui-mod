"""Verify v5 installation/rollback failure boundaries using a fake game."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

VOICE = Path(__file__).resolve().parents[1]/'scripts/voice'
sys.path.insert(0,str(VOICE))
spec = importlib.util.spec_from_file_location('compact_switch',VOICE/'switch_compact_voice_v5.py')
switch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(switch)


class CompactSwitchTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.game = self.root/'steamapps/common/PBZ'
        (self.game/'platform/steam').mkdir(parents=True)
        (self.game/'platform/steam/PBZ.exe').write_bytes(b'fixture; never executed')
        self.target = self.game/'ProjectPBZ/Content/Paks/~mods'
        self.target.mkdir(parents=True)
        (self.root/'steamapps/appmanifest_4115450.acf').write_text('"buildid" "26367565"')
        self.model = self.target/'z_Sui_Model_v10_P.pak'
        self.model.write_bytes(b'current model')
        self.config = self.root/'settings.ini'
        self.config.write_bytes(b'current settings')
        work = self.root/'variants/compact-reviewed-voice-v5'
        delivery = self.root/'delivery/compact-voice-v5'
        oldman = self.root/'delivery/reviewed-voice-v4/manifest.json'
        constants = {'ROOT':self.root,'WORK':work,'DELIVERY':delivery,
            'MAN':delivery/'manifest.json','OLD_MAN':oldman,
            'OLD_RECEIPT':self.root/'old.receipt.json','RECEIPT':self.root/'new.receipt.json',
            'SNAPSHOT':work/'installation-before.json',
            'RECOVERY':oldman.with_name('compact-v5-recovery.manifest.json')}
        for name,value in constants.items():
            p = patch.object(switch,name,value);p.start();self.addCleanup(p.stop)
        for name,value in [('game_root',self.game),('settings_path',self.config)]:
            p = patch.object(switch,name,return_value=value);p.start();self.addCleanup(p.stop)
        p = patch.object(switch.m,'stopped');p.start();self.addCleanup(p.stop)
        old = self.package(oldman.parent/'mod','V4')
        switch.write(oldman,{'variant':'reviewed-natural-voice-v4','steam_app_id':'4115450',
            'game_build':'26367565','files':old,'compatible_files':[self.model.name]})
        switch.m.install(oldman,self.game,switch.OLD_RECEIPT,True)
        rows = self.package(delivery/'mod','V5')
        switch.write(work/'report.json',{'fixture':True})
        switch.write(work/'verification.json',{
            'status':'independent-final-container-readback-verified-runtime-pending',
            'source_report_sha256':switch.m.sha(work/'report.json'),
            'files':rows,'total_bytes':sum(r['bytes'] for r in rows)})
        self.before = {p.name:p.read_bytes() for p in self.target.iterdir()}

    def package(self,directory,label):
        directory.mkdir(parents=True)
        rows = []
        for ext in ['.pak','.utoc','.ucas']:
            p = directory/('z_Sui_'+label+'_P'+ext)
            p.write_bytes((label+ext).encode())
            rows.append({'name':p.name,'bytes':p.stat().st_size,'sha256':switch.m.sha(p)})
        return rows

    def run_main(self,*args):
        with patch.object(sys,'argv',['switch_compact_voice_v5.py',*args]):
            switch.main()

    def assert_restored(self):
        self.assertEqual({p.name:p.read_bytes() for p in self.target.iterdir()},self.before)
        self.assertEqual(self.config.read_bytes(),b'current settings')

    def test_prepare_keeps_game_unchanged(self):
        self.run_main()
        self.assert_restored()
        self.assertTrue(switch.read(switch.OLD_RECEIPT)['applied'])

    def test_rollback_preserves_a_later_model_and_setting_change(self):
        self.run_main('--apply')
        self.model.unlink()
        newer = self.target/'z_Sui_Model_v11_P.pak'
        newer.write_bytes(b'new model installed later')
        self.config.write_bytes(b'new settings chosen later')
        self.run_main('--rollback','--apply')
        expected = {k:v for k,v in self.before.items() if k != self.model.name}
        expected[newer.name] = b'new model installed later'
        self.assertEqual({p.name:p.read_bytes() for p in self.target.iterdir()},expected)
        self.assertEqual(self.config.read_bytes(),b'new settings chosen later')

    def test_new_install_failure_restores_v4(self):
        original = switch.m.install
        def fail(manifest,*args,**kwargs):
            if manifest == switch.MAN:
                raise OSError('simulated install failure')
            return original(manifest,*args,**kwargs)
        with patch.object(switch.m,'install',side_effect=fail):
            with self.assertRaisesRegex(OSError,'simulated'):
                self.run_main('--apply')
        self.assert_restored()

    def test_partial_old_uninstall_is_finished_before_recovery(self):
        original = switch.m.uninstall
        failed = False
        def fail(manifest,game,receipt,apply=False):
            nonlocal failed
            if apply and manifest == switch.OLD_MAN and not failed:
                failed = True
                (self.target/switch.read(manifest)['files'][0]['name']).unlink()
                raise OSError('simulated partial uninstall')
            return original(manifest,game,receipt,apply)
        with patch.object(switch.m,'uninstall',side_effect=fail):
            with self.assertRaisesRegex(OSError,'simulated'):
                self.run_main('--apply')
        self.assert_restored()

    def test_partial_receipt_without_new_files_does_not_prevent_recovery(self):
        original = switch.m.install
        def fail(manifest,*args,**kwargs):
            if manifest == switch.MAN:
                switch.RECEIPT.write_text('{partial')
                raise OSError('simulated receipt failure')
            return original(manifest,*args,**kwargs)
        with patch.object(switch.m,'install',side_effect=fail):
            with self.assertRaisesRegex(OSError,'simulated'):
                self.run_main('--apply')
        self.assert_restored()

    def test_running_game_refuses_before_mutation(self):
        with patch.object(switch.m,'stopped',side_effect=ValueError('PBZ running')):
            with self.assertRaisesRegex(ValueError,'running'):
                self.run_main('--apply')
        self.assert_restored()


if __name__ == '__main__':
    unittest.main()
