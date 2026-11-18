# 地雷岁 Choker1：完整颈圈与心形扣

按用户的游戏近景反馈，对照本机保存的原立绘及正面参考，修复颈圈被脖子遮住、正面只露出碎片的问题。实际旧颈圈和心形表面仍在，但大部分埋进皮肤。新版本沿实际皮肤三角面求交，重建 32 段连续闭合黑带和浅银心形扣，带有黑色衬边。心形略偏角色左侧，位置、宽度和轮廓参考正面图。

重用原生 Suspender、Buckle 分区中颈部饰件的固定顶点及索引槽。黑带和衬边使用 176 顶点、304 三角面，银色心形使用 50 顶点、96 三角面；余下备用索引槽设为零面积，不渲染。黑带和银心各自闭合；黑色衬边为银心背后的支撑环面。黑带高约 0.78 cm，银心宽约 1.58 cm、高约 1.49 cm。贴图、全部 UV、材质和分区不改动，新增表面通过同分区最近旧颈饰顶点复制原颈部权重，不新增骨骼。

候选 `zzzzzzzzzz_Sui_JiraiChoker1_10_P` 仅覆盖地雷岁身体网格一个 package。原 LashLip1、Face3 眼睛、头饰、服装图案、R8 裙型和布料求解均保留。其他顶点位置、切线帧、索引及未复制的权重逐项保持，原生修改范围之外的完整 native 载荷严格不变。原 `.uasset` 头保留，避免单独提取后的重建头丢失原生 PhysicsAsset 或 PostProcess 引用；最终 CUE4Parse 元数据核对保持原值。

本机顺序：`common.py` 冻结实际安装基线 → `author.py` → `verify_geometry.py preflight` → `patch_native.py` → `package_candidate.py` → `verify_geometry.py` → `verify_mount.py` → 最终读回预览与人工检查 → `install.py` 预检、`install.py --apply`。本轮没有 cook 新材质或纹理。

最终容器由 retoc、UAssetAPI 和 CUE4Parse 独立读回，核对实际位置、索引、切线帧、全部 UV、复制权重、骨架、布料和物理配置。两个目录顺序的覆盖优先级均通过；其余 134 个资源的元数据和完整 `.uexp`、`.ubulk`、`.uptnl` 载荷保持。安装前要求游戏退出，失败自动移出新增三件套恢复原 24 文件集合。`install.py --rollback` 只预检，附加 `--apply` 才撤回新增三件套。

四张离线预览分别检查正面、斜侧、侧面颈部和完整脸部，使用最终容器读回几何、源 PNG 和原颈饰常量材质，不复现游戏 shader 和灯光，也不证明所有动作无穿插。新的游戏内观感与动作效果待用户复试。

原参考、图集、容器、预览及可视编辑母版保存于忽略的 `private/jirai-choker-v1/`。`Choker1_Native_Visual_Editable.blend` 内嵌贴图，提供静态可视网格编辑；权威游戏绑定和完整 native 数据为读回 NPZ、原容器及作者脚本，不把静态 Blender 场景当作完整绑定母版。公开证据仅文字、数值与哈希。当前安装事实见 [验证记录](../../evidence/jirai-choker-v1/README.md)。
