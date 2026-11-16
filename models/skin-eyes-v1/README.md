# 皮肤与眼白修复候选 v1

基于当前安装的地雷岁 R6 Detail 与 JK Motion v5，在独立目录制作。最终状态见 `../../evidence/skin-eyes-v1/summary.json`。构建成功、离线预览、实际安装和游戏实测分别记录，不能互相代替。

2026-11-16 22:18（UTC+8）已在游戏退出后安装并核验文件哈希。最终双服装容器 99 包，语音不变，原 R6 模型三件套保存在 `private/skin-eyes-v1/dual/backup-20261116-221810-173`。游戏实际皮肤光照与新眼白效果仍待反馈。

原来所有表面都继承 `MI_ZeroHun_Cloth_02_b`。原生父材质第二层启用了 `T_Fabric_N`、`T_Fabric_C` 与 `Use DetailNormal`，所以只覆盖第 0 层 `Normal` 仍会出现布偶织纹。此版地雷岁皮肤和手继承游戏原生 `MI_ZeroHun_Head_b` 及其皮肤着色器，替换自身 Albedo、Normal、Mix、SCMT 与微法线，保留原生散射配置；不生成自制 shader 或静态排列。

虹膜拆到独立材质，两只新眼白是闭合的椭球表面，完全绑定原有 head 骨。原有 31516 个顶点的位置、UV 和权重逐项保留。头发、皮革与金属改用原生双面通用受光材质，衣服保留较轻的织物细节。JK 的残余主图集同时覆盖多种表面，因此先用平滑的通用受光材质去织纹，不宣称 JK 已有独立的皮肤材质分区；JK 网格和布料原生载荷不变。

可编辑母版在本地 `private/skin-eyes-v1/sui-jirai-motion.blend`，FBX 和来源哈希在同目录。图集沿用 R6 修整版。原游戏模板、shader、工具、密钥和中间容器只留本地。角色、图集及游戏派生内容沿用根目录 NOTICE.md 的许可边界，不适用脚本的 MIT 许可。

`reuse_r6.py` 只在内存中把既有 R6 脚本重定位到本候选；R6 和其他正在制作的候选不被修改。`prepare_candidate.py` 生成小型入口脚本，再通过同样的导入、骨架适配、三组真实 Chaos 测试、新进程重载、cook 和独立最终容器读回流程验证。

本机流程需要已准备的合法模板、Blender、UE、提取工具与 R6/JK5 基线，不是一键重建环境。Blender 保持两线程，UE 单线程，后台隐藏并采用低优先级，不操作游戏进程。

1. 运行 `prepare_candidate.py`。
2. 隐藏运行 Blender 的 `inspect_eyes.py` 和 `author_eyes.py`，再用 `render_eyes.py` 检查正面及斜侧近景。
3. 运行 `build_candidate.py`，再运行 `verify_eyes.py`。后者直接检查最终 cooked 三角面、量化权重、闭合眼白和正面遮挡射线。
4. 运行 `compose_dual.py`，合并为一个完整双服装三件套。独立解析每个包，核验保留内容、材质父级、层索引、纹理和所有标量；再用 `verify_material_contract.py` 检查原生父级纹理约定与最终 112 条纹理绑定，包括 SCMT 厚度通道。
5. 游戏退出后才可运行 `install-verified.ps1`。脚本核验当前安装快照，备份原模型三件套，替换后再次验证哈希并保留语音；若当前模型已换成其他候选则拒绝覆盖。

近景 PNG 是 Blender 离线预览，用于检查眼白几何。它不模拟 PBZ 原生皮肤着色器；最终皮肤、光泽、散射和实际游戏角度需要游戏中确认。本候选不包含另一项 R7 裙摆研究的修改。
