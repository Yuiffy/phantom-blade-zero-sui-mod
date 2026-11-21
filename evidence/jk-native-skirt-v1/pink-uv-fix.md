# 小粉帽裙腰串色修复

单独显示裙片时，裙腰仍出现灰蓝色块和零散白点。裙片和背心分别使用 JK 图集和小粉帽图集。修复在小粉帽裙片的 UV 岛内重新选择深蓝色布面采样，修正了 1,531 个顶点中的 861 个 UV 坐标。离线对照检查了站姿正面、斜侧、背面和抬腿，确认裙腰恢复深蓝，保留下摆白纹。

`apply_pink_uv.py` 使用 `pink-uv-patch.json` 将修正应用到本目录首笔试玩记录所对应的 `PinkBeret_GuYou.uexp`。运行 `python apply_pink_uv.py <试玩版.uexp> <修色版.uexp>` 生成新载荷。输入和输出均按 SHA-256 核验。

最终 IoStore 读回显示两套裙骨结构与试玩样本一致。整合包从 ZIP 解压后校验了 42 个文件，载荷差异只涉及 JK 和小粉帽身体网格。修色后的整合包待游戏内复测。[整合包核验](../../releases/triple-v1.2.0-preview.3/verification-summary.json)
