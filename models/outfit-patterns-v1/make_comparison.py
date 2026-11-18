"""Arrange private reference and same-camera offline detail renders."""
from common import *
from PIL import Image,ImageDraw

def main():
 cases=[('jk-arm','JK armband',(55,310,740,925)),('jk-chest','JK bow',(180,190,685,610)),('jirai-chest','Jirai bow',(175,350,730,715))]
 sheet=Image.new('RGB',(1440,1410),'#20232a');draw=ImageDraw.Draw(sheet)
 for row,(key,label,box) in enumerate(cases):
  outfit,view=key.split('-');y=row*460
  draw.text((20,y+12),label,fill='white')
  for col,tag in enumerate(['before','after']):
   im=Image.open(ROOT/'final'/f'{outfit}-{tag}-{view}.png').convert('RGB').crop(box)
   im.thumbnail((680,400),Image.Resampling.LANCZOS);x=col*720+(720-im.width)//2
   sheet.paste(im,(x,y+45));draw.text((col*720+25,y+30),tag.upper(),fill='white')
 draw.text((25,1390),'Offline native geometry + source PNGs; cooked VT pixel decode / gameplay not tested',fill='white')
 sheet.save(ROOT/'patterns-comparison.jpg',quality=93)
 print('PATTERN_PRIVATE_COMPARISON_READY')
if __name__=='__main__':main()
