"""Bounded byte patch; original skeleton, cloth and unrelated surfaces stay exact."""
from common import *
import numpy as np,shutil,importlib.util
spec=importlib.util.spec_from_file_location('face3_native_reader',REPO/'models/jirai-face-v3/patch_native.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
parse_doc=reader.parse_doc;unpack=reader.unpack
def replace(value):
 if isinstance(value,dict):return {k:replace(v) for k,v in value.items()}
 if isinstance(value,list):return [replace(v) for v in value]
 if isinstance(value,str):return value.replace('/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Face2Hybrid1',PACKAGE).replace('T_Jirai_Face2Hybrid1','T_Jirai_LashLip1')
 return value
def main():
 assert_baseline();d=np.load(ROOT/'patched-render.npz');before=np.load(PIN/'final-render.npz');sel=np.load(ROOT/'author-selections.npz')
 doc=read(PIN/'independent/native.json');pos,w,indices,detail=parse_doc(doc);raw=unpack(doc)
 assert np.array_equal(pos,before['positions']) and np.array_equal(indices,before['indices'])
 source=PIN/'legacy'/(relative_package(BODY)+'.uasset');target=ROOT/'legacy'/(relative_package(BODY)+'.uasset');target.parent.mkdir(parents=True,exist_ok=True)
 assert sha(source.with_suffix('.uexp'))==sha(PIN/'resolved-legacy'/(relative_package(BODY)+'.uexp'))
 for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
  if source.with_suffix(ext).exists():shutil.copy2(source.with_suffix(ext),target.with_suffix(ext))
 edited=bytearray(raw);allowed=np.zeros(len(raw),bool);counts={}
 for key,span,arr,oldarr,stride in [('positions',detail['position_span'],d['positions'].astype('<f4'),before['positions'],12),('frames',detail['tangent_span'],d['packed_tangents'],before['packed_tangents'],8),('indices',detail['index_span'],d['indices'].reshape(-1,3).astype('<u4'),before['indices'].reshape(-1,3),12)]:
  changed=np.any(arr!=oldarr,axis=1);bs=arr.tobytes();assert len(bs)==span['bytes'];counts[key]=int(changed.sum())
  for i in np.where(changed)[0]:
   start=span['offset']+int(i)*stride;edited[start:start+stride]=bs[int(i)*stride:(int(i)+1)*stride];allowed[start:start+stride]=True
 assert np.array_equal(d['uv'][:,1],before['uv'][:,1])
 changed=np.any(d['uv'][:,0]!=before['uv'][:,0],axis=1);counts['uv0']=int(changed.sum())
 for i in np.where(changed)[0]:
  start=detail['uv_span']['offset']+int(i)*8;bs=d['uv'][i,0].tobytes();edited[start:start+4]=bs;allowed[start:start+4]=True
 span=detail['weight_span'];weights=np.frombuffer(raw,'u1',count=span['bytes'],offset=span['offset']).reshape(len(pos),8).copy()
 for dst,src in sel['weight_copies']:
  assert int(dst)<detail['sections'][0]['vertices'] and int(src)<detail['sections'][0]['vertices']
  start=span['offset']+int(dst)*8;edited[start:start+8]=weights[src].tobytes();allowed[start:start+8]=True
 actual=np.frombuffer(raw,'u1')!=np.frombuffer(edited,'u1');assert np.all(allowed[actual]) and actual.any()
 payload=source.with_suffix('.uexp').read_bytes();assert payload.count(raw)==1;start=payload.index(raw)
 target.with_suffix('.uexp').write_bytes(payload[:start]+edited+payload[start+len(raw):]);assert sha(source)==sha(target)
 np.savez_compressed(ROOT/'allowed-bytes.npz',mask=allowed)
 write(ROOT/'native-patch.json',dict(passed=True,changed_native_bytes=int(actual.sum()),changed_records=counts,weight_copied_vertices=len(sel['weight_copies']),original_weights_elsewhere_exact=True,uv1_exact=True,skeleton_sections_cloth_physics_exact=True,source_header_sha256=sha(source),output_payload_sha256=sha(target.with_suffix('.uexp'))))
 # Keep the existing game-native skin shader; replace only its Albedo import.
 source=FACE/'legacy'/(relative_package(SKIN)+'.uasset');target=ROOT/'legacy'/(relative_package(SKIN)+'.uasset');target.parent.mkdir(parents=True,exist_ok=True)
 folder=ROOT/'materials';folder.mkdir(exist_ok=True)
 run('skin-source',[diag.TOOLS/'UAssetGUI.exe','tojson',source,folder/'source.json','VER_UE5_6','PBZ'])
 original=read(folder/'source.json');changed=replace(original);assert changed['Exports']==original['Exports'] and changed!=original
 write(folder/'edited.json',changed);run('skin-write',[diag.TOOLS/'UAssetGUI.exe','fromjson',folder/'edited.json',target,'PBZ'])
 assert target.is_file() and sha(target.with_suffix('.uexp'))==sha(source.with_suffix('.uexp'))
 print('LASHLIP_NATIVE_PATCHED',int(actual.sum()))
if __name__=='__main__':main()
