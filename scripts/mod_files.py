"""Verify/install/remove one PBZ container triplet using a local receipt.

Python 3.10+, standard library. Mutations require Windows and --apply.
Does not start, stop, inspect the screen of, or attach to the game.
"""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess


def require(condition, message):
    if not condition:
        raise ValueError(message)


def plain(path):
    for p in [path, *path.parents]:
        if p.exists() or p.is_symlink():
            info = p.lstat()
            require(not p.is_symlink() and not (
                getattr(info, 'st_file_attributes', 0) &
                getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)),
                f'Reparse/symlink path refused: {p}')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def validate_rows(rows):
    require(len(rows) == 3, 'Expected one three-file container')
    names = [r['name'] for r in rows]
    require(len(set(names)) == 3, 'Duplicate file names')
    require(all(re.fullmatch(r'z_Sui_[A-Za-z0-9_]+\.(pak|utoc|ucas)', n) for n in names),
            'Unexpected name or path traversal')
    require(len({Path(n).stem for n in names}) == 1 and
            {Path(n).suffix for n in names} == {'.pak', '.utoc', '.ucas'},
            'Expected matching pak/utoc/ucas names')
    for row in rows:
        require(isinstance(row['bytes'], int) and row['bytes'] > 0, 'Invalid byte size')
        require(re.fullmatch(r'[0-9a-f]{64}', row['sha256']) is not None, 'Invalid SHA256')


def check_file(path, row):
    plain(path)
    require(path.is_file(), f'Missing: {path}')
    require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'],
            f'Content differs: {path}')


def verify(manifest):
    plain(manifest)
    data = read(manifest)
    validate_rows(data['files'])
    require(data['steam_app_id'] == '4115450', 'Wrong application')
    require(re.fullmatch(r'\d+', data['game_build']) is not None, 'Invalid build')
    for row in data['files']:
        check_file(manifest.parent / 'mod' / row['name'], row)
    return data


def stopped():
    require(os.name == 'nt', 'Game installation/removal is supported on Windows only')
    p = subprocess.run(['tasklist.exe', '/FO', 'CSV', '/NH'], check=True,
                       capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    names = [row[0].lower() for row in csv.reader(io.StringIO(p.stdout)) if row]
    require(not any('pbz' in n and n.endswith('.exe') for n in names),
            'PBZ is running; exit it manually before changing MOD files')


def target_for(game_root, data, check_build):
    plain(game_root)
    game_root = game_root.absolute()
    require((game_root / 'ProjectPBZ/Content/Paks').is_dir(), 'Invalid PBZ game directory')
    require((game_root / 'platform/steam/PBZ.exe').is_file(), 'Missing PBZ Steam executable')
    if check_build:
        app = game_root.parent.parent / 'appmanifest_4115450.acf'
        plain(app)
        match = re.search(r'"buildid"\s+"(\d+)"', app.read_text(encoding='utf-8'))
        require(match is not None and match[1] == data['game_build'],
                'Build differs from the tested package; revalidate before installation')
    target = game_root / 'ProjectPBZ/Content/Paks/~mods'
    plain(target)
    return target


def install(manifest, game_root, receipt, apply=False):
    data = verify(manifest)
    target = target_for(game_root, data, True)
    plain(receipt)
    require(not receipt.exists(), 'Receipt already exists; verify or uninstall the existing installation')
    require(not receipt.is_relative_to(target), 'Store receipt outside ~mods')
    for row in data['files']:
        plain(target / row['name'])
        require(not (target / row['name']).exists(), 'Destination already exists; refusing overwrite')
    # Known earlier Sui packages overlap these targets. Other projects may also
    # conflict; the caller must review package paths, not just filenames.
    own_names = {r['name'] for r in data['files']}
    conflicts = [p.name for p in target.glob('z_Sui_*')
                 if p.name not in own_names and p.name not in data.get('compatible_files', [])]
    require(not conflicts, f'Other Sui candidate files present: {conflicts}')
    result = {'variant': data['variant'], 'game_build': data['game_build'],
              'target': str(target), 'files': data['files'], 'applied': apply,
              'runtime_tested': False, 'manifest_sha256': sha(manifest)}
    if not apply:
        return result
    stopped()
    target.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for row in data['files']:
            stopped()
            dest = target / row['name']
            plain(dest)
            with dest.open('xb') as out:
                created.append(dest)
                out.write((manifest.parent / 'mod' / row['name']).read_bytes())
            check_file(dest, row)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        with receipt.open('x', encoding='utf-8') as out:
            out.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    except BaseException:
        for dest in reversed(created):
            plain(dest)
            dest.unlink()
        raise
    return result


def uninstall(manifest, game_root, receipt, apply=False):
    plain(manifest)
    data = read(manifest)
    validate_rows(data['files'])
    target = target_for(game_root, data, False)  # rollback still works after game update
    plain(receipt)
    saved = read(receipt)
    require(saved['applied'] and Path(saved['target']) == target, 'Wrong installation receipt')
    require(saved['manifest_sha256'] == sha(manifest) and saved['files'] == data['files'],
            'Manifest/receipt differs')
    for row in saved['files']:
        # A missing file may be from an interrupted uninstall; never touch any
        # existing file until all remaining hashes have passed.
        if (target / row['name']).exists():
            check_file(target / row['name'], row)
    if apply:
        stopped()
        for row in saved['files']:
            stopped()
            dest = target / row['name']
            plain(dest)
            if dest.exists():
                check_file(dest, row)
                dest.unlink()
        saved.update(applied=False, removed=True)
        receipt.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'removed': apply, 'files': [r['name'] for r in saved['files']]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['verify', 'install', 'uninstall'])
    ap.add_argument('--manifest', required=True, type=Path)
    ap.add_argument('--game-root', type=Path)
    ap.add_argument('--receipt', type=Path)
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    manifest = args.manifest.absolute()
    if args.action == 'verify':
        data = verify(manifest)
        result = {'verified': True, 'variant': data['variant'], 'files': len(data['files'])}
    else:
        require(args.game_root is not None, '--game-root is required')
        receipt = (args.receipt or manifest.with_suffix('.receipt.json')).absolute()
        fn = install if args.action == 'install' else uninstall
        result = fn(manifest, args.game_root.absolute(), receipt, args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
