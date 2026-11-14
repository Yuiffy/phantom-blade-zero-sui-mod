# JK 后续加分项：材质与动态部件

2026-11-15。用户希望当前形变修复搞定后，再优化单马尾、书包、外套、裙子和背带挂饰。本文是准备方案，不是已经制作或验证的功能。当前 v10 为离线候选，尚未安装和游戏实测；先复核长柄防御的右背、白色穿插与整体稳定性，再开始动态实验。

## 目标与顺序

| 部位 | 外观目标 | 动态目标与首选实验 |
| --- | --- | --- |
| 单马尾 | 保留批准的侧单马尾轮廓与前垂方向，做发束方向、高光和粗糙度区分 | 发根固定、发梢逐渐灵活，转身和跑动有滞后；先试少量分段骨骼，验证游戏实际驱动与身体碰撞后再考虑 Groom |
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

保留 v10 与前版回退材料，每次只启用一项动态变化。离线先核验资产类型、导入、骨架、材质、包白名单和最终容器；人工诊断姿势只证明诊断范围。

游戏实测由用户方便时完成：原地/跑停/转身、跳攻、长柄防御、闪避/蹲伏、换装、读档和过场。重点看头发穿胸背/武器、挂饰离开挂点、包体塌陷、裙摆上翻、瞬移后爆振、LOD 切换与性能。当前没有宣称这些测试已通过。

准备研究不安装 MOD、不控制游戏，不启动 TTS、桌面采集或重型模拟。实际构建继续采用已约定的后台低优先级与线程限制。

## 官方资料

以下仅说明 UE 通用能力，不证明 PBZ 定制引擎或现有 MOD 入口兼容。

- [UE 5.7 Hair Rendering and Simulation](https://dev.epicgames.com/documentation/en-us/unreal-engine/hair-rendering-and-simulation-in-unreal-engine?application_version=5.7)：发丝与卡片式表达、渲染和模拟。
- [UE 5.7 Cloth Simulation](https://dev.epicgames.com/documentation/en-us/unreal-engine/cloth-simulation-in-unreal-engine?application_version=5.7)：布料编辑与配置入口。
- [AnimDynamics](https://dev.epicgames.com/documentation/unreal-engine/animation-blueprint-animdynamics-in-unreal-engine)：轻量次级动画；约束并不等于完整物理碰撞。检索返回 5.8 文档，仅用于通用概念，落地须核对本机 5.7 与游戏实现。
- [RigidBody](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-blueprint-rigid-body-in-unreal-engine)：使用物理资产的次级结构模拟；同样须核对版本和实际入口。
