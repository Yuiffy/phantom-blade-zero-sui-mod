岁己 JK＋地雷系双皮肤＋战斗语音 · v1.0.0 一体包

模型：JK Motion v5＋地雷岁 R5（无翅膀）。
语音：Compact v5 测试版，与已单独发布的语音包文件完全一致。
适用 Steam app 4115450 / build 26367565，成年魂。

安装：
1. 完全退出游戏，备份并移出本项目旧模型和旧语音包，避免不同版本叠装。
2. 将 mod/ 下六个文件一起放入：
   <游戏目录>/ProjectPBZ/Content/Paks/~mods/
   模型三件套：z_Sui_DualOutfit_JK5_JiraiR5_P.pak / .utoc / .ucas
   语音三件套：z_Sui_Hun_NaturalVoice_Compact_v5_P.pak / .utoc / .ucas
   已装同名同哈希文件可保留，无需重复安装。无需 Python、UE 或本地声音生成。
3. 黑伤（逃亡）选择 JK 外套侧马尾；黑伤选择地雷系双马尾。
   语音为成年魂共享战斗事件，可用于这两套服装及其他成年魂服装。
   不替换少年魂或剧情对白，不改变原服装解锁条件。

语音使用既有二审选定的 21 段岁己录音，不含新生成配音或变声。
语音 v5 仍为测试版：最终容器离线验证通过，不代表所有武器、语言与动作均经游戏实测。
如需纯模型，可只复制模型三件套。不要把完整六件一体包与旧包重复叠装。
卸载语音时退出游戏，仅移除 Compact_v5 三件套；模型可单独保留。
卸载全部时退出游戏，仅移除上述六个文件；需要回退时放回备份。

文件清单见 bundle-manifest.json；来源与许可见 NOTICE.md、voice/NOTICE.md 和 voice/audio-provenance.json。
所有模型、纹理、录音与游戏派生二进制不适用代码 MIT 许可。
previews/ 为离线 Blender 预览。所有战斗、武器、过场与长时间稳定性尚未逐项验证。

可选 Python 3.10+ 校验（不是安装依赖）：
python scripts/mod_files.py verify --manifest model-manifest.json
python scripts/mod_files.py verify --manifest voice-manifest.json
