from common import *
import shutil

def main():
 assert_baseline();atlas=read(ROOT/'atlas-report.json');assert atlas['passed']
 for outfit,row in atlas['outfits'].items():assert sha(ROOT/f'{outfit}-after.png')==row['output_sha256']
 project=PROJECT.parent;template=PBZ/'ue/ProjectPBZ'
 for rel in ['Config/DefaultEngine.ini','Config/DefaultGame.ini','Plugins/HuaShira/HuaShira.uplugin']:
  dst=project/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(template/rel,dst)
 doc=read(template/'ProjectPBZ.uproject');doc['Plugins']=[p for p in doc['Plugins'] if p['Name'] in ['HuaShira','PythonScriptPlugin','EditorScriptingUtilities']];write(PROJECT,doc)
 (project/'Config/DefaultDeviceProfiles.ini').write_text('[Windows DeviceProfile]\nDeviceType=Windows\nBaseProfileName=\n+TextureLODGroups=(Group=TEXTUREGROUP_Character,MinLODSize=1,MaxLODSize=8192,LODBias=0,MinMagFilter=aniso,MipFilter=point)\n',encoding='utf8')
 cmd=[UE,PROJECT,'-unattended','-nop4','-stdout','-FullStdOutLogOutput','-onethread']
 print('IMPORT_OUTFIT_PATTERNS',flush=True)
 output=run('ue-import',cmd+['-run=pythonscript','-script='+str(CODE/'import_texture_ue.py'),'-NullRHI','-NoShaderCompile','-NoShaderWorker']);assert 'OUTFIT_PATTERNS_IMPORT_OK' in output
 imported=read(ROOT/'import-report.json');assert imported['passed']
 for r in imported['textures']:assert r['source_sha256']==sha(ROOT/f"{r['outfit']}-after.png")
 print('COOK_OUTFIT_PATTERNS',flush=True)
 output=run('ue-cook',cmd+['-run=Cook','-TargetPlatform=Windows','-NoDefaultMaps']);assert 'Failure -' not in output
 for package in PACKAGES:assert (project/'Saved/Cooked/Windows'/(relative_package(package)+'.uasset')).is_file()
 write(ROOT/'cook-report.json',dict(passed=True,textures=imported['textures']))
 print('OUTFIT_PATTERNS_COOKED',flush=True)
if __name__=='__main__':main()
