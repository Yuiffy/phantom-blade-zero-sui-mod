# 双服装图案修整验证

对照本地两套正面参考，实施 JK 猫脸臂章、JK 领结交叉格纹、地雷岁领结装饰字和花边修整。地雷岁中央宝石因 UV 与白色衣料重叠保留原样；胸前挂件的梯形造型、袖口和裙边等形状差异未列为本轮已修复内容。

这里仅存数值、检查结果和 SHA256；参考图、衍生图集、离线渲染与游戏容器均保存在本地私人目录。

- `source-hashes.json`：两套参考图哈希、JK 原 4K 图集哈希及最近邻复制到 8K 的说明。
- `atlas-report.json`：三处目标组件、图集哈希和实际修改数量。
- `surface-verification.json`：实际 native UV 归属与 padding 检查，其他消费者表面没有越界涂色；未绘制 JK 原像素按 2×2 精确复制。
- `verification.json`：仅两个 8K/14 mip VT package，最终容器独立解析及载荷/纹理 bulk 核验。没有网格、材质、shader、物理或外观表资源。
- `installation.json`：安装文件清单、此前十二文件哈希保留、实际安装纹理载荷读回与有效 package 元数据核验。
- `visual-review.json`：当前源图集和 native 数据哈希，私人同机位近景/整体图像哈希与审看范围。

离线预览使用冻结的独立 native 读回及源 PNG，未独立将最终 cooked VT 解码为像素，未游戏实测。重新压缩、mip 与实际游戏着色仍有差异，不以离线通过替代实机反馈。
