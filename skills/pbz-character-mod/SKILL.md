---
name: pbz-character-mod
description: Build and debug Phantom Blade Zero character replacement mods, including outfit-scoped skeletal meshes, native material instances, IoStore verification, and Wwise original-recording voice replacements. Use for PBZ asset ports or load/outfit-switch crashes.
---

# 影之刃零角色替换

先明确游戏 build、角色、服装及模型/语音范围，沿用当前会话的授权和资源限制。这里的成功案例是 build 26367565 的成年魂黑伤（逃亡）；不要把它的骨数、材质路径、版本参数推广到其他 build。

## 制作或修复模型

读 [model-pipeline.md](references/model-pipeline.md)。优先检查最终容器与实际安装文件，而不只看编辑器或 JSON。

遇到收窄体型后手指扭曲、袜饰悬空或底层贴图串色，读 [JK 手部与饰件案例](references/jk-hand-accessory-case.md)。先比较表面与骨骼转轴，保留顶点来源索引；替换立体饰件时同时清理底层旧投影，并分别验证新增与保留表面。

制作马尾、挂饰或布料物理时，读 [JK 布料离线实验](references/jk-cloth-case.md)。检查重建后的分区绑定、零时间轮廓及真实求解帧，再用模拟输出和最终 GPU 映射重建表面。v1 获用户对白猫与少量马尾摆动的确认；v2 增强重力、修色并增加挂饰避让，离线三组测试通过，已安装但尚未游戏实测。

- 按外观表实际 ItemId 追踪身体、头部、Groom、ChaosCloth、附件；单套服装替换要克隆部件引用，避免改共享路径而影响其他服装。
- 骨名、父级、参考变换及武器子骨必须和目标资源对齐；不要引入导出的额外 Armature 根节点。
- 游戏定制引擎与官方相同主版本不等于二进制兼容。本案例使用游戏原生父材质的叶子 MaterialInstanceConstant，移除自制 shader resource；贴图真实 cook 成父材质要求的 VT。
- 修改 cooked 网格时，通用 JSON 往返可能丢失 native 属性类型。尽量保留原导出载荷，仅按验证过的格式重定位 header、名称和引用；独立解析成品。
- 每个候选保存输入哈希、包清单、独立读回和安装凭据。安装前确认游戏退出，按当前授权操作。遇到失败按凭据回退，不叠装猜测性修补。

## 闪退诊断

读 [本次案例](references/case-2026-11-14.md)。先确定触发点、移除 MOD 后同存档是否恢复、当前安装包哈希。隔离模型、外观表和语音；设计可证伪的对照。

离线往返只证明数据可读/未变，不证明游戏引擎接受。加密 dump 无法读取时明确记录限制；不要编造调用栈。修复多个材料相关因素后成功，只能支持该修复边界，不可宣称某个单字段已被独立证明为唯一根因。

`scripts/audit_shader_layouts.py` 可只读解析本案例格式的 shader resource 数据并输出布局签名。输入是自行合法取得的原版原生数据或 UAssetGUI JSON；遇到不同结构会失败，不能拿它当通用 UE parser，更不能通过改哈希伪造 ABI 兼容。

## 语音

读 [voice-pipeline.md](references/voice-pipeline.md)。用现有按钮或录播时保存来源、区间和哈希；字幕只是检索线索，不证明说话者。先明确是否允许生成音频，遵守用户选择，不因有 TTS 工具而启动生成。

确认 Wwise EventID/MediaID 与语言、缓存及 bulk 组织，真正编码 WEM 后独立解码，最终容器再读回。模型服装范围不等于共享语音事件范围。音频离线校验、人工听审和游戏实测分别记录。

若某个动作仍发原声，读 [跳攻漏项案例](references/voice-jump-case.md)。从实际技能 timeline、父类和 ActionOverrides 追踪 AkEvent；别凭文件名猜事件。按随机池内的独立媒体检查覆盖率，并对共享 ID 的所有已检查引用保持一致。

若事件局部替换已安装但仍播放原声，读 [原语言库替换成功案例](references/voice-library-case.md)。沿原生资源引用核对库内 bank/media 与原本嵌入的事件；配置与用户语言反馈矛盾时先保留矛盾，不凭配置断言实际播放语言。本案例 v3 已获用户确认生效，但未独立证明缓存优先级或全部武器、双语实测通过。含原库数据的容器只留本地。

用户完成网页听审并要求安装选音结果时，读 [二审到安装案例](references/voice-review-case.md)。冻结 manifest/review 哈希，按真实共享 MediaID 应用选择；保留未选中的 WEM。不要默默忽略尚未实现的逐媒体覆盖，也不要把旧选音时长上限当作已证实的强制停止窗口。

## 交付

用户要求免脚本的小型语音包时，读 [事件局部小包候选](references/voice-compact-case.md)。区分本地仍生成完整库的 v4 差分与直接安装的 v5 三件套；后者通过新的 packaged hash 隔离共享 bulk，保留动作/音频 IDs。缓存解释有同类插件源码依据，但 v5 本游戏实测仍待反馈，不得写成已成功方法。

用户要求缩小语音下载或在其电脑本地生成时，读 [小补丁与本地重建案例](references/voice-local-patch-case.md)。本案例通过 COPY 原库范围、ADD 选定音频/微小字段和 ZERO 填充，精确重建二审 v4；下载不足 1 MB，但生成后仍约 1.26 GB。锁定 build、原 TOC 和源/目标哈希，不捆绑原版语音库、密钥或 Oodle DLL。使用新目录输出，不自动安装，不把字节一致核验写成新增的游戏实测。

原始游戏资产、密钥、崩溃文件和私人录播留在本地。公开文件逐项列明来源与许可，代码许可不自动覆盖角色/语音。只把当前已验证候选提升为发布版，失败历史保持封锁；用户口头成功反馈按原话记录，不补写未报告的全流程测试。
