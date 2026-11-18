# 地雷岁下巴方斑核验

2026-11-18，按用户游戏截图定位下巴偏左灰紫色块。原 LashLip1 源图/最高精度中未出现同程度方块；从实际包 VT bulk 解码 mip4/mip5 后复现。`vt-decoding-before.json` 与 `mip-verification.json` 记录来源哈希、已检查的格式、限定区域及比较数值。新版对应区域相对最高精度 RGB 偏差 p95 从约 19.9/37.5 降到 3.0/3.6，最大约 3.6。

只移动十六个下巴相关 UV 碎岛，共 354 个顶点；隔离图块和扩展肤色边缘避免缩小采样时混入灰紫色。原占用 texel 保持，Normal/Mix/SCMT 常量输入已验证。所有位置、切线、索引、完整权重、UV1、分区、骨架、布料和物理不变；脸型、眼睛、睫毛、嘴型与最新 Choker1 颈圈保留。

`verification.json`、`native-patch.json` 与 `geometry-verification.json` 记录最终三 package、VT bulk 边界及完整 native 读回。`installation.json` 记录替换旧 LashLip1/Choker1 六文件为新三文件，其他十八文件哈希保持，131 个有效资源 metadata 和完整导出载荷保持；回退预检通过。当前集合包含 JK 新脸部，保留本任务期间其他任务移出 JKSkirt1 的实际状态。

`visual-review.json` 绑定最终读回三方向近景。派生图像、用户截图、资产和容器不公开。解码后的贴图投射用于隔离颜色问题，不复现原生 shader、光照和运行时 streaming；极低精度下其他面部区域仍可能串色。本候选新游戏效果尚待用户复试，本次同步源码与数值证据，Release 未更新。
