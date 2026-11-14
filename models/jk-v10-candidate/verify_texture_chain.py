from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent;PBZ=ROOT.parents[2];WORK=PBZ/'variants/new-jk-v10'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
atlas=ROOT/'textures/sui-jk-albedo-v10.png';a=read(ROOT/'atlas-repair.json');assert sha(atlas)==a['output_sha256']
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
(ROOT/'texture-chain.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
