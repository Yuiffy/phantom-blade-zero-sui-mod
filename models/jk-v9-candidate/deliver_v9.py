"""Local source/model archives and verification notes. Does not install/push."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parent;PBZ=ROOT.parents[2];WORK=PBZ/'variants/new-jk-v9';OUT=ROOT/'delivery';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v=read(WORK/'verification.json');skin=read(WORK/'skin-verification.json');b=read(ROOT/'binding-report.json');scope=read(ROOT/'scope-check.json');build=read(WORK/'build-report.json');motion=read(ROOT/'motion-comparison.json');atlas=read(ROOT/'atlas-repair.json');chain=read(ROOT/'texture-chain.json')
assert v['status']=='independent-container-semantics-passed' and skin['max_weight_error_after_UE_quantization']==0
assert skin['source_contract_sha256']==scope['source_contract_sha256']==sha(ROOT/'source-render-contract.json')
assert b['fbx_sha256']==read(WORK/'source-spec.json')['fbx_sha256']==sha(ROOT/'Sui_JK_Hun_Body.fbx')
assert chain['atlas_sha256']==atlas['output_sha256']==sha(ROOT/'textures/sui-jk-albedo-v9.png')
assert scope['head_neck_shoulders_skirt_leg_geometry_unchanged']
hand8=motion['versions']['v8'];hand9=motion['versions']['v9']
text=f'''# 岁己 JK v9：手指、串色、吊带与饰件

2026-11-15；PBZ build 26367565，成年魂「黑伤（逃亡）」。
状态：**离线候选，未安装、未游戏实测**。当前游戏目录仍是 v8 模型；现有语音包不在本次修改范围，只读核对时为 Reviewed v4，不将它误记为本次更新。

## 变化与依据

- v8 手部随上身收窄，但原游戏手指骨位置没有跟着变化。逐点对照 v6 后发现，手部表面离原来的手指转轴最多偏移约 5.65 cm。这版恢复 2,342 个手部顶点及对应权重，连续恢复 568 个远端袖口顶点；保留 v8 的头、颈、肩与上身比例。
- 同一人工 35° 弯指诊断（不是游戏动画），6,988 条手部边的长度比 p99 从 {hand8['edge_ratio_p99']:.3f} 降至 {hand9['edge_ratio_p99']:.3f}；超过 1.6 倍的边从 {hand8['edges_stretched_over_1_6']} 条降至 {hand9['edges_stretched_over_1_6']} 条。仍有少数局部拉伸，不能据此保证所有武器握持动作。
- 删除原先 100% 跟随骨盆的多余吊带条（72 顶点、140 三角面），在大腿表面恢复单根粉色吊带；没有新布料物理。保留的右侧袜口小装饰重新绑定对应大腿，左袜多余的三颗凸点随饰件重建一起移除。
- 按 UV 所属表面和三维位置修复原 Tripo 图集：裙子粉色、外套背部书包投影、袜口缺色和旧吊带残影。左袜上方整理为深色袜口和粉色横带，扣带背面的旧猫投影一并清理。四像素补边只进入未被其他 UV 表面占用的间隙，防止过滤时旧色渗回。
- 对照原单马尾立绘重建白色分层羽翼和小金心；饰件统一跟随 thigh_l。背带白猫补出眼睛、耳内、腮红、胡须、金心蝴蝶结和连接环；根据预览反馈增大身体、上移蝴蝶结并补齐颈部，消除头身分离。整组猫挂件统一跟随 spine_04，不新增摆动物理。
- 新增一份象牙白纯色叶子材质，仍复用已验证的原生父材质。脸部、头发的布料质感按用户意见保留。

## 核验与限制

- {b['vertices']:,} 源顶点、{b['triangles']:,} 三角面、264 骨、{b['material_slots']} 材质；{v['package_count']} 个包。骨名、父级和 Blender 参考矩阵与 v8 完全一致，原有保留表面的 UV、拓扑和材质索引逐面核对。
- 仅替换指定吊带/饰件，保留表面的位置修改限于手及远端袖口；头、颈、肩、裙子和腿的几何保持 v8。既有裙子/腋下穿插限制仍可能出现。
- 最终 IoStore 已由独立读取器检查原生父材质、VT、外观表、隐藏部件和骨架。没有自制 shader map。最终 {skin['render_vertices']:,} 个 cooked 渲染顶点覆盖所有源顶点，位置最大误差 {skin['max_position_error_cm']:.9f} cm，按安装 UE 的权重量化规则复算后误差为 0。
- 修改图集 {atlas['changed_pixels']:,} / 16,777,216 像素（含 UV 间隙补边）；脸、头发和手部 UV 内像素未改。准备的 RGBA 与编辑图集逐像素一致；导入确认 VT 4096²，新的 cooked VT payload 与最终容器逐字节一致。**没有独立将最终 VT 解码成像素**。
- 预览是 Blender CPU 渲染，弯指、分腿等是人工诊断姿势。没有执行真实游戏动画，没有运行或操作游戏，没有实测性能、所有武器、过场和稳定性。近距离仍可能见到原低分辨率 UV 边缘和原模型局部折痕；这些饰件是参照立绘的手工重建，并非原作者模型。

## 文件、重建与安装

`sui-jk-hun-bound.blend`、`Sui_JK_Hun_Body.fbx` 和 `textures/sui-jk-albedo-v9.png` 是配套候选；FBX 不嵌贴图。源文件 ZIP 内带检查脚本及图集，但不是独立 UE 工程。
`build_candidate.py` 从本机 v6/v8 检查点重建手/袜修复，再重建饰件。它依赖本机目录布局、v6/v8 模型、v8 原始 Tripo 图集、合法提取的游戏模板与骨架、UE 5.7.4、Blender、打包及独立解析工具。`export_atlas_provenance.py` 可从 v8 重新生成图集表面索引，避免依赖手工挑色。
`finish_build.py` 从现有审核 FBX 和图集构建；运行后执行 `verify_texture_chain.py`。脚本保留本机路径约定；复制到仓库不代表能直接运行。`render_ornaments.py`、`review_motion.py` 等生成诊断预览。
本机 `variants/new-jk-v9/install-verified.ps1` 已准备 v8→v9 的哈希核验与备份回退流程，**未执行**。安装须等待用户要求并确认游戏退出，不能把离线候选当已安装。
模型 ZIP 含本机原游戏模板派生数据，仅留本地。公开仓库不收录游戏提取模板、密钥、私人录播、游戏动画或模型容器。原创脚本与文字适用仓库代码许可；角色设计、模型、图集、骨架及派生数据不自动适用 MIT 许可，见根目录 NOTICE。
'''
(ROOT/'RESULT.md').write_text(text,encoding='utf8');(OUT/'README.md').write_text(text,encoding='utf8')
report_names=['binding-report.json','model-audit.json','scope-check.json','motion-comparison.json','atlas-repair.json','texture-chain.json','ornament-refinement.json']
reports={n:ROOT/n for n in report_names};reports.update({n:WORK/n for n in ['verification.json','skin-verification.json']})
common={'README.md':OUT/'README.md',**{'reports/'+n:p for n,p in reports.items()}}
for p in OUT.glob('*.jpg'):common['preview/'+p.name]=p
for n in ['bound-front.png','bound-side.png','bound-back.png','v9-charm-detail.png','v9-wing-detail.png']:
 common['preview/'+n]=ROOT/n
mod=dict(common)
for row in build['container_files']:
 p=PBZ/row['path'];assert sha(p)==row['sha256'];mod['mods/'+p.name]=p
sources=dict(common)
for n in ['sui-jk-hun-bound.blend','Sui_JK_Hun_Body.fbx']:sources['models/'+n]=ROOT/n
sources['textures/sui-jk-albedo-v9.png']=ROOT/'textures/sui-jk-albedo-v9.png'
scripts=['adjust_v9.py','refine_ornaments.py','repair_atlas.py','export_atlas_provenance.py','refresh_texture.py','v7_helpers.py','audit_bound_model.py','verify_scope.py','review_motion.py','measure_motion.py','render_ornaments.py','render_details.py','render_final.py','compare_v9.py','build_candidate.py','finish_build.py','prepare_mod.py','import_mod_ue.py','run_blender.py','run_ue.py','package_mod.py','verify_mod.py','verify_texture_chain.py','offline_tools.py','game-materials.json','deliver_v9.py']
for n in scripts:sources['scripts/'+n]=ROOT/n
def bundle(name,files):
 manifest={n:{'bytes':p.stat().st_size,'sha256':sha(p)} for n,p in files.items()};dest=OUT/name
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
  for n,p in files.items():z.write(p,n)
  z.writestr('SHA256.json',json.dumps(manifest,indent=2))
 with zipfile.ZipFile(dest) as z:
  assert z.testzip() is None
  for n,row in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==row['sha256']
 return {'path':str(dest),'bytes':dest.stat().st_size,'sha256':sha(dest)}
result={'mod':bundle('Sui_JK_HeiShang_v9_ModelOnly.zip',mod),'source':bundle('Sui_JK_Refined_v9_Source.zip',sources),'installed':False,'runtime_tested':False}
(OUT/'delivery-manifest.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
