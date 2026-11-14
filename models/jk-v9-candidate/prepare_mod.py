from pathlib import Path
import json,shutil,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parent;PBZ=ROOT.parents[2]
WORK=PBZ/'variants/new-jk-v9';PROJECT=WORK/'ue/ProjectPBZ';BASE=PBZ/'ue/ProjectPBZ'
def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2),encoding='utf8')
def copy(rel):
    dst=PROJECT/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/rel,dst)
for rel in ['ProjectPBZ.uproject','Config/DefaultEngine.ini','Config/DefaultGame.ini','Plugins/HuaShira/HuaShira.uplugin']:
    copy(rel)
for suffix in ['Hun_Skin_Skeleton.uasset','PA_Hun.uasset','Rig/ABP_Hun_PostProcess.uasset']:
    copy('Plugins/HuaShira/Content/Characters/Hero/Hero_Hun/'+suffix)
materials=json.loads((ROOT/'game-materials.json').read_text());textures=[];mats=[]
def tex(name,kind,color=None,src=None):
    out=WORK/'textures'/(name+'.png');out.parent.mkdir(parents=True,exist_ok=True)
    if src:Image.open(src).convert('RGBA').save(out)
    else:Image.new('RGBA',(256,256),color).save(out)
    package='/HuaShira/Mods/SuiPBZ/JKVT/'+name
    textures.append({'name':name,'kind':kind,'path':str(out),'package':package,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()});return package
normal=tex('T_JK_FlatNormal','normal',(128,128,255,255))
def srgb(v):return round(max(0,min(1,12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))*255)
for m in materials:
    name=m['slot'].removeprefix('MI_JK_')
    src=ROOT/'textures/sui-jk-albedo-v9.png' if m['source_texture'] else None
    albedo=tex('T_JK_'+name,'albedo',tuple(srgb(x) for x in m['base_color_linear'][:3])+(255,),src)
    arm=tex('T_JK_ARM_'+name,'mask',(255,round(m['roughness']*255),round(m['metallic']*255),255))
    mats.append({'slot':m['slot'],'parent':'/Game/PBZContent/Characters/Hero/Hun_New_V2b/Material/MI_ZeroHun_Cloth_02_b','textures':{'Albedo':albedo,'Normal':normal,'Mix':arm}})
write(WORK/'material-spec.json',{'textures':textures,'materials':mats})
write(WORK/'source-spec.json',{'source_root':str(ROOT),'body_package':'/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple','fbx':str(ROOT/'Sui_JK_Hun_Body.fbx'),'fbx_sha256':hashlib.sha256((ROOT/'Sui_JK_Hun_Body.fbx').read_bytes()).hexdigest(),'expected_triangles':json.loads((ROOT/'binding-report.json').read_text())['triangles']})
print(json.dumps({'project':str(PROJECT),'materials':len(mats),'textures':len(textures)}))
