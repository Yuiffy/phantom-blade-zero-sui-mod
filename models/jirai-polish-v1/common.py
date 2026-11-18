"""Local runtime-feedback repair over the frozen Patterns1/Hairpin1 stack."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
CODE=Path(__file__).resolve().parent; REPO=CODE.parents[1]
ROOT=REPO/'private/jirai-polish-v1'; FACE=REPO/'private/jirai-face-v3'; PIN=REPO/'private/jirai-hairpin-v1'; PAT=REPO/'private/outfit-patterns-v1'
PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
sys.path.insert(0,str(PBZ/'tools'));sys.path.append(str(REPO/'models/jirai-face-v3'))
import run_native_diagnostic as diag
from package_model import relative_package
MODS=Path('F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods')
NAME='zzzzzz_Sui_JiraiPolish1_5_P'
BODY='/HuaShira/Mods/SuiPBZ/JiraiOnly/Hun_Body_Simple'
SKIN='/HuaShira/Mods/SuiPBZ/Materials/MI_Jirai_Skin'
PACKAGE='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Polish1'
PACKAGES=[BODY,SKIN,PACKAGE]
PROJECT=ROOT/'ue/ProjectPBZ/ProjectPBZ.uproject'
UE=Path('F:/FTools/UE57/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe')
BLENDER=Path('D:/develop/Blender/blender-4.5.14-windows-x64/blender.exe')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def unit(v):
 import numpy as np
 return v/np.maximum(1e-12,np.linalg.norm(v,axis=-1,keepdims=True))
def snapshot():return [dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(MODS.iterdir()) if p.is_file()]
def assert_baseline():assert snapshot()==read(ROOT/'baseline.json')['files'],'Installed MOD set changed'
def run(label,args,env=None):
 logs=ROOT/'logs';logs.mkdir(parents=True,exist_ok=True)
 child=dict(os.environ,RAYON_NUM_THREADS='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',DOTNET_PROCESSOR_COUNT='2');child.update(env or {})
 result=subprocess.run([str(a) for a in args],capture_output=True,env=child,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 out=(result.stdout+result.stderr).decode('utf8',errors='replace')
 if child.get('PBZX_AES'):out=out.replace(child['PBZX_AES'],'[REDACTED]')
 (logs/(label+'.log')).write_text(out,encoding='utf8')
 assert result.returncode==0,(label,result.returncode,out[-2200:])
 assert not any(x in out for x in ['panicked','failed to convert','[ERR]','Exception']),label
 return out
if __name__=='__main__':
 ROOT.mkdir(parents=True,exist_ok=True)
 baseline=dict(files=snapshot(),patterns_receipt_sha256=sha(PAT/'installation-receipt.json'))
 assert baseline['files']==read(PAT/'installation-receipt.json')['after']
 if (ROOT/'baseline.json').exists():assert baseline==read(ROOT/'baseline.json')
 else:write(ROOT/'baseline.json',baseline)
 write(ROOT/'runtime-feedback.json',dict(date='2026-11-17',source='User-provided gameplay screenshots and messages',observations=['Eyes improved but look frightening / too wide open','Facial color patches','Previous mouth preferred','Halo looks flat and crooked; compare JK halo','Hollow upper-arm to sleeve transition'],previous_gameplay_tested=True,new_candidate_gameplay_tested=False))
 print('POLISH_BASELINE_FROZEN',len(baseline['files']))
