# JK FaceShape1 证据

2026-11-17，本轮只调整 JK 脸型，保留其眼睛、嘴巴和全部布料。当前地雷岁作为轮廓参考，没有复制 Face3 五官。

- `author-report.json`：选区、位移和固定高度范围的宽度对比。
- `geometry-verification.json`：成品五官保护、UV/索引/切线符号、接缝和三角面检查。
- `patch-report.json`：限定 native 字节修改及源/输出载荷哈希。
- `verification.json`、`installed-verification.json`：候选与实际安装集合独立读回、包范围和保留载荷。
- `visual-review.json`：成品三视角审阅与图像哈希，原图和对比图留在 private。
- `editable-source.json`：完整可编辑绑定母版的保护检查和哈希。
- `skirt-diagnosis.json`：原裙摆 MaxDistance 等限制；本轮无裙摆修改、无新布料求解或游戏测试。
- `input-hashes.json`、`installation-summary.json`：输入/脚本哈希、安装时间与保留文件事实。

离线验证不代表游戏实测。贴图、模型、安装容器及原始游戏派生资源未包含在此证据目录；现有 Release 未更新。
