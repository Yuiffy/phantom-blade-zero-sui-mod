# 地雷岁 R3 肩部修正

R2 肩部收窄了网格，却沿用了原男体的上臂转轴；袖根又人为转移了大量锁骨权重。该版本已保存在本地 `private/jirai-v1/rejected-r2-shoulder`，不可用于交付。

R3 把真实上臂转轴由 Blender 厘米坐标 `(±19.3434, 7.0304, 150.6286)` 移到 `(±14.5, 6.5, 157)`，每侧移动约 8.02 cm。肘、腕、手指和武器骨的全局静止位置保留。上臂辅助骨沿新肩肘段调整，重新计算精确的局部参考变换。撤销近端上臂向锁骨任意转移的权重，并移除遮缝内衬。

`private/jirai-v1/intended-reference-skeleton.json` 是新的逐骨参考契约。导入与最终验证按该契约逐项比较，不扩大原有误差容限。UE 导入最大局部平移误差约 0.0031 cm。

游戏原 USkeleton 的肩臂采用 AnimationScaled；该模式只缩放动画平移的长度，不能保证新参考平移方向。因此创建仅本角色引用的 `/HuaShira/Mods/SuiPBZ/JiraiRig/Hun_Skin_Skeleton`，让局部平移实际变化的 8 根骨采用 Skeleton 模式。其余 1134 骨的模式、参考骨架 native 数据、曲线和辅助数据保留，并声明原骨架为兼容动画来源。共享原游戏骨架不打包覆盖。

`prepare_shoulder_skeleton.py` 创建隔离编辑工程骨架和原生克隆；`verify_shoulder_skeleton.py` 将原生克隆转换为 IoStore，再通过 CUE4Parse 独立读取模式、兼容来源、骨名及父级。`test_shoulder_retarget_ue.py` 用原参考平移和 0/30/60/90 度人工抬臂轨道执行 UE 动画求值，对比旧设置与本角色设置。它不代表实际游戏动画或游戏引擎测试。

工作顺序：原有 source/bind/finish/motion、prepare_mod/import，接着 prepare_shoulder_animation、prepare_shoulder_skeleton、UE shoulder、verify_shoulder_skeleton，再进行 cloth/test/cook/package/最终独立验证。重新运行 prepare_mod 会恢复隔离原骨架模板，必须重跑 prepare_shoulder_skeleton。打包入口要求当前 FBX 哈希对应的肩部动画测试和原生骨架独立验证均通过。

0/30/60/90 度预览及测量位于 `private/jirai-v1/shoulder-r3-*`。青色标记是实际姿态骨头位置的正面投影，不是手画的理想关节点。90 度近腋下仍有较大表面拉伸，应与游戏实测分开报告。

本轮验证结果：UE 真实 Raw 动画求值中，旧模式的肩肘腕目标误差约 4.557 cm；按骨名对应后，新模式在四档动作中的最大误差约 0.01341 cm，原断言上限仍为 0.03 cm。编辑工程导入后有 226 根骨的顺序与游戏 USkeleton 不同，编辑骨树设置必须解析其实际骨名，不能直接套用原序号；原生克隆保留游戏原序号。此测试没有运行原游戏动作、PostProcess、压缩动画或实际游戏。

本轮可交付审查源文件为 `private/jirai-v1/review-r3-shoulder/Sui_Jirai_Shoulder_R3.blend`，将物理辅助面拆成隐藏对象，保留模型与权重可编辑。最终 MOD 的布料重建、cook、成品容器验证仍须在此基础上完成；此审查文件不能当作已完成的游戏安装包。现有 JK v3 与 Compact v5 的六个安装文件 SHA256 均未变化。
