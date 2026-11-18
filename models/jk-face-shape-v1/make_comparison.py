from common import *
from PIL import Image, ImageDraw, ImageFont

def main():
    folder=ROOT/'final-preview';font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
    canvas=Image.new('RGB',(1000,1030),(28,29,33));draw=ImageDraw.Draw(canvas)
    for row,view in enumerate(['front','threequarter']):
        for col,tag in enumerate(['before','final']):
            im=Image.open(folder/(tag+'-'+view+'.png')).convert('RGB')
            im=im.crop((0,340,900,1000)).resize((500,367),Image.Resampling.LANCZOS)
            y=40+row*410;canvas.paste(im,(col*500,y))
            draw.text((col*500+18,y-30),('调整前' if tag=='before' else '脸型调整后')+(' · 正面' if row==0 else ' · 斜侧'),font=font,fill=(238,238,240))
    draw.text((20,880),'同机位离线渲染；眼睛、嘴巴和贴图保持原样',font=font,fill=(225,225,230))
    draw.text((20,920),'下颌横向约收窄 9.5%，不代表游戏内灯光效果',font=font,fill=(195,196,205))
    canvas=canvas.crop((0,0,1000,970));canvas.save(folder/'comparison.png')
    print('JK_FACE_COMPARISON_SAVED')

if __name__=='__main__':main()
