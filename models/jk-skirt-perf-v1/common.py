"""Local-only JK skirt authoring; compose onto the latest installed mesh."""
from pathlib import Path
import sys, json, os, subprocess, hashlib
C=Path(__file__).resolve().parent
REPO=C.parents[1]
W=REPO/'private/jk-skirt-perf-v1'
P=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
sys.path.insert(0,str(P/'tools'))
import run_native_diagnostic as diag
from package_model import relative_package
from ue_pipeline import game_pids
BODY='/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple'
PA='/HuaShira/Mods/SuiPBZ/Physics/PA_JK_SkirtCollision1'
PROJECT=W/'variant/ue/ProjectPBZ/ProjectPBZ.uproject'
MODS=diag.PAKS/'~mods'
NAME='zzzzzzzzz_Sui_JKSkirtPerf1_10_P'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snapshot():return [dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(MODS.iterdir()) if p.is_file()]
def run(label,args,extra=None):
 env=dict(os.environ,RAYON_NUM_THREADS='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',DOTNET_PROCESSOR_COUNT='2')
 env.update(extra or {})
 log=W/'logs'/(label+'.log');log.parent.mkdir(exist_ok=True)
 with log.open('wb') as f:r=subprocess.run([str(a) for a in args],stdout=f,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 text=log.read_text(encoding='utf8',errors='replace')
 if env.get('PBZX_AES'):log.write_text(text.replace(env['PBZX_AES'],'[REDACTED]'),encoding='utf8')
 assert r.returncode==0,(label,r.returncode,text[-2200:])
 return text
def ue(label,script=None,cook=False,extra=None):
 args=['F:/FTools/UE57/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe',PROJECT,'-unattended','-nop4','-stdout','-onethread']
 args+=['-run=Cook','-TargetPlatform=Windows','-NoDefaultMaps',*[('-CookDir='+str(PROJECT.parent/'Plugins/HuaShira/Content/Mods/SuiPBZ'/n)) for n in ['Physics','EscapeOnly']]] if cook else ['-run=pythonscript','-script='+str(C/script),'-NullRHI','-NoShaderCompile','-NoShaderWorker']
 result=run(label,args,extra)
 assert not any(s in result for s in ['Traceback (most recent call last)','LogPython: Error:','Fatal error:']),result[-3000:]
 print(label,'OK',flush=True)
