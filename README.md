# 岁己 × 影之刃零

成年「魂」的完整岁己角色替换 MOD：脸、头发、身体和服装，仅由 **黑伤（逃亡）** 外观启用。不处理少年魂。本仓库收录当前可用模型、可安装模型包、制作经验和 Codex skill。

2026-11-14，用户已报告 `native-shaders-v1` 模型实机成功。测试游戏为 Steam app **4115450**、build **26367565**。这不是全流程兼容性认证：战斗、武器、过场、长时间游玩仍需逐项验证；游戏更新后应重新核验。

目前使用旧衣服的粗模，来自 Yuiffy 的 my-pixijs-game。新衣服版本尚未制作。所有部位暂用游戏原版布料材质，脸部光照和细微自发光仍有改进空间。

## 安装模型

从本仓库 **Releases** 下载 `Sui_HeiShang_Model_v1.0.0.zip`，解压。关闭游戏，将 `mod/` 下同名的 `.pak`、`.utoc`、`.ucas` 三件套放入：

```text
<PBZ游戏目录>/ProjectPBZ/Content/Paks/~mods/
```

进入游戏选择黑伤（逃亡）。不要混装本项目旧版或修改同一外观表的 MOD。

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

手动卸载也只需移除 `z_Sui_HeiShang_NativeShaders_v1_P` 的三个文件。不要清空整个 mods 目录、删缓存或改存档。

## 模型与制作经验

- [绑定后的 GLB](models/sui-hun-binding.glb)：当前 MOD 使用的几何和绑定，内嵌贴图，可导入 Blender；不是现成 UE 工程。
- [模型说明与来源](models/README.md)
- [制作 skill](skills/pbz-character-mod/SKILL.md)
- [闪退诊断与修复](skills/pbz-character-mod/references/model-pipeline.md)
- [原声语音替换](skills/pbz-character-mod/references/voice-pipeline.md)
- [实测范围与数据](evidence/runtime-result.json)

将 `skills/pbz-character-mod/` 复制到 `~/.codex/skills/pbz-character-mod/`，可使用 `$pbz-character-mod`。Skill 包含本次验证过的约束和可移植核验工具；不包含游戏解密密钥、提取的原版资产、第三方工具或全自动重建流水线。

## 语音实验

独立原声包已完成离线封装核验，已在本地独立安装并核对哈希；**尚无游戏内声音或缓存行为通过的反馈**。22 个成年魂中文战斗事件，109 个媒体 ID 使用 17 段岁己按钮原声，97 个所选媒体保留游戏原声。剧情对白、英语、少年魂保持原样；部分攻击仍会听到原声。

语音事件为成年魂共享，**不限定黑伤（逃亡）服装**。没有 TTS、CosyVoice、变声、新 ASR 或人声分离。切口、背景声、音量和语气仍待听审。语音实验与稳定模型分开回退；本次公开 Release 仅包含模型，仓库公开语音方法和来源索引，不打包私人录播或未听审音频。

## 致谢与使用范围

方法参考 [ccd775/GameModdingKnowledge](https://github.com/ccd775/GameModdingKnowledge) 的 PBZ 技术记录，以及 [StarryNightSquad/Phantom-Blade-Zero](https://github.com/StarryNightSquad/Phantom-Blade-Zero) 的作者经验。具体适用性与版本差异见 [案例记录](skills/pbz-character-mod/references/case-2026-11-14.md)。本仓库未复制它们的代码或资产。

岁己为相关权利方的角色；影之刃零及游戏派生内容的权利属于其各自权利方。本仓库是非官方同人实验。原创脚本与文字按 [LICENSE](LICENSE) 许可；该许可不覆盖角色形象、模型、贴图、语音或游戏派生 MOD 数据。详见 [NOTICE](NOTICE.md)。
