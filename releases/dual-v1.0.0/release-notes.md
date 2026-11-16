岁己双皮肤合并正式版，直接采用当前已安装、获用户认可并批准发布的 **JK Motion v5＋地雷岁 R5**。推荐下载 **`Sui_JK_Jirai_WithVoice_PBZ_v1.0.0.zip`**，内含两套皮肤与 Compact v5 战斗语音。原纯模型包继续保留。

| 游戏内服装 | 替换皮肤 |
| --- | --- |
| 黑伤（逃亡） | 岁己 JK 服有外套侧马尾（JK Motion v5） |
| 黑伤 | 地雷系双马尾，无翅膀（Jirai R5） |

黑伤内部无帽变体同样使用地雷系。不处理少年魂，保留服装原有解锁条件。

JK 包含马尾、白猫挂饰和受限衣摆、裙摆、包体摆动，修复不透明安全裤覆盖，增加白猫厚度和局部衣服碰撞避让。地雷系包含比例、手部、肩袖与腿根修正，双马尾和裙摆物理，已移除棉花翅膀。

1. 退出游戏，备份并移出本项目旧模型和旧语音包，避免不同版本叠装。
2. 一体包将 `mod/` 内六个文件（模型三件套＋语音三件套）一起放入 `<游戏目录>/ProjectPBZ/Content/Paks/~mods/`。
3. 进入游戏，选择上表对应服装。退出游戏后可分别卸载：模型移除 `z_Sui_DualOutfit_JK5_JiraiR5_P` 三件套，语音移除 `z_Sui_Hun_NaturalVoice_Compact_v5_P` 三件套；卸载全部则移除这六个文件。

无需 Python 或 UE。本包已合并外观表，**不要叠装旧模型或修改同一外观表的其他 MOD**。一体包已含语音；原 `Sui_JK_Jirai_DualOutfit_PBZ_v1.0.0.zip` 仍是纯模型。也可单独下载本页的 `Sui_Voice_v5_Compact_Beta1.zip`。

验证环境：Steam app **4115450**、build **26367565**。最终 88 个资源包经独立读取器核对，两个模型的骨架和渲染数据、布料映射与材质依赖及 68 行合并外观表均已检查；发布模型三件套与已安装版 SHA256 完全一致。用户反馈“不错，可以发布一版release了，直接作为两个皮肤一起发布”。所有动作、武器、过场、长时间运行和其他游戏版本尚未逐项验证；离线测试不保证任何动作下都无穿模。

下图是本项目离线 Blender 预览：地雷系全身、JK 白猫挂饰细节，均非游戏截图。

![地雷系双马尾全身预览](https://raw.githubusercontent.com/Yuiffy/phantom-blade-zero-sui-mod/dual-v1.0.0/releases/dual-v1.0.0/previews/jirai-front.png)

![JK v5 白猫挂饰细节](https://raw.githubusercontent.com/Yuiffy/phantom-blade-zero-sui-mod/dual-v1.0.0/releases/dual-v1.0.0/previews/jk-pendant.png)

ZIP SHA256：`252aae5f8643a6de607b55717e080263fee0f83dd510a0811ee10a2070efc168`。另附 `SHA256SUMS.txt` 与 `manifest.json`；包内含安装说明、校验清单和来源说明。模型、角色、贴图及游戏派生数据不适用代码 MIT 许可，详见包内 `NOTICE.md`。

语音使用二审选定的 21 段既有岁己录音，覆盖 28 个修改后战斗事件、474 个语言/媒体槽；适用于成年魂共享战斗声音，不替换少年魂或剧情对白。没有新生成配音或变声。语音仍保留 **Compact v5 测试版** 状态：离线核验通过，全部武器、语言和动作的实机覆盖尚未逐项确认。语音可单独卸载，仅移出 `z_Sui_Hun_NaturalVoice_Compact_v5_P` 三件套即可保留模型。已安装这版语音的用户无需重复安装。

一体包大小：22,095,334 字节；SHA256：`0e77ef7e2ead67119f8071cdf8d7132fbe21e66ae36c0973054fa1c14dedd894`。语音独立 ZIP：728,751 字节，SHA256：`bbed38b7b28ba08f11d70e1d2c5f25ab11015d670efed97ebb74291c4d118624`。新增 `BUNDLE_SHA256SUMS.txt` 与 `bundle-manifest.json`，保留原纯模型校验值不变。包内附逐段录音来源与许可范围。
