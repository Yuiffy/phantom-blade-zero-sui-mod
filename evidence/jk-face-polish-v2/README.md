# JK 岁脸部与虹膜候选核验

2026-11-18，JKFacePolish2 已按凭据替换 JKFaceShape1 三件套。保留 JK 原眼眶、细眉睫毛、眼球位置和笑嘴；采用地雷岁同款虹膜图案并向 JK 原图红瞳调色。下巴轻微抬高、圆润，下颊局部收敛。脸部 537 个原生位置变化，最大约 0.370 cm；两组虹膜共 386 顶点只改 UV。最终成品没有三角翻转，原重合接缝位移差为零。

三 package 白名单：JK 身体、MI_JK_Base 和新 8K sRGB VT。材质父类、shader、Normal、Mix 与导出载荷保持，只有 Albedo 导入指向新图集。旧图集原 Skin/Base 占用像素全保持，新虹膜在独立空区采样；原拓扑、完整蒙皮、骨架、布料与物理不变。构建时使用保留原外部依赖引用的作者 header，避免把缺依赖上下文的 retoc 提取 header 重新打包造成空引用；该草稿未安装，成品依赖和 metadata 已独立检查。

`verification.json` 记录 CUE4Parse、retoc、UAssetAPI 及 native reader 的最终读回、VT bulk 边界和限定字节变化。`geometry-verification.json` 记录五官、接缝、三角形与像素保护。`installation.json` 记录实际安装读回，其他十八文件逐项哈希不变，131 个保留资源的 metadata 和完整导出载荷相同，包括地雷岁及语音。回退预检通过，未执行回退。

`visual-review.json` 绑定三方向离线近景、JK 原图和地雷岁对照输入哈希；预览 native 数据与最终容器读回相同。`editable-source.json` 记录完整 264 骨绑定母版。预览使用源 PNG，不代替 cooked VT 像素解码、原生 shader 和游戏灯光。没有启动或操作游戏，新候选外观与动态表现尚待用户复试。
