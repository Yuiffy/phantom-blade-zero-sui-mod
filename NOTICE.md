# 内容来源与许可范围

本仓库的原创脚本和原创技术文字由 Yuiffy 发布，按 LICENSE 中的 MIT 条款提供。第三方链接指向各自作者的作品；本仓库没有代其授予许可。

`models/` 内模型来自 Yuiffy 的 `my-pixijs-game` 中旧版岁己模型，经本项目适配成年魂骨架、修正刚性附件绑定。角色设计、游戏骨骼及其派生内容的权利仍归各自权利方。模型和 Release 中的 MOD 二进制不适用本仓库的 MIT 许可，未额外授予商业使用或再授权权利。这不是官方模型或官方支持项目。

模型 Release 分发安装此替换所需的修改后容器；语音 Release 分发本地重建补丁。没有附带原版游戏容器、原版角色几何、动画库、提取工具、UE、AES 密钥、Oodle DLL、崩溃转储、用户存档或完整直播录播。

语音实验素材索引来自 Yuiffy 的 `suiji-sui-button`。早期公开内容为方法、事件映射和来源文件名/哈希；本地重建补丁另包含下述 21 段选定岁己 WEM。说话者、背景声和实际听感不能只凭文件标签判断。

2026-11-15 用户确认语音 v3 总体生效；此反馈不代替逐段音源听审。v3 本地容器包含大量原版 VO_CN/VO_EN 语言库数据，未随仓库或 Release 公开分发；公开的文件名、大小与哈希仅用于标识本地测试候选。

参考：

- https://github.com/Yuiffy/my-pixijs-game
- https://github.com/Yuiffy/suiji-sui-button
- https://github.com/ccd775/GameModdingKnowledge
- https://github.com/StarryNightSquad/Phantom-Blade-Zero

不把参考作者在其他游戏 build 的经验当成本项目当前版本的实测结论。

二审 v4 的公开内容包含原创听审网页模板与本地构建/核验/回退代码，以及选择摘要；没有发布原版对照声音、完整 native 元数据、私人路径或安装凭据。脚本保留 build 26367565 的格式约束，第三方工具需自行取得，其许可不由本仓库授予。

2026-11-15 新增 `voice-patch/`：`payload.bin` 中包含 21 段选定岁己录音的 WEM 编码（合计 164,334 字节），以及微小修改字段和生成的容器头；`utoc.bin`/`pak.bin` 为本 MOD 新生成的模板。原游戏完整语音库、原版 WEM 和原版完整 bank 不在补丁内，由用户工具从自己的游戏读取。逐段来源、PCM 区间、录音及编码哈希见 `voice-patch/audio-provenance.json`。岁己角色、录音、第三方编码格式和游戏派生补丁数据不适用 MIT；本仓库没有替权利人授予商业使用或再授权许可。原创生成代码与原创文字仍按 MIT 提供。
