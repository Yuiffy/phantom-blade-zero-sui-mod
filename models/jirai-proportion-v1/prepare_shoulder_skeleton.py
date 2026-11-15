"""Patch only isolated editor skeletons and create a native per-character clone."""
import json,sys,copy,hashlib,shutil,base64,struct
from pathlib import Path
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]/'private/jirai-proportion-v1';W=ROOT/'variant';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
sys.path.insert(0,str(PBZ/'tools'));import build_native_shader_assets as native
from offline_tools import native_run
old_path='/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton';new_path='/HuaShira/Mods/SuiPBZ/JiraiRig/Hun_Skin_Skeleton'
raw=json.loads((PBZ/'research/hun-skeleton.json').read_text(encoding='utf8'));raw_bones=json.loads((PBZ/'research/hun-skeleton-raw.json').read_text())['bones']
contract=json.loads((ROOT/'shoulder-animation-contract.json').read_text());changed={n.lower() for n in contract['skeleton_translation_bones']}
original=next(e for e in raw['Exports'] if e['ObjectName']=='Hun_Skin_Skeleton');modes=next(d for d in original['Data'] if d['Name']=='BoneTree')['Value']
mode_by_name={b['name'].lower():m['Value'][0]['Value'] for b,m in zip(raw_bones,modes)}
scratch=W/'shoulder-rig';scratch.mkdir(exist_ok=True)
soft={'$type':'UAssetAPI.PropertyTypes.Objects.SoftObjectPropertyData, UAssetAPI','Name':'0','ArrayIndex':0,'PropertyGuid':None,'IsZero':False,'PropertyTagFlags':'None','PropertyTypeName':None,'PropertyTagExtensions':'NoExtension','Value':{'$type':'UAssetAPI.PropertyTypes.Objects.FSoftObjectPath, UAssetAPI','AssetPath':{'$type':'UAssetAPI.PropertyTypes.Objects.FTopLevelAssetPath, UAssetAPI','PackageName':old_path,'AssetName':'Hun_Skin_Skeleton'},'SubPathString':None}}
def editor_order(doc):
 e=next(e for e in doc['Exports'] if e['ObjectName']=='Hun_Skin_Skeleton');data=base64.b64decode(e['Extras']);count=struct.unpack_from('<i',data)[0];offset=4;result=[]
 for i in range(count):
  idx,number,parent,size=struct.unpack_from('<iiii',data,offset);offset+=16+abs(size)*(2 if size<0 else 1);assert number==0;result.append({'i':i,'name':doc['NameMap'][idx],'parent':parent})
 assert struct.unpack_from('<i',data,offset)[0]==count==1134
 return result
def patch(doc,target):
 e=next(e for e in doc['Exports'] if e['ObjectName']=='Hun_Skin_Skeleton');tree=next(d for d in e['Data'] if d['Name']=='BoneTree');assert len(tree['Value'])==len(modes)==len(raw_bones)==1134
 order=raw_bones if doc['HasUnversionedProperties'] else editor_order(doc)
 if not doc['HasUnversionedProperties']:(scratch/'editor-bone-order.json').write_text(json.dumps(order,indent=2))
 for dst,b in zip(tree['Value'],order):
  value='Skeleton' if target and b['name'].lower() in changed else mode_by_name[b['name'].lower()]
  field=dst['Value'][0]
  if 'BytePropertyData' in field['$type']:
   field['EnumValue']='EBoneTranslationRetargetingMode::'+value;native.add_name(doc,field['EnumValue'])
  else:field['Value']=value;native.add_name(doc,value)
 if target and doc['HasUnversionedProperties']:
  e['Data']=[d for d in e['Data'] if d['Name']!='CompatibleSkeletons'];arr=copy.deepcopy(tree);arr.update(Name='CompatibleSkeletons',ArrayType='SoftObjectProperty',Value=[copy.deepcopy(soft)]);e['Data'].append(arr)
  for n in ['CompatibleSkeletons','SoftObjectProperty',old_path,new_path,'Hun_Skin_Skeleton','Skeleton']:native.add_name(doc,n)
 doc['NamesReferencedFromExportDataCount']=len(doc['NameMap']);return doc
project=W/'ue/ProjectPBZ/Plugins/HuaShira/Content'
for path,target in ([] if '--native-only' in sys.argv else [(old_path,False),(new_path,True)]):
 asset=project/(path.removeprefix('/HuaShira/')+'.uasset');asset.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(PBZ/'ue/ProjectPBZ/Plugins/HuaShira/Content/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton.uasset',asset)
 label='target' if target else 'source';dump=scratch/(label+'-editor.json');native_run('read-'+label+'-editor',[native.TOOLS/'UAssetGUI.exe','tojson',asset,dump,'VER_UE5_7','PBZ']);doc=json.loads(dump.read_text(encoding='utf8'));doc=patch(doc,target);edited=scratch/(label+'-edited.json');edited.write_text(json.dumps(doc),encoding='utf8');native_run('write-'+label+'-editor',[native.TOOLS/'UAssetGUI.exe','fromjson',edited,asset,'PBZ'])
 # Read the serialized properties back, instead of trusting an in-memory edit.
 check=scratch/(label+'-readback.json');native_run('readback-'+label+'-editor',[native.TOOLS/'UAssetGUI.exe','tojson',asset,check,'VER_UE5_7','PBZ']);got=json.loads(check.read_text(encoding='utf8'));e=next(e for e in got['Exports'] if e['ObjectName']=='Hun_Skin_Skeleton')
 actual=next(d for d in e['Data'] if d['Name']=='BoneTree')['Value']
 for row,bone in zip(actual,editor_order(got)):
  want='Skeleton' if target and bone['name'].lower() in changed else mode_by_name[bone['name'].lower()];field=row['Value'][0];assert field.get('EnumValue',field.get('Value')).split('::')[-1]==want,(bone['name'],field,want)
doc=copy.deepcopy(raw)
doc['FolderName']=new_path
doc['NameMap']=[new_path if n==old_path else n for n in doc['NameMap']];patch(doc,True)
edited=scratch/'native-clone.json';edited.write_text(json.dumps(doc),encoding='utf8');asset=scratch/'native/ProjectPBZ/Plugins/HuaShira/Content/Mods/SuiPBZ/JiraiRig/Hun_Skin_Skeleton.uasset';asset.parent.mkdir(parents=True,exist_ok=True)
native_run('write-native-shoulder-skeleton',[native.TOOLS/'UAssetGUI.exe','fromjson',edited,asset,'PBZ'])
check=scratch/'native-readback.json';native_run('read-native-shoulder-skeleton',[native.TOOLS/'UAssetGUI.exe','tojson',asset,check,'VER_UE5_6','PBZ']);got=json.loads(check.read_text(encoding='utf8'));g=next(e for e in got['Exports'] if e['ObjectName']=='Hun_Skin_Skeleton');assert g['Extras']==original['Extras'] and got['FolderName']==new_path
(scratch/'native-clone-report.json').write_text(json.dumps({'new_package':new_path,'source_package':old_path,'retargeted_bones':sorted(changed),'native_reference_payload_preserved':True,'full_bone_count':1134,'shared_game_skeleton_overridden':False,'game_runtime_tested':False},indent=2));print('Native shoulder skeleton clone built')
