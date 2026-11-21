# 岁己 × 影之刃零

## 下载最新版

[双皮肤＋战斗语音 v1.1.0](https://github.com/Yuiffy/phantom-blade-zero-sui-mod/releases/tag/dual-v1.1.0) 对应 Steam build 26367565。黑伤（逃亡）使用 JK 外套侧马尾，黑伤使用地雷系双马尾。本版同步本地已装的脸部、图案、饰件和裙摆性能更新，以及 Compact v5 语音。ZIP 内含 36 个文件，逐项核对了当前安装的哈希。

完全退出游戏，备份并移出旧版岁己模型、补丁和语音，然后将解压后 mod/ 内的文件原样复制到 `ProjectPBZ/Content/Paks/~mods/`。只装模型时可以略过 Compact v5 的三个文件。完整组合仍待进一步实机核验。[安装说明](releases/dual-v1.1.0/README.txt)

[小粉帽 JK · 故友 v0.4.4](https://github.com/Yuiffy/phantom-blade-zero-sui-mod/releases/tag/jk-pink-beret-v0.4.4) 是双皮肤 v1.1.0 的可选扩展。安装后，成年魂可在 **角色 → 外观 → 故友** 使用无外套的小粉帽 JK。支持 Steam build 26367565。[安装说明](releases/jk-pink-beret-v0.4.4/README.txt)

## 开发记录

**2026-11-18 JK 裙子性能优化：**已安装 [JKSkirtPerf1](models/jk-skirt-perf-v1/README.md)，撤下旧高开销 JKSkirt1。隐藏裙子模拟网格由 288 点降为 64 点，共享求解由 32 次迭代/8 子步降为 12/3；匹配合成跑步的单线程离线布料求解中位数从 315.47 ms 降到 37.10 ms，约减少 88%，仍高于早先 8/2 约 20.6 ms 的成本。六组连续动作、最终映射表面、二十张离线图像和实际安装独立读回通过，原 21 文件、最新脸部及地雷岁下巴修补/颈圈保持。**离线计时不是游戏 FPS，尚未证明裙子是约 9 帧的唯一原因；内衬和深蹲仍有残余穿插，需实机复试。**[参数与安装证据](evidence/jk-skirt-perf-v1/README.md)，Release 未更新。

**2026-11-18 JK 裙子跑步避让历史：**[JKSkirt1](models/jk-skirt-v1/README.md) 曾通过连续求解及跑步避让检查，但遗漏性能验收，共享 32/8 参数造成明显离线开销回归。**已移出安装并封锁重新安装，由上方 JKSkirtPerf1 接替。**历史交线、图像和安装凭据保留，不代表当前状态。[历史证据与回归说明](evidence/jk-skirt-v1/README.md)。

**2026-11-18 JK 岁脸部与虹膜细修：**已安装 [JKFacePolish2](models/jk-face-polish-v2/README.md)。对照 JK 原图与两套现有模型，保留 JK 柔和眼眶、细眉睫毛及原笑嘴，加入地雷岁同款虹膜图案并适配红瞳；下巴轻微抬高、圆润，下颊局部收敛，最大几何改动约 0.370 cm。三 package 最终容器、实际安装读回及 131 个保留资源 metadata/完整导出载荷核验通过，另十八文件逐项哈希不变，回退预检通过。三方向离线近景已审阅，**新 JK 候选游戏效果待用户复试**。此前获认可的地雷岁细修已推送至 `codex/jk-proportion-fix`（`a08a7fc`）；本 JK 候选暂留本地，Release 未更新。[数值与安装证据](evidence/jk-face-polish-v2/README.md)。

**2026-11-18 地雷岁下巴方斑修补：**已安装 [ChinClean1](models/jirai-chin-clean-v1/README.md)。从旧版实际 BC1 虚拟纹理解码 mip4/mip5，复现用户截图下巴灰紫方斑；将十六个相关 UV 碎岛隔离并补足肤色边缘，指定区域的缩小采样色差显著降低。脸型、五官、嘴角、完整权重及最新颈圈保持。最终三 package、实际安装包及 131 个保留资源 metadata/完整导出载荷核验通过；替换旧 LashLip1/Choker1 六文件为新三文件，其余十八文件哈希保持，回退预检通过。**新候选游戏效果待复试；其他面部极低精度串色不在本次修复承诺内。**[数值和安装证据](evidence/jirai-chin-clean-v1/README.md)，本次同步源码与数值证据，Release 未更新。

**2026-11-18 地雷岁颈圈修复：**已安装 [Choker1](models/jirai-choker-v1/README.md)，根据原参考重建连续黑色颈带、银色心形扣和黑色衬边，解决原饰件埋进脖子只露出碎片的问题。仅覆盖地雷岁身体一个 package，最终容器和实际安装独立读回通过；其他 134 个资源的元数据与完整载荷及原 24 文件哈希保持。四方向离线近景已检查，回退预检通过。**游戏内观感与动态待用户复试。**[安装证据](evidence/jirai-choker-v1/README.md)，Release 未更新。

**2026-11-18 07:50（北京时间）地雷岁睫毛与嘴角细修：**已安装 [LashLip1](models/jirai-lash-lip-v1/README.md)，将上睫毛、外眼角睫毛翼与四组下睫毛统一染黑，右嘴角下方分叉合到原上方嘴线。眼眶和睫毛几何、Face3 瞳孔/虹膜与闭合眼白保留；嘴角仅局部 72 个顶点沿 Z 调整，最大约 0.306 cm，索引、切线帧及完整权重不变。三 package 最终容器和实际安装载荷独立读回通过，另十八文件与 102 个有效资源 metadata 保留，三方向离线近景已检查；用户随后反馈“不错”并要求提交远端；未报告完整动作、过场及长时间测试。[数值及安装记录](evidence/jirai-lash-lip-v1/README.md)，本次同步源码及数值证据，Release 未更新。

**2026-11-18 07:23（北京时间）地雷岁 Face2＋Face3 组合：**已按用户要求安装 [Face2Hybrid1](models/jirai-face2-hybrid-v1/README.md)：恢复 Face2 脸部、眼眶、眉睫毛和嘴型，保留 Face3 瞳孔/虹膜与闭合眼白；嘴型、UV 和嘴唇颜色不变，仅平滑嘴部局部着色以减少暗碎块。保留新版头饰、图案、光环和袖内补面。被否定的 Polish1 三件套已移入本地备份，另十八文件哈希原样；三 package 最终容器、指定来源、67 个臂部权重副本、实际安装载荷及其余 102 个有效 package 的 metadata 独立读回通过，七视角离线预览已审阅。**本组合游戏内观感及动态效果仍待用户复试。**[数值与安装记录](evidence/jirai-face2-hybrid-v1/README.md)，未提交、推送或更新 Release。

**2026-11-18 Polish1 实机反馈：**用户否定本候选眼睛，已标记失败并封锁重新安装。原离线证据只证明数据与结构检查，不代表外观获认可。按用户明确要求，改为 Face2 脸部、眼眶和嘴型配 Face3 瞳孔与闭合眼白，嘴部仅清理暗碎块；袖内补面和光环修复保留。[失败历史](models/jirai-polish-v1/README.md)。

**2026-11-17 23:32（北京时间）JK 脸型修整候选：**已安装 [JK FaceShape1](models/jk-face-shape-v1/README.md)，参考地雷岁较收敛的下半脸轮廓，渐进收窄 JK 脸颊、下颌及上部侧缘；指定下颌高度段宽度约减少 9.5%，眼睛、嘴巴、鼻尖和贴图保留 JK 原样。单网格叠加包的成品几何、五官保护、接缝、其他 131 个有效 package 载荷及实际安装集合独立读回均通过，三视角离线近景已审阅。按用户允许的范围，本轮裙摆保留，已记录实际活动上限约 0.627 cm 等限制，**未修复深蹲穿裙，脸型游戏内效果仍待反馈**。[数值与安装证据](evidence/jk-face-shape-v1/README.md) 已保存，现有 Release 未更新。

**2026-11-17 14:58（北京时间）双服装图案修整候选：**已在本机安装 [Patterns1](models/outfit-patterns-v1/README.md)，对照两套正面参考重画 JK 猫脸臂章、补齐 JK 领结交叉格纹，并修整地雷岁领结装饰字与黑花边。JK 图集由 4K 提至 8K，为新绘图案增加采样空间；地雷岁维持 8K。叠加包仅覆盖两张 VT 贴图，表面保护、最终容器独立读回及实际安装载荷/挂载核验通过，离线前后近景已审阅。地雷岁心形宝石因共用 UV 保留原样，胸前挂件等造型差异仍待处理。**游戏内效果尚待反馈。**[验证证据](evidence/outfit-patterns-v1/README.md) 仅含数值与哈希；正式 Release 仍为下述 R5 版。

**2026-11-17 10:07（北京时间）头饰修整候选：**已安装 [Hairpin1](models/jirai-hairpin-v1/README.md)，重做地雷岁头部右上方的粉色爱心、黑边、细十字及交叉发夹，清理承载头发上的旧投影。三 package 叠加包的最终 native 读回、拓扑与表面保护、安装哈希及实际挂载核验通过，三个方向离线近景已审阅。保留 Face3、R8 裙型及语音。**游戏内效果尚待反馈。**[验证证据](evidence/jirai-hairpin-v1/README.md) 仅含数值和哈希；正式 Release 仍为下述 R5 版。

**2026-11-17 03:12（北京时间）脸部修复候选：**已安装 [Face3](models/jirai-face-v3/README.md)，修复眼白与虹膜深度衔接、鼻侧黑带及碎块高光，收细眉毛与睫毛，清理刘海串色和嘴周裂口。基于 R8 Shape1 局部修改，保留现有裙型、布料、权重、骨架与语音；7 package 最终容器独立读回、安装文件哈希和挂载检查通过，三个角度离线近景已审阅。**游戏内效果尚待反馈。**[验证证据](evidence/jirai-face-v3/README.md) 仅含数值与哈希，参考图和衍生贴图留在本地；正式 Release 仍为下述 R5 版。

**2026-11-17 02:55（北京时间）裙型修整候选：**已安装 [R8 Shape1](models/jirai-skirt-shape-v1/README.md)，撤回之前为避让抬腿增加的 4 cm 径向外扩，裙子最宽处收窄约 13.6%，平滑压低下摆和侧缘，保留腰线与连通黑安全裤。最终可见摆动上限为 35%，物理参数沿用 Recovery1；新几何重新绑定与连续求解，最终映射的六组、18 轮回落检查通过，24 张离线形状/动作/遮挡图已审阅。双服装成品独立读回、安装哈希及 Face2 叠加核验均通过，JK、Face2 和语音保留。**尚待用户实机复试，深蹲等大动作仍可能局部穿裙。**[同机位对比图](evidence/jirai-skirt-shape-v1/shape-comparison.png) 左为旧版、中为新静态、右为新版本走停后；全部为离线渲染。[参数与证据](evidence/jirai-skirt-shape-v1/README.md)。正式 Release 仍为下述 R5 版。

**2026-11-17 02:12（北京时间）裙摆回落候选：**已安装 [R7 Recovery1](models/jirai-skirt-recovery-v1/README.md)，保留新版裙型与连通不透明安全裤，加强恢复驱动和重力、降低惯性，并将可见物理混合限制到 40%。修正离线测试初始化重置后，六组连续走停、跑停、蹲起测试及成品映射重建通过；18 张动作/站定/安全裤离线图已审阅。最终双服装包独立读回、安装哈希及 Face2 叠加解析均通过，JK、语音和 Face2 文件保留。**尚待用户实机复试，大动作仍可能局部穿裙。**[参数与验证证据](evidence/jirai-skirt-recovery-v1/README.md)。正式 Release 仍为下述 R5 版。

**2026-11-17 地雷岁 R7 实机反馈：**用户报告普通走动后裙摆翻起，停止时裙型异常，实机效果退步。R7 已标记失败并封锁重新安装；原有离线证据保留，它们未覆盖本次问题。用户随后同意保留新版裙型与连通安全裤，转入[独立参数恢复实验](models/jirai-skirt-recovery-v1/README.md)，重点检查反复走动、停下和裙摆回落；R6 SkinEyes1＋Fishnet1 的已核验备份及回退脚本保留。已于 2026-11-17 01:23（北京时间）在游戏退出后恢复 R6 SkinEyes1＋Fishnet1，六文件哈希与 R7 安装前完全一致，JK 与语音保留。[实机反馈记录](evidence/jirai-r7-skirt/runtime-feedback.json)。正式 Release 仍为下述 R5 版。

**2026-11-16 本地修复更新：**已安装 [皮肤材质与闭合眼白修复](models/skin-eyes-v1/README.md) 及其上的 [地雷岁渔网袜修整](models/fishnet-v1/README.md)。渔网清理断线和重影、统一网线并提高图集至 8K；最终 99 包中仅一张贴图变化，其余 98 包、皮肤/眼白修复、物理与语音保留。用户认可优化结果并要求提交远端。[离线对比](evidence/fishnet-v1/compare-back.jpg)、[安装与验证摘要](evidence/fishnet-v1/summary.json) 已收录；尚未记录完整游戏实测。本次提交代码和验证证据，现有 Release 下载包仍为下述 R5 版。

**地雷岁 R5 可回退检查点（2026-11-16）：**已保存 [可编辑母版](models/jirai-r5-checkpoint/README.md)、[本轮修整代码](models/jirai-proportion-v1/README.md) 和 [用户试玩记录](evidence/jirai-r5-dual-v2/runtime-feedback.json)。用户认可整体质量，同时报告深蹲/跑动大腿穿裙、单手刀柄贴合、左腿暗痕/吊带凸起，并希望侧发和马尾避衣物摆动。这些转入独立实验，不包含在本检查点的修复承诺中。

成年「魂」的完整岁己角色替换 MOD：脸、头发、身体和服装。当前双皮肤版由 **黑伤（逃亡）** 启用 JK 外套侧马尾，**黑伤** 启用地雷系双马尾。不处理少年魂。本仓库收录模型、可安装模型包、制作经验和 Codex skill。

2026-11-14，用户已报告 `native-shaders-v1` 模型实机成功。测试游戏为 Steam app **4115450**、build **26367565**。这不是全流程兼容性认证：战斗、武器、过场、长时间游玩仍需逐项验证；游戏更新后应重新核验。

历史首个双皮肤版本为 [岁己 JK＋地雷系双皮肤 · dual-v1.0.0](https://github.com/Yuiffy/phantom-blade-zero-sui-mod/releases/tag/dual-v1.0.0)，合并 **JK Motion v5＋地雷岁 R5**。一个三件套即可在游戏服装菜单切换两套完整角色；保留原解锁规则和独立语音包。JK 包含不透明安全裤覆盖、立体白猫挂饰与增强衣服碰撞避让；地雷系为无翅膀双马尾版，包含比例、手部、肩袖修正及双马尾、裙摆物理。

同一 Release 现提供 **`Sui_JK_Jirai_WithVoice_PBZ_v1.0.0.zip` 双皮肤＋语音一体包**（约 22.1 MB），推荐直接下载。解压后 `mod/` 中为模型、语音各一套三件套，共六个文件；语音沿用已发布 Compact v5 的既有录音，保持测试版状态。原纯模型 ZIP 和独立语音 ZIP 也保留，已安装同版语音无需重复安装。详见 [一体包说明](releases/dual-v1.0.0/README-with-voice.txt) 与 [六文件清单](releases/dual-v1.0.0/bundle-manifest.json)。

2026-11-16 已核对当前安装与发布制品哈希，用户反馈“不错”并批准两个皮肤合并发布。最终 88 个资源、两套模型骨架与渲染数据、布料映射和材质依赖、68 行合并外观表均已核验；所有武器、动作、过场与长时间稳定性尚未逐项验证。详见 [双皮肤发布说明](releases/dual-v1.0.0/release-notes.md)、[文件清单](releases/dual-v1.0.0/manifest.json) 和 [核验摘要](releases/dual-v1.0.0/verification-summary.json)。

![地雷系 R5 离线模型预览](releases/dual-v1.0.0/previews/jirai-front.png)

历史 [JK 单皮肤首版 jk-v1.0.0](https://github.com/Yuiffy/phantom-blade-zero-sui-mod/releases/tag/jk-v1.0.0) 基于 v3，曾有低角度安全裤遮挡问题。[v4 修复](models/jk-motion-v4-candidate/README.md) 已收入当前双皮肤正式版；升级时请移出旧版模型三件套。

[v11 静态细修候选](models/jk-v11-candidate/README.md) 包含裙子残留粉色清理、清晰猫脸袜和另一侧袜口、手指体积及实际背带吊点，保留为静态回退。基于它的 [物理实验 v1](models/jk-motion-v1-candidate/README.md) 已通过真实离线 Chaos 模拟及最终容器读回，并已安装获用户初步试玩反馈。物理预览是离线求解结果。

历史源与证据保留：[v8 肩颈和比例](models/jk-v8-candidate/README.md)、[v9 手部转轴与饰件](models/jk-v9-candidate/README.md)、[v10 右背与包内投影](models/jk-v10-candidate/README.md)。候选目录中的旧状态文字记录当时检查阶段；当前安装事实以上述物理 v3 凭据为准。人工诊断姿势不能保证实际长柄防御或所有动作无穿插。

## 安装模型

安装历史 v1.0.0 时，从 [双皮肤 v1.0.0 Release](https://github.com/Yuiffy/phantom-blade-zero-sui-mod/releases/tag/dual-v1.0.0) 下载 `Sui_JK_Jirai_DualOutfit_PBZ_v1.0.0.zip`，解压。关闭游戏，先备份并移出本项目旧 JK、旧地雷系或旧双服装模型三件套，保留独立语音包；再将 `mod/` 下同名的 `.pak`、`.utoc`、`.ucas` 三件套放入：

需要一起安装语音时，改为下载 `Sui_JK_Jirai_WithVoice_PBZ_v1.0.0.zip`，先移出旧模型及旧语音包，再把 `mod/` 下六个文件放入同一目录。原纯模型包的以下命令使用 `manifest.json`；一体包的可选校验分别使用 `model-manifest.json`、`voice-manifest.json`，安装时两份清单分别保存凭据。

```text
<PBZ游戏目录>/ProjectPBZ/Content/Paks/~mods/
```

进入游戏选择 **黑伤（逃亡）→ JK 外套侧马尾**，或 **黑伤 → 地雷系双马尾**。黑伤内部无帽变体也使用地雷系。两套皮肤共用本包合并外观表，不要再分别安装单皮肤包或修改同一外观表的其他 MOD。

也可用 Python 3.10+ 执行带哈希核验的安装工具。以下命令从解压目录运行；默认只预览，加 `--apply` 才写入：

```powershell
python scripts/mod_files.py verify --manifest manifest.json
python scripts/mod_files.py install --manifest manifest.json --game-root '你的PBZ游戏目录'
python scripts/mod_files.py install --manifest manifest.json --game-root '你的PBZ游戏目录' --apply
```

脚本要求 Windows、Steam 目录结构和本次已验证的 build；不会启动、停止或操作游戏。卸载使用同一解压目录保存的凭据，核对哈希后只删除本包文件：

```powershell
python scripts/mod_files.py uninstall --manifest manifest.json --game-root '你的PBZ游戏目录' --apply
```

手动卸载也只需移除 `z_Sui_DualOutfit_JK5_JiraiR5_P` 的三个文件。不要清空整个 mods 目录、删缓存或改存档。

## 模型与制作经验

- [v11 细修候选：裙色、两侧袜口、手指体积与吊点](models/jk-v11-candidate/README.md)：离线核验完成，尚未安装；真实摆动物理未加入此包。
- [物理实验 v1 源码、模型和验证边界](models/jk-motion-v1-candidate/README.md)、[实际离线模拟动图](evidence/jk-motion-v1-offline/motion-preview.gif)
- [物理细修 v2：贴图、光环、重力马尾与挂饰避让](models/jk-motion-v2-candidate/README.md)、[离线模拟动图](evidence/jk-motion-v2-offline/motion-preview.gif)：三组模拟及最终容器读回通过，用户反馈整体不错；现保留为本地回退。
- [物理细修 v3：缩短黑色内衬裤脚](models/jk-motion-v3-candidate/README.md)：保留腰臀与裆部覆盖，裤脚上收约 6 cm；三组模拟及最终容器读回通过，用户认可并批准作为 JK 首个正式版发布。
- [v10 安装凭据摘要与用户试玩反馈](evidence/jk-v10-installation/installation-summary.json)
- [绑定后的旧衣服 GLB](models/sui-hun-binding.glb)：早期公开 Release 的几何和绑定，内嵌贴图，可导入 Blender；新衣 JK 源码见上述候选目录。
- [模型说明与来源](models/README.md)
- [v7 候选：肩颈权重、颈长与下摆衔接](models/jk-v7-candidate/README.md)
- [制作 skill](skills/pbz-character-mod/SKILL.md)
- [闪退诊断与修复](skills/pbz-character-mod/references/model-pipeline.md)
- [原声语音替换](skills/pbz-character-mod/references/voice-pipeline.md)
- [轻击/跳攻语音修复成功案例](skills/pbz-character-mod/references/voice-library-case.md)
- [二审选音、构建与回退经验](skills/pbz-character-mod/references/voice-review-case.md)
- [本地听审网页与语音流水线代码](scripts/voice/README.md)
- [实测范围与数据](evidence/runtime-result.json)
- [v7 离线核验数据](evidence/jk-v7-offline/summary.json)

将 `skills/pbz-character-mod/` 复制到 `~/.codex/skills/pbz-character-mod/`，可使用 `$pbz-character-mod`。Skill 包含本次验证过的约束和可移植核验工具；不包含游戏解密密钥、提取的原版资产或第三方工具。语音 v4 另有下面的本地重建补丁。

## 语音替换经验

**2026-11-15，用户确认 `library-natural-voice-v3` 已生效：“不错，真的改好了！”** 此前 v2 虽补齐跳攻静态漏项，用户仍反馈轻击、跳攻为男声。v3 在原 `VO_CN`、`VO_EN` 资源库中替换实际载荷，并补齐原本嵌入媒体的六个事件；保留原生加载策略和索引结构，覆盖 27 个所选事件的完整随机池，共中文 238、英语 236 个独立 MediaID，使用 30 段既有原声。方法与核验见 [成功案例](skills/pbz-character-mod/references/voice-library-case.md) 和 [脱敏证据](evidence/voice-library-v3.json)。

这条反馈确认本轮修复总体有效，未逐项说明测试过的武器、连段或语言；英语覆盖是离线核验结果，不能写成双语实机通过。静态追踪涉及 49 个空中/跳跃技能及父类，共 66 个资源；检查范围不代表全部地面连段、动态事件或剧情。v3 同时调整库载荷、随机池覆盖和英语分支，尚未单独证明某个缓存优先级是唯一原因。

语音事件为成年魂共享，**不限定黑伤（逃亡）服装**。没有 TTS、CosyVoice、变声、新 ASR 或人声分离；逐段听审仍未单独完成。语音与模型独立回退。**v3 约 1.25 GB 的完整容器包含大量原版语言库数据，仅保留本地，不上传 GitHub 或 Release。** `audio/source-index.json` 保留为 v2 的历史音源索引。

## 二审语音 v4 与代码

2026-11-15 已按用户二审的 **12 项选择**构建并安装 `reviewed-natural-voice-v4`：246 个语言/媒体槽更新，228 个保持 v3 字节不变；仍覆盖原来中文 238、英语 236 个媒体。最终使用 21 个独立片段，仅 3 个新增编码。最终容器读回与独立解码通过，**v4 运行听感尚待实测**；v3 的总体成功反馈不能直接套给 v4。

公开 [听审网页、构建/核验及安装回退代码](scripts/voice/README.md)、[二审经验](skills/pbz-character-mod/references/voice-review-case.md) 和 [脱敏证据](evidence/voice-reviewed-v4.json)。这套维护者流水线依赖本地已提取、已建索引的数据，个人路径已改为环境配置；不附带原版对照音频、第三方程序或密钥。v4 约 1.256 GB 的完整库容器仍仅留本地；普通用户可改用下述小补丁。

候选素材按本轮选择冻结，以后岁己按钮增加再优化。较长选择保留试听的完整区间，连续出招时的截断/叠音/衔接仍需人工游戏测试，不能以离线解码通过代替。

## 免脚本的小型语音 v5（测试版）

[下载 v5 测试版](https://github.com/Yuiffy/phantom-blade-zero-sui-mod/releases/tag/voice-v5-compact-beta.1) · [安装说明](voice-compact/README.md) · [方法与验证范围](skills/pbz-character-mod/references/voice-compact-case.md)

ZIP 约 **729 KB**，解压后三件套本体合计约 **3.29 MB**，包含相同的 21 段二审选音，不携带完整原语音库。玩家退出游戏、移走旧语音三件套后，复制新三件套到 `~mods` 即可，不需要 Python、UE、密钥、Oodle 或本地生成。新的 packaged hash 用来隔离原库的共享 bulk；474 个媒体槽、28 个事件的最终容器读回已通过。**新加载方式的游戏实测待反馈**，不宣称已修复所有运行问题；下面的 v4 重建补丁保留作原库布局的备选。

## 小下载：用户本地生成语音 v4

Release `voice-v4-localpatch-v1.0.0` 提供 **不足 1 MB** 的 `Sui_Voice_v4_LocalPatch_1.0.0.zip`。下载只带去重后的 21 段选定岁己 WEM、微小字段差分、MOD 容器索引和原创生成代码；原版语音库从用户自己安装的游戏读取。

[使用说明](voice-patch/README.md) · [差分经验与社区形式比较](skills/pbz-character-mod/references/voice-local-patch-case.md) · [完整重建证据](evidence/voice-local-patch-v1.json)

需要 Windows、64 位 Python、自己的 Oodle DLL 和游戏 AES 密钥，仅支持 Steam build 26367565；不需要 UE 或预先提取原库。工具不自动安装。**本地生成的三件套仍占约 1.26 GB**，已核验与二审 v4 逐字节相同；这只减少下载量，不代表额外的游戏运行测试。

语音事件为成年魂共享，**不限定某一服装**。没有 TTS、CosyVoice、变声、新 ASR 或人声分离。切口、背景声、音量和语气仍待听审。语音实验与模型分开回退；双皮肤 Release 已附 Compact v5 独立语音和一体包，保留语音测试版状态，不打包完整私人录播。语音可独立卸载，移出 `z_Sui_Hun_NaturalVoice_Compact_v5_P` 三件套即可保留模型。

## 致谢与使用范围

方法参考 [ccd775/GameModdingKnowledge](https://github.com/ccd775/GameModdingKnowledge) 的 PBZ 技术记录，以及 [StarryNightSquad/Phantom-Blade-Zero](https://github.com/StarryNightSquad/Phantom-Blade-Zero) 的作者经验。具体适用性与版本差异见 [案例记录](skills/pbz-character-mod/references/case-2026-11-14.md)。本仓库未复制它们的代码或资产。

岁己为相关权利方的角色；影之刃零及游戏派生内容的权利属于其各自权利方。本仓库是非官方同人实验。原创脚本与文字按 [LICENSE](LICENSE) 许可；该许可不覆盖角色形象、模型、贴图、语音或游戏派生 MOD 数据。详见 [NOTICE](NOTICE.md)。
