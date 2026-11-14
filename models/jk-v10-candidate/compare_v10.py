from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parent;V9=R.parent/'tripo-refine-v9';OUT=R/'delivery';OUT.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
canvas=Image.new('RGB',(1440,1600),'#20232a');d=ImageDraw.Draw(canvas)
rows=[('抬臂侧后方：v9 → v10（人工诊断姿势）',V9/'guard-before-high-side.png',R/'guard-after-high-side.png'),('书包朝向身体的一面：隐藏身体以便检查',R/'bag-inner-v9.png',R/'bag-inner-v10.png')]
for row,(label,left,right) in enumerate(rows):
 y=42+row*760;d.text((22,y),label,font=font,fill='white')
 for col,p in enumerate([left,right]):
  im=Image.open(p).convert('RGB');im.thumbnail((700,660));canvas.paste(im,(col*720+(720-im.width)//2,y+46))
  d.text((col*720+24,y+710),'v9 修正前' if col==0 else 'v10 修正后',font=small,fill='white')
d.text((22,1560),'Blender CPU 预览；未安装、未执行游戏动画，仍需游戏内验证。',font=small,fill='#c6cbd4')
canvas.save(OUT/'guard-and-bag-v9-v10.jpg',quality=92)
b=json.loads((V9/'guard-before.json').read_text());a=json.loads((R/'guard-after.json').read_text())
(R/'guard-comparison.json').write_text(json.dumps({'baseline':'JK v9 ce1a1de','baseline_positions_used_for_same_region':True,'each_version_uses_own_rest_edge_lengths':True,'geometry_also_changed':True,'manual_proxies_only':True,'runtime_tested':False,'before':b['poses'],'after':a['poses']},indent=2))
