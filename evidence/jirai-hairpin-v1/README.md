# Hairpin1 验证记录

2026-11-17，基于 Face3 + R8 Shape1 重做右上方头饰，已本地安装，尚未游戏实测。这里仅存数值与 SHA256；原立绘、图集、游戏资源、容器及离线渲染均留在私人目录。

- `author-report.json`：限定原头饰组件，新建 394 顶点、768 三角面、五个实体；保留固定缓冲大小和 head 权重。
- `native-patch.json`：限定 native 字节修改范围，非头饰、UV1、权重、骨架、布料和物理不变。
- `atlas-report.json`：源与结果图集哈希、局部投影清理数量和新 UV 区域。
- `verification.json`：最终三 package 白名单、独立读回、8K/14 mip VT 和容器哈希。
- `geometry-verification.json`：闭合与一致朝向、切线法线、其他表面保护及爱心正面间隙。
- `installation.json`：实际安装十二文件清单，原有九文件精确保留，实际挂载与 native 载荷读回通过。
- `visual-review.json`：正面、细节、斜角及同机位对比已审阅，记录私人图像哈希。

离线渲染使用独立解码的最终 native 几何与源 PNG，未独立解码 cooked VT 像素，不能代表游戏 shader 和灯光。装饰边为简化轮廓，未逐圈重建参考图蕾丝。没有自动启动或操作游戏。
