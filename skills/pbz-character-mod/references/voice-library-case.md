# 轻击与跳攻仍是男声：原语言库替换成功案例

2026-11-15，用户在安装 `library-natural-voice-v3` 后反馈：“不错，真的改好了！” 测试基线为 Steam app **4115450**、build **26367565**，范围为成年魂的所选战斗发声。此处记录用户总体成功反馈；没有逐武器、逐连段、双语或长时间游玩的实测清单。脱敏数据见仓库根目录的 `evidence/voice-library-v3.json`。

## 从失败中确认了什么

v2 的三件套安装哈希与离线候选一致，没有发现叠装其他 Sui 语音包，用户仍报告轻击与跳跃攻击是原版男声。它已补齐 [静态跳攻漏项](voice-jump-case.md)，但还有两类问题需要分开检查：

- 覆盖：`SFX_Combat_Vo_Hun_Attack_Short` 整个事件未覆盖，9 个中文随机媒体全为原声；其他所选事件还保留 95 个独立中文原声媒体。部分随机池替换必然允许抽到未替换资源，但这不证明它解释了所有跳攻反馈。
- 资源位置：v2 将中文非流式资源从 `External=4` 转为事件局部 `BulkData=3`，保留 packaged hash，原 `VO_CN` 库不变。原预加载库或 hash 缓存优先的可能性存在，但没有独立的运行时读取记录证明。

当时 `GameUserSettings.ini` 的 `WwiseCultureName=English(US)`、`CultureName=en-us` 与用户“游戏里选择中文”的反馈矛盾。最初据配置断言英语是根因的判断已撤回。日志为 `PBZLOGE1` 加密格式，未取得实际播放语言、事件 ID 或可读栈；配置不能代替实时证据。

## 先追真实动作，再检查完整随机池

技能发声位于 `LegoAbilityBlueprintGeneratedClass` 的 `LGATimeline.Actions`；沿 `Super` 继承并以 Guid 应用 `ActionOverrides`，最后解析 AkEvent。Montage/AnimSequence 中脚步通知不能解释这批战斗发声，编辑期序列化的 PlayingID 也不是实时记录。

49 个命名 Air/Jump 成年技能连同父类共 66 个资源，直接引用五组：`BiQi_02_Long`、`ChuZhao_02`、`ShouZhao_DoubleBlade`、`ShouZhao_LongBlade`、`ShouZhao_TangBlade`（均为 `SFX_Combat_VO_Hun_` 前缀）。其他检查过的空中武器形态复用这些事件。共享媒体还涉及 `ZhongZhuan`，相同语言和 MediaID 必须一致。该静态范围不包含所有地面连段、动态调用或剧情。

v3 覆盖 27 个所选事件的所有现存随机媒体：中文 **238**、English(US) **236** 个独立 MediaID，含 Attack_Short 和五组空中事件。英语 Charge_SuperLong 的原池为空，不能把事件条目数解释为 27 个非空英语池。沿 42 个已解析成年战斗事件检查共享媒体一致性，不宣称扫描过全游戏。

## 保留原加载方式，替换实际源库载荷

最终仅覆盖 **8 个资产**：`VO_CN`、`VO_EN` 两库，以及六个原本嵌入媒体的事件：

```text
SFX_Combat_VO_Hun_Break
SFX_Combat_Vo_Hun_Charge_Long
SFX_Combat_Vo_Hun_Charge_Release_Light
SFX_Combat_Vo_Hun_Cough
SFX_Combat_Vo_Hun_Heavy_Release
SFX_Combat_VO_Hun_Snort
```

外部事件继续使用原生 External 引用；六个嵌入事件保留原有属性、ID、原生索引和封装方式。未将全部事件改成自带媒体。

两个源库的原始 `.ubulk` **完整保留为字节一致的前缀**。把目标非流式 WEM 和修正后的 BNK 追加到末尾，按资源要求对齐，本案例至少 16 字节；只改对应 `DataResources.SerialOffset/SerialSize/RawSize`。其他资源映射、流式数据、prefetch、填充和原对齐保持不变。

`PackagedFiles` 的数量、顺序、hash、IDs、stream flags、策略、原生尾部和索引表保持不变。按结构解析 bank，仅把目标 source 的 `in_memory_size` 更新为新 WEM 的真实长度；其余 source/object ID 和字段不变。禁止用裸字节搜索无条件改值。不同 build 或 streamed 资源要重新确认布局，不能套用本案例偏移。

中文库修改 221 个资源槽、英语库 218 个；两库与嵌入事件合计修改 529 个独立 `(language, kind, id)` 载荷，含 bank 和 media。保留 v2 已替换的 **134 个中文 WEM 字节不变**。最终使用 30 段已有自然录音活动区间，无 TTS、变声、新 ASR、分离、时间拉伸或按目标时长强裁。

## 最终成品的独立核验

先构建，再从最终容器解包读回，独立核验以下内容：

1. 精确 8 资产白名单；NameMap、imports 和原生元数据/ID/索引与原资源一致。
2. 两库完整原 bulk 前缀字节一致，未修改资源的映射不变；追加载荷范围、大小、哈希与候选相符。
3. 逐事件沿实际原引用解析到新媒体，而非只比较修改脚本输出；bank 源大小与最终媒体匹配。
4. 42 个已检查成年战斗事件内的共享媒体一致，27 个所选事件的完整随机池覆盖，旧 134 个中文 WEM 不变。
5. 30 个候选经独立 vgmstream 解码，源采样区间、样本数和来源哈希对应，相关性 >0.98、SNR >18 dB。此为编码/来源核验，逐段听审未单独完成。

v2 按哈希凭据撤下，v3 在游戏退出时独立安装，稳定模型与语言设置未修改。运行由用户手动完成，2026-11-15 获上述成功反馈。

v3 同时改了库载荷路径、随机池覆盖和英语分支；成功支持这一组合修复边界，**不能归因于唯一缓存字段，也不能声称用户实际使用英语**。保留离线报告的原始“待运行”状态与哈希，后续运行反馈单独追加，避免把后来的证据写回旧报告。

## 公开与复用范围

v3 三件套共 **1,255,012,322 字节**，含大量原版语言库数据，留在本地，不上传仓库或 Release。公开的是技术经验、覆盖统计及核验摘要；游戏资产、音频、密钥、私有路径不进入公开材料。未来若做可分发补丁，应另行设计本地重建流程，不把当前库容器当成公开发布包。

格式依据来自本地锁定的 CUE4Parse/Wwise 解析器（`FWwisePackagedFile`、`FWwiseAssetLibraryCookedData`、`UWwiseAssetLibrary`）及原生资源/最终容器读回。网络检索未获得可核实的本游戏缓存优先级说明；未读取成功的网页不作为已验证教程。
