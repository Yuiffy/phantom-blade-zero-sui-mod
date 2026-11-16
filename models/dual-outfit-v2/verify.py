"""Validate final IoStore with independent CUE4Parse against both verified sources."""
import json
import shutil
from pathlib import Path
from build import (WORK, JK, JIRAI, TABLE, OLD_BODY, NEW_BODY, NAME, TARGETS,
                   SELECTORS, EXTS, MODS, read, write, sha, installed, relative_package)


def relocated(value):
    if isinstance(value, dict):
        return {k: relocated(v) for k, v in value.items()}
    if isinstance(value, list):
        return [relocated(v) for v in value]
    return value.replace(OLD_BODY, NEW_BODY) if isinstance(value, str) else value


def getdocs(root, package):
    return read(root / 'independent/json' / (relative_package(package) + '.json'))


def verify():
    b = read(WORK / 'build-report.json')
    jk_packages = set(read(JK / 'build-report.json')['packages'])
    for mode in ['json', 'skel']:
        result = read(WORK / ('independent-' + mode + '.json'))
        assert result['exit_code'] == 0 and not result['parser_warnings_or_errors']
    for f in b['container_files']:
        assert sha(Path(f['path'])) == f['sha256']
    docs = {}
    unchanged = []
    for package in b['packages']:
        doc = getdocs(WORK, package)
        assert doc and not any(e['Type'] == 'Material' for e in doc), package
        docs[package] = doc
        if package == TABLE:
            continue
        root = JK if package in jk_packages else JIRAI
        source_package = OLD_BODY if package == NEW_BODY else package
        expected = getdocs(root, source_package)
        if package == NEW_BODY:
            expected = relocated(expected)
        assert doc == expected, ('final semantic source mismatch', package)
        for ext in EXTS[1:]:
            source = root / 'legacy' / (relative_package(source_package) + ext)
            final = WORK / 'final-legacy' / (relative_package(package) + ext)
            assert source.exists() == final.exists(), (package, ext)
            if source.exists():
                assert sha(source) == sha(final), (package, ext)
        unchanged.append(package)

    # Verify both actual selector chains, every other row, and new component types.
    baseline = getdocs(JK, TABLE)[0]['Rows']
    actual = docs[TABLE][0]['Rows']
    assert len(baseline) == 61 and len(actual) == 68
    for ident, row in baseline.items():
        if ident in TARGETS:
            expected = dict(row)
            expected.update({field: ids[1] for field, ids in SELECTORS.items()})
            assert actual[ident] == expected, ident
        else:
            assert actual[ident] == row, ident
    for donor, new_id in SELECTORS.values():
        expected = relocated(baseline[donor])
        expected['ItemId'] = new_id
        assert actual[new_id] == expected, new_id
    routes = []
    for ident, body in [('Hun_OutFit_Default', OLD_BODY), *[(i, NEW_BODY) for i in TARGETS]]:
        row = actual[ident]
        bodyitem = actual[row['OutfitBodyItem']]
        assert bodyitem['BodyMeshAsset']['AssetPathName'] == body + '.Hun_Body_Simple'
        usedparts = []
        for field in SELECTORS:
            part = actual[row[field]]
            assert not any(part[k] for k in ['BodyClothDataArray', 'GroomDataArray', 'HeadClothDataArray', 'HeadClothDataArrayHatHidden'])
            assert not part['GroomPhysicsAsset']['AssetPathName']
            usedparts.append(row[field])
        routes.append({'outfit': ident, 'body': body, 'parts': usedparts})
    assert actual['Hun_OutFit_GuYou'] == baseline['Hun_OutFit_GuYou']

    bodies = []
    material_sets = []
    for body, root, skeleton, physics in [
        (OLD_BODY, JK, '/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton', '/HuaShira/Mods/SuiPBZ/Physics/PA_Sui_ClothCollision'),
        (NEW_BODY, JIRAI, '/HuaShira/Mods/SuiPBZ/JiraiRig/Hun_Skin_Skeleton', '/HuaShira/Mods/SuiPBZ/Physics/PA_Jirai_ClothCollision'),
    ]:
        mesh = next(e for e in docs[body] if e['Type'] == 'SkeletalMesh')
        p = mesh['Properties']
        for key, path in [('Skeleton', skeleton), ('PhysicsAsset', '/HuaShira/Characters/Hero/Hero_Hun/PA_Hun'),
                          ('PostProcessAnimBlueprint', '/HuaShira/Characters/Hero/Hero_Hun/Rig/ABP_Hun_PostProcess')]:
            assert p[key]['ObjectPath'].rsplit('.', 1)[0] == path, (body, key)
        cloths = [e for e in docs[body] if e['Type'] == 'ClothingAssetCommon']
        assert len(cloths) == (5 if body == OLD_BODY else 3)
        if body == NEW_BODY:
            assert all('Wing' not in e['Name'] for e in docs[body])
        for cloth in cloths:
            assert cloth['Properties']['PhysicsAsset']['ObjectPath'].rsplit('.', 1)[0] == physics
        suffix = '.Hun_Body_Simple.skel.json'
        skel = read(WORK / 'independent/skel' / (relative_package(body) + suffix))
        original = read(root / 'independent/skel' / (relative_package(OLD_BODY) + suffix))
        assert skel == original, ('reference skeleton or render data changed', body)
        assert len(skel['bones']) == 264
        triangles = sum(s['NumTriangles'] for s in skel['lods'][0]['sections'])
        assert triangles == read(root / 'build-report.json')['triangles']
        materials = {m['mat'] for m in skel['materials']}
        assert None not in materials
        material_sets.append(materials)
        bodies.append({'body': body, 'bones': 264, 'triangles': triangles, 'cloth_assets': [e['Name'] for e in cloths],
                       'skeleton': skeleton, 'cloth_collision': physics,
                       'reference_skeleton_render_data_and_physics_unchanged': True})
    assert not material_sets[0] & material_sets[1], 'Bodies share a visible material unexpectedly'
    assert installed() == read(WORK / 'installed-before.json'), 'Installed state changed during offline build'
    result = {'status': 'independent-final-container-verified-runtime-pending', 'package_count': len(docs),
              'outfits': b['outfits'], 'selector_chains': routes, 'bodies': bodies,
              'source_equivalent_asset_semantics_and_payloads': len(unchanged),
              'one_combined_appearance_table': True, 'other_outfits_unchanged': True,
              'installed_files_unchanged': True, 'installed': False, 'runtime_tested': False,
              'container_files': b['container_files']}
    write(WORK / 'verification.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ['container_files', 'selector_chains', 'bodies']}, ensure_ascii=False))
    delivery = WORK / 'delivery'
    delivery.mkdir(exist_ok=True)
    for item in b['container_files']:
        shutil.copy2(item['path'], delivery / item['name'])
    write(delivery / 'verification.json', result)
    write(delivery / 'installation-plan.json', {
        'installed': False, 'target': str(MODS), 'replace_model_files': [f['name'] for f in installed() if f['name'].startswith('z_Sui_DualOutfit_JK_Jirai_v1_P.')],
        'add_files': [f['name'] for f in b['container_files']],
        'voice_files_unchanged': True, 'no_unlock_or_save_edits': True,
        'do_not_stack_with_old_jk_or_jirai_model_pack': True})
    (delivery / '说明.txt').write_text(
        '双服装共存修正版：黑伤（逃亡）= JK 岁己 v4；黑伤 = 地雷岁 R5。\n'
        '已完成最终容器独立读回，尚未安装、尚未游戏实测。故友及其他外观保持原样。\n'
        '这一个模型包包含两套模型和一份合并外观表，不能再叠装旧 JK/地雷岁模型包。\n'
        '安装须先退出游戏，备份并移出现用双服装 v1 三件套，再复制这里同名前缀的 pak/utoc/ucas 三件套。独立语音包保留。\n'
        '地雷岁缩短手臂与脖子，改善手部关节权重、肩袖遮挡和腿根穿裙；移除棉花翅膀及对应物理。双马尾与裙摆物理保留。JK v4 的几何和动态数据保持原样。\n'
        '黑伤的内部无帽变体也使用地雷岁。服装名称、图标、解锁条件和过场选择条件不改，不负责解锁服装。\n'
        '游戏内需检查双向换装、预览、战斗、过场，以及地雷岁高角度抬臂的腋下拉伸。共享语音仍适用于成年魂。\n', encoding='utf8')
    write(delivery / 'manifest.json', {'status': result['status'], 'installed': False,
          'files': [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(delivery.iterdir()) if p.name != 'manifest.json']})


if __name__ == '__main__':
    verify()
