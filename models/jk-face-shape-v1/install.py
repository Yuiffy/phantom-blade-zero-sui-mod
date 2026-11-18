"""Hash-gated, transactional installation/rollback of this one-mesh overlay."""
from common import *
import argparse, shutil
from datetime import datetime, timezone, timedelta
from ue_pipeline import game_pids

def exited():
    assert not game_pids(), 'PBZ is running; exit the game before installation'

def matches(rows):
    assert snapshot()==rows, 'Installed MOD set changed; preserve the new work'

def gate():
    v=read(ROOT/'verification.json');g=read(ROOT/'geometry-verification.json');visual=read(ROOT/'visual-review.json')
    assert v['passed'] and g['passed'] and visual['reviewed']
    assert v['package_count']==1 and v['preserved_package_count']>=100 and v['directory_order_independent']
    assert v['native_render_sha256']==g['native_sha256']==visual['native_sha256']==sha(ROOT/'final.npz')
    assert v['all_other_native_export_bytes_exact'] and v['uv_indices_weights_skeleton_cloth_physics_exact']
    assert g['eyes_lips_and_other_components_positions_and_frames_exact'] and g['no_triangle_flips']
    renders=read(ROOT/'final-preview/render-manifest.json')
    assert renders['final']['native_sha256']==sha(ROOT/'final.npz')
    for row in renders.values():
        for p,h in row['images'].items():assert sha(p)==h
    assert visual['render_manifest_sha256']==sha(ROOT/'final-preview/render-manifest.json')
    assert visual['container_files']==v['container_files']
    allowed={NAME+ext for ext in ['.pak','.ucas','.utoc']}
    assert {r['name'] for r in v['container_files']}==allowed
    for row in v['container_files']:
        assert sha(ROOT/'container'/row['name'])==row['sha256']
    return v

def install(apply):
    exited();assert_baseline();v=gate()
    for row in v['container_files']:assert not (MODS/row['name']).exists()
    if not apply:
        print('JK_FACE_INSTALL_PREFLIGHT_PASSED');return
    before=snapshot();exited();matches(before)
    now=datetime.now(timezone(timedelta(hours=8)))
    record=ROOT/('installation-'+now.strftime('%Y%m%d-%H%M%S-%f'));record.mkdir()
    write(record/'before.json',before)
    copied=[]
    try:
        for row in v['container_files']:
            exited()
            target=MODS/row['name']
            with target.open('xb') as f:f.write((ROOT/'container'/row['name']).read_bytes())
            copied.append(row)
            assert sha(target)==row['sha256']
        after=snapshot()
        assert {r['name']:r['sha256'] for r in after}=={r['name']:r['sha256'] for r in before+v['container_files']}
        receipt=dict(status='installed-hash-verified-runtime-pending',installed_at=now.isoformat(),target=str(MODS),record=str(record),before=before,after=after,added=[r['name'] for r in copied],
                     native_sha256=v['native_render_sha256'],previous_files_exact=True,game_runtime_tested=False)
        write(ROOT/'installation-receipt.json',receipt);write(record/'installation-receipt.json',receipt)
    except Exception:
        for row in reversed(copied):
            p=MODS/row['name']
            assert sha(p)==row['sha256']
            shutil.move(str(p),str(record/p.name))
        matches(before)
        raise
    print('JK_FACE_INSTALLED_HASH_VERIFIED')

def rollback(apply):
    exited();receipt=read(ROOT/'installation-receipt.json');matches(receipt['after'])
    if not apply:
        print('JK_FACE_ROLLBACK_PREFLIGHT_PASSED');return
    target=Path(receipt['record'])/'rollback';target.mkdir()
    expected={r['name']:r['sha256'] for r in receipt['after']}
    for name in receipt['added']:
        exited();p=MODS/name
        assert p.resolve().parent==MODS.resolve() and sha(p)==expected[name]
        shutil.move(str(p),str(target/name))
    matches(receipt['before'])
    write(target/'receipt.json',dict(status='rolled-back-hash-verified',after=snapshot(),only_face_shape_overlay_removed=True))
    print('JK_FACE_ROLLED_BACK_HASH_VERIFIED')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--rollback',action='store_true')
    a=parser.parse_args();rollback(a.apply) if a.rollback else install(a.apply)
