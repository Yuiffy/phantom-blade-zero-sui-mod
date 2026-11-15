# 岁己 × 影之刃零

**地雷岁 R5 可回退检查点（2026-11-16）：**已保存 [可编辑母版](models/jirai-r5-checkpoint/README.md)、[本轮修整代码](models/jirai-proportion-v1/README.md) 和 [用户试玩记录](evidence/jirai-r5-dual-v2/runtime-feedback.json)。用户认可整体质量，同时报告深蹲/跑动大腿穿裙、单手刀柄贴合、左腿暗痕/吊带凸起，并希望侧发和马尾避衣物摆动。这些转入独立实验，不包含在本检查点的修复承诺中。

成年「魂」的完整岁己角色替换 MOD：脸、头发、身体和服装。当前双皮肤版由 **黑伤（逃亡）** 启用 JK 外套侧马尾，**黑伤** 启用地雷系双马尾。不处理少年魂。本仓库收录模型、可安装模型包、制作经验和 Codex skill。

2026-11-14，用户已报告 `native-shaders-v1` 模型实机成功。测试游戏为 Steam app **4115450**、build **26367565**。这不是全流程兼容性认证：战斗、武器、过场、长时间游玩仍需逐项验证；游戏更新后应重新核验。

当前正式版为 [岁己 JK＋地雷系双皮肤 · dual-v1.0.0](https://github.com/Yuiffy/phantom-blade-zero-sui-mod/releases/tag/dual-v1.0.0)，合并 **JK Motion v5＋地雷岁 R5**。一个三件套即可在游戏服装菜单切换两套完整角色；保留原解锁规则和独立语音包。JK 包含不透明安全裤覆盖、立体白猫挂饰与增强衣服碰撞避让；地雷系为无翅膀双马尾版，包含比例、手部、肩袖修正及双马尾、裙摆物理。

2026-11-16 已核对当前安装与发布制品哈希，用户反馈“不错”并批准两个皮肤合并发布。最终 88 个资源、两套模型骨架与渲染数据、布料映射和材质依赖、68 行合并外观表均已核验；所有武器、动作、过场与长时间稳定性尚未逐项验证。详见 [双皮肤发布说明](releases/dual-v1.0.0/release-notes.md)、[文件清单](releases/dual-v1.0.0/manifest.json) 和 [核验摘要](releases/dual-v1.0.0/verification-summary.json)。

![地雷系 R5 离线模型预览](releases/dual-v1.0.0/previews/jirai-front.png)

历史 [JK 单皮肤首版 jk-v1.0.0](https://github.com/Yuiffy/phantom-blade-zero-sui-mod/releases/tag/jk-v1.0.0) 基于 v3，曾有低角度安全裤遮挡问题。[v4 修复](models/jk-motion-v4-candidate/README.md) 已收入当前双皮肤正式版；升级时请移出旧版模型三件套。

[v11 静态细修候选](models/jk-v11-candidate/README.md) 包含裙子残留粉色清理、清晰猫脸袜和另一侧袜口、手指体积及实际背带吊点，保留为静态回退。基于它的 [物理实验 v1](models/jk-motion-v1-candidate/README.md) 已通过真实离线 Chaos 模拟及最终容器读回，并已安装获用户初步试玩反馈。物理预览是离线求解结果。

历史源与证据保留：[v8 肩颈和比例](models/jk-v8-candidate/README.md)、[v9 手部转轴与饰件](models/jk-v9-candidate/README.md)、[v10 右背与包内投影](models/jk-v10-candidate/README.md)。候选目录中的旧状态文字记录当时检查阶段；当前安装事实以上述物理 v3 凭据为准。人工诊断姿势不能保证实际长柄防御或所有动作无穿插。

## 安装模型

从 [双皮肤正式版 Release](https://github.com/Yuiffy/phantom-blade-zero-sui-mod/releases/tag/dual-v1.0.0) 下载 `Sui_JK_Jirai_DualOutfit_PBZ_v1.0.0.zip`，解压。关闭游戏，先备份并移出本项目旧 JK、旧地雷系或旧双服装模型三件套，保留独立语音包；再将 `mod/` 下同名的 `.pak`、`.utoc`、`.ucas` 三件套放入：

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
- [实测范围与数据](evidence/runtime-result.json)
- [v7 离线核验数据](evidence/jk-v7-offline/summary.json)

将 `skills/pbz-character-mod/` 复制到 `~/.codex/skills/pbz-character-mod/`，可使用 `$pbz-character-mod`。Skill 包含本次验证过的约束和可移植核验工具；不包含游戏解密密钥、提取的原版资产、第三方工具或全自动重建流水线。

## 语音实验

用户反馈 v1 跳攻仍是男声后，已定位到实际技能引用的漏项并安装原声实验 v2。检查了 49 个空中/跳跃技能及其父类，共 66 个资源；五组直接空中发声的 33 个独立媒体现均有替换。新包共 26 事件、134 个媒体替换，使用 20 段既有按钮原声；其他所选事件仍保留 95 个原声媒体。**v2 待再次游戏实测与听审**，详情见 [跳攻漏项案例](skills/pbz-character-mod/references/voice-jump-case.md)。剧情对白、英语、少年魂保持原样，检查范围不代表所有地面连段。

语音事件为成年魂共享，**不限定某一服装**。没有 TTS、CosyVoice、变声、新 ASR 或人声分离。切口、背景声、音量和语气仍待听审。语音实验与模型分开回退；双皮肤 Release 仅包含模型，可配合独立 [Compact v5 语音包](https://github.com/Yuiffy/phantom-blade-zero-sui-mod/releases/tag/voice-v5-compact-beta.1)，不打包私人录播。

## 致谢与使用范围

方法参考 [ccd775/GameModdingKnowledge](https://github.com/ccd775/GameModdingKnowledge) 的 PBZ 技术记录，以及 [StarryNightSquad/Phantom-Blade-Zero](https://github.com/StarryNightSquad/Phantom-Blade-Zero) 的作者经验。具体适用性与版本差异见 [案例记录](skills/pbz-character-mod/references/case-2026-11-14.md)。本仓库未复制它们的代码或资产。

岁己为相关权利方的角色；影之刃零及游戏派生内容的权利属于其各自权利方。本仓库是非官方同人实验。原创脚本与文字按 [LICENSE](LICENSE) 许可；该许可不覆盖角色形象、模型、贴图、语音或游戏派生 MOD 数据。详见 [NOTICE](NOTICE.md)。
