# 地雷岁脸部修整 Face2

2026-11-17 用户近景反馈：鼻侧眼白发黑，刘海出现像眉毛/眼线的块状污染。对照最初地雷服立绘，清理刘海的错误烘焙投影，保留刘海后方的原眉毛；把前置旧眼窝的有限鼻侧内部改为暖白。虹膜、闭合眼白几何、眼睑边缘和粉挑染保留。

`face-comparison.jpg` 左为修改前、右为修改后，均为同几何与灯光的 Blender 离线预览。眼睛正常阴影及虹膜边缘仍存在，预览不代表 PBZ 原生着色器或游戏实测。

`surface-verification.json` 记录 UV 与鼻侧取样检查。衣服复用了部分被改绘的位置，因此使用独立 `T_Jirai_Face2`，仅绑定皮肤与头发；原图及其他材质保持。`material-rebinding.json` 与 `verification.json` 记录原生材质载荷和最终三包容器的独立读回。`mount-verification.json` 检查与实际安装基线组合时的目录顺序独立性；`installed-mount-verification.json` 从安装目录重新挂载读取资源。

实际状态以 `summary.json` 为准。没有新启游戏、操作存档、控制进程或录制桌面。包含图集的成品和可编辑母版只留本地 private，参考图和游戏原资产没有复制到公开证据目录。
