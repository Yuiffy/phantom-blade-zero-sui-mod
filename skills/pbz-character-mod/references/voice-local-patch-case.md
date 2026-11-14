# 以小下载分发已验证的语音库替换

2026-11-15，用户要求把二审 v4 做成用户本地生成的小补丁。已验证的三件套合计 **1,256,044,008 字节**；主要原因是 VO_CN/VO_EN 完整原 bulk 前缀保留。不能把它直接上传成“只有岁己声音”的包，也不能仅压缩后假设低于 100 MB。

## 社区发布形式

当天读取的作者页面：

- Aimerrove 的 [2B Combat Voice 说明](https://www.nexusmods.com/phantombladezero/mods/892)：在 `~mods/PBZ2BVoice/` 放 `.pak/.utoc/.ucas` 三件套，说明战斗发声覆盖为部分覆盖；[文件页](https://www.nexusmods.com/phantombladezero/mods/892?tab=files) 显示 1.1.0 中文包 11.3 MB、英语包 11.0 MB，上传于 2026-11-12。
- QOutlaw 的 [白赤练文件页](https://www.nexusmods.com/phantombladezero/mods/388?tab=files)：独立语音选装包 976 KB，上传于 2026-11-05。

这些作者发布页能证明下载大小和公开说明，不能证明内部 bank、库引用或缓存实现。没有下载、修改或再分发其内容。小体积并不要求换掉本项目刚验证成功的加载方式。

## 本案差分格式

17 个目标物理 chunk 连续且未压缩；前 16 个逻辑 chunk ID 在原游戏中存在，最后一个为新生成的容器头。8 个资产的原 bulk 是目标 bulk 的字节一致前缀，目标 metadata 与原 metadata 等长。追加的 media 来自 21 段已选 WEM，合计 164,334 字节；bank 仅少量字段变化。

维护者工具生成三种操作：COPY 当前源 chunk 的范围，ADD 去重补丁数据，ZERO 对齐填充。bank 和小型 metadata 用等偏移字节段比较，未变部分全部 COPY，避免把原版 bank/音频打包进补丁。新增 media 必须匹配二审选定的 21 个 WEM 哈希，不允许任意原声进入 ADD。generated TOC 与空 pak 作为新 MOD 模板携带。

用户工具从自己的原游戏按范围解密/解压；密钥由隐藏输入、本地密钥文件、环境变量或只读 AST 解析的本地 Bladesmith 配置提供，不进入公开文件。Oodle DLL 由用户自行提供，不捆绑。普通用户无需 UE、Wwise、编码器或预先提取的私有目录。

## 验证和边界

锁定 Steam build 26367565 和原 TOC 哈希。逐源 chunk 核对长度和 SHA-256，逐目标 chunk 及完整三件套再核对。大 bulk 在复制完整原前缀时同步计算源哈希，小 metadata 先验证再应用差分。输出写入新临时目录，全部通过后同卷重命名，不覆盖已有输出，不自动安装。

实际从本机原游戏成功重建，三件套与二审 v4 的大小及 SHA-256 完全相同。此证据复用了已独立读回的 v4 成品，不代表新增了游戏运行测试。v3 用户成功反馈与 v4 待运行状态应分别保留。

下载不足 1 MB，但生成/安装大小仍约 1.26 GB。以后要减少安装体积，应另建候选、检查库 native 引用并重新游戏实测；本地差分本身没有解决这个问题。见根目录 `voice-patch/README.md`、`scripts/voice_patch/` 与 `evidence/voice-local-patch-v1.json`。
