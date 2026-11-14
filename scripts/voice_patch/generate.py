"""Reconstruct the reviewed voice container from the user's own game, offline."""
import argparse
import ast
import csv
import ctypes
import getpass
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from iostore import FormatError, RangeReader, require

STEP = 4 * 1048576


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda: f.read(STEP), b''):
            h.update(data)
    return h.hexdigest()


def game_running():
    if os.name != 'nt':
        raise FormatError('This verified builder requires 64-bit Windows')
    result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], check=True,
                            capture_output=True, text=True, errors='replace',
                            creationflags=subprocess.CREATE_NO_WINDOW)
    return any(row and re.fullmatch(r'(?:Project)?PBZ(?:-Win64-(?:Shipping|Development))?\.exe',
                                   row[0], re.I)
               for row in csv.reader(io.StringIO(result.stdout)))


def idle():
    require(not game_running(), 'Close Phantom Blade Zero before building; no files were installed')


def local_file(root, name):
    require(isinstance(name, str) and '\\' not in name and ':' not in name,
            'Invalid bundle path')
    target = (root / name).resolve()
    require(target.is_relative_to(root.resolve()) and target != root.resolve(),
            'Bundle path escapes its directory')
    return target


def validate(recipe, payload_size):
    require(recipe['format'] == 'pbz-voice-recipe-1', 'Unsupported recipe')
    names = [x['name'] for x in recipe['outputs']]
    require(len(names) == len(set(names)) == 3, 'Expected three unique outputs')
    for name in names:
        require(re.fullmatch(r'z_Sui_[A-Za-z0-9_]+\.(pak|utoc|ucas)', name), 'Unsafe output name')
    for chunk in recipe['chunks']:
        source = chunk.get('source')
        if source:
            require(re.fullmatch('[0-9a-f]{24}', source['id']) is not None, 'Invalid source ID')
            require(0 < source['bytes'] <= 2_000_000_000, 'Invalid source size')
        count = 0
        for op in chunk['ops']:
            require(isinstance(op, list) and op, 'Invalid operation')
            if op[0] == 'copy':
                require(len(op) == 3 and source is not None, 'COPY needs a source')
                _, offset, size = op
                require(0 <= offset and 0 < size and offset + size <= source['bytes'], 'COPY out of bounds')
            elif op[0] == 'add':
                require(len(op) == 3, 'Invalid ADD')
                _, offset, size = op
                require(0 <= offset and 0 < size and offset + size <= payload_size, 'ADD out of bounds')
            elif op[0] == 'zero':
                require(len(op) == 2 and 0 < op[1] <= 1048576, 'Invalid ZERO')
                size = op[1]
            else:
                raise FormatError('Unknown recipe operation')
            count += size
        require(count == chunk['bytes'], 'Chunk operation sizes do not match')
        if source and source['bytes'] > STEP:
            require(chunk['ops'][0] == ['copy', 0, source['bytes']], 'Large sources need a full verified prefix')
    ucas = next(x for x in recipe['outputs'] if x['name'].endswith('.ucas'))
    require(sum(c['bytes'] for c in recipe['chunks']) == ucas['bytes'], 'Incorrect UCAS total')


def rebuild(bundle, output, reader, check_idle=idle):
    """Output is promoted only after all sources and all three outputs pass hashes."""
    bundle, output = Path(bundle).resolve(), Path(output).resolve()
    require(not output.exists(), 'Output already exists; choose a new empty output path')
    recipe = json.loads((bundle / 'recipe.json').read_text(encoding='utf-8'))
    payload = local_file(bundle, recipe['payload']['name']).read_bytes()
    require(len(payload) == recipe['payload']['bytes'] and digest(payload) == recipe['payload']['sha256'],
            'Patch payload integrity failure')
    validate(recipe, len(payload))
    # Validate tiny templates before any substantial work.
    for item in recipe['outputs']:
        if 'template' in item:
            p = local_file(bundle, item['template'])
            require(p.stat().st_size == item['bytes'] and file_hash(p) == item['sha256'], 'Template integrity failure')
    check_idle()
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.pbz-voice-building-', dir=output.parent))
    try:
        ucas = next(x for x in recipe['outputs'] if x['name'].endswith('.ucas'))
        with (temp / ucas['name']).open('wb') as target:
            for index, chunk in enumerate(recipe['chunks']):
                check_idle()
                print(f"Chunk {index + 1}/{len(recipe['chunks'])}: {chunk['bytes']:,} bytes", flush=True)
                source = chunk.get('source')
                small = None
                if source:
                    require(reader.chunk(source['id'])[1] == source['bytes'], 'Source chunk size mismatch')
                    if source['bytes'] <= STEP:
                        small = reader.read(source['id'], 0, source['bytes'])
                        require(digest(small) == source['sha256'], 'Source chunk integrity failure')
                h = hashlib.sha256()
                for op_index, op in enumerate(chunk['ops']):
                    if op[0] == 'copy':
                        _, offset, size = op
                        prefix_hash = hashlib.sha256()
                        for start in range(0, size, STEP):
                            n = min(STEP, size - start)
                            data = (small[offset + start:offset + start + n] if small is not None
                                    else reader.read(source['id'], offset + start, n))
                            if start and start % (64 * 1048576) == 0:
                                check_idle()
                            target.write(data); h.update(data); prefix_hash.update(data)
                        if small is None and op_index == 0:
                            require(prefix_hash.hexdigest() == source['sha256'], 'Source bulk integrity failure')
                    else:
                        data = (payload[op[1]:op[1]+op[2]] if op[0] == 'add' else bytes(op[1]))
                        target.write(data); h.update(data)
                require(h.hexdigest() == chunk['sha256'], 'Reconstructed chunk hash mismatch')
        for item in recipe['outputs']:
            if 'template' in item:
                shutil.copyfile(local_file(bundle, item['template']), temp / item['name'])
            p = temp / item['name']
            require(p.stat().st_size == item['bytes'] and file_hash(p) == item['sha256'], 'Final output hash mismatch')
        check_idle()
        # Rename within the same volume. Never merge with an existing output/game directory.
        require(not output.exists(), 'Output appeared during build; refusing overwrite')
        temp.rename(output)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return recipe


def read_key(args):
    if args.key_file:
        value = Path(args.key_file).read_text(encoding='utf-8-sig').strip()
    elif args.bladesmith_config:
        tree = ast.parse(Path(args.bladesmith_config).read_text(encoding='utf-8-sig'))
        values = [ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'PBZ_AES' for t in n.targets)]
        require(len(values) == 1 and isinstance(values[0], str), 'Local config must define one literal PBZ_AES')
        value = values[0]
    else:
        value = os.environ.get('PBZ_AES') or getpass.getpass('Your private game AES key (hidden): ')
    value = value.strip().removeprefix('0x')
    require(re.fullmatch('[0-9a-fA-F]{64}', value) is not None, 'Expected a private 256-bit hex key')
    return bytes.fromhex(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='New directory outside the game; never auto-installs')
    parser.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parents[2] / 'voice-patch')
    parser.add_argument('--oodle-dll', type=Path, required=True, help='Your own trusted oo2core_9_win64.dll')
    private = parser.add_mutually_exclusive_group()
    private.add_argument('--key-file', type=Path)
    private.add_argument('--bladesmith-config', type=Path, help='Read literal PBZ_AES only; never executes the file')
    args = parser.parse_args()
    try:
        idle()
        require(ctypes.sizeof(ctypes.c_void_p) == 8, 'Use 64-bit Python')
        root, out = args.game_root.resolve(), args.output.resolve()
        require(not out.is_relative_to(root) and not root.is_relative_to(out), 'Choose an output outside the game directory')
        recipe = json.loads((args.bundle / 'recipe.json').read_text(encoding='utf-8'))
        appmanifest = root.parent.parent / 'appmanifest_4115450.acf'
        require(appmanifest.is_file() and re.search(r'"buildid"\s+"' + re.escape(recipe['build_id']) + r'"',
                appmanifest.read_text(encoding='utf-8')), 'Only Steam build 26367565 is verified; game build mismatch')
        toc = root / 'ProjectPBZ/Content/Paks/ProjectPBZ-Windows.utoc'
        require(file_hash(toc) == recipe['source_toc_sha256'], 'Original TOC mismatch; do not use this patch on another build')
        # Reduce contention; Oodle is synchronous and this program has one worker.
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
        with RangeReader(toc, key=read_key(args), oodle_dll=args.oodle_dll) as reader:
            rebuild(args.bundle, out, reader)
        print('Verified. Created three MOD files in: ' + str(out))
        print('Nothing was installed. Follow README for manual installation and conflicts.')
    except (FormatError, OSError, ValueError, KeyError, SyntaxError, subprocess.SubprocessError) as exc:
        # Key/config contents are never echoed.
        if isinstance(exc, SyntaxError):
            print('Build failed: invalid local config syntax')
        else:
            print('Build failed: ' + str(exc))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
