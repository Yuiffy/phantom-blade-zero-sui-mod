"""Private, equally scaled before/after contact sheet; no generated imagery."""
from common import *
from PIL import Image,ImageDraw,ImageFont

def main():
    previews=ROOT/'native-preview'
    before=Image.open(previews/'before-front.png').convert('RGB')
    after=Image.open(previews/'after-front.png').convert('RGB')
    assert before.size==after.size==(1100,1000)
    canvas=Image.new('RGB',(1440,980),(31,34,42));draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',26)
    small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
    for x,label,im in [(16,'修复前：Face2',before),(728,'修复后：Face3 / R8',after)]:
        draw.text((x,12),label,font=font,fill='white')
        canvas.paste(im.resize((696,633),Image.Resampling.LANCZOS),(x,54))
        crop=im.crop((110,520,990,720)).resize((696,158),Image.Resampling.LANCZOS)
        canvas.paste(crop,(x,705))
    draw.text((16,883),'同机位、同灯光的离线预览；几何来自容器读回，颜色使用对应源贴图。',font=small,fill=(218,222,230))
    draw.text((16,921),'尚未进行游戏实测。保留现有刘海轮廓；此次修复眼部、眉毛、发色串色和嘴周破面。',font=small,fill=(218,222,230))
    path=ROOT/'face3-before-after.jpg';canvas.save(path,quality=94)
    print(path)

if __name__=='__main__':main()
