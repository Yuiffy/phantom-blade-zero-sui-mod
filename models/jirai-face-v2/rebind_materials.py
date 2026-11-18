"""Clone native leaves; change only their albedo import to an isolated atlas."""
from common import *

def replace(value):
 if isinstance(value,dict):return {k:replace(v) for k,v in value.items()}
 if isinstance(value,list):return [replace(v) for v in value]
 if isinstance(value,str):return value.replace(OLD_ATLAS,PACKAGE).replace('T_Jirai_Base','T_Jirai_Face2')
 return value

def build():
 records=[]
 for package in MATERIALS:
  name=package.rsplit('/',1)[-1];source=BASE/'legacy'/(relative_package(package)+'.uasset')
  original=ROOT/'materials'/(name+'-original.json');original.parent.mkdir(exist_ok=True)
  run(name+'-source',[diag.TOOLS/'UAssetGUI.exe','tojson',source,original,'VER_UE5_6','PBZ'])
  doc=read(original);edited=replace(doc)
  assert edited!=doc
  assert edited['Exports']==doc['Exports'],'Only the import/name table may change'
  path=ROOT/'materials'/(name+'-edited.json');write(path,edited)
  target=ROOT/'legacy'/(relative_package(package)+'.uasset');target.parent.mkdir(parents=True,exist_ok=True)
  run(name+'-write',[diag.TOOLS/'UAssetGUI.exe','fromjson',path,target,'PBZ'])
  reread=ROOT/'materials'/(name+'-readback.json')
  run(name+'-read',[diag.TOOLS/'UAssetGUI.exe','tojson',target,reread,'VER_UE5_6','PBZ'])
  got=read(reread)
  for actual,wanted in zip(got['Exports'],doc['Exports']):
   assert {k:v for k,v in actual.items() if k!='SerialOffset'}=={k:v for k,v in wanted.items() if k!='SerialOffset'}
  assert got['Imports']==edited['Imports'] and got['NameMap']==edited['NameMap']
  assert source.with_suffix('.uexp').read_bytes()==target.with_suffix('.uexp').read_bytes(),'Leaf properties/native export must be byte exact'
  records.append(dict(package=package,changed='Albedo texture import only',all_export_bytes_exact=True,parent_scalars_normals_mix_and_shader_payload_unchanged=True,source_payload_sha256=sha(source.with_suffix('.uexp')),output_payload_sha256=sha(target.with_suffix('.uexp'))))
 write(ROOT/'material-rebinding.json',dict(passed=True,albedo=PACKAGE,materials=records))
 print('NATIVE_FACE_ALBEDO_REBOUND',len(records),flush=True)

if __name__=='__main__':build()
