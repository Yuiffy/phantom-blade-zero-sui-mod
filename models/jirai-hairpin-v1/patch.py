"""Reuse verified native buffer slots; preserve all bytes outside the hairpin."""
from common import *
import numpy as np,shutil
from patch_native import parse_doc,unpack

def replace(value):
 if isinstance(value,dict):return {k:replace(v) for k,v in value.items()}
 if isinstance(value,list):return [replace(v) for v in value]
 if isinstance(value,str):return value.replace(OLD_ATLAS,PACKAGE).replace('T_Jirai_Face3','T_Jirai_Hairpin1')
 return value

def main():
 assert_installed_baseline();author=read(ROOT/'author-report.json');assert author['passed']
 assert author['texture_sha256']==sha(ROOT/'T_Jirai_Base.png')
 assert author['native_source_sha256']==sha(FACE/'native/final-render.npz')
 source=FACE/'legacy'/(relative_package(BODY)+'.uasset');target=ROOT/'legacy'/(relative_package(BODY)+'.uasset');target.parent.mkdir(parents=True,exist_ok=True)
 assert sha(source.with_suffix('.uexp'))==sha(FACE/'final-legacy'/(relative_package(BODY)+'.uexp'))
 for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
  p=source.with_suffix(ext)
  if p.exists():shutil.copy2(p,target.with_suffix(ext))
 doc=read(FACE/'native/final.json');pos,weights,indices,detail=parse_doc(doc);raw=unpack(doc)
 before=np.load(FACE/'native/final-render.npz');after=np.load(ROOT/'patched-render.npz');model=np.load(ROOT/'authored-geometry.npz')
 selected=model['selected_vertices'];triangles=model['selected_triangles']
 assert np.array_equal(pos,before['positions']) and np.array_equal(indices,before['indices'])
 assert all(weights[i]=={'head':1.0} for i in selected)
 assert np.array_equal(after['uv'][:,1],before['uv'][:,1])
 selected_mask=np.zeros(len(pos),bool);selected_mask[selected]=True
 for key in ['positions','normals','packed_tangents','uv']:
  assert np.array_equal(after[key][~selected_mask],before[key][~selected_mask]),key
 tmask=np.zeros(len(indices)//3,bool);tmask[triangles]=True
 assert np.array_equal(after['indices'].reshape(-1,3)[~tmask],indices.reshape(-1,3)[~tmask])
 assert np.all(selected_mask[after['indices'].reshape(-1,3)[tmask]])
 edited=bytearray(raw);allowed=np.zeros(len(raw),bool)
 for span,data,ids,stride in [(detail['position_span'],after['positions'].astype('<f4'),selected,12),
    (detail['tangent_span'],after['packed_tangents'],selected,8),
    (detail['index_span'],after['indices'].reshape(-1,3).astype('<u4'),triangles,12)]:
  bs=data.tobytes();assert len(bs)==span['bytes']
  for i in ids:
   start=span['offset']+int(i)*stride;edited[start:start+stride]=bs[int(i)*stride:(int(i)+1)*stride];allowed[start:start+stride]=True
 assert detail['indices_16_bit'] is False
 tex=after['uv'];stride=tex.dtype.itemsize*4
 for i in selected:
  start=detail['uv_span']['offset']+int(i)*stride;bs=tex[i,0].tobytes();edited[start:start+len(bs)]=bs;allowed[start:start+len(bs)]=True
 changed=np.frombuffer(raw,'u1')!=np.frombuffer(edited,'u1');assert changed.any() and np.all(allowed[changed])
 payload=source.with_suffix('.uexp').read_bytes();assert payload.count(raw)==1
 start=payload.index(raw);result=payload[:start]+edited+payload[start+len(raw):];assert len(result)==len(payload)
 target.with_suffix('.uexp').write_bytes(result);assert sha(target)==sha(source)
 np.savez_compressed(ROOT/'allowed-bytes.npz',mask=allowed)
 write(ROOT/'native-patch.json',dict(passed=True,base='Face3_2 on R8Shape1',source_header_sha256=sha(source),output_header_sha256=sha(target),source_payload_sha256=sha(source.with_suffix('.uexp')),output_payload_sha256=sha(target.with_suffix('.uexp')),
  changed_native_bytes=int(changed.sum()),selected_native_vertices=len(selected),selected_triangle_slots=len(triangles),all_non_accessory_bytes_exact=True,face3_geometry_frames_uv_exact=True,uv1_weights_skeleton_cloth_physics_exact=True,game_runtime_tested=False))
 # Only Hair's Albedo import changes. The native export payload and parent
 # shader data remain byte-identical, avoiding a new shader compatibility path.
 source=FACE/'legacy'/(relative_package(HAIR)+'.uasset');target=ROOT/'legacy'/(relative_package(HAIR)+'.uasset');target.parent.mkdir(parents=True,exist_ok=True)
 out=ROOT/'material';out.mkdir(exist_ok=True)
 run('hair-source',[diag.TOOLS/'UAssetGUI.exe','tojson',source,out/'source.json','VER_UE5_6','PBZ'])
 original=read(out/'source.json');edited_doc=replace(original);assert edited_doc['Exports']==original['Exports'] and edited_doc!=original
 write(out/'edited.json',edited_doc)
 run('hair-write',[diag.TOOLS/'UAssetGUI.exe','fromjson',out/'edited.json',target,'PBZ'])
 assert target.is_file() and sha(target.with_suffix('.uexp'))==sha(source.with_suffix('.uexp'))
 print('HAIRPIN_NATIVE_PATCHED',int(changed.sum()))
if __name__=='__main__':main()
