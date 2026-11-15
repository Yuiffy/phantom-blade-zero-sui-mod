# 内容来源与许可范围

本仓库的原创脚本和原创技术文字由 Yuiffy 发布，按 LICENSE 中的 MIT 条款提供。第三方链接指向各自作者的作品；本仓库没有代其授予许可。

`models/sui-hun-binding.glb` 来自 Yuiffy 的 `my-pixijs-game` 中旧版岁己模型，经本项目适配成年魂骨架、修正刚性附件绑定。角色设计、游戏骨骼及其派生内容的权利仍归各自权利方。模型和 Release 中的 MOD 二进制不适用本仓库的 MIT 许可，未额外授予商业使用或再授权权利。这不是官方模型或官方支持项目。

`models/jk-v6-candidate` 至 `models/jk-v10-candidate` 的新衣 JK 模型源于用户在 Tripo 智能网格模式生成并导出的 FBX（原始 ZIP 标识 `cd0cef28-06a8-4cc8-87d2-1ff513c2bf17`），随后在 Blender 中清理、细化并适配骨架。设计依据为岁己单马尾新衣参考立绘及用户确认的生成三视图；v9 的羽翼、金心和白猫挂件在此基础上重新建模，图集有局部修复；v10 继续修正抬臂衣身绑定与外套/书包内侧图集。这些角色、模型、纹理和游戏骨架派生文件不适用代码 MIT 许可，仓库不代表角色权利方、Tripo 或游戏开发者作额外授权。预览图为本项目 Blender 渲染，不是游戏实测截图。

`models/jk-v11-candidate`、`models/jk-motion-v1-candidate` 和 `models/jk-motion-v2-candidate` 继续派生自上述来源：细修裙色、袜饰、手部、吊点，添加作者制作的受限模拟导向网格、挂饰图集、物理配置及局部表面修复。相同的角色、模型、纹理和骨架许可边界继续适用。物理预览由本地离线 Chaos 输出重建，不是游戏录像；v2 本轮没有调用 AI 图像润色。编辑器辅助插件源码为本项目作者工具，未将编译后的插件或 UE 分发进仓库。

`models/jk-motion-v3-candidate` 在 v2 上裁短独立内衬裤脚，保留相同来源与许可边界；该目录未改贴图，FBX 复用 v2 的 PNG，Blend 内嵌贴图。前后对比为离线 Blender 渲染。

`models/jk-motion-v4-candidate` 继续派生自相同来源，修复安全裤裆底、裤口与内部材质覆盖；未新增贴图。模型、角色、纹理及游戏骨架派生内容沿用上述许可边界，姿势预览为离线渲染。

Release 仅分发安装此替换所需的修改后容器。没有附带原版游戏容器、原版角色几何、动画库、提取工具、UE、AES 密钥、崩溃转储、用户存档、完整直播录播或语音音源。

语音实验素材索引来自 Yuiffy 的 `suiji-sui-button`。当前公开内容仅为方法、事件映射和来源文件名/哈希，不包含原声文件；说话者、背景声和实际听感仍需人工核验。

参考：

- https://github.com/Yuiffy/my-pixijs-game
- https://github.com/Yuiffy/suiji-sui-button
- https://github.com/ccd775/GameModdingKnowledge
- https://github.com/StarryNightSquad/Phantom-Blade-Zero

不把参考作者在其他游戏 build 的经验当成本项目当前版本的实测结论。
