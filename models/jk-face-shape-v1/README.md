# JK FaceShape1：保留五官的脸型修整

2026-11-17 23:32（北京时间）已安装，实际安装集合独立读回和回退预检通过；游戏内观感尚待反馈。

参考当前地雷岁下半脸较收敛的轮廓，对 JK 原有脸型作渐进式收窄。只修改原 JK 连通头部表面的 947 个 native 顶点位置和切线帧；沿眼周和嘴周平滑减弱调整，保留 JK 的眼睛、嘴唇、鼻尖和侧面中心轮廓，没有复制地雷岁 Face3 的眼睛、嘴巴或贴图。

下颌高度段（169–171 cm、正面表面）的横向宽度由 12.703 降至 11.501 cm，约收窄 9.5%；上部轮廓高度段（180–183 cm）由 20.681 降至 19.623 cm，约收窄 5.1%。这些是固定范围的几何宽度，不代表整张脸统一缩小。脸颊到眼周使用较缓的过渡，避免保持眼睛位置时将脸颊收出突然的凹陷。颈部和头发未变。

叠加包 `zzzzzz_Sui_JKFaceShape1_P` 只含 `/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple`。基于当前 R8 双服装安装的 JK 原始 native 载荷，保留 native header、全部 UV、索引、量化权重、264 骨参考、布料映射、物理资源及其他 export 字节。所有既有有效资源载荷分别核对，地雷岁、Patterns1 图案及语音均保留。现有 Release 未更新。

本地作者输入、原始游戏派生资源、容器、带完整绑定和内嵌贴图的 `Sui_JK_FaceShape1_Bound.blend`、成品近景与同机位对比图均留在忽略的 `private/jk-face-shape-v1/`。公开证据只含数值和哈希。代码许可不覆盖角色、美术或原游戏资产。

## 裙子本轮保留

用户允许暂不修改裙子，本轮没有替换 JK 裙摆或声称修复深蹲穿模。已核对原有 288 粒子裙摆及成品映射：实际 MaxDistance 最大约 0.627 cm，名义上限为 0.65 cm；重力比例 0.15，弯曲刚度 0.95。活动范围很小，限制了碰撞避让空间；这支持“当前自由度不足”的诊断，不能据此证明实机穿模的唯一原因。

后续裙摆实验需同时检查固定区、活动范围、专属大腿碰撞和动作后回落。可以借鉴地雷岁 R8 的连续测试与 GPU 表面重建方法，但不能直接照搬 35% 可见混合或扩大裙子掩盖交线。旧 JK helper 的每帧重置问题使旧运动测试不足以证明连续稳定性；本轮没有对新裙摆参数进行求解，也未增加布料效果。

## 本机流程与验证边界

依赖已存在的私人 JK Motion v5、R8、Patterns1 输入与本机工具，不能从公开目录独立重建。

1. `author_shape.py` 冻结已安装十五文件清单，读取原 JK native 表面，限定组件和五官保护区并保存位置及切线变换。
2. `package_candidate.py` 只修改验证过的 native 位置/切线字节，白名单打包一个 mesh；retoc 重新提取，UAssetAPI 独立解析网格，再用 CUE4Parse 检查两种目录顺序。其他 131 个有效 package 的 export/bulk 载荷保持。
3. `verify_geometry.py` 检查五官/其他组件、UV、索引、切线符号和接缝。受影响三角面没有翻面，边长比约 0.799–1.152。
4. `run_blender.py render_review.py` 从成品读回表面渲染正面、斜侧、侧面；`make_comparison.py` 生成对比。`final-preview/render-manifest.json` 将各张图与实际 native 输入哈希关联，人工审看后保存 `visual-review.json`。
5. `run_blender.py save_editable.py` 把同一位移带回完整 JK 母版，保留原绑定、拓扑、UV、权重与物理导向网格，内嵌当前 Patterns1 图集。
6. `install.py` 默认只读检查；`--apply` 仅在游戏退出、基线和全部证据匹配时添加本轮三件套。`package_candidate.py installed` 重新读取实际安装集合。`install.py --rollback` 默认核验，加 `--apply` 才只移出本轮三件套；其他安装变动会令回退停止。
7. `record_skirt_diagnosis.py`、`collect_evidence.py` 保存裙摆限制与纯数值证据。

Blender 隐藏、2 线程、低优先级；原生读取工具单线程或受限线程、隐藏运行。本轮不会启动、操作或结束游戏，不截图/录屏，不改存档或缓存。近景使用当前源 PNG 和 Blender 着色，不能等同于游戏 shader、压缩采样、灯光和实际动作；游戏内观感仍待用户反馈。
