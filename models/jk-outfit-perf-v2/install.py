"""Check quality, compare like-for-like solve samples and read back the installed override."""
import shutil
from datetime import datetime

import numpy as np
from deliver import common, prior, root, stage, read, write, sha, verify


def review():
    costs={}
    for label in ['baseline','shell','bend','both','repeat','reduced','reduced-full']:
        path=root/label/'jog-60.json'
        data=read(path)
        times=data['timings'][:121]
        assert [t['step'] for t in times]==list(range(60,181))
        median,tail=np.percentile([t['solve_ms'] for t in times],[50,95])
        costs[label]=dict(median_ms=float(median),p95_ms=float(tail),source_sha256=sha(path))
    for k in ['median_ms','p95_ms']:
        assert max(costs[n][k] for n in ['reduced','reduced-full']) < .3*min(costs[n][k] for n in ['baseline','repeat'])
    ev=read(stage/'evaluation.json')
    assert ev['passed'] and ev['document_sha256']==sha(root/'native/final.json')
    shape=read(root/'visible-motion.json')
    assert len(shape)==6
    for row in shape:
        assert row['simulation_sha']==sha(stage/row['file'])
        part=row['deviations']
        assert max(part[k]['max_cm'] for k in ['0','2'])<.001
        assert max(v['max_cm'] for v in part.values())<1.6
    cover=read(root/'coverage.json')
    assert cover['up32cm_test_rear_and_oblique']==[0,0] and len(cover['rows'])==6
    assert all(r['max_rear_shorts_pixels']==0 for r in cover['rows'])
    contacts=[{k:v for k,v in row.items() if k!='samples'} for row in read(stage/'contacts.json')['records']]
    return dict(offline_solve=costs,matched_ticks=121,coverage=cover,visible_motion=shape,contacts=contacts,
                physical_vertices=[len(a['positions']) for a in read(stage/'cloth-details.json')['assets']],
                previous_reported_game_fps=[45,48],new_game_fps=None)


def install():
    evidence=review()
    build=read(root/'build.json')
    assert common.snapshot()==build['before'] and not common.game_pids()
    files=build['files']
    created=[]
    try:
        for row in files:
            src=root/'container'/row['name']
            target=common.MODS/src.name
            assert sha(src)==row['sha256'] and not common.game_pids()
            with src.open('rb') as source,target.open('xb') as destination:
                created.append(target)
                shutil.copyfileobj(source,destination)
            assert sha(target)==row['sha256']
        after=common.snapshot()
        expected={r['name']:r for r in build['before']+files}
        assert len(after)==len(expected) and all(r==expected[r['name']] for r in after)
        verify('installed',[common.MODS])
        assert common.snapshot()==after
        receipt=dict(installed_at=datetime.now().astimezone().isoformat(),added=files,before=build['before'],after=after)
        write(root/'installation.json',receipt)
    except Exception:
        if not common.game_pids():
            for target in reversed(created):
                if sha(target)==sha(root/'container'/target.name):
                    target.unlink()
        raise
    evidence.update(installed_at=receipt['installed_at'],files=files,retained_files=len(build['before']),
                    effective_payload_sha256=build['payload'],independent_installed_readback=True)
    write(common.REPO/'evidence/jk-outfit-perf-v2/verification.json',evidence)


if __name__=='__main__':
    install()
