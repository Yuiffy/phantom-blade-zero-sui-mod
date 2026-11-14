"""Receipt-based offline v3 -> reviewed v4 switch, with automatic recovery.

--rollback restores v3 while preserving the currently installed model files.
Never launches, stops, captures, or attaches to PBZ.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import mod_files as m
from paths import ROOT, game_root, settings_path
from resolve_bilingual_voice_inventory import read, write

WORK=ROOT/'variants/reviewed-natural-voice-v4'
DELIVERY=ROOT/'delivery/reviewed-voice-v4'
GAME=game_root()
OLD_MAN=ROOT/'delivery/library-voice-trial-v3/manifest.json'
OLD_RECEIPT=ROOT/'runtime-test-kit/library-natural-voice-v3-installation.receipt.json'
MAN=DELIVERY/'manifest.json'
RECEIPT=ROOT/'runtime-test-kit/reviewed-natural-voice-v4-installation.receipt.json'
CONFIG=settings_path()
STATUS=ROOT/'runtime-test-kit/reviewed-natural-voice-v4-status.json'


def unrelated(target, excluded):
    result={}
    for p in target.rglob('*'):
        m.plain(p)
        if p.is_file() and p.name not in excluded:
            result[p.relative_to(target).as_posix()]={'bytes':p.stat().st_size,'sha256':m.sha(p)}
    return result


def save_once(path,data):
    if path.exists():assert read(path)==data
    else:write(path,data)


def recovery_manifest(compatible, filename):
    old=read(OLD_MAN)
    old['compatible_files']=compatible
    dest=OLD_MAN.with_name(filename)
    save_once(dest,old)
    m.verify(dest)
    return dest


def rollback():
    m.stopped()
    current=m.verify(MAN)
    target=m.target_for(GAME,current,True)
    excluded={r['name'] for r in current['files']}
    before=unrelated(target,excluded)
    settings=m.sha(CONFIG)
    m.uninstall(MAN,GAME,RECEIPT,False)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=recovery_manifest(list(before),f'v4-rollback-{stamp}.manifest.json')
    restore_receipt=ROOT/f'runtime-test-kit/v4-rollback-v3-{stamp}.receipt.json'
    m.uninstall(MAN,GAME,RECEIPT,True)
    m.install(backup,GAME,restore_receipt,True)
    old_names={r['name'] for r in read(backup)['files']}
    assert unrelated(target,old_names)==before and m.sha(CONFIG)==settings
    write(ROOT/f'runtime-test-kit/v4-rollback-{stamp}.json',
          {'restored':'library-natural-voice-v3','receipt':str(restore_receipt),
           'model_files_unchanged':True,'settings_unchanged':True})
    write(STATUS,{'status':'rolled-back-to-library-natural-voice-v3',
                  'runtime_tested':False,'restore_receipt':str(restore_receipt),
                  'model_files_unchanged':True,'settings_unchanged':True})
    print('Restored v3; unrelated MODs and configuration unchanged.')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--apply',action='store_true')
    ap.add_argument('--rollback',action='store_true')
    args=ap.parse_args()
    if args.rollback:
        assert args.apply,'Rollback requires --apply'
        rollback();return
    m.stopped()
    report=read(WORK/'report.json');audit=read(ROOT/'public-export-audits/reviewed-natural-voice-v4/verification.json')
    assert audit['status']=='independently-readback-verified-runtime-pending'
    assert audit['source_report_sha256']==m.sha(WORK/'report.json')
    assert audit['exact_round2_choices_verified'] and audit['reviewed_issue_count']==12
    assert not RECEIPT.exists(),'Already installed or attempted; inspect receipt before repeating'
    old=m.verify(OLD_MAN)
    target=m.target_for(GAME,old,True)
    old_names={r['name'] for r in old['files']}
    for row in old['files']:m.check_file(target/row['name'],row)
    m.uninstall(OLD_MAN,GAME,OLD_RECEIPT,False)
    before=unrelated(target,old_names);settings=m.sha(CONFIG)
    rows=[{k:r[k] for k in ['name','bytes','sha256']} for r in report['container_files']]
    manifest={'variant':report['variant'],'steam_app_id':'4115450','game_build':'26367565',
              'files':rows,'compatible_files':list(before),'local_only':True}
    (DELIVERY/'mod').mkdir(parents=True,exist_ok=True)
    for row,source in zip(rows,report['container_files']):
        dest=DELIVERY/'mod'/row['name']
        if not dest.exists():shutil.copyfile(ROOT/source['path'],dest)
        m.check_file(dest,row)
    save_once(MAN,manifest);m.verify(MAN)
    # Keep the original receipt before the old install is marked removed.
    snapshot=WORK/'review-evidence/installation-before.json'
    before_data={'old_manifest_sha256':m.sha(OLD_MAN),'old_receipt':read(OLD_RECEIPT),
                 'old_receipt_sha256':m.sha(OLD_RECEIPT),'unrelated_mod_files':before,
                 'settings_sha256':settings,'build_id':'26367565'}
    save_once(snapshot,before_data)
    recovery=recovery_manifest(list(before),'v4-recovery.manifest.json')
    if not args.apply:
        print('Prepared and verified; game files unchanged.');return
    # Recheck process, source files, model files and config immediately before mutation.
    m.stopped()
    assert unrelated(target,old_names)==before and m.sha(CONFIG)==settings
    try:
        m.uninstall(OLD_MAN,GAME,OLD_RECEIPT,True)
        m.install(MAN,GAME,RECEIPT,True)
    except BaseException:
        # Uninstaller is interruption tolerant: finish checking/removing remaining v3 files.
        m.stopped()
        if read(OLD_RECEIPT).get('applied'):
            m.uninstall(OLD_MAN,GAME,OLD_RECEIPT,True)
        # install() removes all newly created files if receipt writing fails.
        # A partial receipt must not block recovery when no new files remain.
        if any((target/row['name']).exists() for row in rows):
            m.uninstall(MAN,GAME,RECEIPT,True)
        m.install(recovery,GAME,ROOT/'runtime-test-kit/v4-auto-recovery-v3.receipt.json',True)
        raise
    for row in rows:m.check_file(target/row['name'],row)
    assert all(not (target/n).exists() for n in old_names)
    new_names={r['name'] for r in rows}
    assert unrelated(target,new_names)==before and m.sha(CONFIG)==settings
    status={'status':'installed-human-reviewed-v4-offline-verified-runtime-pending',
            'installed_at':datetime.now(timezone.utc).isoformat(),'variant':report['variant'],
            'build_id':'26367565','files':rows,'reviewed_issue_count':12,
            'changed_media':audit['human_selected_changed_media'],
            'unchanged_media':audit['unchanged_v3_media_byteidentical'],
            'model_files_unchanged':True,'settings_unchanged':True,
            'unrelated_mod_files':before,'settings_sha256':settings,
            'review_sha256':read(WORK/'review-evidence/snapshot.json')['review_sha256'],
            'source_report_sha256':m.sha(WORK/'report.json'),
            'verification_sha256':m.sha(ROOT/'public-export-audits/reviewed-natural-voice-v4/verification.json'),
            'receipt':str(RECEIPT.relative_to(ROOT)),'runtime_tested':False,
            'duration_playback_runtime_pending':True,
            'rollback_command':'python -X utf8 "'+str(Path(__file__).resolve())+'" --rollback --apply'}
    write(STATUS,status)
    write(WORK/'review-evidence/installation-after.json',status)
    print('Installed v4. Exact final triplet verified. Model/config unchanged. Runtime pending.')


if __name__=='__main__':main()
