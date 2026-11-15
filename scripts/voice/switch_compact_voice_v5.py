"""Optional maintainer-only v4/v5 switch. Players can just copy the triplet.

Uses existing hash/receipt installer; never starts or stops PBZ or captures UI.
Prepared manifests record the actual unrelated MODs, including current models.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mod_files as m
from paths import ROOT, game_root, settings_path
from resolve_bilingual_voice_inventory import read, write

WORK = ROOT/'variants/compact-reviewed-voice-v5'

DELIVERY = ROOT/'delivery/compact-voice-v5'
MAN = DELIVERY/'manifest.json'
OLD_MAN = ROOT/'delivery/reviewed-voice-v4/manifest.json'
OLD_RECEIPT = ROOT/'runtime-test-kit/reviewed-natural-voice-v4-installation.receipt.json'
RECEIPT = ROOT/'runtime-test-kit/compact-reviewed-voice-v5-installation.receipt.json'
SNAPSHOT = WORK/'installation-before.json'
RECOVERY = OLD_MAN.with_name('compact-v5-recovery.manifest.json')


def unrelated(target, excluded):
    rows = {}
    for p in target.rglob('*'):
        m.plain(p)
        if p.is_file() and p.name not in excluded:
            rows[p.relative_to(target).as_posix()] = {'bytes':p.stat().st_size,'sha256':m.sha(p)}
    return rows


def snapshot_once(path, data):
    if path.exists():
        assert read(path) == data, 'Existing preparation differs; inspect before proceeding'
    else:
        write(path,data)


def main():
    if not __debug__:
        raise RuntimeError('Do not disable installation assertions with python -O')
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply',action='store_true')
    ap.add_argument('--rollback',action='store_true')
    args = ap.parse_args()
    m.stopped()
    game = game_root()
    if args.rollback:
        assert args.apply
        target = m.target_for(game,read(MAN),False)
        before = unrelated(target,{r['name'] for r in read(MAN)['files']})
        settings = m.sha(settings_path())
        recovery = RECOVERY.with_name('compact-v5-active-rollback.manifest.json')
        snapshot_once(recovery,{**read(RECOVERY),'compatible_files':list(before)})
        m.verify(recovery)
        m.uninstall(MAN,game,RECEIPT,False)
        restore = ROOT/'runtime-test-kit/compact-v5-restored-v4.receipt.json'
        assert not restore.exists()
        m.uninstall(MAN,game,RECEIPT,True)
        m.install(recovery,game,restore,True)
        assert unrelated(target,{r['name'] for r in read(recovery)['files']}) == before
        assert m.sha(settings_path()) == settings
        write(WORK/'rollback.json',{'restored':'reviewed-natural-voice-v4','runtime_tested':False,
                                  'unrelated_mod_files_unchanged':True,'settings_unchanged':True})
        print('Restored v4.');return
    audit = read(WORK/'verification.json')
    assert audit['status'] == 'independent-final-container-readback-verified-runtime-pending'
    assert audit['source_report_sha256'] == m.sha(WORK/'report.json')
    assert not RECEIPT.exists(), 'Existing attempt: inspect receipt before retrying'
    old = m.verify(OLD_MAN)
    target = m.target_for(game,old,True)
    for row in old['files']:
        m.check_file(target/row['name'],row)
    m.uninstall(OLD_MAN,game,OLD_RECEIPT,False)
    before = unrelated(target,{r['name'] for r in old['files']})
    settings = m.sha(settings_path())
    expected = {'files':audit['files'],'variant':'compact-reviewed-voice-v5',
                'steam_app_id':'4115450','game_build':'26367565','compatible_files':list(before),
                'runtime_tested':False}
    snapshot_once(MAN,expected)
    m.verify(MAN)
    data = {'old_manifest_sha256':m.sha(OLD_MAN),'old_receipt':read(OLD_RECEIPT),
            'unrelated_mod_files':before,'settings_sha256':settings}
    snapshot_once(SNAPSHOT,data)
    recovery = {**old,'compatible_files':list(before)}
    snapshot_once(RECOVERY,recovery)
    # Keep recovery beside the original local delivery: no extra GB copy.
    m.verify(RECOVERY)
    if not args.apply:
        print('Prepared. Game unchanged.');return
    m.stopped()
    assert unrelated(target,{r['name'] for r in old['files']}) == before
    assert m.sha(settings_path()) == settings
    try:
        m.uninstall(OLD_MAN,game,OLD_RECEIPT,True)
        m.install(MAN,game,RECEIPT,True)
    except BaseException:
        m.stopped()
        if read(OLD_RECEIPT).get('applied'):
            m.uninstall(OLD_MAN,game,OLD_RECEIPT,True)
        if any((target/row['name']).exists() for row in expected['files']):
            m.uninstall(MAN,game,RECEIPT,True)
        m.install(RECOVERY,game,ROOT/'runtime-test-kit/compact-v5-auto-restored-v4.receipt.json',True)
        raise
    assert unrelated(target,{r['name'] for r in expected['files']}) == before
    assert m.sha(settings_path()) == settings
    for row in expected['files']:
        m.check_file(target/row['name'],row)
    write(WORK/'installation-after.json',{'status':'installed-offline-verified-runtime-pending',
          'variant':WORK.name,'files':expected['files'],'total_bytes':audit['total_bytes'],
          'unrelated_mod_files_unchanged':True,'settings_unchanged':True,'runtime_tested':False,
          'old_v4_preserved_in_local_delivery':True,'source_report_sha256':m.sha(WORK/'report.json'),
          'verification_sha256':m.sha(WORK/'verification.json')})
    print('Installed compact v5; model/config unchanged; runtime pending.')


if __name__ == '__main__':
    main()
