"""Isolated skin/eye experiment. Reads game assets; writes only this candidate."""
from pathlib import Path
import hashlib, json, os, subprocess, sys

CODE = Path(__file__).resolve().parent
REPO = CODE.parents[1]
ROOT = REPO / 'private/skin-eyes-v1'
PBZ = Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
sys.path.insert(0, str(PBZ / 'tools'))
import run_native_diagnostic as diag
from package_model import relative_package

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def write(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(label, args, env=None):
    assert ROOT.resolve().is_relative_to((REPO / 'private').resolve())
    logs = ROOT / 'logs'; logs.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([str(a) for a in args], capture_output=True,
        env=env or dict(os.environ, RAYON_NUM_THREADS='1', OMP_NUM_THREADS='1', DOTNET_PROCESSOR_COUNT='2'),
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    output = (result.stdout + result.stderr).decode('utf8', errors='replace')
    if env and env.get('PBZX_AES'): output = output.replace(env['PBZX_AES'], '[REDACTED]')
    (logs / (label + '.log')).write_text(output, encoding='utf8')
    assert result.returncode == 0, (label, result.returncode, output[-1800:])
    assert not any(t in output for t in ['failed to convert', 'panicked', '[ERR]', 'Exception']), label
    return output

def diagnostic(label, mode, packages, extra=''):
    env = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1',
        DOTNET_PROCESSOR_COUNT='2', PBZX_GAME='GAME_UE5_7', PBZX_SCRIPT='1',
        PBZX_AES=diag.private_key(), PBZX_EXTRA=str(extra))
    out = ROOT / 'research' / label
    return run(label, [diag.DOTNET, diag.DLL, diag.PAKS, diag.MAPPING,
        diag.TOOLS / 'oo2core_9_win64.dll', out, mode, *packages], env)

if __name__ == '__main__':
    if sys.argv[1] == 'parents':
        print(diagnostic('material-list', 'list', [r'(Hun_New_V2b/Material/.*(Skin|Face|Eye)|MaterialLibrary/Template/Character/MAI_).*uasset$']))
        print(diagnostic('cloth-parent', 'json', ['ProjectPBZ/Plugins/AkashaEffects/Content/MaterialLibrary/Template/Character/MAI_Cloth']))
