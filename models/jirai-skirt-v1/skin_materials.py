"""Native shader leaves only: no custom shader compilation or static switches."""
from skin_material_support import *
import copy, base64, struct
from PIL import Image
import build_native_shader_assets as native

VARIANT = ROOT / 'variant'
SKIN = '/Game/PBZContent/Characters/Hero/Hun_New_V2b/Material/MI_ZeroHun_Head_b'
LIT = '/AkashaEffects/MaterialLibrary/Template/Character/MAI_Equipment_Mask'
CLOTH = '/Game/PBZContent/Characters/Hero/Hun_New_V2b/Material/MI_ZeroHun_Cloth_02_b'

def configure(m):
    slot = m['slot']
    if slot in ['MI_Jirai_Skin','MI_Jirai_Hands']:
        m.update(parent=SKIN,layer_remap=[0],scalars=[
            ['Roughness Max',.62,0],['Specular Max',.35,0],
            ['SkinMicroNormalIntensity',.08,0],['Thickness Max',.7,0]])
        m['textures']['SkinNormal_MICRO'] = m['textures']['Normal']
        m['textures']['SCMT_Map'] = '/HuaShira/Mods/SuiPBZ/JiraiVT/T_SkinEyes_SCMT'
    elif slot in ['MI_Jirai_Blouse','MI_Jirai_Skirt','MI_Jirai_Legwear',
                  'MI_Jirai_ShortLining','MI_Jirai_Suspender'] or any(
                  n in slot for n in ['Cardigan','PleatedSkirt','Stockings','SafetyLining']):
        m.update(parent=CLOTH,layer_remap=[0,1],scalars=[
            ['NormalIntensity',.08,1],['BaseColor Intensity',0.,1]])
    else:
        m.update(parent=LIT,layer_remap=[0],scalars=[])
    return m

def prepare():
    spec = read(VARIANT/'material-spec.json')
    path = VARIANT/'textures/T_SkinEyes_SCMT.png'
    Image.new('RGBA',(256,256),(89,255,0,96)).save(path)
    spec['textures'].append(dict(name='T_SkinEyes_SCMT',kind='mask',path=str(path),
        package='/HuaShira/Mods/SuiPBZ/JiraiVT/T_SkinEyes_SCMT',sha256=sha(path)))
    spec['materials'] = [configure(m) for m in spec['materials']]
    write(VARIANT/'material-spec.json',spec)

def build_rows(materials, work, legacy):
    template = read(native.BASE/'final-readback-json/MI_Sui_13.json')
    records = []
    for m in materials:
        package = '/HuaShira/Mods/SuiPBZ/Materials/'+m['slot']
        albedo = m['textures']['Albedo']
        replacements = {
            '/HuaShira/Mods/SuiPBZ/Materials/MI_Sui_13':package,
            '/HuaShira/Mods/SuiPBZ/Materials/M_Sui_Textured':m['parent'],
            'M_Sui_Textured':m['parent'].rsplit('/',1)[-1],
            '/HuaShira/Mods/SuiPBZ/Textures/T_Sui_00':albedo,
            'T_Sui_00':albedo.rsplit('/',1)[-1]}
        doc = native.replace_text(copy.deepcopy(template),replacements)
        e = doc['Exports'][0]; e['ObjectName'] = m['slot']
        native.add_name(doc,m['slot'])
        doc['Imports'][1]['ClassName'] = 'MaterialInstanceConstant'
        p = native.props(e['Data']); ta = p['TextureParameterValues']
        tt = copy.deepcopy(ta['Value'][0]); ta['Value'] = []; dependencies = [-2]
        for name, path in m['textures'].items():
            idx = native.add_texture(doc,path)
            ta['Value'].append(native.parameter(tt,name,idx)); dependencies.append(idx)
            native.add_name(doc,name)
        sa = p['ScalarParameterValues']; st = copy.deepcopy(sa['Value'][0]); sa['Value'] = []
        scalars = [[n,0.,-1] for n in ['Wetness Min','Wetness Max',
            'RainDrops | StaticDrops Intensity','RainDrops | DrippingDrop Intensity']]+m['scalars']
        for name, value, layer in scalars:
            encoded = '+0' if value == 0 else struct.unpack('<f',struct.pack('<f',value))[0]
            row = native.parameter(st,name,encoded,layer=layer>=0)
            info = native.props(native.props(row['Value'])['ParameterInfo']['Value'])
            info['Index']['Value'] = layer
            sa['Value'].append(row); native.add_name(doc,name)
        values = [p['Parent'],ta,sa]
        if m['parent'] == SKIN:
            va = p['VectorParameterValues']; vt = copy.deepcopy(va['Value'][0])
            color = native.props(vt['Value'])['ParameterValue']['Value']
            color[0]['Value'].update(R=1.,G=1.,B=1.,A='+0')
            va['Value'] = [native.parameter(vt,'Albedo Controls',color)]
            native.add_name(doc,'Albedo Controls'); values.append(va)
        e['Data'] = values
        e['CreateBeforeSerializationDependencies'] = dependencies
        raw = bytearray(base64.b64decode(e['Extras']))
        assert len(raw)==57 and struct.unpack_from('<II',raw)==(0,1)
        remap = m['layer_remap']
        struct.pack_into('<I',raw,40,4+4*len(remap))
        raw = raw[:45]+struct.pack('<i',len(remap))+struct.pack('<'+'i'*len(remap),*remap)+raw[49:]
        e['Extras'] = base64.b64encode(raw).decode()
        for n in ['LayerParameter',package]+[x['ObjectName'] for x in doc['Imports']]:native.add_name(doc,n)
        doc['NamesReferencedFromExportDataCount'] = len(doc['NameMap'])
        edited = work/'edited-materials'/(m['slot']+'.json'); write(edited,doc)
        dest = legacy/(relative_package(package)+'.uasset'); dest.parent.mkdir(parents=True,exist_ok=True)
        run('write-'+m['slot'],[diag.TOOLS/'UAssetGUI.exe','fromjson',edited,dest,'PBZ'])
        parsed = work/'material-readback'/(m['slot']+'.json'); parsed.parent.mkdir(parents=True,exist_ok=True)
        run('read-'+m['slot'],[diag.TOOLS/'UAssetGUI.exe','tojson',dest,parsed,'VER_UE5_6','PBZ'])
        got = read(parsed)
        assert got['Exports'][0]['Data']==e['Data'] and got['Exports'][0]['Extras']==e['Extras']
        assert got['Imports']==doc['Imports']
        records.append(dict(package=package,parent=m['parent'],textures=m['textures'],
            scalars=scalars,layer_remap=remap,shader_resources=0,readback_sha256=sha(parsed)))
    write(work/'material-build.json',records)
    print('NATIVE_MATERIALS_READ_BACK',len(records),flush=True)

def build():
    build_rows(read(VARIANT/'material-spec.json')['materials'],VARIANT,VARIANT/'legacy')
