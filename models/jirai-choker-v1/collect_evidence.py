"""Publish hashes and numeric evidence; keep reference/model/media assets local."""
from common import *

def main():
 out=REPO/'evidence/jirai-choker-v1';out.mkdir(parents=True,exist_ok=True)
 gate=read(ROOT/'verification.json');geometry=read(ROOT/'geometry-verification.json');mount=read(ROOT/'installed-mount-verification.json');receipt=read(ROOT/'installation-receipt.json');visual=read(ROOT/'visual-review.json')
 assert gate['passed'] and geometry['passed'] and mount['passed'] and mount['installed'] and visual['reviewed'] and receipt['after']==snapshot()
 write(out/'request.json',dict(date='2026-11-18',user_request='脖子的choker不全，根据原参考图修修',installation_authorization='已退出，继续安装',game_runtime_tested=False))
 for name in ['author-report','geometry-verification','verification','native-patch']:write(out/(name+'.json'),read(ROOT/(name+'.json')))
 write(out/'installation.json',dict(status=receipt['status'],installed_at=receipt['installed_at'],added=receipt['added'],files=receipt['after'],retained_previous_files_exact=receipt['retained_previous_files_exact'],actual_installed_payload_readback_exact=mount['installed_payload_readback_exact'],retained_effective_packages=mount['retained_effective_packages'],retained_metadata_and_complete_export_payloads_exact=mount['retained_metadata_and_complete_export_payloads_exact'],game_runtime_tested=False))
 write(out/'visual-review.json',dict(reviewed=True,native_render_sha256=visual['native_render_sha256'],images={Path(p).name:digest for p,digest in visual['images'].items()},scope=visual['scope'],game_runtime_tested=False))
 print('CHOKER_EVIDENCE_EXPORTED')
if __name__=='__main__':main()
