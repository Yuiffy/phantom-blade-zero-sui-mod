# 地雷岁 R7 离线证据

**2026-11-17：用户实机否定此候选，普通走动后裙摆翻卷。已禁止重新安装。**原离线结果仅保留历史，不能作为游戏内恢复正常的证明。用户同意保留几何与安全裤，另做参数恢复实验。`models/jirai-skirt-v1/rollback-verified.ps1` 可只读核验原 R6 SkinEyes1＋Fishnet1 备份，加 `-Apply` 才恢复，游戏运行时拒绝写入。后续修改见根 README；不要直接重跑本目录安装流程。

`result.json` 记录本次输入、独立读回、安装状态和旧版对比。原有动作预览均为离线 Blender 渲染，来自真实 Chaos 输出及最终 cooked 网格重建，不是游戏截图。作者合成动作不覆盖原游戏全部动画。

`coverage-*.png` 隐藏了裙子和其他衣饰，用于检查安全裤裤底与分腿覆盖。腿/裙交线同时保留原始统计和有限视线遮挡后的统计；这些数量不是穿模面积，也不能证明所有游戏视角完全无穿模。模型与预览沿用根目录 NOTICE.md 的许可边界。

`user-runtime-skirt-flip.png` 是用户主动提供的实机附件，展示站姿下裙摆翻起；不是代理截图。R7 的安装前六文件状态已按哈希恢复，见 `rollback-summary.json`。

复查离线 helper 发现初始化的 `ClothTeleportMode=TeleportAndReset` 未被消费，旧流程不能证明连续物理稳定或回落行为，见 `evidence/jirai-r7-skirt/harness-audit.json`。历史数值与图像保留，但不再用来宣称连续模拟通过。新候选已修正标记消费并记录逐采样帧状态。
