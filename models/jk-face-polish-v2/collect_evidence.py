"""Publish only prose, numerical checks and hashes; keep artwork private."""
from common import *

def main():
 out=REPO/'evidence/jk-face-polish-v2';out.mkdir(parents=True,exist_ok=True)
 gate=read(ROOT/'verification.json');geometry=read(ROOT/'geometry-verification.json');mount=read(ROOT/'installed-mount-verification.json');receipt=read(ROOT/'installation-receipt.json');visual=read(ROOT/'visual-review.json')
 assert gate['passed'] and geometry['passed'] and mount['passed'] and mount['installed'] and visual['reviewed'] and receipt['after']==snapshot()
 for name in ['author-report','geometry-verification','verification','atlas-report','native-patch','editable-source','uv-input-verification']:write(out/(name+'.json'),read(ROOT/(name+'.json')))
 write(out/'request.json',dict(date='2026-11-18',user_request='另一个模型JK岁的脸看看能否也优化下，瞳孔增加同款图案，然后脸型也参考地雷岁修改一下。但JK岁也有JK岁的优势，对比一下。也参考JK岁原图。',previous_accepted_jirai_commit='a08a7fc',candidate='JKFacePolish2',new_candidate_game_runtime_tested=False))
 write(out/'installation.json',dict(status=receipt['status'],installed_at=receipt['installed_at'],files=receipt['after'],replaced_previous_files=receipt['removed'],retained_previous_files_exact=receipt['retained_previous_files_exact'],actual_installed_payload_readback_exact=mount['installed_payload_readback_exact'],retained_effective_packages=mount['retained_effective_packages'],retained_metadata_and_export_payloads_exact=mount['retained_metadata_and_complete_export_payloads_exact'],rollback_preflight_passed=True,new_candidate_game_runtime_tested=False))
 write(out/'visual-review.json',dict(reviewed=True,native_render_sha256=visual['native_render_sha256'],source_atlas_sha256=visual['source_atlas_sha256'],reference_sha256=visual['reference_sha256'],jirai_comparison_sha256=visual['jirai_comparison_sha256'],images={Path(p).name:digest for p,digest in visual['images'].items()},scope=visual['scope'],game_runtime_tested=False))
 write(out/'code-hashes.json',{p.name:sha(p) for p in sorted(CODE.glob('*.py'))})
 print('JK_POLISH_EVIDENCE_EXPORTED')

if __name__=='__main__':main()
