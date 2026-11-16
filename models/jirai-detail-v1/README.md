# 地雷岁 R6 细节修复

此版从用户认可的 R5 母版重新制作，修复左大腿吊带的几何/贴图错位。旧凸起铁扣组件 77 被移除，底层旧黑带、扣子投影和大腿后侧竖向脏色一并清理；新增贴腿黑带 940 与方形金属扣 941。黑带按下方实际皮肤三角面的重心插值传递蒙皮，避免只按高度混合 pelvis/thigh 而在弯腿时悬空。新增表面的朝向也经过核对。

图集另清理颈部烘焙的杂乱项圈碎片，实体项圈、金属饰件使用独立材质。修色按表面/UV 所属生成蒙版；蒙版外像素保持一致，没有整图覆盖。

恢复了收短手臂时被误改的非变形 IK 参考位置，保留 IK/weapon 标记的动画平移。UE 中对五个 IK 标记施加动态平移并读取实际求值结果；这证明标记能够跟随测试动画，尚不能证明游戏中每一种武器都握合正确。

本版保持 R5 头发、裙摆及其三个导向网格的位置和权重；cloth 配方和八个碰撞球沿用 R5。手臂、头颈比例及其他变形骨转轴保持 R5。额外的裙摆/侧发/马尾实验在 `../jirai-secondary-v1`，没有通过动作表面接触检查，不进入本版。

可编辑文件为 `Sui_Jirai_R6_Detail_Editable.blend`，图集内嵌，三个物理导向网格另存为隐藏对象。源哈希见 `source-manifest.json`。没有包含原版魂的可见几何或原版动画库；内容来源和许可见根目录 NOTICE.md。

构建与独立核验记录见 `../../evidence/jirai-r6-detail`。该目录预览均为离线 Blender 渲染；弯腿预览的位置由最终容器的实际蒙皮/GPU cloth 映射与离线 UE 动作求值重建，不是游戏截图。未宣称原有蹲跑穿裙或马尾穿衣已解决。

## 本机流程

需要现有私有 R5/R4 母版、原生模板、合法游戏安装及既有提取工具。不是一键重建环境。保持 Blender 两线程、UE 单线程、隐藏运行和 BelowNormal；不会启动或控制游戏。

1. 修复图集并运行 `run_blender.py author_revision verify_source`。
2. 用研究目录的 `build_pose_tools.py` 构建离线作者插件；`prepare_mod.py` 从其本地编译目录复用，不将 DLL 分发进 MOD。
3. `prepare_pose_contract.py` 生成作者自制动作；`build_candidate.py` 导入、验证、cook、打包，再用独立读取器检查成品。
4. `reconstruct_articulation.py`、`run_blender.py audit_suspender render_suspender_poses` 检查贴腿距离与动作近景。
5. `compose_dual.py` 与当前 JK Motion v5 合并，逐包核对 JK、外观表及其他保留资源。
6. `install-verified.ps1` 仅在游戏退出、候选核验与现有 MOD 哈希均一致时替换模型三件套，保留语音，并保存 R5 回退备份。
