# 模型

2026-11-16 后续本地安装版为 JK Motion v5 + 地雷岁 R6 SkinEyes1 Fishnet1：[皮肤材质与眼白修复](skin-eyes-v1/README.md)、[规则渔网袜与 8K 图集](fishnet-v1/README.md)。制作代码和离线证据已保存，原始游戏模板、图集、可编辑母版及安装容器留在 private；现有 Release 仍为 R5。

2026-11-16 保存的 [地雷岁 R5 检查点](jirai-r5-checkpoint/README.md)：无棉花翅膀，包含完整可编辑母版和内嵌贴图，已获用户整体质量认可。当时安装的双服装对应为黑伤（逃亡）= JK Motion v5，黑伤=地雷岁 R5。旧版源与历史说明继续保留，当前事实以根 README 和安装摘要为准。

`sui-hun-binding.glb` 是本次实机成功版本使用的旧岁己几何和刚性附件绑定，源自 `Yuiffy/my-pixijs-game` 的 `assets/after-hours/sui.blend`。GLB 包含 46 个 mesh、1 个 skin，贴图内嵌，无外部路径依赖；可以导入 Blender 继续编辑。

原始项目是浏览器游戏，游戏内换装使用的材质和烘焙纹理由后续 UE 流水线生成，因此 GLB 预览不代表游戏最终光照效果。上述 GLB 是旧衣模型；新衣 JK 当前安装版本是 [v8](jk-v8-candidate/README.md)。v8 恢复更紧凑的实际白领口和较窄的上身比例，保留 v7 下半身及握点，已获游戏内截图反馈，裙子串色、吊带和手指问题待下一版修复，测试范围见 v8 说明。没有完整面部曲线适配或新的头发物理。

绑定适配使用目标 build 的骨名和参考变换，不附带原版角色的可见几何或动画。替换新模型时保留目标骨架，再重做权重、刚性附件与材质烘焙；不要直接换 GLB 文件就认为 MOD 已更新。

文件 SHA256 见 `manifest.json`。模型及角色形象不适用仓库代码的 MIT 许可，见根目录 NOTICE.md。

[v9 离线候选](jk-v9-candidate/README.md) 修复手指转轴偏移、裙/外套串色及重复吊带，重建白羽翼金心和背带白猫。已按用户近景反馈连好猫头、蝴蝶结与放大的身体，清理翼饰上方的旧贴图残影。保留 v8 肩颈、头、裙和腿的几何。未安装、未游戏实测；[对照图](../evidence/jk-v9-offline/ornaments-v8-v9.jpg)。

[v10 离线候选](jk-v10-candidate/README.md) 修正右腋下衣身权重泄漏及对应表面位置，清理右背串色和书包内侧投影。保留 v9 手部、猫挂件与袜饰修复。未安装、未游戏实测；[离线对照](../evidence/jk-v10-offline/guard-and-bag-v9-v10.jpg)。
