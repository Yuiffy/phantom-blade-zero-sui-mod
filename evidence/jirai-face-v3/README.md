# Face3 检查证据

基于当前 R8Shape1 的局部脸部补丁。此目录只保存检查数值、哈希与安装状态，不附参考图、衍生贴图、Blender 工程或游戏文件。

- `verification.json`：最终 7 package 容器、真实 VT、原生材质、最终网格独立读回。
- `native-patch.json`：变更字节范围；其余 native 载荷保持 R8 不变。
- `geometry-verification.json`：最终眼部可见性、鼻侧连续性及 UV0 精度。
- `surface-verification.json`：原图集和其他表面保护，采用实际半精度 UV。
- `visual-review.json`：离线三个方向审看记录及私人图像哈希。
- `installation.json`：实际安装清单、Face2 替换和 R8/语音保留状态。

**游戏实测待反馈。** 离线预览使用最终 native 几何和相应源贴图，不能证明游戏 shader/灯光或全部动作表现。
