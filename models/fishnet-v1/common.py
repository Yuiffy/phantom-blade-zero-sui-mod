"""Isolated texture-only candidate; retain the installed skin/eye mesh."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
CODE=Path(__file__).resolve().parent; REPO=CODE.parents[1]
ROOT=REPO/'private/fishnet-v1'; BASE=REPO/'private/skin-eyes-v1/dual'
PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
sys.path.insert(0,str(PBZ/'tools'))
import run_native_diagnostic as diag
from package_model import relative_package
PACKAGE='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Base'
NAME='z_Sui_DualOutfit_JK5_JiraiR6_SkinEyes1_Fishnet1_P'
PROJECT=ROOT/'ue/ProjectPBZ/ProjectPBZ.uproject'
UE=Path('F:/FTools/UE57/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(label,args,env=None):
    logs=ROOT/'logs';logs.mkdir(parents=True,exist_ok=True)
    result=subprocess.run([str(a) for a in args],capture_output=True,
        env=env or dict(os.environ,RAYON_NUM_THREADS='1',OMP_NUM_THREADS='1',DOTNET_PROCESSOR_COUNT='2'),
        creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    output=(result.stdout+result.stderr).decode('utf8',errors='replace')
    if env and env.get('PBZX_AES'):output=output.replace(env['PBZX_AES'],'[REDACTED]')
    (logs/(label+'.log')).write_text(output,encoding='utf8')
    assert result.returncode==0,(label,result.returncode,output[-2500:])
    assert not any(t in output for t in ['failed to convert','panicked','[ERR]','Exception']),label
    return output
def copyasset(source,target,package):
    for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
        a=source/(relative_package(package)+ext);b=target/(relative_package(package)+ext)
        if a.exists():b.parent.mkdir(parents=True,exist_ok=True);b.write_bytes(a.read_bytes())
