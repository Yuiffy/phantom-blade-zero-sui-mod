"""Freeze installed bytes and prepare exact native surfaces for UV-local painting."""
from common import *
import base64,numpy as np,shutil

def main():
 ROOT.mkdir(parents=True,exist_ok=True)
 pin=read(REPO/'private/jirai-hairpin-v1/installation-receipt.json')
 assert snapshot()==pin['after']
 baseline=dict(files=snapshot(),hairpin_receipt_sha256=sha(REPO/'private/jirai-hairpin-v1/installation-receipt.json'),game_runtime_tested=False)
 if (ROOT/'baseline.json').exists():assert read(ROOT/'baseline.json')==baseline
 else:write(ROOT/'baseline.json',baseline)
 jk=PBZ/'variants/jk-motion-v5';spec=read(jk/'material-spec.json')
 doc=read(jk/'independent/body-uassetapi.json');raw=base64.b64decode(next(e for e in doc['Exports'] if e['ObjectName']=='Hun_Body_Simple')['Extras'])
 rel=relative_package('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple')+'.uexp'
 current=REPO/'private/jirai-skirt-shape-v1/dual/final-legacy'/rel
 source=jk/'final-legacy'/rel
 assert sha(current)==sha(source),'JK native payload changed'
 detail=read(jk/'independent/cloth-native-details.json');d=np.load(jk/'independent/render-data.npz');n=len(d['positions'])
 s=detail['tangent_span'];frames=np.frombuffer(raw,'u1',count=s['bytes'],offset=s['offset']).reshape(n,8).copy()
 s=detail['uv_span'];uv=np.frombuffer(raw,'<f2',count=s['count']*2,offset=s['offset']).reshape(n,1,2).copy()
 mat=np.full(n,-1,int)
 for s in detail['sections']:mat[s['base_vertex']:s['base_vertex']+s['vertices']]=s['material']
 assert np.all(mat>=0)
 np.savez_compressed(ROOT/'jk-native.npz',positions=d['positions'],indices=d['indices'],packed_tangents=frames,normals=frames[:,4:7].view('i1').astype(float)/127,uv=uv,materials=mat)
 shutil.copy2(REPO/'private/jirai-hairpin-v1/final-render.npz',ROOT/'jirai-native.npz')
 tex={r['package']:r for r in spec['textures']};src=Path(tex[PACKAGES[0]]['path']);assert sha(src)==tex[PACKAGES[0]]['sha256']
 shutil.copy2(src,ROOT/'jk-original-4k.png')
 from PIL import Image
 Image.open(src).convert('RGB').resize((8192,8192),Image.Resampling.NEAREST).save(ROOT/'jk-before.png')
 shutil.copy2(REPO/'private/fishnet-v1/T_Jirai_Base.png',ROOT/'jirai-before.png')
 recipes={}
 for outfit,specpath in [('jk',jk/'material-spec.json'),('jirai',REPO/'private/jirai-skirt-shape-v1/variant/material-spec.json')]:
  s=read(specpath);textures={r['package']:r for r in s['textures']};rows=[]
  for m in s['materials']:
   path=textures[m['textures']['Albedo']]['path']
   if outfit=='jirai' and m['slot']=='MI_Jirai_Skin':path=str(REPO/'private/jirai-face-v3/T_Jirai_Base.png')
   if outfit=='jirai' and m['slot']=='MI_Jirai_Hair':path=str(REPO/'private/jirai-hairpin-v1/T_Jirai_Base.png')
   if outfit=='jirai' and Path(path).name=='T_Jirai_Base.png' and m['slot'] not in ['MI_Jirai_Skin','MI_Jirai_Hair']:path=str(ROOT/'jirai-before.png')
   if outfit=='jk' and m['textures']['Albedo']==PACKAGES[0]:path=str(ROOT/'jk-before.png')
   rows.append(dict(slot=m['slot'],path=path,package=m['textures']['Albedo']))
  if outfit=='jirai':
   rows.extend([dict(slot='MI_Jirai_EyeIris',path=str(REPO/'private/jirai-face-v3/T_Face3_Iris.png'),package='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Face3_Iris'),dict(slot='MI_Jirai_EyeWhite',path=str(REPO/'private/jirai-face-v3/T_Jirai_Base.png'),package='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Face3')])
  recipes[outfit]=rows
 write(ROOT/'preview-materials.json',recipes)
 write(ROOT/'sources.json',dict(jk_native_sha256=sha(ROOT/'jk-native.npz'),jirai_native_sha256=sha(ROOT/'jirai-native.npz'),jk_payload_sha256=sha(current),jk_original_4k_sha256=sha(ROOT/'jk-original-4k.png'),jk_upscale='4096 to 8192 nearest-neighbor; exact repeated original pixel blocks before local repaint',jk_atlas_sha256=sha(ROOT/'jk-before.png'),jirai_atlas_sha256=sha(ROOT/'jirai-before.png'),jk_reference=str(PBZ/'models/new-outfit-20261114/single-image-trial-v1/sui-front-input.png'),jirai_reference=str(REPO/'private/tripo-bridge-20261115/original-jirai-design.png')))
 print('OUTFIT_PATTERNS_BASELINE_FROZEN')
if __name__=='__main__':main()
