"""Archive only the independently verified offline candidate; never installs."""
from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parent;PBZ=R.parents[2];W=PBZ/'variants/new-jk-v10';OUT=R/'delivery';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v=read(W/'verification.json');skin=read(W/'skin-verification.json');b=read(R/'binding-report.json');scope=read(R/'scope-check.json');build=read(W/'build-report.json');atlas=read(R/'atlas-repair.json');chain=read(R/'texture-chain.json');motion=read(R/'guard-comparison.json')
assert v['status']=='independent-container-semantics-passed' and skin['max_weight_error_after_UE_quantization']==0
assert skin['source_contract_sha256']==scope['source_contract_sha256']==sha(R/'source-render-contract.json')
assert b['fbx_sha256']==read(W/'source-spec.json')['fbx_sha256']==sha(R/'Sui_JK_Hun_Body.fbx')
assert chain['atlas_sha256']==atlas['output_sha256']==sha(R/'textures/sui-jk-albedo-v10.png')
assert scope['changes_confined_to_right_proximal_component0']
text=f'''# 岁己 JK v10：抬臂时右背部与书包内侧

2026-11-15；PBZ build 26367565，成年魂「黑伤（逃亡）」。
**离线候选，未安装、未游戏实测。** 在已推送的 v9 检查点 ce1a1de 上修改，包含 v9 手指、袜口与猫挂件修复。本次不改语音，不控制游戏。最近一次只读核对安装模型为 v8、语音为 Reviewed v4。

## 本次修改

- 修正右腋下衣身误跟上臂的问题。旧绑定先按袖子来源分区，随后又按离臂章的空间距离覆盖权重，误将邻近衣身顶点赋予最高 100% 上臂权重。抬臂时相邻衣身几乎不动，形成尖锐拉伸。现在按已有袖子/衣身来源字段连续过渡，保留真正的袖子与臂章。
- 同时将误分类的衣身表面恢复到既有娇小躯干轮廓；相对 v9 改动 {scope['moved_vertices']} 个位置和 {scope['weight_changed_vertices']} 个权重，个别错误袖笼点最大回移 {scope['max_position_change_cm']:.2f} cm。没有移动骨骼。
- 按三维表面与 UV 归属清理右背/侧面的白灰、蓝色旧投影。将书包朝向身体的内侧面用干净粉色边缘样本重新补色，去掉混入的衣服和臂章投影。修改 {atlas['changed_pixels']:,} 个图集像素（含 {atlas['padding_pixels']:,} 个未占用 UV 间隙补边像素）。头、手、裙子和 v9 新饰件的 UV 内像素逐项保持不变。
- 保留 v9 的全部拓扑、UV、材质索引和骨架参考矩阵。头、手、腿、裙子、书包和饰件的位置与权重不变；没有新增布料或碰撞系统。

## 验证与限制

两组人工抬臂姿势中，同一区域的 11,096 条边，前举 p99 拉伸 {motion['before'][0]['p99']:.3f} → {motion['after'][0]['p99']:.3f}，高举 {motion['before'][1]['p99']:.3f} → {motion['after'][1]['p99']:.3f}；超过 1.6 倍的边分别 {motion['before'][0]['over_1_6']} → {motion['after'][0]['over_1_6']}、{motion['before'][1]['over_1_6']} → {motion['after'][1]['over_1_6']}。各版用自己的静止边长作分母，几何和权重都变了，不能将改善单独归因于权重。

这些是 Blender 诊断姿势，**不是提取的游戏防御动画**。仍有少数折痕/拉伸，尚不能保证长柄防御或所有动作无穿插。截图里的白色不能仅凭颜色认定为独立白衬衣几何；本次处理已确认的绑定问题与烘焙串色，实际是否还有层间穿模须游戏复核。

{b['vertices']:,} 源顶点、{b['triangles']:,} 三角面、264 骨、10 材质、{v['package_count']} 个包，无自制 shader。最终 IoStore 已由独立读取器核对原生父材质、虚拟纹理、外观表与骨架。{skin['render_vertices']:,} 个 cooked 渲染顶点覆盖全部源顶点，位置最大误差 {skin['max_position_error_cm']:.9f} cm；按 UE 权重量化复算后误差为 0。编辑图集与准备 RGBA 逐像素一致，cooked VT payload 与最终容器逐字节一致；未独立将最终 VT 解码成像素。

## 文件和重建

模型文件为 `sui-jk-hun-bound.blend`、`Sui_JK_Hun_Body.fbx`、`textures/sui-jk-albedo-v10.png`；Blend 内嵌最终图集。FBX 不嵌贴图，沿用原 v9 贴图文件名引用，外部导入须手动指定 v10 PNG；游戏构建按 `prepare_mod.py` 显式使用 v10 图集。
`build_candidate.py` 依赖同级 v9 检查点及随附的 `sleeve-source-field.npy`（v8 编号下的已创作袖子来源字段，按 `v8_vertex_index` 映射；不是独立真值）。本机脚本目录名为 `tripo-refine-v9`/`tripo-refine-v10`，仓库目录名不同，运行时须调整根目录/基线路径。公开源文件不是开箱即用 UE 工程。
`finish_build.py` 从现有审核 FBX/图集继续；随后运行 `verify_texture_chain.py`。构建依赖本机合法取得的游戏模板、UE 5.7.4、Blender 和打包/解析工具。Blender CPU 双线程、低优先级；UE commandlet 单线程，不修改全局配置。
`review_guard.py`、`render_bag.py`、`compare_v10.py` 生成离线预览与比较。模型安装包含游戏模板派生数据，仅留本地；不公开原游戏容器、提取模板、密钥、动画或私人音源。

本机 `variants/new-jk-v10/install-verified.ps1` 准备 v8→v10 的校验、备份与回退，**未执行**。安装需要用户要求并确认游戏退出。角色、模型、图集及游戏骨架派生数据不适用代码 MIT 许可，见仓库 NOTICE.md。v9 和原始 ZIP 均保留。
'''
(R/'RESULT.md').write_text(text,encoding='utf8');(OUT/'README.md').write_text(text,encoding='utf8')
scripts=['adjust_v10.py','repair_atlas_v10.py','refresh_texture.py','v7_helpers.py','audit_bound_model.py','verify_scope.py','review_guard.py','render_bag.py','render_final.py','render_details.py','compare_v10.py','build_candidate.py','finish_build.py','prepare_mod.py','import_mod_ue.py','run_blender.py','run_ue.py','package_mod.py','verify_mod.py','verify_texture_chain.py','offline_tools.py','game-materials.json','deliver_v10.py','publish_v10_sources.py']
reports=['binding-report.json','model-audit.json','scope-check.json','guard-comparison.json','atlas-repair.json','texture-chain.json']
common={'README.md':OUT/'README.md',**{'reports/'+n:R/n for n in reports},**{'reports/'+n:W/n for n in ['verification.json','skin-verification.json']}}
for n in ['guard-after-high.png','guard-after-high-side.png','guard-after-forward.png','bag-inner-v9.png','bag-inner-v10.png','bound-front.png','bound-side.png','bound-back.png']:common['preview/'+n]=R/n
common['preview/guard-and-bag-v9-v10.jpg']=OUT/'guard-and-bag-v9-v10.jpg'
mod=dict(common)
for row in build['container_files']:
 p=PBZ/row['path'];assert sha(p)==row['sha256'];mod['mods/'+p.name]=p
source=dict(common)
for n in ['sui-jk-hun-bound.blend','Sui_JK_Hun_Body.fbx','sleeve-source-field.npy']:source['models/'+n]=R/n
source['textures/sui-jk-albedo-v10.png']=R/'textures/sui-jk-albedo-v10.png'
for n in scripts:source['scripts/'+n]=R/n
def bundle(name,files):
 manifest={n:{'bytes':p.stat().st_size,'sha256':sha(p)} for n,p in files.items()};dest=OUT/name
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
  for n,p in files.items():z.write(p,n)
  z.writestr('SHA256.json',json.dumps(manifest,indent=2))
 with zipfile.ZipFile(dest) as z:
  assert z.testzip() is None
  for n,row in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==row['sha256']
 return {'path':str(dest),'bytes':dest.stat().st_size,'sha256':sha(dest)}
result={'model':bundle('Sui_JK_HeiShang_v10_ModelOnly.zip',mod),'source':bundle('Sui_JK_Refined_v10_Source.zip',source),'installed':False,'runtime_tested':False}
(OUT/'delivery-manifest.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
