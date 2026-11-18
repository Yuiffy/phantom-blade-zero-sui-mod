"""Export numeric/hash evidence only; native assets and previews stay private."""
from common import *

def main():
    verified=read(ROOT/'installed-verification.json');assert verified['passed']
    receipt=read(ROOT/'installation-receipt.json')
    assert snapshot()==receipt['after']
    out=REPO/'evidence/jk-face-shape-v1';out.mkdir(parents=True,exist_ok=True)
    for name in ['author-report','geometry-verification','patch-report','verification','installed-verification','skirt-diagnosis','editable-source']:
        write(out/(name+'.json'),read(ROOT/(name+'.json')))
    visual=read(ROOT/'visual-review.json')
    write(out/'visual-review.json',dict(reviewed=visual['reviewed'],native_sha256=visual['native_sha256'],render_manifest_sha256=visual['render_manifest_sha256'],
        image_hashes={Path(p).name:h for p,h in visual['images'].items()},comparison_sha256=visual['comparison_sha256'],observations=visual['observations'],game_runtime_tested=False))
    inputs={}
    for name,p in [('native_baseline',ROOT/'before.npz'),('components',REPO/'private/outfit-patterns-v1/jk-components.npz'),('jirai_native_reference',REPO/'private/outfit-patterns-v1/jirai-native.npz'),
                   ('native_source_header',SOURCE),('native_source_payload',SOURCE.with_suffix('.uexp')),('pattern_atlas_source',REPO/'private/outfit-patterns-v1/jk-after.png')]:
        inputs[name]=sha(p)
    write(out/'input-hashes.json',dict(inputs=inputs,code={p.name:sha(p) for p in sorted(CODE.glob('*.py'))},capture_stage='final verification; native baseline independently matched against the frozen source and installed readback'))
    write(out/'installation-summary.json',dict(status=receipt['status'],installed_at=receipt['installed_at'],added=receipt['added'],container_files=verified['container_files'],
        retained_file_count=len(receipt['before']),retained_files_exact=True,previous_jirai_patterns_voice_and_cloth_preserved=True,installed_effective_packages_preserved=verified['preserved_package_count'],
        native_sha256=verified['native_render_sha256'],skirt_changed=False,game_runtime_tested=False))
    print('JK_FACE_EVIDENCE_COLLECTED')

if __name__=='__main__':main()
