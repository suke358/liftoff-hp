"""python3 thumb.py <pc.png> <sp.png> <out.jpg> <bg hex>  → 1200x780 の一覧画像"""
import sys
from PIL import Image, ImageDraw, ImageFilter
pc,sp,out,bg=sys.argv[1:5]
W,H=1200,780
im=Image.new('RGB',(W,H),bg)
def shadow(box,r,blur=28,alpha=60,off=14):
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(sh)
    x0,y0,x1,y1=box; d.rounded_rectangle((x0,y0+off,x1,y1+off),r,fill=(20,25,30,alpha))
    return sh.filter(ImageFilter.GaussianBlur(blur))
# PC
bx,by,bw=40,56,960; bar=28
p=Image.open(pc).convert('RGB').resize((bw,600))
im.paste(Image.alpha_composite(im.convert('RGBA'),shadow((bx,by,bx+bw,by+bar+600),6)).convert('RGB'))
d=ImageDraw.Draw(im)
d.rectangle((bx,by,bx+bw,by+bar),fill='#efefef')
for i,c in enumerate(['#ff5f57','#febc2e','#28c840']): d.ellipse((bx+12+i*20,by+8,bx+24+i*20,by+20),fill=c)
im.paste(p,(bx,by+bar))
# phone
fx,fy,fw,fh=890,190,270,560; bez=12
im2=Image.alpha_composite(im.convert('RGBA'),shadow((fx,fy,fx+fw,fy+fh),40,24,90,12)).convert('RGB')
d=ImageDraw.Draw(im2); d.rounded_rectangle((fx,fy,fx+fw,fy+fh),40,fill='#1c1c1e')
sw,shh=fw-2*bez,fh-2*bez
s=Image.open(sp).convert('RGB'); s=s.resize((sw,int(s.height*sw/s.width))).crop((0,0,sw,shh))
m=Image.new('L',(sw,shh),0); ImageDraw.Draw(m).rounded_rectangle((0,0,sw,shh),30,fill=255)
im2.paste(s,(fx+bez,fy+bez),m)
im2.save(out,quality=86)
