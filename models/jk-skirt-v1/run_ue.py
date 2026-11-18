from common import *
import shutil
plugin=W/'pose-tools-host/Plugins/PBZModTools'
dst=PROJECT.parent/'Plugins/PBZModTools'
for a in plugin.rglob('*'):
 if a.is_file() and a.relative_to(plugin).parts[0] in ['PBZModTools.uplugin','Binaries','Source']:
  b=dst/a.relative_to(plugin)
  if not b.exists() or sha(a)!=sha(b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
stage=sys.argv[1]
ue(stage,stage+'_ue.py',cook=stage=='cook',extra={'JK_SKIRT_STAGE':sys.argv[2]} if len(sys.argv)>2 else None)
