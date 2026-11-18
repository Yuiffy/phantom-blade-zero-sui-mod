"""Bounded JK silhouette edits over the frozen installed five-overlay set."""
from pathlib import Path
import hashlib, json, os, subprocess, sys

CODE = Path(__file__).resolve().parent
REPO = CODE.parents[1]
ROOT = REPO / 'private/jk-face-shape-v1'
PBZ = Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
sys.path.insert(0, str(PBZ / 'tools'))
import run_native_diagnostic as diag
from package_model import relative_package

MODS = diag.PAKS / '~mods'
NAME = 'zzzzzz_Sui_JKFaceShape1_P'
BODY = '/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple'
BLENDER = Path('D:/develop/Blender/blender-4.5.14-windows-x64/blender.exe')
JK = PBZ / 'variants/jk-motion-v5'
SOURCE = REPO / 'private/jirai-skirt-shape-v1/dual/legacy' / (relative_package(BODY) + '.uasset')

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def write(p, value):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def snapshot():
    return [dict(name=p.name, bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(MODS.iterdir()) if p.is_file()]

def assert_baseline():
    assert snapshot() == read(ROOT / 'baseline.json')['files'], 'Installed MOD set changed'

def run(label, args, env=None):
    child = dict(os.environ, RAYON_NUM_THREADS='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='1', DOTNET_PROCESSOR_COUNT='2')
    if env:
        child.update(env)
    p = subprocess.run([str(a) for a in args], capture_output=True, env=child,
                       creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    output = (p.stdout + p.stderr).decode('utf8', errors='replace')
    if child.get('PBZX_AES'):
        output = output.replace(child['PBZX_AES'], '[REDACTED]')
    log = ROOT / 'logs' / (label + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(output, encoding='utf8')
    assert p.returncode == 0, (label, p.returncode, output[-2500:])
    assert not any(s in output for s in ['panicked', 'failed to convert', '[ERR]', 'Exception']), label
    return output
