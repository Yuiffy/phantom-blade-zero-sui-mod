from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent;PBZ=ROOT.parents[2];WORK=PBZ/'variants/jk-motion-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
STATIC=ROOT.parent/'tripo-refine-v11'
atlas=STATIC/'textures/sui-jk-albedo-v11.png';a=read(STATIC/'atlas-repair.json');assert sha(atlas)==a['output_sha256']
spec=read(WORK/'material-spec.json');row=next(t for t in spec['textures'] if t['name']=='T_JK_Base');prepared=Path(row['path']);assert sha(prepared)==row['sha256']
assert np.array_equal(np.asarray(Image.open(atlas).convert('RGBA')),np.asarray(Image.open(prepared).convert('RGBA')))
imported=next(t for t in read(WORK/'import-report.json')['textures'] if t['package']==row['package']);assert imported['vt'] and imported['width']==imported['height']==4096
rel='ProjectPBZ/Plugins/HuaShira/Content/Mods/SuiPBZ/JKVT/T_JK_Base'
records=[]
for ext in ['.uexp','.ubulk','.uptnl']:
 a=WORK/'fresh-legacy'/(rel+ext);b=WORK/'final-legacy'/(rel+ext)
 assert a.exists()==b.exists()
 if a.exists():assert a.read_bytes()==b.read_bytes();records.append({'extension':ext,'bytes':b.stat().st_size,'sha256':sha(b)})
assert records
report={'status':'repaired-atlas-input-and-final-container-payload-chain-passed','atlas_sha256':sha(atlas),'prepared_texture_sha256':sha(prepared),'prepared_RGBA_pixels_exactly_match_repaired_atlas':True,'imported_virtual_texture_dimensions':[4096,4096],'cooked_VT_payload_preserved_in_final_container':True,'payload_files':records,'final_VT_not_independently_decoded_to_pixels':True,'runtime_tested':False}
all_textures=[]
for row in spec['textures']:
 assert sha(Path(row['path']))==row['sha256'],row['name']
 rel='ProjectPBZ/Plugins/HuaShira/Content/Mods/SuiPBZ/JKVT/'+row['name'];files=[]
 for ext in ['.uexp','.ubulk','.uptnl']:
  x=WORK/'fresh-legacy'/(rel+ext);y=WORK/'final-legacy'/(rel+ext)
  assert x.exists()==y.exists()
  if x.exists():assert x.read_bytes()==y.read_bytes();files.append({'extension':ext,'sha256':sha(y)})
 assert files;all_textures.append({'name':row['name'],'input_sha256':row['sha256'],'payloads':files})
report['all_texture_payload_chains']=all_textures
(WORK/'texture-chain.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='all_texture_payload_chains'}))
