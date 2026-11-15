# 直接安装的小型语音包：v5 候选

2026-11-15，用户要求免 Python 的小型语音包。基线为 Steam app 4115450、build 26367565，成年魂既有战斗选音。**v5 是离线验证候选，实机待用户反馈；不能沿用 v3 的成功结论。**

## 社区形式

[Aimerrove 的 2B Combat Voice](https://www.nexusmods.com/phantombladezero/mods/892) 作者说明把 `.pak/.utoc/.ucas` 放入 `ProjectPBZ/Content/Paks/~mods/PBZ2BVoice/`。[文件页](https://www.nexusmods.com/phantombladezero/mods/892?tab=files) 2026-11-12 的 1.1.0 分中文/英语下载，标注 11.3 MB / 11.0 MB。[作者回复](https://www.nexusmods.com/phantombladezero/mods/892?tab=posts) 说明只替换战斗声音。直接访问部分页面返回 403，信息由搜索索引中的作者页面核对。没有取得作者制作脚本或解析其 MOD，**不能声称复现其内部方法**；未复制其声音或容器。

先前 234,287 字节的 v4 补丁只是下载小，本地仍重建 1,256,044,008 字节的完整库容器。v5 尝试只封装目标事件和选音，玩家直接复制三件套，不需要 Python、AES、Oodle、UE 或本地重建。

## 缓存依据与推断边界

公开工程随附的 Audiokinetic 2025 集成代码：[WwisePackagedFile.cpp，锁定提交](https://github.com/NBcampUnrealTrack/1st-Team1-Final-Project/blob/33d442e17cfae2c9cd27d51bf9c28cb77772b767/Plugins/Wwise/Source/WwiseFileHandler/Private/Wwise/WwisePackagedFile.cpp)。这是插件源码的公开副本，不是 PBZ 自身源码；未把第三方源码复制到本仓库。

`UpdateBulkDataArrayToSharedVersion` 按 `KnownBulkDatas.Find(Hash)` 复用共享 bulk 数组。`SerializeBulkData` 先建立共享数组；External 不携带新数据；BulkData 若发现数组已有内容，会忽略自己随后读入的数据而继续用共享数据。`WITH_EDITORONLY_DATA` 中重新计算 hash 的代码不适用于通常的 cooked 运行版本。

[UWwiseAssetLibrary](https://github.com/NBcampUnrealTrack/1st-Team1-Final-Project/blob/33d442e17cfae2c9cd27d51bf9c28cb77772b767/Plugins/Wwise/Source/WwisePackaging/Private/Wwise/Packaging/WwiseAssetLibrary.cpp) 在反序列化时登记 bulk；[资源加载器](https://github.com/NBcampUnrealTrack/1st-Team1-Final-Project/blob/33d442e17cfae2c9cd27d51bf9c28cb77772b767/Plugins/Wwise/Source/WwiseResourceLoader/Private/Wwise/WwiseResourceLoaderImpl.cpp) 的 `LoadAssetLibraryNode` 挂接库节点，不等于把每个 bank/media 装进声音引擎。[媒体管理器](https://github.com/NBcampUnrealTrack/1st-Team1-Final-Project/blob/33d442e17cfae2c9cd27d51bf9c28cb77772b767/Plugins/Wwise/Source/WwiseFileHandler/Private/Wwise/WwiseMediaManagerImpl.cpp) 还有按 MediaID 复用的机制，因此共享 ID 的其他事件也要核对。

**推断**：v1/v2 保留旧 hash，可能让新媒体复用了原库 bulk。这有具体的同类插件源码依据，但没有 PBZ 缓存日志，也没有“只改 hash”的单变量游戏对照，不能宣布是之前失败的唯一原因。

## v5 实现

维护者入口：`scripts/voice/build_compact_voice_v5.py` 和 `verify_compact_voice_v5.py`。需要本地已校验 v4、原事件 JSON/schema、VO 库索引、retoc 和 UAssetGUI；**制作工具不是玩家安装依赖**。

复用二审全部 **21 个 WEM，164,334 字节**，逐字节保留 474 个语言/媒体选择（中文 238、英语 236）；没有重新编码、生成、拉伸或强裁。覆盖原 27 个事件，并添加共享媒体关联事件 `SFX_Combat_VO_Hun_ZhongZhuan_01`。它在原库替换方式下本就读到新声音，增加这个资产不是增加新选音。

把目标事件非流式 bank/media 封装为 `BulkData=3`，按 MemoryAlignment（至少 16）对齐。每个独立 `(language, kind, id)` 分配确定性、非零的新 packaged hash，530 个 hash 内部唯一且不碰撞本地完整 VO_CN/VO_EN 索引或 42 个已解析成年事件。同一共享媒体在不同事件中必须用相同字节和 hash；此碰撞范围不等于全游戏扫描。

保留资产路径、EventID、LanguageID、SoundBankID、MediaID、HIRC object/source/cache IDs、随机池和 native duration/attenuation。bank 只修正 source `in_memory_size`；非空 bank 与 v4 最终读回字节一致。英语 Charge_SuperLong 原池为空，其空 bank 无须创造声音。

按 unversioned schema 定位 PackagingStrategy/Hash，再重建 bulk index 和 DataResources；禁止裸字节全局替换。streaming、prefetch、SwitchContainerLeaves 或部分未选随机池超出本案例结构时重新设计，不能套偏移。

## 成品检查与交付

从最终三件套读回，独立比较原事件与 v4 数据：

1. 精确 28 个事件，无完整 VO 库、模型、少年魂或剧情资产。NameMap/imports、export 属性、native 其他字段保持一致。
2. 资源有效、对齐、无交叠；零填充，无未引用数据或尾随 bulk；新 hash 不撞已检查原 hash，共享引用一致。
3. 474 个槽、21 段声音全部出现，WEM 与冻结 v4 字节一致，没有原版 WEM；bank 只有 BKHD/HIRC，无 DATA/DIDX 原音频。
4. 逐语言解析 bank source ID/大小与媒体匹配，非空 bank 与 v4 最终读回一致；42 个检查事件内不留下同 MediaID 的旧引用。
5. 安装只替换语音三件套，保存旧 v4 与凭据，核验其他 MOD 和设置不变。候选应在完全退出游戏后单独加载，不能叠装 v4 取得假成功。

离线证据见 `evidence/voice-compact-v5.json`。用户需手动重启，检查轻击、跳攻、各武器、受击和连续出招的声音及长片段衔接。若仍原声或异常，按凭据回退，不盲目重映射全部 HIRC/EventID，不把格式检查写成实机通过。

发布包包含三件套、说明、manifest 和选音来源记录，以及必要的修改后事件/bank 元数据；没有原版语音、完整原库或其他 MOD 的声音。原创代码许可不覆盖角色、录音或游戏派生二进制。
