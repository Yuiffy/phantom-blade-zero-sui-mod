# 小粉帽背心下缘修整

在 0.4.10-preview.1 的基础上，将整圈下缘拉齐，沿新下缘重绘双白纹，并平滑折痕处的表面光照。离线测得下缘高低差由 2.38 厘米降至 0.93 厘米。游戏版 0.4.11-preview.1 收入三皮肤整合包。

用 SUI_HEM_WORK 指定临时工作目录。在加载基线绑定模型的 Blender 中运行 surface.py，导出 vest.npz。将基线图集置为 source-albedo.png。在 top.npz 中提供其他材质的 UV 占用数据 other_uv，形状为 N × 3 × 2。用 Python 3.12、NumPy、SciPy、OpenCV 和 Pillow，依次运行 level_hem.py、shading.py 和 trim.py，输出几何增量、法线混合数据和虚拟纹理源图。基线模型、图集及游戏工具由本地环境提供。

最终容器覆盖故友独立网格和图集。整合包的外观映射、骨架、语音事件与有效资源已核验。极端蹲姿的离线预览仍有少量浅色衬层露出。[发布核验](../../releases/triple-v1.2.0-preview.2/verification-summary.json)
