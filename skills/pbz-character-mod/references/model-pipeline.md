# 模型制作与验证

## 1. 定位目标

记录 Steam app/build、目标外观和提取工具版本。按外观表 ItemId 解析选择关系，再追踪部件引用。显示名称或中文行名不一定是 ItemId。默认/高潮/过场可能绕过外观表，不能靠表内检查声称全场景替换。

单服装策略：复制待替换部件 ID，令目标服装引用自有 mesh/material 路径；其他服装继续引用原资源。清点头发、帽子、身体与附件实际类型，不把 GroomAsset 或 ChaosClothAsset 路径粗暴替换成 SkeletalMesh。隐藏仍需尊重原导出类型和依赖。

## 2. Blender 与骨架

从对应游戏 mesh 读出参考骨架，而不只用 USkeleton 全集。检查 root、父子索引、局部矩阵、骨名及武器子骨。FBX/GLB 导出后再次读取验证；Blender 中看起来一致不能保证序列化数据一致。

本次成年身体 264 骨，包含 4 根 weapon child 骨；隐藏 head 889，hat 1，四个隐藏附件各 1134。它们是本案例的检查值。刚性翅膀/发饰绑定到合适的原骨，保持骨名映射；没有新增物理。

## 3. 材质是定制引擎的兼容边界

官方 UE 5.7.4 烘焙出的自定义母材质可被工具解析，但其 FMaterialShaderMapContent 布局签名与本游戏不一致。解决方案是复用本机游戏存在的父材质及 shader，不是修改签名。

本次叶子 MI 的 parent：

```text
/Game/PBZContent/Characters/Hero/Hun_New_V2b/Material/MI_ZeroHun_Cloth_02_b
```

15 个叶子 MI 无自有 shader resource/静态排列。`Albedo`、`Normal`、`Mix` 使用 `LayerParameter`、Index `0`；缓存 `ParentLayerIndexRemap = [0,1]`。这些是本父材质的约定，换父材质须重新读取参数和缓存结构。隐藏路径原先为 Material，改成 MaterialInstanceConstant 后，所有相关 Import 的 ClassName 也要改。

30 张纹理实际导入、保存并 cook 为虚拟纹理。Albedo 使用 sRGB；Normal 使用 normalmap 压缩；Mix 使用线性 mask 数据。不能只把普通贴图的 VT 标记翻转。原 5 张绘制 PNG 未修改，纯色与 ARM 数据来自旧材质数值。最终容器检查 VT 数据与 bulk 边界。

UE commandlet 的参数形态（环境路径由调用者指定）：

```text
UnrealEditor-Cmd <project.uproject> -unattended -nop4 -stdout -onethread -run=pythonscript -script=<import.py> -NullRHI -NoShaderCompile -NoShaderWorker
UnrealEditor-Cmd <project.uproject> -unattended -nop4 -stdout -onethread -run=Cook -TargetPlatform=Windows -NoDefaultMaps
```

自制资源采用 versioned cook。项目、目标插件挂载点和 cook 输出路径必须匹配最终引用。该流程需要使用者自行准备提取的原版模板和工具，仓库未附游戏资产或一键重建环境。

## 4. cooked 数据编辑的陷阱

- UAssetGUI 1.1.0 在某些 FName 无效时会退出码 0、却不产出文件；同时检查文件存在、结构与日志。
- `MI_Sui_13` 的数字后缀通常编码为基础名+实例号，`_02` 不同。添加全名时还要按 FName 规则准备基础名。
- 新增名称后更新 `NamesReferencedFromExportDataCount`，否则容器转换可能遗漏名称。
- JSON 重写曾丢失 `OptionalProperty<BoolProperty>` 的 BoolProperty 类型参数。对只改路径/材质引用的网格，保留原 `.uexp` 和 export records，重定位 header 偏移；再用独立 parser 验证。不要盲目复用旧导出到已改变数据布局的资产。
- 原版无版本头资产和自制有版本头资产可能需要不同回退解释。本次原版外观表 legacy 转换使用 UE5_6；UE5_7 回退失败。retoc UE5_6/UE5_7 对本次 versioned body/material 结果字节相同，改选项不是修复。
- 不打包 Engine/global shader/config/JS/AssetRegistry 等无关内容。只允许本次目标 package 白名单。

## 5. 最终核验与实机

列出最终 IoStore 包清单；解包后核验实际父材质、imports、骨架、纹理 bulk、完整 native payload，以及外观选择表。独立读取器应与写入工具不同，本次使用 CUE4Parse。保存每个输出文件大小/SHA256；已安装文件再次核验。

本次成功包 53 packages：7 mesh、15 MI、30 VT、1 外观表。网格与外观表完整导出载荷相对失败 v3 不变，材料依赖改变。

实机按实际授权测试存档加载、外观选择、动作、武器、过场和长时间游玩，记录观察范围。先确保没有其他候选叠装。新增语音用独立容器，失败时能只撤语音。不要删缓存、改存档或自动启动游戏来替代诊断。
