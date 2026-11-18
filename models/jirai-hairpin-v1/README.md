# 地雷岁头饰 Hairpin1

按本地原立绘重做头部右上方的粉色爱心、黑色包边、立体细十字及两条交叉发夹，同时清理头发承载面上的旧饰件投影。没有生成或公开参考美术。爱心边缘采用简化的细装饰边，未逐个重建参考图的蕾丝圈。

基于已安装的 Face3 + R8 Shape1，替换原来三个头饰组件的固定 native 缓冲槽。新饰件为五个闭合实体、394 顶点和 768 三角面，保留原 head 刚性权重。未使用的三角槽归零为无面积备用槽；不改变分区或缓冲区大小。非头饰位置、切线帧、UV 和索引逐字节核验，UV1、权重、骨架、布料及物理载荷保持原样。

`zzzz_Sui_JiraiHairpin1_3_P` 为三个 package 的叠加包：身体网格、Hair 叶子材质和一张真实 cook 的 8K VT。Hair 材质仅改 Albedo 引用，继续使用现有原生父材质和 shader。Skin 与虹膜继续解析为 Face3 资源。当前安装仍保留 Face3、R8 双服装及独立语音文件。

## 本地流程

依赖本机合法取得的游戏模板、Face3 私人源、工具与映射，不能只从公开仓库重建。

1. `common.py` 冻结安装基线；`author.py` 创建饰件、分配未占用的 Hair UV 区域并修补局部旧投影。
2. `patch.py` 仅写入允许的 native 字节；`verify_geometry.py preflight` 检查拓扑、法线、保留表面、UV 归属和爱心正面与头发的间隙。
3. `cook_texture.py` 隐藏、单线程运行 UE；`package_candidate.py` 白名单打包并独立读回最终容器、纹理 bulk 和 native 缓冲。
4. 顺序执行 `verify_geometry.py`、`verify_mount.py`，确认不同输入目录顺序下均解析到候选，Face3 皮肤和虹膜保持原样。
5. `run_blender.py render_preview.py` 隐藏运行 Blender，2 线程、低优先级，渲染正面、近景及斜角。逐张审看后记录当前图集、native 数据与图像哈希到私人 `visual-review.json`。
6. 游戏退出后执行 `install-verified.ps1`，核对全部门禁和九个基线文件，仅添加头饰三件套；随后执行 `verify_mount.py installed`，从实际安装集合读回身体载荷。
7. `collect_evidence.py` 仅导出数值和哈希。`rollback-verified.ps1` 按凭据移出头饰三件套，恢复 Face3 + R8 的解析结果；检测到后续安装变化会停止。

原始立绘、图集、渲染、Blender 工程和容器保存在忽略的 `private/jirai-hairpin-v1/`。公开检查在 `evidence/jirai-hairpin-v1/`，代码许可不覆盖角色、美术和游戏资产。

## 验证边界

离线预览使用最终容器独立解码的几何和对应源 PNG，不能等同游戏 shader、压缩采样或游戏灯光；未独立解码最终 VT 像素。游戏实测待反馈，不会自动启动或控制游戏、截图、录屏、删除缓存或改动存档。
