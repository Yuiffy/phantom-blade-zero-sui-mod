"""Query revised cloth projection in a disposable project, preserving solve inputs."""
from common import *
import shutil
clone=W/'mapping-query/ProjectPBZ'
clone.mkdir(parents=True,exist_ok=True)
for name in ['ProjectPBZ.uproject','Config','Content','Plugins/HuaShira']:
 src=PROJECT.parent/name;dst=clone/name
 if src.is_dir():shutil.copytree(src,dst,dirs_exist_ok=True)
 elif src.exists():shutil.copy2(src,dst)
shutil.copytree(W/'pose-tools-host/Plugins/PBZModTools',clone/'Plugins/PBZModTools',dirs_exist_ok=True,ignore=shutil.ignore_patterns('Intermediate'))
args=['F:/FTools/UE57/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe',clone/'ProjectPBZ.uproject','-unattended','-nop4','-stdout','-onethread','-run=pythonscript','-script='+str(C/'query_mapping_ue.py'),'-NullRHI','-NoShaderCompile','-NoShaderWorker']
result=run('query-mapping',args)
assert (W/'reprojected-mapping.json').exists() and 'Traceback' not in result,result[-3000:]
print('QUERY_MAPPING_OK')
