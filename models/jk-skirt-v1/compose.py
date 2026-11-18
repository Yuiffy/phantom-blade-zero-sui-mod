"""Merge only skirt exports and mapping bytes into the latest effective JK mesh.

UAssetGUI is used to encode the edited property exports and relocate its header.
Every retained export record/payload is restored from the installed source,
including the body's native OptionalProperty encoding and concurrent face work.
"""
from common import *
from native import decode,unpack,DT
from evaluate import mask,projection,render_settings,target_positions
import shutil,copy,struct,base64
import numpy as np
from preserve_relocated_mesh_payload import unique

REFERENCE_REPORT=P/'variants/native-types-v1/reference-context-report.json'
REFERENCE_PACKAGES=set(read(REFERENCE_REPORT)['packages'])

def extract(label,dirs):
 context=W/(label+'-input');context.mkdir(exist_ok=True)
 for folder in dirs:
  for p in folder.iterdir():
   if p.suffix in ['.utoc','.ucas']:shutil.copy2(p,context/p.name)
 for ext in ['.utoc','.ucas']:shutil.copy2(diag.PAKS/('global'+ext),context/('global'+ext))
 for row in read(REFERENCE_REPORT)['files']:
  p=P/row['path'];assert sha(p)==row['sha256']
  if p.suffix in ['.utoc','.ucas']:shutil.copy2(p,context/p.name)
 dest=W/(label+'-legacy');run(label,[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',context,dest]);return dest
def tojson(label,p):
 target=W/'native'/(label+'.json');target.parent.mkdir(exist_ok=True);run(label,[diag.TOOLS/'UAssetGUI.exe','tojson',p,target,'VER_UE5_6','PBZ']);assert target.exists();return read(target)
def export_key(doc,index):
 e=doc['Exports'][index];outer=e['OuterIndex'];return(e['ObjectName'],export_key(doc,outer-1) if outer>0 else outer)
def prepare_document(original,cooked):
 doc=copy.deepcopy(original)
 for n in cooked['NameMap']:
  if n not in doc['NameMap']:doc['NameMap'].append(n)
 doc['NamesReferencedFromExportDataCount']=len(doc['NameMap'])
 def import_ref(index):
  if index>=0:
   key=export_key(cooked,index-1);return next(i+1 for i in range(len(doc['Exports'])) if export_key(doc,i)==key)
  a=copy.deepcopy(cooked['Imports'][-index-1]);a['OuterIndex']=import_ref(a['OuterIndex']) if a['OuterIndex'] else 0
  for i,b in enumerate(doc['Imports']):
   if a==b:return -i-1
  doc['Imports'].append(a);return -len(doc['Imports'])
 def references(value):
  if isinstance(value,dict):
   if any(t in value.get('$type','') for t in ['ObjectPropertyData,','WeakObjectPropertyData,','LazyObjectPropertyData,']) and isinstance(value.get('Value'),int) and value['Value']:
    value['Value']=import_ref(value['Value'])
   else:
    for v in value.values():references(v)
  elif isinstance(value,list):
   for v in value:references(v)
 wanted=[]
 for i,e in enumerate(original['Exports']):
  outer=original['Exports'][e['OuterIndex']-1]['ObjectName'] if e['OuterIndex']>0 else ''
  if e['ObjectName']=='CA_Sui_Skirt_0' or (e['ObjectName']=='ChaosClothConfig' and outer=='CA_Sui_Skirt_0') or e['ObjectName']=='ChaosClothSharedSimConfig':
   j=next(j for j in range(len(cooked['Exports'])) if export_key(cooked,j)==export_key(original,i));data=copy.deepcopy(cooked['Exports'][j]['Data']);references(data);doc['Exports'][i]['Data']=data;wanted.append(i)
 assert len(wanted)==3
 return doc,wanted
def patch_mapping(original,payload):
 raw=unpack(original);_,_,_,detail=decode(original);s=detail['sections'][14];settings=render_settings(read(W/'chosen-stage.json')['stage']);values,report=mask(original,settings);out=bytearray(raw);allowed=set()
 mapping=projection(original,settings);records=np.zeros(s['vertices'],dtype=DT)
 positions=target_positions(original,settings);lo=s['base_vertex'];hi=lo+s['vertices'];start=detail['position_span']['offset']+12*lo
 out[start:start+12*s['vertices']]=positions[lo:hi].astype('<f4').tobytes();allowed.update(range(start,start+12*s['vertices']))
 for key in mapping:records[key]=mapping[key]
 records['source'][:,3]=values
 for j,record in enumerate(records):
  for start in [s['cloth_map_spans'][0]['offset']+64*j,detail['gpu_cloth_mapping_span']['offset']+64*(s['gpu_mapping_offset']+j)]:
   out[start:start+64]=record.tobytes();allowed.update(range(start,start+64))
 changes={i for i,(a,b) in enumerate(zip(raw,out)) if a!=b};assert changes and changes<=allowed
 assert payload.count(raw)==1;at=payload.index(raw);new=payload[:at]+out+payload[at+len(raw):]
 report.update(changed_native_bytes=len(changes),both_section_and_gpu_mappings_patched=True,all_other_native_bytes_exact=True,render_settings=settings)
 return new,report
def compose():
 baseline=snapshot();write(W/'composition-baseline.json',baseline)
 source=extract('latest',[MODS])/(relative_package(BODY)+'.uasset');original=tojson('latest',source)
 # Only for decoding dependencies: no competing JK body, no game references
 # delivered. This keeps native material imports resolvable in standalone readback.
 dep_legacy=W/'dependency-legacy';dep_legacy.mkdir(exist_ok=True)
 for p in (W/'latest-legacy').rglob('*.uasset'):
  rel=p.relative_to(W/'latest-legacy')
  if rel.as_posix()==relative_package(BODY)+'.uasset' or rel.as_posix() in REFERENCE_PACKAGES:continue
  for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
   a=p.with_suffix(ext)
   if a.exists():b=(dep_legacy/rel).with_suffix(ext);b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
 dep=W/'dependency-context';dep.mkdir(exist_ok=True)
 run('pack-verification-dependencies',[diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',dep_legacy,dep/'JK_Skirt_Dependencies_Verification_Only.utoc'])
 cooked_path=PROJECT.parent/'Saved/Cooked/Windows'/(relative_package(BODY)+'.uasset');cooked=tojson('cooked',cooked_path)
 assert original['IsUnversioned'] is cooked['IsUnversioned'] is False
 document,wanted=prepare_document(original,cooked);temp=W/'serialize/body.uasset';temp.parent.mkdir(exist_ok=True)
 write(W/'serialize/body.json',document);run('encode-edited-properties',[diag.TOOLS/'UAssetGUI.exe','fromjson',W/'serialize/body.json',temp]);rewritten=tojson('rewritten',temp)
 assert rewritten['NameMap'][:len(original['NameMap'])]==original['NameMap']
 old_header=source.read_bytes();header=bytearray(temp.read_bytes());old_payload=source.with_suffix('.uexp').read_bytes();new_payload=temp.with_suffix('.uexp').read_bytes();assert old_payload[-4:]==new_payload[-4:]==bytes.fromhex('c1832a9e')
 bulk_at=unique(header,struct.pack('<q',len(header)+len(new_payload)-4));blocks=[];offset=len(header);preserved=[];map_report=None
 for i,(a,b) in enumerate(zip(original['Exports'],rewritten['Exports'])):
  x=unique(old_header,struct.pack('<qq',a['SerialSize'],a['SerialOffset']));y=unique(header,struct.pack('<qq',b['SerialSize'],b['SerialOffset']))
  base=old_header if i not in wanted else bytes(header);pos=x if i not in wanted else y
  record=bytearray(base[pos-28:pos+84]);assert len(record)==112
  if i in wanted:
   start=b['SerialOffset']-len(header);block=new_payload[start:start+b['SerialSize']]
  else:
   start=a['SerialOffset']-len(old_header);block=old_payload[start:start+a['SerialSize']]
   if a['ObjectName']=='Hun_Body_Simple':block,map_report=patch_mapping(original,block)
   else:preserved.append(i)
  assert len(block)>0;struct.pack_into('<qq',record,28,len(block),offset);header[y-28:y+84]=record;blocks.append(block);offset+=len(block)
 struct.pack_into('<q',header,bulk_at,offset)
 dest=W/'legacy'/(relative_package(BODY)+'.uasset');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(header);dest.with_suffix('.uexp').write_bytes(b''.join(blocks)+old_payload[-4:])
 pa=PROJECT.parent/'Saved/Cooked/Windows'/(relative_package(PA)+'.uasset');out=W/'legacy'/(relative_package(PA)+'.uasset');out.parent.mkdir(parents=True,exist_ok=True)
 for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
  if pa.with_suffix(ext).exists():shutil.copy2(pa.with_suffix(ext),out.with_suffix(ext))
 assert snapshot()==baseline,'Installation changed during composition; recompose to retain new face work'
 write(W/'composition.json',dict(passed=True,baseline=baseline,wanted_exports=wanted,preserved_exports=preserved,source_header_sha256=sha(source),source_payload_sha256=sha(source.with_suffix('.uexp')),body_native_mapping=map_report,source= str(source),latest_face_bytes_preserved=True))
 print('JK_SKIRT_COMPOSED_WITH_LATEST_FACE',flush=True)
if __name__=='__main__':compose()
