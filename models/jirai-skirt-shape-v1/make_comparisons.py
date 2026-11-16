"""Technical contact sheets of existing offline renders; no synthetic repainting."""
from pathlib import Path
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parents[2]/'private/jirai-skirt-shape-v1';O=W/'preview'
def sheet(files,columns,path,labels=None):
 width,height=400,530;rows=(len(files)+columns-1)//columns
 out=Image.new('RGB',(width*columns,height*rows),'#eeeeee');d=ImageDraw.Draw(out)
 for i,p in enumerate(files):
  im=Image.open(p);im.thumbnail((width,height-30));x=i%columns*width;y=i//columns*height
  out.paste(im,(x,y+30));d.text((x+6,y+8),labels[i] if labels else p.stem,fill='black')
 out.save(path)
files=[O/'shape'/f'{mode}-{angle}.png' for angle in ['front','side'] for mode in ['before','after-static','after-stopped']]
sheet(files,3,O/'shape-comparison.png',['Recovery1 rest','R8 authored rest','R8 after walk/stop']*2)
sheet(sorted((O/'recovery').glob('*.png')),4,O/'recovery-contact.png')
sheet(sorted(p for p in O.glob('coverage-*.png') if p.stem!='coverage-contact'),3,O/'coverage-contact.png')
print('TECHNICAL_COMPARISONS_SAVED')
