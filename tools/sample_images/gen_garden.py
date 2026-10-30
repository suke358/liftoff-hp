#!/usr/bin/env python3
"""造園・庭づくり系のお店の試作用：庭のサンプル画像（イラスト）を描く。写真ではない。角に「サンプル画像」と入れる（2026/10/30 山口造庭舎で作成）
使い方:  python3 tools/sample_images/gen_garden.py 出力フォルダ
  できるもの：menu-sentei/niwa/gaikou/bassai.jpg・belt-1〜4.jpg・cmp-before/after.jpg（1000×750）・hero-garden.jpg（1600×1000）
  本物の写真（オーナー撮影・了承ずみ）が来たら差しかえる。差しかえるときはファイル名も変える
  要 Pillow（pip3 install pillow）。日本語のフォントは Noto Sans CJK（Mac は FONT の行を Hiragino などに変える）"""
import os, sys, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else './garden-out'
os.makedirs(OUT, exist_ok=True)
FONT = next((f for f in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc', '/Library/Fonts/Arial Unicode.ttf'] if os.path.exists(f)), '')
S = 2  # 描く大きさの倍率（あとで縮めてなめらかにする）


def font(size):
    for i in range(6):
        try:
            f = ImageFont.truetype(FONT, size, index=i)
            if 'JP' in f.getname()[0] or 'ヒラギノ' in f.getname()[0] or 'Hiragino' in f.getname()[0]:
                return f
        except Exception:
            pass
    return ImageFont.truetype(FONT, size)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Scene:
    def __init__(self, W, H, sky_top, sky_bot, seed=1):
        self.W, self.H = W * S, H * S
        self.w, self.h = W, H
        self.im = Image.new('RGB', (self.W, self.H))
        self.d = ImageDraw.Draw(self.im)
        self.r = random.Random(seed)
        for y in range(self.H):
            self.d.line([(0, y), (self.W, y)], fill=mix(sky_top, sky_bot, y / self.H))

    def X(self, v): return int(v * self.W)
    def Y(self, v): return int(v * self.H)

    def hills(self, y, color, amp=0.05, k=1.0, ph=0.0):
        pts = [(0, self.H)]
        for x in range(0, self.W + 8, 8):
            yy = self.Y(y) - math.sin(x / self.W * math.pi * 2 * k + ph) * self.Y(amp) - math.sin(x / self.W * 9 + ph) * self.Y(amp * 0.25)
            pts.append((x, yy))
        pts.append((self.W, self.H))
        self.d.polygon(pts, fill=color)

    def ground(self, y, c1, c2, rake=False):
        for yy in range(self.Y(y), self.H):
            self.d.line([(0, yy), (self.W, yy)], fill=mix(c1, c2, (yy - self.Y(y)) / max(1, self.H - self.Y(y))))
        if rake:  # 砂利の筋
            for i in range(14):
                yy = self.Y(y) + (self.H - self.Y(y)) * (i + 1) / 15
                pts = [(x, yy + math.sin(x / 90 + i) * 4) for x in range(0, self.W, 20)]
                self.d.line(pts, fill=mix(c1, (255, 255, 255), .25), width=2 * S // 2 + 1)

    def blob(self, cx, cy, rx, ry, c, shade=True):
        cx, cy, rx, ry = self.X(cx), self.Y(cy), self.X(rx), self.X(ry)
        if shade:
            self.d.ellipse([cx - rx, cy - ry + ry // 5, cx + rx, cy + ry + ry // 5], fill=mix(c, (0, 0, 0), .28))
        self.d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=c)
        self.d.ellipse([cx - rx * .7, cy - ry * .95, cx + rx * .6, cy + ry * .1], fill=mix(c, (255, 255, 255), .12))

    def trunk(self, x0, y0, x1, y1, w0, w1, c):
        x0, y0, x1, y1, w0, w1 = self.X(x0), self.Y(y0), self.X(x1), self.Y(y1), self.X(w0), self.X(w1)
        self.d.polygon([(x0 - w0, y0), (x0 + w0, y0), (x1 + w1, y1), (x1 - w1, y1)], fill=c)

    def pine(self, cx, base, h, c=(52, 84, 58), trunk=(88, 62, 44), tiers=4, spread=0.13, shaggy=False):
        top = base - h
        self.trunk(cx, base, cx + .02, top + h * .1, .012 * h * 2.2, .006 * h * 2.2, trunk)
        for i in range(tiers):
            t = i / max(1, tiers - 1)
            y = base - h * (0.38 + 0.55 * t)
            side = -1 if i % 2 == 0 else 1
            sp = spread * (1 - t * .55) * h * 1.6
            ccx = cx + side * sp * .35
            self.trunk(cx, y + h * .06, ccx, y, .006 * h * 2, .004 * h * 2, trunk)
            wide = sp * (0.9 + (0.25 if shaggy else 0))
            self.blob(ccx, y, wide, wide * .27, c)
            if shaggy:
                for _ in range(6):
                    self.blob(ccx + self.r.uniform(-wide, wide), y + self.r.uniform(-.02, .03) * h, wide * .22, wide * .1, mix(c, (30, 60, 30), .3), False)
        self.blob(cx + .01, top + h * .04, spread * h * .9, spread * h * .26, c)

    def lantern(self, x, y, s):
        gray, dark = (150, 148, 140), (95, 94, 90)
        u = self.X(s)
        cx, by = self.X(x), self.Y(y)
        self.d.rectangle([cx - u * .3, by - u * .9, cx + u * .3, by], fill=gray)
        self.d.polygon([(cx - u * .9, by - u * .9), (cx + u * .9, by - u * .9), (cx + u * .7, by - u * 1.2), (cx - u * .7, by - u * 1.2)], fill=dark)
        self.d.rectangle([cx - u * .55, by - u * 1.9, cx + u * .55, by - u * 1.2], fill=gray)
        self.d.rectangle([cx - u * .25, by - u * 1.75, cx + u * .25, by - u * 1.35], fill=(236, 208, 140))
        self.d.polygon([(cx - u * 1.1, by - u * 1.9), (cx + u * 1.1, by - u * 1.9), (cx, by - u * 2.6)], fill=dark)
        self.d.ellipse([cx - u * .2, by - u * 2.8, cx + u * .2, by - u * 2.5], fill=gray)

    def stones(self, pts, c=(168, 164, 154)):
        for (x, y, rx, ry) in pts:
            self.blob(x, y, rx, ry, c)

    def hedge(self, x0, x1, y, h, c=(58, 96, 62)):
        x0, x1, y, h = self.X(x0), self.X(x1), self.Y(y), self.Y(h)
        self.d.rounded_rectangle([x0, y - h, x1, y], radius=h // 3, fill=mix(c, (0, 0, 0), .25))
        self.d.rounded_rectangle([x0, y - h, x1, y - h * .15], radius=h // 3, fill=c)
        for _ in range(int((x1 - x0) / 7)):
            px = self.r.randint(x0 + 5, x1 - 5); py = self.r.randint(int(y - h + 5), int(y - 5))
            self.d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=mix(c, (255, 255, 255), .18))

    def shaggy_bush(self, cx, cy, r, c=(70, 100, 55)):
        for _ in range(26):
            self.blob(cx + self.r.uniform(-r, r), cy + self.r.uniform(-r * .6, r * .5), r * self.r.uniform(.2, .45), r * self.r.uniform(.15, .3), mix(c, (self.r.randint(40, 120), self.r.randint(70, 130), 30), .3), False)

    def weeds(self, y0, y1, n=260, c=(98, 128, 60)):
        for _ in range(n):
            x = self.r.randint(0, self.W); y = self.r.randint(self.Y(y0), self.Y(y1))
            hgt = self.r.randint(10, 34) * S
            cc = mix(c, (150, 150, 70), self.r.random() * .5)
            for k in (-4, 0, 4):
                self.d.line([(x, y), (x + k * S, y - hgt)], fill=cc, width=S)

    def sun(self, x, y, r, c=(255, 238, 196)):
        for i in range(5, 0, -1):
            self.d.ellipse([self.X(x) - self.X(r) * i / 2, self.Y(y) - self.X(r) * i / 2, self.X(x) + self.X(r) * i / 2, self.Y(y) + self.X(r) * i / 2], fill=mix(c, (255, 255, 255), .0) if i == 1 else mix(self.im.getpixel((self.X(x), max(0, self.Y(y) - 2))), c, .12 + .1 * (5 - i)))

    def save(self, name, label='サンプル画像', quality=84):
        im = self.im.resize((self.w, self.h), Image.LANCZOS)
        d = ImageDraw.Draw(im, 'RGBA')
        f = font(max(13, self.w // 55))
        tw = d.textlength(label, font=f)
        pad = max(6, self.w // 160)
        d.rounded_rectangle([self.w - tw - pad * 3, self.h - f.size - pad * 3, self.w - pad, self.h - pad], radius=8, fill=(0, 0, 0, 120))
        d.text((self.w - tw - pad * 2, self.h - f.size - pad * 2.2), label, font=f, fill=(255, 255, 255, 235))
        im.save(os.path.join(OUT, name), quality=quality)
        print('wrote', name, im.size)


SKY = {'day': ((196, 218, 226), (240, 236, 220)), 'warm': ((222, 196, 170), (246, 228, 200)), 'cool': ((170, 196, 208), (226, 232, 226))}


def sentei(W=1000, H=750, sky='day', seed=1, name='menu-sentei.jpg'):
    s = Scene(W, H, *SKY[sky], seed=seed)
    s.hills(.62, (150, 176, 150), .05, 1.0, 0.5); s.hills(.68, (110, 146, 110), .04, 1.4, 2)
    s.ground(.74, (190, 176, 150), (160, 146, 120), rake=True)
    s.pine(.5, .86, .66, tiers=5, spread=.15)
    s.stones([(.2, .86, .06, .02), (.8, .88, .08, .025), (.72, .84, .03, .012)])
    s.save(name)


def niwa(W=1000, H=750, sky='day', seed=2, name='menu-niwa.jpg'):
    s = Scene(W, H, *SKY[sky], seed=seed)
    s.hills(.55, (140, 170, 140), .05, 1.2, 1); s.hedge(.0, 1.0, .66, .09, (62, 98, 66))
    s.ground(.66, (176, 190, 140), (120, 150, 100))
    s.pine(.2, .72, .38, tiers=3, spread=.14)
    s.lantern(.78, .74, .03)
    # 飛び石
    for i, (x, y, rx) in enumerate([(.34, .95, .09), (.44, .88, .075), (.54, .82, .065), (.62, .77, .055), (.69, .73, .045)]):
        s.blob(x, y, rx, rx * .32, (176, 172, 162))
    s.shaggy_bush(.12, .8, .1, (84, 112, 62))
    s.shaggy_bush(.9, .86, .09, (74, 104, 60))
    s.blob(.82, .78, .035, .012, (200, 70, 60), False); s.blob(.86, .80, .03, .011, (214, 90, 70), False)
    s.save(name)


def gaikou(W=1000, H=750, sky='day', seed=3, name='menu-gaikou.jpg'):
    s = Scene(W, H, *SKY[sky], seed=seed)
    s.hills(.5, (150, 176, 150), .04, 1, 0)
    # 塀
    s.d.rectangle([0, s.Y(.46), s.W, s.Y(.7)], fill=(232, 226, 210))
    for x in range(0, s.W, s.X(.12)):
        s.d.rectangle([x, s.Y(.46), x + s.X(.012), s.Y(.7)], fill=(205, 198, 180))
    s.d.rectangle([0, s.Y(.44), s.W, s.Y(.47)], fill=(86, 78, 72))
    # 門
    s.d.rectangle([s.X(.34), s.Y(.3), s.X(.66), s.Y(.7)], fill=(120, 88, 62))
    s.d.polygon([(s.X(.3), s.Y(.3)), (s.X(.7), s.Y(.3)), (s.X(.64), s.Y(.22)), (s.X(.36), s.Y(.22))], fill=(70, 66, 64))
    s.d.rectangle([s.X(.4), s.Y(.34), s.X(.6), s.Y(.7)], fill=(96, 68, 48))
    s.d.line([(s.X(.5), s.Y(.34)), (s.X(.5), s.Y(.7))], fill=(60, 44, 32), width=3 * S)
    s.ground(.7, (196, 190, 176), (166, 160, 146))
    # アプローチ
    s.d.polygon([(s.X(.42), s.Y(.7)), (s.X(.58), s.Y(.7)), (s.X(.8), s.H), (s.X(.2), s.H)], fill=(214, 208, 194))
    for i in range(6):
        yy = .72 + i * .05
        s.d.line([(s.X(.42 - i * .035), s.Y(yy)), (s.X(.58 + i * .035), s.Y(yy))], fill=(188, 182, 168), width=2 * S)
    s.hedge(.0, .3, .78, .08); s.hedge(.7, 1.0, .78, .08)
    s.pine(.12, .7, .32, tiers=3); s.lantern(.84, .7, .025)
    s.save(name)


def bassai(W=1000, H=750, sky='cool', seed=4, name='menu-bassai.jpg'):
    s = Scene(W, H, *SKY[sky], seed=seed)
    s.hills(.5, (126, 150, 130), .06, 1.1, 1); s.hills(.58, (92, 120, 98), .05, 1.6, 3)
    for x in (.08, .2, .86, .94):
        s.pine(x, .66, .36, c=(46, 76, 52), tiers=3, spread=.1)
    s.ground(.66, (150, 130, 96), (120, 100, 72))
    # 切り株
    cx, cy = s.X(.5), s.Y(.78)
    s.d.rectangle([cx - s.X(.1), cy, cx + s.X(.1), cy + s.Y(.1)], fill=(104, 76, 54))
    s.d.ellipse([cx - s.X(.1), cy - s.Y(.04), cx + s.X(.1), cy + s.Y(.04)], fill=(214, 178, 128))
    for k in range(1, 5):
        s.d.ellipse([cx - s.X(.1) * k / 5, cy - s.Y(.04) * k / 5, cx + s.X(.1) * k / 5, cy + s.Y(.04) * k / 5], outline=(172, 132, 90), width=S)
    # 丸太
    for i, (x, y) in enumerate([(.2, .84), (.26, .9), (.78, .86), (.84, .92)]):
        s.d.rounded_rectangle([s.X(x) - s.X(.1), s.Y(y), s.X(x) + s.X(.1), s.Y(y) + s.Y(.055)], radius=s.Y(.025), fill=(112, 82, 58))
        s.d.ellipse([s.X(x) + s.X(.07), s.Y(y), s.X(x) + s.X(.11), s.Y(y) + s.Y(.055)], fill=(206, 170, 122))
    s.save(name)


def cmp_pair(W=1000, H=750):
    for tidy, name in ((False, 'cmp-before.jpg'), (True, 'cmp-after.jpg')):
        s = Scene(W, H, *SKY['day'], seed=7)
        s.hills(.5, (150, 176, 150), .05, 1, .3)
        s.ground(.6, (150, 176, 120), (120, 150, 96))
        if tidy:
            s.hedge(.0, 1.0, .64, .08, (60, 98, 64))
            s.d.polygon([(s.X(.4), s.Y(.64)), (s.X(.6), s.Y(.64)), (s.X(.78), s.H), (s.X(.22), s.H)], fill=(206, 200, 184))
            s.pine(.22, .72, .5, tiers=4, spread=.13)
            s.lantern(.78, .72, .03)
        else:
            s.hedge(.0, 1.0, .64, .16, (66, 96, 56))
            s.shaggy_bush(.5, .72, .3, (80, 104, 54))
            s.pine(.22, .72, .6, tiers=4, spread=.2, shaggy=True)
            s.weeds(.64, 1.0, 420)
            s.shaggy_bush(.84, .8, .12, (96, 112, 54))
        s.save(name, 'サンプル画像（' + ('作業後' if tidy else '作業前') + '）')


def hero(W=1600, H=1000):
    s = Scene(W, H, (58, 62, 56), (120, 112, 92), seed=11)
    s.hills(.58, (70, 88, 70), .06, 1.0, 0.8); s.hills(.66, (50, 70, 54), .05, 1.5, 2)
    s.ground(.72, (96, 92, 76), (60, 58, 48), rake=True)
    s.pine(.42, .9, .78, c=(56, 92, 62), tiers=6, spread=.16)
    s.pine(.82, .78, .36, c=(48, 80, 54), tiers=3, spread=.14)
    s.lantern(.12, .82, .035)
    s.stones([(.62, .92, .09, .03), (.25, .94, .07, .024), (.72, .86, .04, .014)], (122, 120, 110))
    s.save('hero-garden.jpg', 'サンプル画像（イラスト）', 82)


if __name__ == '__main__':
    sentei(); niwa(); gaikou(); bassai(); cmp_pair(); hero()
    # 帯用（色や時間帯を変えた別の絵）
    sentei(sky='warm', seed=21, name='belt-1.jpg'); niwa(sky='warm', seed=22, name='belt-2.jpg')
    gaikou(sky='cool', seed=23, name='belt-3.jpg'); bassai(sky='day', seed=24, name='belt-4.jpg')
