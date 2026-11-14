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
- [轻击/跳攻语音修复成功案例](skills/pbz-character-mod/references/voice-library-case.md)
- [二审选音、构建与回退经验](skills/pbz-character-mod/references/voice-review-case.md)
- [本地听审网页与语音流水线代码](scripts/voice/README.md)
- [实测范围与数据](evidence/runtime-result.json)

将 `skills/pbz-character-mod/` 复制到 `~/.codex/skills/pbz-character-mod/`，可使用 `$pbz-character-mod`。Skill 包含本次验证过的约束和可移植核验工具；不包含游戏解密密钥、提取的原版资产或第三方工具。语音 v4 另有下面的本地重建补丁。

## 语音替换经验

**2026-11-15，用户确认 `library-natural-voice-v3` 已生效：“不错，真的改好了！”** 此前 v2 虽补齐跳攻静态漏项，用户仍反馈轻击、跳攻为男声。v3 在原 `VO_CN`、`VO_EN` 资源库中替换实际载荷，并补齐原本嵌入媒体的六个事件；保留原生加载策略和索引结构，覆盖 27 个所选事件的完整随机池，共中文 238、英语 236 个独立 MediaID，使用 30 段既有原声。方法与核验见 [成功案例](skills/pbz-character-mod/references/voice-library-case.md) 和 [脱敏证据](evidence/voice-library-v3.json)。

这条反馈确认本轮修复总体有效，未逐项说明测试过的武器、连段或语言；英语覆盖是离线核验结果，不能写成双语实机通过。静态追踪涉及 49 个空中/跳跃技能及父类，共 66 个资源；检查范围不代表全部地面连段、动态事件或剧情。v3 同时调整库载荷、随机池覆盖和英语分支，尚未单独证明某个缓存优先级是唯一原因。

语音事件为成年魂共享，**不限定黑伤（逃亡）服装**。没有 TTS、CosyVoice、变声、新 ASR 或人声分离；逐段听审仍未单独完成。语音与模型独立回退。**v3 约 1.25 GB 的完整容器包含大量原版语言库数据，仅保留本地，不上传 GitHub 或 Release。** `audio/source-index.json` 保留为 v2 的历史音源索引。

## 二审语音 v4 与代码

2026-11-15 已按用户二审的 **12 项选择**构建并安装 `reviewed-natural-voice-v4`：246 个语言/媒体槽更新，228 个保持 v3 字节不变；仍覆盖原来中文 238、英语 236 个媒体。最终使用 21 个独立片段，仅 3 个新增编码。最终容器读回与独立解码通过，**v4 运行听感尚待实测**；v3 的总体成功反馈不能直接套给 v4。

公开 [听审网页、构建/核验及安装回退代码](scripts/voice/README.md)、[二审经验](skills/pbz-character-mod/references/voice-review-case.md) 和 [脱敏证据](evidence/voice-reviewed-v4.json)。这套维护者流水线依赖本地已提取、已建索引的数据，个人路径已改为环境配置；不附带原版对照音频、第三方程序或密钥。v4 约 1.256 GB 的完整库容器仍仅留本地；普通用户可改用下述小补丁。

候选素材按本轮选择冻结，以后岁己按钮增加再优化。较长选择保留试听的完整区间，连续出招时的截断/叠音/衔接仍需人工游戏测试，不能以离线解码通过代替。

## 小下载：用户本地生成语音 v4

Release `voice-v4-localpatch-v1.0.0` 提供 **不足 1 MB** 的 `Sui_Voice_v4_LocalPatch_1.0.0.zip`。下载只带去重后的 21 段选定岁己 WEM、微小字段差分、MOD 容器索引和原创生成代码；原版语音库从用户自己安装的游戏读取。

[使用说明](voice-patch/README.md) · [差分经验与社区形式比较](skills/pbz-character-mod/references/voice-local-patch-case.md) · [完整重建证据](evidence/voice-local-patch-v1.json)

需要 Windows、64 位 Python、自己的 Oodle DLL 和游戏 AES 密钥，仅支持 Steam build 26367565；不需要 UE 或预先提取原库。工具不自动安装。**本地生成的三件套仍占约 1.26 GB**，已核验与二审 v4 逐字节相同；这只减少下载量，不代表额外的游戏运行测试。

## 致谢与使用范围

方法参考 [ccd775/GameModdingKnowledge](https://github.com/ccd775/GameModdingKnowledge) 的 PBZ 技术记录，以及 [StarryNightSquad/Phantom-Blade-Zero](https://github.com/StarryNightSquad/Phantom-Blade-Zero) 的作者经验。具体适用性与版本差异见 [案例记录](skills/pbz-character-mod/references/case-2026-11-14.md)。本仓库未复制它们的代码或资产。

岁己为相关权利方的角色；影之刃零及游戏派生内容的权利属于其各自权利方。本仓库是非官方同人实验。原创脚本与文字按 [LICENSE](LICENSE) 许可；该许可不覆盖角色形象、模型、贴图、语音或游戏派生 MOD 数据。详见 [NOTICE](NOTICE.md)。
