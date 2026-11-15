# JK 后续加分项：材质与动态部件

2026-11-15。当前安装 [物理细修 v2](../models/jk-motion-v2-candidate/README.md)，21:18:32 核验哈希，尚未游戏实测。首个 [物理实验 v1](../models/jk-motion-v1-candidate/README.md) 已获用户对白猫摆动及少量马尾运动的确认，也收到挂饰偶发穿衣、袜口/皮肤/手心色差、扁光环和马尾前倾反馈。v2 针对这些反馈修改，v1 已本地备份。此次实际保留的独立语音是 Compact v5；早期记录中的 Reviewed v4 不代表当前安装事实。反馈不等于全面稳定性或全部动作验证通过。

## 目标与顺序

| 部位 | 外观目标 | 动态目标与首选实验 |
| --- | --- | --- |
| 单马尾 | 保留侧单马尾和固定发根，按新反馈减少下段默认前倾，做发束方向、高光和粗糙度区分 | 当前用受限平面导向布料；增强重力和惯性，保留发束轮廓，验证游戏实际效果后再考虑 Groom |
| 背带白猫/金属连接件 | 白猫偏柔软、连接环偏金属，保留 v9 头身连接与比例 | 用短骨链或受限摆锤，挂点固定；猫本体保持形状，限制摆角和与胸口/背带的穿插 |
| 裙子 | 布料粗糙度与褶皱细节 | 腰部固定、下摆有限跟随；遵守用户“贴腿、不要翘太高”的要求，保留安全内衬；先检验既有裙骨驱动，再决定是否使用受限 Chaos 布料 |
| 外套 | 针织或织物质感，清楚区分衬衣 | 先保持肩颈和袖笼的已修正蒙皮，只尝试下摆/袖口局部柔动，避免再次拉坏肩背 |
| 书包和背带 | 按参考细分包身织物、背带与五金；具体材质以参考为准 | 包体保持容量与轮廓，允许小幅惯性；背带保留承重点，避免整个包像裙子一样塌陷或卷曲 |

首轮优先单马尾和小挂饰，分别验证；随后裙摆、外套下摆，最后包体和背带。材质分区可以单独先实验，但不混入尚待确认的 v10 基础修复包。

## 已确认的本地条件

- v10 沿用 264 骨身体参考架。`source-render-contract.json` 中可见 `bns_skirt_*` 等裙部骨，未见名称包含 hair/pony 的骨。这仅说明当前身体的骨名清单，不证明游戏一定会动态驱动裙骨，也不证明角色其他部件没有发骨。
- 当前外观表构建脚本 `build_escape_scoped_variant.py::edit_table` 会清空新增私有部件行中的 `BodyClothDataArray`、`GroomDataArray`、`HeadClothDataArray`、`HeadClothDataArrayHatHidden`，并清空 `GroomPhysicsAsset`。因此不能只给当前身体增加一条新骨链，就宣称已经接入游戏动态。
- 当前图集主体共享 `MI_JK_Base`，粗糙度约 0.85；头发、皮肤、衣物和包身需要按真实表面拆分材质归属，不能全局降低粗糙度。`MI_JK_HairGroove` 仅是现有装饰槽，不代表头发主体已使用头发着色模型。
- 此游戏的自定义材质 ABI 曾导致加载/换装闪退；继续优先复用经确认的原生父材质。Groom、ChaosCloth、Skeleton、PhysicsAsset、AnimBP 分别核验类型和引用，不能互相冒充。
- `rigid-accessories-v1/ue/readback-CA_Hun_*.json` 属于早期替身实验的骨架读回；文件名含 CA 不证明其中数据是原版 ChaosClothAsset。不能将该目录当作原生动态能力的证据。

## 第一轮需要查清的接口

1. 沿真实外观表和原版资产追踪目标部件的类型、Skeleton、物理配置、动画或 post-process 驱动，以及普通/过场分支。保留完整引用链，再选择原生可用入口。
2. 若复用原有裙/发骨，先核对骨名、参考变换、驱动范围和空间位置；原长袍或原发束的运动参数不能直接视为适合 JK 短裙/侧马尾。不要为了贴合附件移动主角色武器/手指参考架。
3. 如果需要新增骨链，优先独立附件组件与独立驱动路径，验证从服装私有选择项可接入；避免修改共享角色蓝图影响其他外观。若无法通过已有入口接入，明确记录限制，再决定方案。
4. 材质负责表面观感；摆动需要实际骨骼/布料/毛发模拟及其运行入口。AnimDynamics 的约束近似与 RigidBody/物理资产碰撞不是同一机制，不能将轻量弹簧当作已具备身体碰撞。
5. Groom 并非侧马尾摆动的必选路线。先试符合二次元发束轮廓的低成本网格方案；是否切换 Groom 取决于实际兼容、外观收益及性能。

## 验证边界

2026-11-15 补充：v11 静态细修已增加真实支撑面上的吊点，并以支撑三角面的重心权重连接挂环、猫本体。近景和人工转身检查保留在 `evidence/jk-v11-offline`。这一步只修几何与绑定，不代表已具备摆动。

用户授权补装后，实际 MSVC 14.44.35230、Windows SDK 10.0.22621.0、NetFx SDK 4.8 已安装并经 UBT 单 action 构建验证，没有重启或绕过禁用规则。五组 skeletal legacy cloth 已在独立工程完成导入、作者绑定、真实同步 Chaos 求解与 cook；1,745 粒子，原 264 骨和 v11 可见几何/权重保留。最终 57 包已独立核验 cloth 资产、GPU 映射、碰撞体、蒙皮、原生 MI 和 VT payload。编辑器辅助插件不进入游戏容器。

两组参考姿势下的横移/偏航模拟通过；实际 60 Hz 求解结果重建表面最大位移约为马尾 3.45 cm、白猫 1.95 cm、裙摆 0.19 cm、衣摆 0.51 cm、包体 0.28 cm。没有新增骨链、Groom 或自制 shader。粗管状马尾 cage 的启用瞬间变形已通过平面导向改进，六色白猫分区改为单图集分区以避免重建后绑定丢失。见 [验证摘要](../evidence/jk-motion-v1-offline/candidate-summary.json) 和 [skill 案例](../skills/pbz-character-mod/references/jk-cloth-case.md)。

本机保留独立物理测试包、v11 静态包及 v10 回退材料；物理包已安装，用户初步试玩反馈见安装摘要。两组测试输入不同，不能据此宣称帧率无关。用户确认白猫与少量马尾摆动；未序列化的类默认值、其他部位、真实动画与碰撞仍未全面验证。

游戏实测由用户方便时完成：原地/跑停/转身、跳攻、长柄防御、闪避/蹲伏、换装、读档和过场。重点看头发穿胸背/武器、挂饰离开挂点、包体塌陷、裙摆上翻、瞬移后爆振、LOD 切换与性能。当前没有宣称这些测试已通过。

准备研究不安装 MOD、不控制游戏，不启动 TTS、桌面采集或重型模拟。实际构建继续采用已约定的后台低优先级与线程限制。

## v2 已完成的修正与验证

袜口和裸露大腿按实际表面/UV 归属补色，清理手心的烘焙暗色并分开控制皮肤粗糙度。光环中心线约 31.19 × 29.63 cm，保留朝向，叶饰刚性移动。马尾根部不变，下段默认后移并增强重力；白猫身体向外让开约 1.2 cm，保留背带挂点，cloth-only 碰撞体新增六个局部外套球。

三组离线参考姿势测试包括横移/偏航及前后/俯仰/侧倾。最终 cooked GPU 映射重建的马尾最大位移约 7.53 cm；猫与外套前表面最小采样间距约 0.161 cm。检查没有使用提取的真实游戏骨骼动画，不能保证所有战斗动作无穿模。骨架、全部源蒙皮和可见三角面数量保留。

零时间绑定映射误差约 0.285 cm，第一真实重力积分帧位移约 0.342 cm，分别核验。独立读回最终容器、cloth/config/碰撞体、蒙皮、原生父材质和 VT payload；未将最终 VT 独立解码到像素。[验证摘要](../evidence/jk-motion-v2-offline/candidate-summary.json) 和 [安装摘要](../evidence/jk-motion-v2-offline/installation-summary.json) 保留限制。

## 贴图后续润色

现有颜色图集已导出为 4096² PNG，但 UV 岛非常碎。可先制作容易识别的局部视图，由图像编辑工具润色，再经投射/烘焙回到原 UV；验证遮挡、图案位置、接缝和 mip 边缘。保持材质与动态资源引用独立，颜色以 sRGB 导入；法线及线性 ARM 数值图单独处理，继续用原生父材质和真正 VT cook。本轮尚未执行 AI 图像润色。

## 官方资料

以下仅说明 UE 通用能力，不证明 PBZ 定制引擎或现有 MOD 入口兼容。

- [UE 5.7 Hair Rendering and Simulation](https://dev.epicgames.com/documentation/en-us/unreal-engine/hair-rendering-and-simulation-in-unreal-engine?application_version=5.7)：发丝与卡片式表达、渲染和模拟。
- [UE 5.7 Cloth Simulation](https://dev.epicgames.com/documentation/en-us/unreal-engine/cloth-simulation-in-unreal-engine?application_version=5.7)：布料编辑与配置入口。
- [AnimDynamics](https://dev.epicgames.com/documentation/unreal-engine/animation-blueprint-animdynamics-in-unreal-engine)：轻量次级动画；约束并不等于完整物理碰撞。检索返回 5.8 文档，仅用于通用概念，落地须核对本机 5.7 与游戏实现。
- [RigidBody](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-blueprint-rigid-body-in-unreal-engine)：使用物理资产的次级结构模拟；同样须核对版本和实际入口。
