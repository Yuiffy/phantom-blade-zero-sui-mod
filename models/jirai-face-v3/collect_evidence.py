"""Export numerical evidence only; keep textures, references and assets private."""
from common import *

def main():
    gate=read(ROOT/'verification.json');receipt=read(ROOT/'installation-receipt.json')
    mount=read(ROOT/'installed-mount-verification.json');visual=read(ROOT/'visual-review.json')
    assert gate['passed'] and mount['passed'] and visual['reviewed']
    for row in receipt['after']:assert sha(MODS/row['name'])==row['sha256']
    out=REPO/'evidence/jirai-face-v3'
    for name in ['verification.json','geometry-verification.json','surface-verification.json']:
        doc=read(ROOT/name)
        if name=='verification.json':
            doc['container_files']=[{k:v for k,v in row.items() if k!='path'} for row in doc['container_files']]
        write(out/name,doc)
    write(out/'native-patch.json',read(ROOT/'native/patch-report.json'))
    write(out/'installation.json',dict(status=receipt['status'],installed_at=receipt['installed_at'],
        base_model='R8Shape1',files=receipt['after'],removed_face2=receipt['removed_face2'],
        added_face3=receipt['added_face3'],current_skirt_base_and_voice_files_exact=receipt['current_skirt_base_and_voice_files_exact'],
        installed_mount_verified=mount['passed'],game_runtime_tested=False))
    write(out/'visual-review.json',dict(reviewed=True,views=visual['views'],observations=visual['observations'],
        source_atlas_sha256=visual['source_atlas_sha256'],source_iris_sha256=visual['source_iris_sha256'],surface_sha256=visual['surface_sha256'],
        native_render_sha256=visual['native_render_sha256'],private_image_sha256=list(visual['images'].values()),
        renderer='Blender Cycles, independently decoded native geometry, matching source albedo PNGs',game_runtime_tested=False))
    print('FACE3_NUMERICAL_EVIDENCE_EXPORTED')

if __name__=='__main__':main()
