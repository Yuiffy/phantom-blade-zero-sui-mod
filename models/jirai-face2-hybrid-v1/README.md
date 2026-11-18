> 2026-11-18 后续已由 LashLip1 替换安装：睫毛染黑并合并右嘴角分叉。本目录保留原组合检查点和当时安装历史。

# 地雷岁 Face2 + Face3 组合

按用户 2026-11-18 的明确选择制作：Face2 的脸部、眼眶、眉毛、睫毛和嘴型，配 Face3 的独立虹膜/瞳孔与闭合眼白。撤回被用户否定的 Polish1 眼眶变形、新眼睑、眼线与新嘴线。恢复 Face2 原皮肤图集；嘴型、嘴部 UV 和嘴唇颜色完全保留，只对嘴唇局部切线帧作平滑，处理原细小面造成的暗碎块。此处理针对着色，未改变嘴部位置或拓扑。

继续保留 Hairpin1 头发与头饰、Patterns1 图案、R8 裙型、JK 和语音。沿用 Polish1 的光环几何与双侧袖内补面，但不保留其眼睑权重覆盖。仅复制 67 个臂部接缝顶点的完整原生权重；四圈断边检查逐边反向闭合。臂部使用 Face2 图集未占用区域的新肤色小块，不改变任何原 Skin 三角面采样到的像素。

候选 `zzzzzzz_Sui_JiraiFace2Hybrid1_6_P` 仅覆盖地雷岁身体网格、原生 Skin MI 的 Albedo 引用及一张新 8K VT。骨架、分区、布料、物理及 UV1 等保持原生字节。Face2/Face3 Skin MI 的完整导出载荷相同，继续使用原生 shader。

本机顺序：`common.py` 冻结当前安装基线，再执行 `author.py` → `verify_geometry.py preflight` → `patch_native.py` → `cook_texture.py` → `package_candidate.py` → `verify_geometry.py` → `verify_mount.py` → `run_blender.py render_review.py`。作者脚本使用已冻结的私人来源，最终容器由 CUE4Parse、retoc、UAssetAPI 与 native reader 独立读回，再逐项核验指定来源。

`install.py` 默认预检；`--apply` 仅在游戏退出且最终读回、来源保护和离线预览门禁通过时，将旧 Polish1 三件套移到凭据绑定的本地备份，再装新三件套。实际安装读回失败时自动恢复原安装集合。`--rollback` 默认预检，配合 `--apply` 可恢复安装前集合（包含被否定的旧 Polish1，仅供诊断）。不启动或控制游戏，不截图、录屏、清缓存或修改存档。

原资产、图集、离线预览和安装容器留在忽略的 `private/jirai-face2-hybrid-v1/`，公开证据仅文字、数值和哈希。Blender 隐藏、2 线程、低优先级；UE 隐藏、单线程。离线预览使用源 PNG 与读回几何，不复现游戏 shader 或 cooked VT 采样，不能代替游戏内观感与动作测试。当前实际状态见 `../../evidence/jirai-face2-hybrid-v1/README.md`。

2026-11-18 07:23（北京时间）已在游戏退出状态下替换安装，三件套哈希与实际安装载荷独立读回通过。保留其余十八文件和 102 个有效资源的 metadata，七视角离线近景已审阅；回退预检通过，未执行回退。游戏内观感与动态效果待用户复试。
