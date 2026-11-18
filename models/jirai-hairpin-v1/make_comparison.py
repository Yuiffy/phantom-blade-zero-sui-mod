"""Arrange existing offline renders into a private comparison sheet."""
from common import *
from PIL import Image,ImageDraw

def main():
 before=Image.open(FACE/'native-preview/after-front.png').convert('RGB')
 after=Image.open(ROOT/'preview/after-front.png').convert('RGB')
 sheet=Image.new('RGB',(1200,840),'#20232a');draw=ImageDraw.Draw(sheet)
 for x,im,label in [(0,before,'BEFORE'),(600,after,'AFTER')]:
  detail=im.crop((850,90,1100,480)).resize((500,780),Image.Resampling.LANCZOS)
  sheet.paste(detail,(x+50,50));draw.text((x+50,15),label,fill='white')
 draw.text((50,825),'Offline native geometry preview / source PNG albedo / game test pending',fill='white')
 sheet.save(ROOT/'hairpin-comparison.png')
 print('HAIRPIN_PRIVATE_COMPARISON_READY')

if __name__=='__main__':main()
