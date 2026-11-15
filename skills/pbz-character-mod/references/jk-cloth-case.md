# JK 物理实验 v1：离线验证与初步实测反馈

2026-11-15，PBZ build 26367565，官方 UE 5.7.4。本页记录实验候选及有限用户试玩反馈。基于 v11 静态细修的物理 v1 已于 2026-11-15 17:31:28 安装并核验哈希；用户确认白猫与少量马尾摆动，也报告挂饰偶发穿衣、袜口/肤色/手心色差及马尾前倾。公开源与证据见 `models/jk-motion-v1-candidate`、`evidence/jk-motion-v1-offline`。后续 v2 已于 21:18:32 安装，仍待游戏实测。

## 工具链与资源限制

本机 MSVC 14.42 被 UE 明确禁用。用户授权补装后，更新既有 VS 2022 Build Tools 得到实际 MSVC 14.44.35230，安装 Windows SDK 10.0.22621.0 和 .NET Framework SDK 4.8，UBT 构建通过。旧 17.12 安装器 catalog 的 modify 没有真正装入 14.44；以编译日志和实际文件为准，不能只看安装器退出码。SwarmInterface 规则也需要 NetFx SDK。

UBT 使用 `DOTNET_PROCESSOR_COUNT=2`、单 action、BelowNormal；本机设成 1 曾出现长期停滞与内存膨胀。该现象不是所有机器的普遍规则。编辑器辅助插件只用于离线作者工程，不进入 MOD 容器；后台工作沿用用户对线程、游戏控制、屏幕和音频的限制。

## 单分区、资源身份与初始轮廓

资源工厂可能将 `CA_Sui_Charm` 命名成 `CA_Sui_Charm_0`。创建前后比较 asset GUID 集合，要求只新增一个，后续保存真实名称。不要用不明确的前缀匹配。

本机 `UClothingAssetCommon::BindToSkeletalMesh` 不允许同一 cloth LOD 再次映射；手工把多个颜色分区接到同一个 cage，之后 UE rebuild/restore 会丢掉额外分区绑定。实验未继续使用这个失败入口。白猫的六个纯色分区合为一个 albedo/ARM 小图集、一个 render section，再走标准绑定。只绑定身体、漏掉五官会导致动态分离。

粗管状 cage 在曲率变化和端盖处可能触发 normal-offset 投影回退。即使静态顶点与权重完全不变，刚启用布料也会改轮廓。此例马尾初始误差约 1.3 cm；改成位于同一平面的导向网格后接近零，立体渲染发束仍保留。衣摆增加模拟网格细分；最终全身首帧重建最大误差约 0.289 cm。平面导向不是通用最佳解，需检查实际体积和摆动后的表面。

## 验证真正的输出

- `FClothingSimulationInstance` 构造时已做初始化。同步测试每步调用 `FillContextAndPrepareTick(..., false)`、interactor sync、simulate、append；再次将第一步标为初始化会留下空输出。确认世界物理场景、有效 LOD、实际 actor 和非空粒子。
- 分别检查固定粒子、MaxDistance、边长比、有限坐标和静止后实际运动。本例 1,745 粒子，60 Hz/15 cm 和 30 Hz/25 cm 横移加偏航的两组测试通过。这两组输入不同，不能据此声称帧率无关。没有测试提取的游戏骨骼动画。
- 从最终 IoStore 独立读回 cloth GUID、asset index、物理顶点/索引、MaxDistance、序列化 config 和碰撞 PA。保留身体原 gameplay/ragdoll PA，另建 cloth-only kinematic spheres。
- 单 influence 的 `FMeshToMeshVertData` 为 64 字节。GPU cloth mapping buffer 的 index mapping 对每个 render section 都有一条；未绑定分区是全零，不是仅包含五条 cloth 分区。
- 按已安装 `GpuSkinVertexFactory.ush` 用实际模拟位置及法线重建渲染表面，检查首帧和峰值。只看 cage 能动不足以证明渲染发束正常。禁用 cage 的渲染分区必须在 cooked 数据中仍禁用。

最终 57 packages、264 原骨、69,041 可见三角面，含隐藏 cage 共 72,305 三角面；可见位置及蒙皮相对 v11 保持。没有自制 shader 或 Groom。原生父材质和 VT 仍按既有配方核验。

游戏蓝图模板的 CharacterMesh0 使用主动画类和 Hun_Body_Simple；围巾/发带模板含 `PBZ.AllowLegacyClothLeaderPose` tag。用户后来明确确认白猫在游戏中摆动；不能将此推广为五组 cloth、全部动画和性能均验证通过。游戏自定义 CDO 默认值、运行时开关、真实动画碰撞、LOD、瞬移和性能尚待实测。不得以官方 UE 求解成功代替游戏内验证，也不要为试运行自动改共享角色蓝图或游戏配置。

## v2：重力、接触与零时间误差

马尾用更下垂的默认形状、较强重力及更低恢复驱动增强运动。白猫外移约 1.2 cm、上端挂点不变，独立 cloth PA 增加六个局部外套球（总 16 球），保持原身体 gameplay/ragdoll PA。碰撞余量过大时颈部边长比失败；收小余量、8 次迭代/2 子步后仍用原形状范围检查，通过三组测试。不要通过放宽阈值掩盖接触挤压。

除两组横移/偏航外，新增前后移动加俯仰/侧倾，检查惯性方向变化。最终 GPU 映射表面里，60 Hz 横移的马尾最大位移约 7.53 cm。用真实求解输出对参考姿势外套前面做射线间距检查，三组猫表面最小采样间距约 0.161 cm，未采到外套内侧点；这只覆盖组件运动和参考骨架姿势，不是实际战斗动画碰撞证明。源与证据见 `models/jk-motion-v2-candidate`、`evidence/jk-motion-v2-offline`。

增强重力后，第一实际求解帧已积分 1/60 秒，不能当零时间绑定误差。本例分别检查静态映射约 0.285 cm 和第一重力帧约 0.342 cm。零时间重建应按 `ClothingMeshUtils::ComputeAveragedNormals` 从最终物理三角形累加**单位面法线**再归一化，并核对与 GPU 的符号约定；直接用导入后存储的 normals 曾得到错误的约 17 cm 结果。固定旧阈值前先确认测量对象与法线构造是否一致。

袜口、手心等修色按表面与 UV 岛归属生成 mask；Albedo 和线性 ARM 分别处理。v2 输入 PNG、导入像素及最终 VT payload 链已核验，但最终 VT 未独立解码为像素；不可写成最终游戏像素已验证。AI 图片润色若后续使用，要保留 UV 或将局部视图投射回原图集，再检查接缝；本次尚未调用。
