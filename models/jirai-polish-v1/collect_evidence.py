"""Publish numerical evidence and hashes, excluding private assets and paths."""
from common import *
def main():
 out=REPO/'evidence/jirai-polish-v1';out.mkdir(parents=True,exist_ok=True)
 gate=read(ROOT/'verification.json');geometry=read(ROOT/'geometry-verification.json');mount=read(ROOT/'installed-mount-verification.json');receipt=read(ROOT/'installation-receipt.json');visual=read(ROOT/'visual-review.json');author=read(ROOT/'author-report.json')
 assert gate['passed'] and geometry['passed'] and mount['passed'] and mount['installed'] and visual['reviewed']
 assert receipt['after']==snapshot()
 write(out/'runtime-feedback.json',read(ROOT/'runtime-feedback.json'))
 write(out/'author-summary.json',{k:v for k,v in author.items() if k!='bridges'})
 write(out/'geometry-verification.json',geometry)
 write(out/'verification.json',gate)
 write(out/'installation.json',dict(status=receipt['status'],installed_at=receipt['installed_at'],files=receipt['after'],previous_files_exact=receipt['previous_files_exact'],actual_installed_payload_readback_exact=mount['installed_payload_readback_exact'],retained_effective_packages=mount['retained_effective_packages'],new_candidate_game_runtime_tested=False))
 write(out/'visual-review.json',dict(reviewed=True,native_render_sha256=visual['native_render_sha256'],source_atlas_sha256=visual['source_atlas_sha256'],images={Path(p).name:digest for p,digest in visual['images'].items()},scope=visual['scope'],game_runtime_tested=False))
 print('POLISH_NUMERICAL_EVIDENCE_EXPORTED')
if __name__=='__main__':main()
