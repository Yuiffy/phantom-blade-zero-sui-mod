"""Keep all visual/game assets private; publish bound numerical evidence."""
from common import *

def main():
 out=REPO/'evidence/jirai-chin-clean-v1';out.mkdir(parents=True,exist_ok=True)
 gate=read(ROOT/'verification.json');geo=read(ROOT/'geometry-verification.json');mount=read(ROOT/'installed-mount-verification.json');receipt=read(ROOT/'installation-receipt.json');visual=read(ROOT/'visual-review.json')
 assert gate['passed'] and geo['passed'] and mount['passed'] and mount['installed'] and receipt['after']==snapshot() and visual['reviewed']
 for name in ['author-report','atlas-report','native-patch','geometry-verification','verification','vt-decoding-before','vt-decoding-after','mip-verification']:write(out/(name+'.json'),read(ROOT/(name+'.json')))
 write(out/'request.json',dict(date='2026-11-18',user_request='地雷岁下巴上有方块斑点呢',reported_image_sha256=sha('C:/Users/yuiffy/AppData/Local/Temp/codex-clipboard-c82fa184-9b2f-4bf1-a656-3fc4020ff3e4.png'),diagnosis='Grey-purple chin blocks reproduced from actual previous BC1 VT mip4/mip5. Repack only fragmented lower-face charts with wide skin padding.',game_runtime_tested=False))
 write(out/'installation.json',dict(status=receipt['status'],installed_at=receipt['installed_at'],files=receipt['after'],replaced_previous_files=receipt['removed'],retained_previous_files_exact=receipt['retained_previous_files_exact'],actual_installed_payload_readback_exact=mount['installed_payload_readback_exact'],retained_effective_packages=mount['retained_effective_packages'],retained_metadata_and_complete_export_payloads_exact=mount['retained_metadata_and_complete_export_payloads_exact'],choker_and_jk_face_preserved=True,rollback_preflight_passed=True,new_candidate_game_runtime_tested=False))
 write(out/'visual-review.json',dict(reviewed=True,native_render_sha256=visual['native_render_sha256'],source_atlas_sha256=visual['source_atlas_sha256'],images={Path(p).name:h for p,h in visual['images'].items()},scope=visual['scope'],game_runtime_tested=False))
 write(out/'code-hashes.json',{p.name:sha(p) for p in sorted(CODE.glob('*.py'))})
 print('CHIN_EVIDENCE_EXPORTED')

if __name__=='__main__':main()
