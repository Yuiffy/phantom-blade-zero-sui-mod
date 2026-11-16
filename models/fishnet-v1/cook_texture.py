from common import *
import shutil

def prepare():
    project=PROJECT.parent; template=PBZ/'ue/ProjectPBZ'
    for rel in ['Config/DefaultEngine.ini','Config/DefaultGame.ini','Plugins/HuaShira/HuaShira.uplugin']:
        dst=project/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(template/rel,dst)
    doc=read(template/'ProjectPBZ.uproject')
    doc['Plugins']=[p for p in doc['Plugins'] if p['Name'] in ['HuaShira','PythonScriptPlugin','EditorScriptingUtilities']]
    write(PROJECT,doc)
    # Explicitly allow the authored top mip in this isolated cook project.
    profile=project/'Config/DefaultDeviceProfiles.ini'
    profile.write_text('[Windows DeviceProfile]\nDeviceType=Windows\nBaseProfileName=\n'
        '+TextureLODGroups=(Group=TEXTUREGROUP_Character,MinLODSize=1,MaxLODSize=8192,LODBias=0,MinMagFilter=aniso,MipFilter=point)\n',encoding='utf8')
    write(ROOT/'cook-input.json',dict(package=PACKAGE,source_sha256=sha(ROOT/'T_Jirai_Base.png'),
        authored=read(ROOT/'atlas-report.json'),project=str(PROJECT)))

def cook():
    prepare()
    cmd=[UE,PROJECT,'-unattended','-nop4','-stdout','-FullStdOutLogOutput','-onethread']
    print('IMPORT_FISHNET_VT',flush=True)
    output=run('ue-import',cmd+['-run=pythonscript','-script='+str(CODE/'import_texture_ue.py'),'-NullRHI','-NoShaderCompile','-NoShaderWorker'])
    assert 'FISHNET_IMPORT_OK' in output
    assert read(ROOT/'import-report.json')['source_sha256']==sha(ROOT/'T_Jirai_Base.png')
    print('COOK_FISHNET_VT',flush=True)
    output=run('ue-cook',cmd+['-run=Cook','-TargetPlatform=Windows','-NoDefaultMaps'])
    assert 'Failure -' not in output
    cooked=PROJECT.parent/'Saved/Cooked/Windows'
    assert (cooked/(relative_package(PACKAGE)+'.uasset')).is_file()
    write(ROOT/'cook-report.json',dict(passed=True,input_sha256=sha(ROOT/'T_Jirai_Base.png')))
    print('FISHNET_TEXTURE_COOKED',flush=True)

if __name__=='__main__':cook()
