"""Scoped low-priority V3 build/readback. No install or game-process control."""
from pathlib import Path
import os,subprocess,json
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]/'private/jirai-skirt-recovery-v1'
PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
WORK=ROOT/'variant'
def isolated():
    assert ROOT.name=='jirai-skirt-recovery-v1'
    assert WORK.resolve().is_relative_to(ROOT.resolve())
    assert not WORK.resolve().is_relative_to(Path('F:/FGames').resolve())
    WORK.mkdir(parents=True,exist_ok=True)
def native_run(label,cmd):
    isolated()
    assert Path(cmd[0]).name.lower() in {'unrealpak.exe','retoc.exe','uassetgui.exe'}
    logs=WORK/'logs';logs.mkdir(exist_ok=True)
    with (logs/(label+'.log')).open('wb') as f:
        p=subprocess.run([str(a) for a in cmd],stdout=f,stderr=subprocess.STDOUT,
            env=dict(os.environ,RAYON_NUM_THREADS='1',OMP_NUM_THREADS='1',DOTNET_PROCESSOR_COUNT='2'),
            creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    assert p.returncode==0,(label,p.returncode)
    log=(logs/(label+'.log')).read_text(encoding='utf8',errors='replace')
    assert 'failed to convert' not in log.lower() and 'panicked' not in log.lower()
    return log
def diagnostic_run(label,args,env):
    isolated()
    out=WORK/'independent';out.mkdir(exist_ok=True)
    assert Path(args[0]).name.lower()=='dotnet.exe'
    assert Path(args[1]).name=='PbzExport.dll'
    assert Path(args[5]).resolve().is_relative_to(out.resolve())
    assert args[6] in {'json','skel'}
    p=subprocess.run([str(a) for a in args],env=env,capture_output=True,timeout=600,
        creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    log=(p.stdout+p.stderr).decode('utf8',errors='replace')
    if env.get('PBZX_AES'):log=log.replace(env['PBZX_AES'],'[REDACTED]')
    (out/(label+'.log')).write_text(log,encoding='utf8')
    report={'label':label,'exit_code':p.returncode,'log':label+'.log',
        'parser_warnings_or_errors':any(w in log for w in ['Failed to','Exception','failed to','[WRN]','[ERR]'])}
    (out/(label+'.result.json')).write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report),flush=True)
    assert p.returncode==0,(label,p.returncode)
