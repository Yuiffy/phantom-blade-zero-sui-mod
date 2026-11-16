# 地雷岁渔网袜修整 v1

基于已安装的 JK5 + 地雷岁 R6 SkinEyes1。只替换 `/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Base`，其余 98 个包的独立解析结果、网格/布料/眼白 native 载荷保持一致。不会改动其他候选目录。构建、安装和游戏实测分别记录，最终状态见 `../../evidence/fishnet-v1/summary.json`。

检查发现渔网画在 component 5 的负 X 小腿皮肤图集上，使用 `MI_Jirai_Skin`，并不是独立的 Legwear 网格。原图腿侧存在断线、重影、线宽与间距不一；原 4K 图集该处约 10 px/cm。单纯提锐度不能补齐错位网线。

`inspect_surface.py` 只读当前 SkinEyes1 Blender 母版，导出表面来源、UV、材质与检查图。`author_atlas.py` 按三维小腿表面绘制连续的菱形网格，周期绕周闭合，按椭圆半径控制实际线宽。使用稳健拟合恢复网线下的平滑底色，16 个子像素采样保留细线边缘；沿实际下方绑带的倾斜边缘收口，保留两条绑带间的裸肤。补边清除本区域原有残线，并保护其他 UV 岛。

图集增至 8K，使小腿约有 20 px/cm；改绘蒙版外保留原图的双线性放大结果。提高的是网线的有效密度，其他部位不会凭空增加细节。旧输入、改绘蒙版、哈希和未采用的首轮结果只存放在 `private/fishnet-v1`。

`cook_texture.py` 在独立、仅含该贴图的 UE 工程中真实导入并 cook sRGB VT。`package_candidate.py` 从当前 SkinEyes1 成品组合完整 99 包容器；由独立的 CUE4Parse 读回确认 8K、DXT1、14 层 mip、bulk 边界，以及其余 98 包的语义和 native 载荷。保留现有皮肤材质、闭合眼白、JK5 与全部物理。

`render_candidate.py` 使用同一几何、相机和灯光输出正、背、侧面近景对比，只用于检查图案、UV 接缝及袜口范围，不模拟 PBZ 原生着色器。`install-verified.ps1` 在游戏退出时核验当前 MOD 快照，备份旧容器并安装新三件套，验证失败自动回退，语音保持原哈希。不自动启动或结束游戏进程。

本机流程依赖此前已准备的合法游戏模板、UE、Blender 与提取工具，路径见脚本。原游戏资产和含图集的构建产物留在 private，不作为仓库代码许可的一部分；角色内容的许可边界沿用根 NOTICE.md。此项未改动裙摆候选。

1. 后台运行 Blender `inspect_surface.py`。
2. 运行 `python models/fishnet-v1/author_atlas.py`。
3. 后台运行 Blender `render_candidate.py`，人工检查三方向近景。
4. 运行 `python models/fishnet-v1/cook_texture.py` 和 `package_candidate.py`。
5. 最终验证通过且游戏退出后，运行 `pwsh -NoProfile -File models/fishnet-v1/install-verified.ps1`。

已经存在的已打包候选应先归档；`package_candidate.py verify` 仅重验当前候选，不覆盖安装。
