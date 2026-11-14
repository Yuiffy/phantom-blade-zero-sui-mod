from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'delivery';OUT.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',25)
rows=[]
for name,title in [('rear-hem','后裙色斑与书包染色'),('legs-splayed','分腿：吊带和袜口附件'),('hand-curl','同一弯指姿势'),('front-thigh','袜口与贴腿吊带')]:
 canvas=Image.new('RGB',(1208,600),(27,29,33));d=ImageDraw.Draw(canvas);d.text((16,10),title,font=font,fill='white')
 for i,tag in enumerate(['v8','v9']):
  im=Image.open(ROOT/f'{tag}-{name}.png').convert('RGB');im.thumbnail((600,510),Image.Resampling.LANCZOS);canvas.paste(im,(i*608+(600-im.width)//2,85));d.text((i*608+16,47),tag,font=font,fill='white')
 canvas.save(OUT/(name+'-v8-v9.jpg'),quality=94)
 rows.append(canvas)
sheet=Image.new('RGB',(1208,len(rows)*608),(27,29,33))
for i,row in enumerate(rows):sheet.paste(row,(0,i*608))
sheet.save(OUT/'v8-v9-detail-comparison.jpg',quality=94)
ornament_rows=[]
for name,title in [('charm','背带白猫：连贯身体、蝴蝶结与扣带'),('wing','袜饰：分层羽翼、金心与干净袜面')]:
 canvas=Image.new('RGB',(1208,725),(27,29,33));d=ImageDraw.Draw(canvas);d.text((16,10),title,font=font,fill='white')
 for i,tag in enumerate(['v8','v9']):
  im=Image.open(ROOT/f'{tag}-{name}-detail.png').convert('RGB');im.thumbnail((590,630),Image.Resampling.LANCZOS);canvas.paste(im,(i*608+(600-im.width)//2,85));d.text((i*608+16,47),tag,font=font,fill='white')
 canvas.save(OUT/(name+'-v8-v9.jpg'),quality=95);ornament_rows.append(canvas)
sheet=Image.new('RGB',(1208,1466),(27,29,33))
for i,row in enumerate(ornament_rows):sheet.paste(row,(0,i*733))
sheet.save(OUT/'ornaments-v8-v9.jpg',quality=95)
