"""Exercise v4 switching/recovery in temporary fixtures, never the real game."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

VOICE=Path(__file__).resolve().parents[1]/'scripts/voice'
sys.path.insert(0,str(VOICE))
with patch.dict(os.environ,{'PBZ_GAME_ROOT':str(VOICE/'unused-game')}):
    spec=importlib.util.spec_from_file_location('voice_switch',VOICE/'switch_reviewed_voice_v4.py')
    switch=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(switch)


class VoiceSwitchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.game=self.root/'steamapps/common/PBZ'
        (self.game/'platform/steam').mkdir(parents=True)
        (self.game/'platform/steam/PBZ.exe').write_bytes(b'fixture, never executed')
        self.target=self.game/'ProjectPBZ/Content/Paks/~mods'
        self.target.mkdir(parents=True)
        (self.root/'steamapps/appmanifest_4115450.acf').write_text('"buildid" "26367565"')
        self.model=self.target/'z_Sui_Model_v8_P.pak'
        self.model.write_bytes(b'current independent model')
        self.config=self.root/'settings.ini';self.config.write_bytes(b'unchanged settings')
        self.work=self.root/'variants/reviewed-natural-voice-v4'
        self.delivery=self.root/'delivery/reviewed-voice-v4'
        self.oldman=self.root/'delivery/library-voice-trial-v3/manifest.json'
        self.oldreceipt=self.root/'runtime-test-kit/library-natural-voice-v3-installation.receipt.json'
        names={'ROOT':self.root,'WORK':self.work,'DELIVERY':self.delivery,'GAME':self.game,
               'OLD_MAN':self.oldman,'OLD_RECEIPT':self.oldreceipt,
               'MAN':self.delivery/'manifest.json',
               'RECEIPT':self.root/'runtime-test-kit/reviewed-natural-voice-v4-installation.receipt.json',
               'CONFIG':self.config,'STATUS':self.root/'runtime-test-kit/reviewed-natural-voice-v4-status.json'}
        for name,value in names.items():
            p=patch.object(switch,name,value);p.start();self.addCleanup(p.stop)
        p=patch.object(switch.m,'stopped');p.start();self.addCleanup(p.stop)
        self.old=self.package(self.oldman.parent/'mod','OldVoice')
        self.write(self.oldman,{'variant':'library-natural-voice-v3','steam_app_id':'4115450',
                               'game_build':'26367565','files':self.old,'compatible_files':[self.model.name]})
        switch.m.install(self.oldman,self.game,self.oldreceipt,True)
        # Old metadata may list a model which is no longer installed.
        saved=switch.read(self.oldman);saved['compatible_files']=['z_Sui_Model_v1_P.pak'];self.write(self.oldman,saved)
        receipt=switch.read(self.oldreceipt);receipt['manifest_sha256']=switch.m.sha(self.oldman);self.write(self.oldreceipt,receipt)
        rows=self.package(self.work/'container','NewVoice')
        self.report={'variant':'reviewed-natural-voice-v4','container_files':[
            {**r,'path':str((self.work/'container'/r['name']).relative_to(self.root))} for r in rows]}
        self.write(self.work/'report.json',self.report)
        self.write(self.root/'public-export-audits/reviewed-natural-voice-v4/verification.json',
                   {'status':'independently-readback-verified-runtime-pending',
                    'source_report_sha256':switch.m.sha(self.work/'report.json'),
                    'exact_round2_choices_verified':True,'reviewed_issue_count':12,
                    'human_selected_changed_media':246,'unchanged_v3_media_byteidentical':228})
        self.write(self.work/'review-evidence/snapshot.json',{'review_sha256':'1'*64})
        self.before={p.name:p.read_bytes() for p in self.target.iterdir()}

    def write(self,path,data):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(data),encoding='utf-8')

    def package(self,directory,label):
        directory.mkdir(parents=True,exist_ok=True);rows=[]
        for ext in ['.pak','.ucas','.utoc']:
            p=directory/('z_Sui_'+label+'_P'+ext);p.write_bytes((label+ext).encode())
            rows.append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        return rows

    def run_main(self,*args):
        with patch.object(sys,'argv',['switch_reviewed_voice_v4.py',*args]):switch.main()

    def assert_original_restored(self):
        self.assertEqual({p.name:p.read_bytes() for p in self.target.iterdir()},self.before)
        self.assertEqual(self.config.read_bytes(),b'unchanged settings')

    def test_prepare_leaves_game_unchanged(self):
        self.run_main();self.assert_original_restored()
        self.assertTrue(switch.read(self.oldreceipt)['applied'])

    def test_install_then_rollback_preserves_current_model(self):
        self.run_main('--apply')
        self.assertTrue(switch.read(switch.STATUS)['model_files_unchanged'])
        self.assertFalse(switch.read(self.oldreceipt)['applied'])
        self.run_main('--rollback','--apply')
        self.assert_original_restored()
        self.assertEqual(switch.read(switch.STATUS)['status'],'rolled-back-to-library-natural-voice-v3')

    def test_new_install_failure_restores_v3_with_current_model_allowlist(self):
        original=switch.m.install
        def fail_new(manifest,*args,**kwargs):
            if manifest==switch.MAN:raise OSError('simulated new install failure')
            return original(manifest,*args,**kwargs)
        with patch.object(switch.m,'install',side_effect=fail_new):
            with self.assertRaisesRegex(OSError,'simulated'):self.run_main('--apply')
        self.assert_original_restored()
        self.assertTrue((self.root/'runtime-test-kit/v4-auto-recovery-v3.receipt.json').exists())

    def test_partial_old_uninstall_is_finished_before_recovery(self):
        original=switch.m.uninstall;failed=False
        def interrupt(manifest,game,receipt,apply=False):
            nonlocal failed
            if apply and manifest==self.oldman and not failed:
                failed=True;(self.target/self.old[0]['name']).unlink()
                raise OSError('simulated partial old removal')
            return original(manifest,game,receipt,apply)
        with patch.object(switch.m,'uninstall',side_effect=interrupt):
            with self.assertRaisesRegex(OSError,'simulated'):self.run_main('--apply')
        self.assert_original_restored()

    def test_partial_receipt_without_new_files_does_not_block_recovery(self):
        original=switch.m.install
        def fail_receipt(manifest,*args,**kwargs):
            if manifest==switch.MAN:
                switch.RECEIPT.write_text('{partial',encoding='utf-8')
                raise OSError('simulated receipt write failure')
            return original(manifest,*args,**kwargs)
        with patch.object(switch.m,'install',side_effect=fail_receipt):
            with self.assertRaisesRegex(OSError,'simulated'):self.run_main('--apply')
        self.assert_original_restored()

    def test_running_game_blocks_before_mutation(self):
        with patch.object(switch.m,'stopped',side_effect=ValueError('PBZ is running')):
            with self.assertRaisesRegex(ValueError,'running'):self.run_main('--apply')
        self.assert_original_restored()


if __name__=='__main__':unittest.main()
