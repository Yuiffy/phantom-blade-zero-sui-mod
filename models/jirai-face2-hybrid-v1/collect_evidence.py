"""Export numerical evidence; no game assets, derived images or local paths."""
from common import *

def main():
 out=REPO/'evidence/jirai-face2-hybrid-v1';out.mkdir(parents=True,exist_ok=True)
 gate=read(ROOT/'verification.json');geometry=read(ROOT/'geometry-verification.json');mount=read(ROOT/'installed-mount-verification.json');receipt=read(ROOT/'installation-receipt.json');visual=read(ROOT/'visual-review.json');author=read(ROOT/'author-report.json')
 assert gate['passed'] and geometry['passed'] and mount['passed'] and mount['installed'] and visual['reviewed'] and receipt['after']==snapshot()
 write(out/'request.json',dict(date='2026-11-18',user_request='模型保持face2，瞳孔和眼白部分升级到face3，不修改眼眶。嘴巴也用face2，只是把嘴巴的黑色杂色去掉。',previous_candidate='Polish1',previous_candidate_rejected_by_user=True,new_candidate_game_runtime_tested=False))
 for name,value in [('author-summary',{k:v for k,v in author.items() if k!='bridges'}),('geometry-verification',geometry),('verification',gate),('atlas-report',read(ROOT/'atlas-report.json')),('native-patch',read(ROOT/'native-patch.json'))]:write(out/(name+'.json'),value)
 write(out/'installation.json',dict(status=receipt['status'],installed_at=receipt['installed_at'],files=receipt['after'],removed_rejected_files=receipt['removed'],retained_previous_files_exact=receipt['retained_previous_files_exact'],actual_installed_payload_readback_exact=mount['installed_payload_readback_exact'],retained_effective_packages=mount['retained_effective_packages'],new_candidate_game_runtime_tested=False))
 write(out/'visual-review.json',dict(reviewed=True,native_render_sha256=visual['native_render_sha256'],source_atlas_sha256=visual['source_atlas_sha256'],images={Path(p).name:digest for p,digest in visual['images'].items()},scope=visual['scope'],game_runtime_tested=False))
 print('HYBRID_EVIDENCE_EXPORTED')

if __name__=='__main__':main()
