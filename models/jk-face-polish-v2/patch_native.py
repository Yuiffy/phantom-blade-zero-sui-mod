"""Patch only head position/tangent records and the two original iris UVs."""
from common import *
import base64,importlib.util,inspect,shutil,numpy as np

def unpack(doc):return base64.b64decode(next(e for e in doc['Exports'] if e['ObjectName']=='Hun_Body_Simple')['Extras'])

def parse_doc(doc):
 path=PBZ/'models/new-outfit-20261114/tripo-motion-v5/decode_cloth_body.py'
 spec=importlib.util.spec_from_file_location('jk_cloth_decoder',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 code=inspect.getsource(mod.decoder.parse).replace('assert count==14','assert count==24')
 scope=dict(vars(mod.decoder));scope.update(section=mod.section,skeletal_materials=mod.materials);exec(code,scope)
 return scope['parse'](doc,dict(package=BODY),read(JK/'material-spec.json'))

def replace(value):
 if isinstance(value,dict):return {k:replace(v) for k,v in value.items()}
 if isinstance(value,list):return [replace(v) for v in value]
 if isinstance(value,str):return value.replace('/HuaShira/Mods/SuiPBZ/JKVT/T_JK_Base',PACKAGE).replace('T_JK_Base','T_JK_FacePolish2')
 return value

def main():
 assert_baseline();d=np.load(ROOT/'patched-render.npz');old=np.load(ROOT/'before.npz')
 source=PIN/'legacy'/(relative_package(BODY)+'.uasset')
 assert sha(source.with_suffix('.uexp'))==sha(FACE/'installed-legacy'/(relative_package(BODY)+'.uexp'))
 doc=read(PIN/'native/final.json');pos,w,idx,detail=parse_doc(doc);raw=unpack(doc)
 assert np.array_equal(pos,old['positions']) and np.array_equal(idx,old['indices'])
 target=ROOT/'legacy'/(relative_package(BODY)+'.uasset');target.parent.mkdir(parents=True,exist_ok=True)
 for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
  if source.with_suffix(ext).exists():shutil.copy2(source.with_suffix(ext),target.with_suffix(ext))
 edited=bytearray(raw);allowed=np.zeros(len(raw),bool);counts={}
 for key,span,stride in [('positions',detail['position_span'],12),('packed_tangents',detail['tangent_span'],8),('uv',detail['uv_span'],4)]:
  a=d[key];b=old[key];changed=np.any((a!=b).reshape(len(pos),-1),axis=1);data=a.tobytes();assert len(data)==span['bytes'];counts[key]=int(changed.sum())
  if key!='uv':assert all(w[i]=={'head':1.0} for i in np.where(changed)[0])
  for i in np.where(changed)[0]:
   at=span['offset']+int(i)*stride;edited[at:at+stride]=data[int(i)*stride:(int(i)+1)*stride];allowed[at:at+stride]=True
 actual=np.frombuffer(raw,'u1')!=np.frombuffer(edited,'u1');assert actual.any() and np.all(allowed[actual])
 payload=source.with_suffix('.uexp').read_bytes();assert payload.count(raw)==1;at=payload.index(raw)
 target.with_suffix('.uexp').write_bytes(payload[:at]+edited+payload[at+len(raw):]);assert sha(target)==sha(source)
 np.savez_compressed(ROOT/'allowed-bytes.npz',mask=allowed)
 write(ROOT/'native-patch.json',dict(passed=True,changed_native_bytes=int(actual.sum()),changed_records=counts,weights_skeleton_cloth_sections_indices_exact=True,source_payload_sha256=sha(source.with_suffix('.uexp')),output_payload_sha256=sha(target.with_suffix('.uexp')),header_exact=True))
 source=REPO/'private/jirai-skirt-shape-v1/dual/legacy'/(relative_package(SKIN)+'.uasset');target=ROOT/'legacy'/(relative_package(SKIN)+'.uasset');target.parent.mkdir(parents=True,exist_ok=True)
 assert sha(source.with_suffix('.uexp'))==sha(FACE/'installed-legacy'/(relative_package(SKIN)+'.uexp'))
 folder=ROOT/'materials';folder.mkdir(exist_ok=True)
 run('base-material-source',[diag.TOOLS/'UAssetGUI.exe','tojson',source,folder/'source.json','VER_UE5_6','PBZ'])
 original=read(folder/'source.json');changed=replace(original);assert changed!=original and changed['Exports']==original['Exports']
 write(folder/'edited.json',changed);run('base-material-write',[diag.TOOLS/'UAssetGUI.exe','fromjson',folder/'edited.json',target,'PBZ'])
 assert sha(source.with_suffix('.uexp'))==sha(target.with_suffix('.uexp'))
 print('JK_NATIVE_PATCHED',int(actual.sum()),flush=True)

if __name__=='__main__':main()
