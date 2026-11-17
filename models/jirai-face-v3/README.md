# 地雷岁 Face3

眼睛使用连续的眼白表面与贴合的虹膜，修复原本鼻侧深度断层。虹膜改用独立 1024 贴图和 UV0，避免 8K 图集的半精度 UV 将瞳孔、高光挤成碎块。虹膜颜色细节取自用户提供的原立绘，只在本地处理，不包含生成图像。

收细上睫毛与独立眉毛，清理鼻侧烘焙黑带和额头的宽眉印，刘海保持原有轮廓并增加细微发丝明暗。嘴周收拢原模型重叠的口腔薄片、平滑法线，去掉黑裂口和嘴角尖片。眉毛仍位于刘海后方。

候选 `zzz_Sui_JiraiFace3_2_P` 包含 7 个 package：一个身体网格、三个游戏原生叶子材质、三张真实 cook 的 VT。基于当前安装的 **R8Shape1** 身体，仅改变脸部位置/切线帧、虹膜 UV0，以及三个叶子材质的贴图导入。网格 header、其余 export 字节、索引、UV1、权重、骨架、裙摆物理与形状保持不变。初期 R7 候选已留在私人拒绝候选目录，不安装。

公开的检查结果在 `evidence/jirai-face-v3/`。原立绘、衍生虹膜贴图、预览、Blender 工程、游戏资产与容器均在忽略的 `private/jirai-face-v3/` 下。公开代码不授予任何角色、美术或原游戏资产的使用权。

## 本地流程

依赖本机合法提取的 R8 模型、原生材质、工具、映射和本地参考资料，不能从本目录独立重建。

1. `common.py` 冻结安装清单，`run_blender.py author_candidate.py` 保存局部修改与拓扑/UV/权重约束。
2. `author_atlas.py` 按实际半精度 UV 栅格绘制表面归属；之后运行 `reference_iris.py --select` **一次**。重复选择须先重置程序虹膜底图，避免二次混色。
3. `patch_native.py` 以 R8 的预打包规范 header 为源，直接修补原始 native 载荷的限定字节。独立读取头和缓冲区，保存修改清单。
4. `verify_surface.py`、`verify_geometry.py preflight` 检查表面边界、虹膜前后关系和 UV 范围。
5. `cook_texture.py` 使用隔离项目 cook 三张 VT。`package_candidate.py` 白名单打包、重新提取，并用 CUE4Parse 与 native decoder 独立验证。
6. `verify_geometry.py`、`verify_surface.py`，随后 `verify_mount.py`。挂载检查需要几何报告已生成，不能与它同时运行。
7. `run_blender.py render_native.py` 从最终容器读回的几何渲染三视角。预览使用源 PNG 色彩，**不能等同于游戏 shader、压缩采样与游戏灯光**。`make_comparison.py` 生成同机位私人对比图。
8. 实际审看后写入包含当前输入和图像哈希的 `visual-review.json`。`install-verified.ps1` 在游戏退出、全部校验匹配时替换 Face2 三件套；保存安装凭据和旧 Face2 文件。
9. `verify_mount.py installed` 再检查实际安装目录，`collect_evidence.py` 导出纯数值证据。

Blender 隐藏运行、2 线程、低优先级；UE commandlet 隐藏运行、单线程。不会启动或操作游戏、截图、录屏、删除缓存或修改存档。

`rollback-verified.ps1` 使用安装凭据核验当前全部 MOD，回退为 Face2；R8 裙摆和语音保留。检测到后续安装变更会停止，避免覆盖别的修改。

## 验证边界

最终包读回与挂载、三角索引/权重/骨架/物理数据、其他表面保护、三个近景方向离线审看均分别记录。离线通过不代表游戏所有动作或灯光已经实测。现有刘海块面、脸型和发饰轮廓仍属于原模型造型，此次没有重做完整头像。
