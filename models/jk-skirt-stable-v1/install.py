from datetime import datetime
import shutil
from skirt import WORK, PERF, read, write, sha, verify, common


def install():
    build=read(WORK/'build.json')
    ev=read(WORK/'replay/evaluation.json')
    assert ev['passed'] and ev['document_sha256']==sha(WORK/'native/final.json')
    contacts=read(WORK/'replay/contacts.json')['records']
    assert len(contacts)==6 and all(row['thigh_sum']==0 for row in contacts)
    cover=read(WORK/'coverage.json')
    assert cover['preview_sha256']==sha(WORK/'preview/front-comparison.jpg')
    assert all(cover['visible_shorts_pixels'][f'final-{angle}']==0 for angle in [0,38,180,145,-145])
    assert common.snapshot()==build['before']
    assert not common.game_pids(), 'Game is running'
    written=[]
    try:
        for row in build['files']:
            src=WORK/'container'/row['name']
            target=common.MODS/row['name']
            assert sha(src)==row['sha256'] and not common.game_pids()
            with src.open('rb') as inp,target.open('xb') as out:
                written.append((target,row['sha256']))
                shutil.copyfileobj(inp,out)
            assert sha(target)==row['sha256']
        verify('installed',[common.MODS])
        after=common.snapshot()
        expected={r['name']:r for r in build['before']+build['files']}
        assert len(after)==len(expected) and all(r==expected[r['name']] for r in after)
    except Exception:
        for path,h in reversed(written):
            if not common.game_pids() and sha(path)==h:
                path.unlink()
        raise
    write(WORK/'installation.json',dict(installed=True,before=build['before'],after=after,files=build['files']))
    write(common.REPO/'evidence/jk-skirt-stable-v1/verification.json',dict(installed_at=datetime.now().astimezone().isoformat(),
          user_confirmed_previous_version_performance=True,game_tested_this_version=False,added=build['files'],
          installed_payload=build['payload'],offline_coverage=cover,offline_motion=ev,
          contacts=[{k:v for k,v in r.items() if k!='samples'} for r in contacts],
          previous_contacts=[{k:v for k,v in r.items() if k!='samples'} for r in read(PERF/'reduced-full/contacts.json')['records']]))

if __name__=='__main__':
    install()
