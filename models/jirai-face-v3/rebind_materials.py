"""Retain native export payload; replace only selected texture imports."""
from common import *

EYE_MIX='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Face3_EyeMix'
OLD_EYE_MIX='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_ARM_EyeIris'
IRIS='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Face3_Iris'

def replace(value,iris=False):
    if isinstance(value,dict):return {k:replace(v,iris) for k,v in value.items()}
    if isinstance(value,list):return [replace(v,iris) for v in value]
    if isinstance(value,str):
        albedo=IRIS if iris else PACKAGE
        value=value.replace(OLD_ATLAS,albedo).replace('T_Jirai_Base',albedo.rsplit('/',1)[-1])
        if iris:value=value.replace(OLD_EYE_MIX,EYE_MIX).replace('T_Jirai_ARM_EyeIris','T_Face3_EyeMix')
    return value

def build():
    records=[]
    for package in MATERIALS:
        name=package.rsplit('/',1)[-1];iris=name=='MI_Jirai_EyeIris'
        # The standalone final-container extraction has unresolved external
        # game imports (/Engine/UnknownPackage). Use the verified pre-pack
        # legacy header, whose export payload was proven byte-identical.
        source=MODEL/'legacy'/(relative_package(package)+'.uasset')
        assert sha(source.with_suffix('.uexp'))==sha(MODEL/'final-legacy'/(relative_package(package)+'.uexp'))
        original=ROOT/'materials'/(name+'-original.json');original.parent.mkdir(parents=True,exist_ok=True)
        run(name+'-source',[diag.TOOLS/'UAssetGUI.exe','tojson',source,original,'VER_UE5_6','PBZ'])
        doc=read(original);edited=replace(doc,iris);assert edited!=doc and edited['Exports']==doc['Exports']
        path=ROOT/'materials'/(name+'-edited.json');write(path,edited)
        target=ROOT/'legacy'/(relative_package(package)+'.uasset');target.parent.mkdir(parents=True,exist_ok=True)
        run(name+'-write',[diag.TOOLS/'UAssetGUI.exe','fromjson',path,target,'PBZ'])
        reread=ROOT/'materials'/(name+'-readback.json')
        run(name+'-read',[diag.TOOLS/'UAssetGUI.exe','tojson',target,reread,'VER_UE5_6','PBZ'])
        got=read(reread)
        for actual,wanted in zip(got['Exports'],doc['Exports']):
            assert {k:v for k,v in actual.items() if k!='SerialOffset'}=={k:v for k,v in wanted.items() if k!='SerialOffset'}
        assert got['Imports']==edited['Imports'] and got['NameMap']==edited['NameMap']
        assert source.with_suffix('.uexp').read_bytes()==target.with_suffix('.uexp').read_bytes()
        records.append(dict(package=package,changed='Albedo and iris Mix imports' if iris else 'Albedo import',
            all_export_bytes_exact=True,native_parent_and_shader_payload_exact=True,
            output_payload_sha256=sha(target.with_suffix('.uexp'))))
    write(ROOT/'material-rebinding.json',dict(passed=True,albedo=PACKAGE,iris_mix=EYE_MIX,materials=records))
    print('FACE3_NATIVE_MATERIALS_REBOUND')

if __name__=='__main__':build()
