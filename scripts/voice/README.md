# 本地语音听审与 v4 构建代码

免脚本安装的小型三件套候选见 [v5 玩家说明](../../voice-compact/README.md)。维护者构建时沿用下方环境变量和私有输入，另外需要已校验 v4 的完整 report/verification、encoded 和最终 readback：先运行 `python scripts/voice/build_compact_voice_v5.py`，再运行 `python scripts/voice/verify_compact_voice_v5.py`。28 个事件只带局部声音并使用新的 packaged hash，最终 WEM 与二审 v4 逐字节一致；游戏实测仍待反馈，不能把脚本完成当作通过。

本机维护者的可选切换器为 `switch_compact_voice_v5.py --apply`，回退为 `--rollback --apply`；不加 `--apply` 只准备本地 manifest/快照。它要求 `delivery/compact-voice-v5/mod/` 已有校验后的三件套，并保存旧 v4 delivery 和安装凭据。按当前实际模型列表准备恢复 manifest，安装失败会恢复 v4。用六项假 Steam 目录测试验证安装失败、部分卸载/凭据写入失败、游戏运行拒绝，以及后续模型/设置变更后的独立语音回退；不会启动游戏。普通玩家用手动复制方式，无需此脚本。

普通用户生成已选定的语音 v4，请使用 [小补丁说明](../../voice-patch/README.md) 与 `scripts/voice_patch/generate.py`。下文是维护者修改选音/重新编码时使用的完整流水线。

这份代码整理自 2026-11-15 的 `reviewed-natural-voice-v4`。保留实际使用的选择映射、原库追加载荷、bank 源大小修正、编码及独立读回逻辑；把个人绝对路径改为配置，并只导出依赖模块中的所用函数，省略未成功的历史 v1/v2 构建入口。它依赖已经提取、建索引并校验的 **build 26367565** 本地数据，不是下载后就能从游戏自动提取重建的一键工具。

## 配置与输入

Python 3.10+、Windows，以及 `requirements.txt` 中的 numpy/psutil。第三方 retoc、UAssetGUI、wav2wem、vgmstream 和 FFmpeg 需自行安装；本仓库不附带这些程序、schema、游戏资产、密钥或音频。不要用 `python -O`，该构建案例的格式断言必须启用。

从仓库根目录运行，按实际位置设置：

```powershell
$env:PBZ_VOICE_WORKSPACE = '你的本地语音工作目录'
$env:PBZ_GAME_ROOT = '你的PBZ游戏目录'
$env:SUI_BUTTON_ROOT = '你的suiji-sui-button目录'
# 可选：PBZ_VOICE_TOOLS 覆盖 retoc/UAssetGUI 工具目录；
# PBZ_GAME_SETTINGS 覆盖当前用户 GameUserSettings.ini 路径。
python -m pip install -r scripts/voice/requirements.txt
```

`PBZ_VOICE_WORKSPACE` 默认指向本仓库忽略的 `private/voice-workspace`。预期目录包括：

- `variants/library-natural-voice-v3/`：原始 v3 report、bilingual-inventory、encoded、source-json，以及 original-legacy 中两份原库 `.ubulk`。
- `research/`：`wwise-schema.json`、`wwise-libraries/*/parsed-index.json`、`adult-wwise-metadata.json`、`adult-audio-json`、原生提取数据、空中技能审计和 `primary-source/UAkAudioEvent.cs`；以及本地工具目录。
- `voice-review-round2/`：原听审 manifest、audio 和 `reviews/user-review.json`。
- `project-policy.json`：本案例的 tts_enabled、voice_conversion_enabled、new_asr_enabled、source_separation_enabled 均为 false。
- 安装/回退还需本地 `delivery/library-voice-trial-v3` 的三件套与 manifest，以及 `runtime-test-kit/library-natural-voice-v3-installation.receipt.json`。

独立校验和源输入完整性沿 report、inventory 及 schema 逐项核对。输入缺失会停止；不要用公共的脱敏证据替代私有构建报告。音频 manifest 的路径相对于本地工作目录。

## 听审网页

`review-ui/` 只有 HTML/CSS/JS。复制到本地 `voice-review-round2/`，与本地 manifest/audio 同级，再启动：

```powershell
python scripts/voice/serve_voice_review_round2.py --port 9212
```

浏览器打开 `http://127.0.0.1:9212/`。页面可以对照原版、当前 WEM 解码和候选，按语言/事件/媒体查找、循环试听、保存和导出。服务器仅绑定回环地址，写入检查 Host、Origin 与 manifest 哈希；页面不负责安装。UI 是二审时的原样快照，“当前/未安装”等状态描述对应 v3 → v4 的听审阶段。

`build_voice_review_round2.py` 保留本次 12 个问题、19 个候选的构造代码；重做需要第一轮 manifest、反馈、自然录音索引等本地前置数据。不要在已听审的同一目录重建 manifest；更换候选时另建一轮。页面支持逐媒体选择，但**这份 v4 构建器只支持所有 12 项都直接选定候选且 media 为空的结果**；恢复原版、按事件分选及逐媒体覆盖必须先另外实现并校验，不能默默忽略。

## 构建、验证与安装

```powershell
python scripts/voice/freeze_voice_review.py
python scripts/voice/build_reviewed_voice_v4.py
python scripts/voice/verify_reviewed_voice_v4.py
python scripts/voice/switch_reviewed_voice_v4.py
# 用户授权安装且游戏已退出时：
python scripts/voice/switch_reviewed_voice_v4.py --apply
# 日后需要恢复 v3 时：
python scripts/voice/switch_reviewed_voice_v4.py --rollback --apply
```

构建器复用已认可 WEM，仅编码 3 份新选择，不做 TTS、增益调整、拉伸或按原时长强裁。未选中的 228 个媒体沿用 v3 字节；修改的共享 `(language, MediaID)` 在已检查的 42 个事件内保持一致。库的原 bulk 完整保留为前缀，只追加目标载荷，修改其偏移/尺寸并同步 bank 的 `in_memory_size`。

公共版独立校验输出到 `public-export-audits/reviewed-natural-voice-v4/`，不会覆写旧的 verification/readback-json/编码日志；安装器读取该新校验报告。仅校验哈希、native 元数据、索引、完整池映射和独立解码，不代表游戏里的每个声音都能完整播放。

切换器先检查 build、游戏退出状态、旧三件套与凭据；记录**当前实际安装的所有其他 MOD 文件**和设置哈希。原 v3 receipt 会按卸载流程标为 removed，但其原件先保存在本地 installation-before 中。失败恢复及主动回退用当前兼容文件列表，避免把旧 receipt 中过时的模型版本当成唯一允许的模型。所有操作只针对对应凭据的语音三件套。

`--apply` 安装路径已在本机完成；公共版配置适配没有再次安装游戏。自动失败恢复与主动 rollback 分支用临时假 Steam 目录验证，不能写成真实游戏故障回退已实测。v4 的运行听感、长片段衔接和连续出招效果仍待用户反馈。

本次整理验证：14 项单元测试通过，公开选择解析器与已安装 v4 的全部 474 个槽映射一致，Python/JavaScript 语法与 skill 校验通过。公开版完整容器复核因游戏正在运行被进程保护阻止；没有绕过检查、重新编码或改动游戏。
