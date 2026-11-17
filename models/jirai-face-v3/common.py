"""Face3: bounded face edits over the installed skirt recovery container."""
from pathlib import Path
import hashlib, json, os, subprocess, sys

CODE = Path(__file__).resolve().parent
REPO = CODE.parents[1]
ROOT = REPO / 'private/jirai-face-v3'
PBZ = Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
sys.path.insert(0, str(PBZ / 'tools'))
import run_native_diagnostic as diag
from package_model import relative_package

PACKAGE = '/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Face3'
OLD_ATLAS = '/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Base'
MATERIALS = ['/HuaShira/Mods/SuiPBZ/Materials/' + n for n in ['MI_Jirai_Skin', 'MI_Jirai_Hair', 'MI_Jirai_EyeIris']]
BASE = REPO / 'private/fishnet-v1'
MODEL = REPO / 'private/jirai-skirt-shape-v1/dual'
MODEL_NAME = 'z_Sui_DualOutfit_JK5_JiraiR8Shape1_P'
MODS = Path('F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods')
NAME = 'zzz_Sui_JiraiFace3_2_P'
PROJECT = ROOT / 'ue/ProjectPBZ/ProjectPBZ.uproject'
UE = Path('F:/FTools/UE57/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe')
BLENDER = Path('D:/develop/Blender/blender-4.5.14-windows-x64/blender.exe')

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p, v):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(label, args, env=None):
    logs = ROOT / 'logs'; logs.mkdir(parents=True, exist_ok=True)
    child = dict(os.environ, RAYON_NUM_THREADS='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='1', DOTNET_PROCESSOR_COUNT='2')
    if env: child.update(env)
    result = subprocess.run([str(a) for a in args], capture_output=True, env=child,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    output = (result.stdout + result.stderr).decode('utf-8', errors='replace')
    if child.get('PBZX_AES'): output = output.replace(child['PBZX_AES'], '[REDACTED]')
    (logs / (label + '.log')).write_text(output, encoding='utf-8')
    assert result.returncode == 0, (label, result.returncode, output[-3500:])
    assert not any(t in output for t in ['failed to convert', 'panicked', '[ERR]', 'Exception']), label
    return output

def blender(label, script, *args):
    return run(label, [BLENDER, '-b', '-t', '2', '--python-exit-code', '1', '--python', script, '--', *args])

if __name__ == '__main__':
    ROOT.mkdir(parents=True, exist_ok=True)
    assert not (ROOT / 'baseline.json').exists()
    installed = [dict(name=p.name, bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(MODS.iterdir()) if p.is_file()]
    receipt = read(MODEL / 'installation-receipt.json')
    expected = {r['name']: r['sha256'] for r in receipt['after']}
    assert {r['name']: r['sha256'] for r in installed} == expected, 'Installed base changed'
    write(ROOT / 'baseline.json', dict(installed=installed, model_receipt_sha256=sha(MODEL / 'installation-receipt.json'),
        basis='Installed R8Shape1 and Face2; preserve every cloth/weight/index byte', game_runtime_tested=False))
    print('FACE3_BASELINE_FROZEN', len(installed))
