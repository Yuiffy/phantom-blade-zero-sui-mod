"""Combined JK v4 / wingless Jirai R5. Never installs or runs PBZ."""
from pathlib import Path
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
PBZ = Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
sys.path.insert(0, str(PBZ / 'tools'))
from package_model import relative_package
from build_adult_appearance_variant import fields, rows, row_id, semantic
from preserve_relocated_mesh_payload import restore
import run_native_diagnostic as diag

WORK = REPO / 'private/dual-outfit-v2'
JK = PBZ / 'variants/jk-motion-v4'
JIRAI = REPO / 'private/jirai-proportion-v1/variant'
TABLE = '/Game/PBZContent/DataTable/UI/DT_PBZAppearanceTable'
OLD_BODY = '/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple'
NEW_BODY = '/HuaShira/Mods/SuiPBZ/JiraiOnly/Hun_Body_Simple'
NAME = 'z_Sui_DualOutfit_JK_Jirai_v2_P'
TARGETS = ['Hun_OutFit_Climax', 'Hun_OutFit_Climax_Hat']
MODS = Path('F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods')
EXTS = ['.uasset', '.uexp', '.ubulk', '.uptnl']
SELECTORS = {
    'OutfitBodyItem': ('Sui_Escape_Body', 'Sui_Jirai_Body'),
    'OutfitHatItem': ('Sui_Escape_Hat', 'Sui_Jirai_Hat'),
    'OutfitHairStyleItem': ('Sui_Escape_Hair', 'Sui_Jirai_Hair'),
    'OutfitSequenceHairStyleItem': ('Sui_Escape_Hair_Seq', 'Sui_Jirai_Hair_Seq'),
    'OutfitNeckItem': ('Sui_Escape_Neck', 'Sui_Jirai_Neck'),
    'OutfitMeshBandItem': ('Sui_Escape_Band', 'Sui_Jirai_Band'),
    'OutfitBrowLashCardItem': ('Sui_Escape_BrowLash', 'Sui_Jirai_BrowLash'),
}


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def installed():
    return [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p)}
            for p in sorted(MODS.iterdir()) if p.is_file()]


def run(label, args, env=None):
    logs = WORK / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([str(a) for a in args], capture_output=True,
                          env=env or dict(os.environ, RAYON_NUM_THREADS='1', OMP_NUM_THREADS='1', DOTNET_PROCESSOR_COUNT='2'),
                          creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    output = (proc.stdout + proc.stderr).decode('utf8', errors='replace')
    if env and env.get('PBZX_AES'):
        output = output.replace(env['PBZX_AES'], '[REDACTED]')
    (logs / (label + '.log')).write_text(output, encoding='utf8')
    assert proc.returncode == 0, (label, proc.returncode)
    assert 'panicked' not in output.lower() and 'failed to convert' not in output.lower(), label
    print(label + ': passed', flush=True)
    return output


def replace(value, replacements):
    if isinstance(value, dict):
        return {k: replace(v, replacements) for k, v in value.items()}
    if isinstance(value, list):
        return [replace(v, replacements) for v in value]
    return replacements.get(value, value) if isinstance(value, str) else value


def copyasset(root, package, target_package=None):
    for ext in EXTS:
        src = root / (relative_package(package) + ext)
        dest = WORK / 'legacy' / (relative_package(target_package or package) + ext)
        if src.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def check_table(base, actual):
    a = {row_id(r): r for r in rows(base)}
    b = {row_id(r): r for r in rows(actual)}
    assert len(a) == 61 and len(b) == 68
    for ident, old in a.items():
        if ident not in TARGETS:
            assert semantic(old) == semantic(b[ident]), ident
        else:
            oldf, newf = fields(old), fields(b[ident])
            for key in oldf:
                if key in SELECTORS:
                    assert newf[key]['Value'] == SELECTORS[key][1]
                else:
                    assert semantic(oldf[key]) == semantic(newf[key]), key
    for donor, new_id in SELECTORS.values():
        expected = replace(copy.deepcopy(a[donor]), {OLD_BODY: NEW_BODY})
        expected['Name'] = new_id
        fields(expected)['ItemId']['Value'] = new_id
        assert semantic(expected) == semantic(b[new_id]), new_id
    assert actual['Imports'] == base['Imports']
    return {'rows': len(b), 'new_isolated_component_items': 7,
            'changed_existing_rows': TARGETS,
            'only_changed_existing_fields': list(SELECTORS),
            'jk_default_and_all_other_existing_rows_preserved': True,
            'unlock_rules_icons_text_tags_and_sequence_triggers_preserved': True}


def build():
    WORK.mkdir(parents=True, exist_ok=True)
    assert not (WORK / 'build-report.json').exists(), 'Candidate already built; verify instead'
    write(WORK / 'installed-before.json', installed())
    for root in [JK, JIRAI]:
        assert read(root / 'verification.json')['status'] == 'independent-container-semantics-passed'
        for item in read(root / 'build-report.json')['container_files']:
            assert sha(PBZ / item['path']) == item['sha256']
    # Installed v1 already embeds the independently checked JK v4 unchanged.
    prior = REPO / 'private/dual-outfit-v1-heishang'
    verified = read(prior / 'verification.json')
    assert verified['status'] == 'independent-final-container-verified-runtime-pending'
    assert read(prior / 'runtime-user-feedback.json')
    for item in verified['container_files']:
        assert sha(MODS / item['name']) == item['sha256']
    revision = read(JIRAI.parent / 'revision-report.json')
    assert revision['removed_wing_and_guide_vertices'] > 0 and revision['physics_assets'] == 3
    assert read(JIRAI.parent / 'revision-pose-audit.json')['rear_patch_containment_passed']
    jb, rb = read(JK / 'build-report.json'), read(JIRAI / 'build-report.json')
    common = set(jb['packages']) & set(rb['packages'])
    assert len(common) == 12 and OLD_BODY in common and TABLE in common
    # Shared hidden assets must be identical in every stored file before deduplication.
    shared = sorted(common - {TABLE, OLD_BODY})
    for package in shared:
        for ext in EXTS:
            a = JK / 'legacy' / (relative_package(package) + ext)
            b = JIRAI / 'legacy' / (relative_package(package) + ext)
            assert a.exists() == b.exists()
            if a.exists():
                assert sha(a) == sha(b), (package, ext)
    for package in jb['packages']:
        if package != TABLE:
            copyasset(JK / 'legacy', package)
    for package in rb['packages']:
        if package not in common:
            copyasset(JIRAI / 'legacy', package)

    # Read the ORIGINAL cooked header, not a partial IoStore extraction with lost external imports.
    original_asset = JIRAI / 'legacy' / (relative_package(OLD_BODY) + '.uasset')
    original_json = WORK / 'body-original.json'
    run('body-original', [diag.TOOLS / 'UAssetGUI.exe', 'tojson', original_asset, original_json, 'VER_UE5_6', 'PBZ'])
    original = read(original_json)
    assert original['FolderName'] == OLD_BODY
    edited = replace(original, {OLD_BODY: NEW_BODY})
    assert edited['FolderName'] == NEW_BODY
    assert len(edited['NameMap']) == len(original['NameMap'])
    body_json = WORK / 'body-edited.json'
    write(body_json, edited)
    body_asset = WORK / 'legacy' / (relative_package(NEW_BODY) + '.uasset')
    body_asset.parent.mkdir(parents=True, exist_ok=True)
    run('body-relocate', [diag.TOOLS / 'UAssetGUI.exe', 'fromjson', body_json, body_asset, 'PBZ'])
    generated_json = WORK / 'body-generated.json'
    run('body-generated', [diag.TOOLS / 'UAssetGUI.exe', 'tojson', body_asset, generated_json, 'VER_UE5_6', 'PBZ'])
    preservation = restore(original_asset, body_asset, original, read(generated_json))
    for ext in ['.ubulk', '.uptnl']:
        src = original_asset.with_suffix(ext)
        if src.exists():
            shutil.copy2(src, body_asset.with_suffix(ext))
    assert sha(original_asset.with_suffix('.uexp')) == sha(body_asset.with_suffix('.uexp'))
    del original, edited

    base_json = WORK / 'table-base.json'
    run('table-base', [diag.TOOLS / 'UAssetGUI.exe', 'tojson', JK / 'legacy' / (relative_package(TABLE) + '.uasset'), base_json, 'VER_UE5_6', 'PBZ'])
    base = read(base_json)
    table = copy.deepcopy(base)
    byid = {row_id(r): r for r in rows(table)}
    for selector, (donor, new_id) in SELECTORS.items():
        newrow = replace(copy.deepcopy(byid[donor]), {OLD_BODY: NEW_BODY})
        newrow['Name'] = new_id
        fields(newrow)['ItemId'].update(Value=new_id, IsZero=False)
        rows(table).append(newrow)
        for ident in TARGETS:
            fields(byid[ident])[selector].update(Value=new_id, IsZero=False)
        table['NameMap'].append(new_id)
    if NEW_BODY not in table['NameMap']:
        table['NameMap'].append(NEW_BODY)
    table['NamesReferencedFromExportDataCount'] = len(table['NameMap'])
    table_evidence = check_table(base, table)
    edited_json = WORK / 'table-edited.json'
    write(edited_json, table)
    table_asset = WORK / 'legacy' / (relative_package(TABLE) + '.uasset')
    table_asset.parent.mkdir(parents=True, exist_ok=True)
    run('table-write', [diag.TOOLS / 'UAssetGUI.exe', 'fromjson', edited_json, table_asset, 'PBZ'])
    check_json = WORK / 'table-written.json'
    run('table-read', [diag.TOOLS / 'UAssetGUI.exe', 'tojson', table_asset, check_json, 'VER_UE5_6', 'PBZ'])
    check_table(base, read(check_json))
    packages = sorted(set(jb['packages']) | (set(rb['packages']) - {OLD_BODY}) | {NEW_BODY})
    expected = len(set(jb['packages']) | set(rb['packages'])) + 1
    assert len(packages) == expected
    assert not any('Wing' in p for p in packages if p not in jb['packages'])
    assert {p.relative_to(WORK / 'legacy').as_posix() for p in (WORK / 'legacy').rglob('*.uasset')} == {relative_package(p) + '.uasset' for p in packages}
    container = WORK / 'container'
    container.mkdir(exist_ok=True)
    run('pack', [diag.TOOLS / 'retoc.exe', 'to-zen', '--version', 'UE5_6', '--no-parallel', WORK / 'legacy', container / (NAME + '.utoc')])
    listing = run('list', [diag.TOOLS / 'retoc.exe', 'list', '--path', container / (NAME + '.utoc')])
    actual = {l.split()[-1].replace('\\', '/').removeprefix('../../../') for l in listing.splitlines() if l.strip().endswith('.uasset')}
    assert actual == {relative_package(p) + '.uasset' for p in packages}
    input_dir = WORK / 'extract-input'
    input_dir.mkdir(exist_ok=True)
    for folder, stem in [(container, NAME), (diag.PAKS, 'global')]:
        for ext in ['.utoc', '.ucas']:
            shutil.copy2(folder / (stem + ext), input_dir / (stem + ext))
    final = WORK / 'final-legacy'
    run('extract', [diag.TOOLS / 'retoc.exe', 'to-legacy', '--version', 'UE5_6', '--no-shaders', '--no-parallel', input_dir, final])
    for package in packages:
        for ext in ['.uexp', '.ubulk', '.uptnl']:
            a = WORK / 'legacy' / (relative_package(package) + ext)
            b = final / (relative_package(package) + ext)
            assert a.exists() == b.exists()
            if a.exists():
                assert sha(a) == sha(b), (package, ext)
    final_table = WORK / 'table-final.json'
    run('table-final', [diag.TOOLS / 'UAssetGUI.exe', 'tojson', final / (relative_package(TABLE) + '.uasset'), final_table, 'VER_UE5_6', 'PBZ'])
    check_table(base, read(final_table))
    write(WORK / 'build-report.json', {
        'status': 'packaged-independent-verification-pending', 'packages': packages, 'package_count': len(packages),
        'outfits': {'Hun_OutFit_Default': {'label': '黑伤（逃亡）', 'model': 'JK v4', 'body': OLD_BODY},
                    'Hun_OutFit_Climax': {'label': '黑伤', 'model': '地雷岁 R5 无翅膀比例修正版', 'body': NEW_BODY},
                    'Hun_OutFit_Climax_Hat': {'label': '黑伤（内部无帽变体）', 'model': '地雷岁 R5 无翅膀比例修正版', 'body': NEW_BODY}},
        'source_build_reports': {str(r): sha(r / 'build-report.json') for r in [JK, JIRAI]},
        'shared_identical_hidden_packages': shared, 'body_relocation': preservation, 'table': table_evidence,
        'game_build': '26367565', 'installed': False, 'runtime_tested': False,
        'container_files': [{'name': p.name, 'path': str(p.resolve()), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(container.iterdir())],
    })


def gather():
    report = read(WORK / 'build-report.json')
    env = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1', DOTNET_PROCESSOR_COUNT='2',
               PBZX_GAME='GAME_UE5_7', PBZX_SCRIPT='1', PBZX_AES=diag.private_key(), PBZX_EXTRA=str(WORK / 'container'))
    for mode, packages in [('json', report['packages']), ('skel', [OLD_BODY, NEW_BODY])]:
        out = run('independent-' + mode,
                  [diag.DOTNET, diag.DLL, diag.PAKS, diag.MAPPING, diag.TOOLS / 'oo2core_9_win64.dll', WORK / 'independent' / mode, mode,
                   *[relative_package(p) for p in packages]], env)
        clean = not any(w in out for w in ['Failed to', 'Exception', 'failed to', '[WRN]', '[ERR]'])
        write(WORK / ('independent-' + mode + '.json'), {'exit_code': 0, 'parser_warnings_or_errors': not clean})
        assert clean, mode


if __name__ == '__main__':
    {'build': build, 'gather': gather}[sys.argv[1]]()
