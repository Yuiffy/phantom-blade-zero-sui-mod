# 二审 v4 语音：用户本地重建补丁

下载内容只包含 21 段选定的岁己 WEM、微小的字段差分、生成后的容器索引和原创 Python 工具。原版中英文语音库从用户自己安装的游戏读取，不随补丁分发。没有 TTS 或变声步骤。

**下载不足 1 MB；生成后仍为 1,256,044,008 字节，约 1.26 GB。** 此补丁解决分发体积，不改变当前已验证的库加载结构。语音覆盖成年魂共享的 27 个所选战斗事件，中文 238、英语 236 个媒体，不受服装限制；不含剧情配音或少年魂替换。

## 需要什么

- Windows、64 位 Python 3.10+、Steam 游戏 build **26367565**（app 4115450）。其他 build 会拒绝构建。
- 自己取得的游戏 AES 密钥，以及自己可信来源的 `oo2core_9_win64.dll`。补丁不附带这两项，也不下载或执行第三方工具。已有 Bladesmith 本地配置可用 `--bladesmith-config` 读取其中的字面量 `PBZ_AES`；不会执行配置文件。
- 约 1.5 GB 空闲空间，游戏退出。构建使用单工作线程和较低进程优先级，分块读取，定期检查游戏进程；游戏启动后将在下一次检查时退出并清理未完成输出。
- 不需要 UE 编辑器、Wwise、wav2wem、UAssetGUI 或完整的原版音频提取目录。

## 本地生成

下载本仓库 Release 中的 `Sui_Voice_v4_LocalPatch_1.0.0.zip`，完整解压。命令从解压根目录运行。先安装 Python 依赖：

```powershell
python -m pip install -r scripts/voice_patch/requirements.txt
```

以下路径均换成你自己的实际路径；输出目录必须尚不存在，且位于游戏目录以外。省略密钥参数时，会隐藏输入提示，不把密钥写入命令行、输出或补丁文件：

```powershell
python scripts/voice_patch/generate.py --game-root 'F:/SteamLibrary/steamapps/common/PBZ' --output 'F:/Mods/SuiVoiceV4' --oodle-dll 'F:/MyTools/oo2core_9_win64.dll'
```

也可在上述命令末尾加 `--bladesmith-config '本地配置文件路径'`，或 `--key-file '仅存于本机的密钥文本文件路径'`；两者互斥。密钥文本应只有 64 位十六进制字符串，可带 `0x` 前缀。不要把这些私人文件提交到仓库。

工具首先核对 Steam build 和原版 TOC 哈希，随后核对每个源 chunk 的长度和 SHA-256。重建过程使用 COPY 原库范围、ADD 补丁数据、ZERO 对齐填充；完整 bulk 前缀在复制时同步验哈希，小块元数据在改动前验哈希。最后核对全部 17 个目标 chunk 和三个输出文件的长度及 SHA-256，全部通过后才将临时目录重命名为指定输出。不会覆盖已有目录。

## 手动安装与卸载

工具**不会自动安装**。构建成功后，保持游戏退出，将输出目录中的三个同名文件复制到：

```text
<PBZ>/ProjectPBZ/Content/Paks/~mods/SuiVoiceV4/
  z_Sui_Hun_NaturalVoice_Reviewed_v4_P.pak
  z_Sui_Hun_NaturalVoice_Reviewed_v4_P.utoc
  z_Sui_Hun_NaturalVoice_Reviewed_v4_P.ucas
```

先移除旧 Sui 语音三件套或禁用其他成年魂语音 MOD；不要叠装 v2/v3/v4，不要移除模型包或其他无关 MOD。已有同名 v4 时按 `recipe.json` 核对哈希，一致则无需重装。安装前备份自己原有的语音 MOD，回退时在游戏退出后只移除上面三件套，再恢复自己的旧语音包。

角色模型独立安装。中文和 English(US) 均有离线覆盖；用户仅确认过 v3 总体实机生效，**本补丁与二审 v4 文件逐字节一致，但 v4 运行听感尚待用户实测**。较长选音连续出招时是否截断/叠音仍需听感验证。

## 文件和来源

- `recipe.json`：build/源 TOC/源及目标 chunk 哈希、重建操作和三件套哈希。
- `payload.bin`：去重后的 21 段选定 WEM 与极少量修改字段和生成的容器头；WEM 共 **164,334 字节**。不包含原版 WEM 或完整原版 bank。
- `utoc.bin` / `pak.bin`：本 MOD 新生成的索引/空 pak 模板，不是游戏原版容器。
- `audio-provenance.json`：21 段素材的原按钮文件名、源哈希、PCM 区间、WEM 哈希和二审快照哈希。素材来自 `Yuiffy/suiji-sui-button`，按原有完整活动区间使用；非代码内容不适用 MIT。
- `scripts/voice_patch/`：独立生成工具和仅供维护者使用的 `make_recipe.py`。

本机完整重建校验见仓库 `evidence/voice-local-patch-v1.json`；社区发布形式比较见 `skills/pbz-character-mod/references/voice-local-patch-case.md`。禁止通过改 build ID/哈希来绕过版本限制；游戏更新后需要重新解析并验证。
