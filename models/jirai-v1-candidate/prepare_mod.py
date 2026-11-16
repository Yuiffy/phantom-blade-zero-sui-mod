from pathlib import Path
import json,shutil,hashlib
from PIL import Image
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]/'private/jirai-v1';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');WORK=ROOT/'variant';PROJECT=WORK/'ue/ProjectPBZ';BASE=PBZ/'ue/ProjectPBZ'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(json.dumps(d,indent=2).encode('utf8'))
for rel in ['ProjectPBZ.uproject','Config/DefaultEngine.ini','Config/DefaultGame.ini','Plugins/HuaShira/HuaShira.uplugin']+['Plugins/HuaShira/Content/Characters/Hero/Hero_Hun/'+s for s in ['Hun_Skin_Skeleton.uasset','PA_Hun.uasset','Rig/ABP_Hun_PostProcess.uasset']]:
 dst=PROJECT/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/rel,dst)
materials=json.loads((ROOT/'game-materials.json').read_text());textures=[];mats=[];dedup={}
def tex(name,kind,color=None,src=None):
 key=(kind,str(src) if src else tuple(color))
 if key in dedup:return dedup[key]
 out=WORK/'textures'/(name+'.png');out.parent.mkdir(parents=True,exist_ok=True)
 if src:Image.open(src).convert('RGBA').save(out)
 else:Image.new('RGBA',(256,256),color).save(out)
 package='/HuaShira/Mods/SuiPBZ/JiraiVT/'+name;textures.append({'name':name,'kind':kind,'path':str(out),'package':package,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()});dedup[key]=package;return package
normal=tex('T_Jirai_FlatNormal','normal',(128,128,255,255))
def srgb(v):return round(max(0,min(1,12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))*255)
# Every authored surface section reuses one atlas, not a second 4K copy.
atlas=tex('T_Jirai_Base','albedo',src=ROOT/'textures/jirai-albedo.png')
for m in materials:
 name=m['slot'].removeprefix('MI_Jirai_')
 albedo=tex('T_Jirai_'+name,'albedo',src=Path(m['albedo_path'])) if m.get('albedo_path') else atlas if m['source_texture'] else tex('T_Jirai_'+name,'albedo',tuple(srgb(x) for x in m['base_color_linear'][:3])+(255,))
 if m.get('two_color_arm'):
  path=WORK/'textures/wing-arm.png';im=Image.new('RGBA',(64,32),(255,round(.7*255),0,255));im.paste((255,round(.54*255),0,255),(32,0,64,32));im.save(path)
  arm=tex('T_Jirai_ARM_Wing','mask',src=path)
 else:arm=tex('T_Jirai_ARM_'+name,'mask',(255,round(m['roughness']*255),round(m['metallic']*255),255))
 mats.append({'slot':m['slot'],'parent':'/Game/PBZContent/Characters/Hero/Hun_New_V2b/Material/MI_ZeroHun_Cloth_02_b','textures':{'Albedo':albedo,'Normal':normal,'Mix':arm}})
write(WORK/'material-spec.json',{'textures':textures,'materials':mats})
write(WORK/'source-spec.json',{'source_root':str(ROOT),'body_package':'/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple','fbx':str(ROOT/'Sui_Jirai_Hun_Body.fbx'),'fbx_sha256':hashlib.sha256((ROOT/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),'expected_triangles':json.loads((ROOT/'binding-report.json').read_text())['triangles']})
print(json.dumps({'project':str(PROJECT),'materials':len(mats),'textures':len(textures)}))

# Reuse the already compiled, editor-only cloth helper in this isolated project.
plugin=PBZ/'variants/jk-motion-v3/ue/ProjectPBZ/Plugins/PBZModTools'
if not plugin.exists():plugin=PBZ/'variants/jk-motion-v2/ue/ProjectPBZ/Plugins/PBZModTools'
assert plugin.exists(),plugin
shutil.copytree(plugin,PROJECT/'Plugins/PBZModTools',dirs_exist_ok=True)
d=json.loads((PROJECT/'ProjectPBZ.uproject').read_text())
for name in ['PBZModTools','ChaosCloth']:
 p=next((p for p in d['Plugins'] if p['Name']==name),None)
 if p:p['Enabled']=True
 else:d['Plugins'].append({'Name':name,'Enabled':True})
write(PROJECT/'ProjectPBZ.uproject',d)
