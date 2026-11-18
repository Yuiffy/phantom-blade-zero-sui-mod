"""Private comparison only; never publish reference-derived images automatically."""
from common import *
from PIL import Image,ImageDraw,ImageFont
def main():
 font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
 out=Image.new('RGB',(1200,2020),(31,34,39));draw=ImageDraw.Draw(out)
 draw.text((22,12),'修改前',font=font,fill='white');draw.text((622,12),'修改后',font=font,fill='white')
 for row,(view,title) in enumerate([('front','眼部、肤色和嘴线'),('shoulder','大臂与袖内衔接'),('halo','光环')]):
  y=52+row*640;draw.text((20,y),title,font=font,fill='white')
  for col,tag in enumerate(['before','after']):
   path=ROOT/('preview' if tag=='before' else 'final')/f'{tag}-{view}.png'
   im=Image.open(path).convert('RGB');im.thumbnail((580,598),Image.Resampling.LANCZOS);out.paste(im,(col*600+(600-im.width)//2,y+34))
 draw.text((20,1980),'离线渲染：最终几何读回＋源 PNG；游戏灯光、采样和动作待实测。',font=small,fill='white')
 out.save(ROOT/'polish-comparison.jpg',quality=94)
 print('POLISH_COMPARISON_WRITTEN')
if __name__=='__main__':main()
