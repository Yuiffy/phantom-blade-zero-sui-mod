"""Copy only immutable inputs and create small adapters for the proven pipeline."""
from common import *
import shutil

BASE = REPO / 'private/jirai-detail-v1'
ROOT.mkdir(parents=True,exist_ok=True)
for name in ['cloth-spec.json','intended-reference-skeleton.json','pose-contract.json',
             'shoulder-animation-contract.json']:
    shutil.copy2(BASE/name,ROOT/name)
shutil.copytree(BASE/'textures',ROOT/'textures',dirs_exist_ok=True)
stages = ['offline_tools','prepare_mod','prepare_shoulder_animation','run_ue','import_mod_ue',
    'prepare_shoulder_skeleton','test_shoulder_retarget_ue','author_cloth_ue','verify_editor_state_ue',
    'test_cloth_ue','test_articulation_ue','validate_simulation','verify_shoulder_skeleton',
    'verify_mod','decode_cloth_body','verify_cloth_assets','deform_readback','reconstruct_articulation']
for name in stages:
    (CODE/(name+'.py')).write_text("from pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).resolve().parent))\nfrom reuse_r6 import execute\nexecute("+repr(name)+", globals())\n",encoding='utf8')
write(CODE/'pipeline-source-hashes.json',{name:sha(CODE.parent/'jirai-detail-v1'/(name+'.py')) for name in stages+['package_mod']})
# Material preparation adds native skin inputs after the standard VT import list.
with (CODE/'prepare_mod.py').open('a',encoding='utf8') as f:
    f.write("from material_recipe import prepare\nprepare()\n")
with (CODE/'package_mod.py').open('w',encoding='utf8') as f:
    f.write("from common import PBZ\nimport build_native_shader_assets as native\nfrom material_recipe import build\nnative.materials = build\nfrom reuse_r6 import execute\nexecute('package_mod', globals())\n")
print('ISOLATED_R6_INPUTS_PREPARED')
