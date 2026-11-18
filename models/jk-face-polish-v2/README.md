# JK 岁脸部与同款虹膜细修

以用户认可的地雷岁 LashLip1 所在实际安装集合为基线，单独优化 JK 身体路径 `EscapeOnly/Hun_Body_Simple`。参考 JK 原立绘、JK FaceShape1 三视图与地雷岁当前近景后，保留 JK 较细的眼线、柔和眼眶和原笑嘴；沿用地雷岁的虹膜图案，并压低橙色分量以接近 JK 原图的红瞳。两套模型不共用眼眶或嘴部几何。

在 FaceShape1 之上，小幅抬高、圆润尖下巴，轻收下颊。537 个原生顶点位置变化，最大约 0.370 cm；眼眶、眉睫毛、眼球位置、鼻子和嘴型保持。下巴附近侧视可见的尖片经对照是原有侧发发梢，本轮不改发型。现有眼部几何边缘仍有原生小碎面，未声称完整重建眼球或所有面部瑕疵。

原生虹膜组件 40、41 共 386 个顶点只改 UV，投射到一块独立 1024² 图块。复制当前 Patterns1 的 8K 图集，只在 MI_JK_Base 未占用的区域写入图案；旧图集被使用的像素全部保持。只重定向该原生叶子材质的 Albedo，其他材质继续使用旧图集。Normal 与 Mix 的常量输入另行验证。保留原生 shader、全部索引、分区、蒙皮、264 骨、布料和物理。

顺序为 `common.py` → `author.py` → `verify_geometry.py preflight` → `patch_native.py` → `cook_texture.py` → `package_candidate.py` → `verify_geometry.py` → `verify_mount.py`，再检查隐藏 Blender 的正面、斜面、侧面近景。两线程、低优先级 Blender；单线程隐藏 UE。最终数据独立读回与预览输入哈希完全一致。

`install.py` 默认预检，`--apply` 在游戏退出后按哈希备份替换 JKFaceShape1 三件套，实际读回失败会恢复安装前集合。`--rollback` 默认核验回退，配合 `--apply` 才回退。本次保留地雷岁 LashLip1、裙型、服装图案及语音，其他十八文件哈希不变；131 个保留资源 metadata 与完整导出载荷逐项相同。安装凭据与可回退文件留在 `private/jk-face-polish-v2/`。

原图、角色资产、图集、离线预览、可编辑绑定母版和游戏容器仅留忽略的 private 目录。公开证据只有文字、数值与哈希。没有将 cooked VT 独立解码成像素；源 PNG 离线预览不能复现游戏 shader 与灯光。新 JK 候选已安装，游戏观感尚待用户复试；本候选源码尚未提交远端，Release 未更新。此前认可的地雷岁修改已推送为 `a08a7fc`。
