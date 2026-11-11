#!/usr/bin/env python3
# shop_nemu.py — 見本帳の shop（よもぎ蒸しサロン hiyori）と nemunoha（ねむの葉）を、写真と型で作り直す（2026/11/11 見本帳の作り直し）
# 使い方: python3 tools/mihon/shop_nemu.py [~/src/liftoff-hp]
# shop：絵（SVG）を ~/src/_素材写真/よもぎ蒸し/ の写真にして site.json を直し、make_site.py で作り直す。型は frame
# nemunoha：写真はそのまま。型を cards にして make_site.py で作り直し、前と同じく「見本帳にもどる」を付ける
import os, re, sys, json, subprocess
from PIL import Image, ImageOps
ROOT = os.path.abspath(os.path.expanduser(sys.argv[1])) if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PR = os.path.join(os.path.dirname(ROOT), '_素材写真', 'よもぎ蒸し')

def photo(src, dst, w, h):
    im = ImageOps.exif_transpose(Image.open(os.path.join(PR, src))).convert('RGB')
    W, H = im.size; r = w / h
    if W / H > r: nw = int(H * r); im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
    else: nh = int(W / r); im = im.crop((0, (H - nh) // 2, W, (H - nh) // 2 + nh))
    im = im.resize((w, h), Image.LANCZOS); im.save(dst, 'JPEG', quality=80, optimize=True, progressive=True)
    return w, h

def build(d):
    subprocess.run([sys.executable, f'{ROOT}/tools/make_site.py', f'{ROOT}/samples/{d}/site.json', f'{ROOT}/samples/{d}'], stdout=subprocess.DEVNULL, check=True)
    old = f'{ROOT}/samples/{d}/index.old.html'
    if os.path.exists(old): os.remove(old)

# ---- shop ----
d = 'shop'; out = f'{ROOT}/samples/{d}'; cf = f'{out}/site.json'
c = json.load(open(cf, encoding='utf-8'))
c['layout'] = 'frame'; c['hero_style'] = 'light'
w, h = photo('yomo_int3.jpg', f'{out}/images/hero.jpg', 1200, 1500)
c['hero'] = dict(image='images/hero.jpg', w=w, h=h, alt='サロンの雰囲気のイメージ写真（見本）')
MENU = {'yomogi': 'yomo_steam.jpg', 'facial': 'yomo_facial1.jpg', 'set': 'yomo_towel1.jpg'}
for m in c['menus']:
    if m['id'] in MENU:
        w, h = photo(MENU[m['id']], f'{out}/images/menu-{m["id"]}.jpg', 1000, 750)
        m.update(image=f'images/menu-{m["id"]}.jpg', w=w, h=h, alt=m['name'] + 'のイメージ写真（見本）')
ITEM = {'item-herb': 'yomo_herb2.jpg', 'item-socks': 'yomo_socks.jpg', 'item-gift': 'yomo_gift.jpg'}
for it in c['parts']['shop']['items']:
    k = os.path.splitext(os.path.basename(it['image']))[0]
    if k in ITEM:
        photo(ITEM[k], f'{out}/images/{k}.jpg', 1000, 1000)
        it['image'] = f'images/{k}.jpg'; it['alt'] = re.sub(r'の写真（見本）$', 'のイメージ写真（見本）', it.get('alt', ''))
json.dump(c, open(cf, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
build(d)
for f in os.listdir(f'{out}/images'):
    if f.endswith('.svg') and f'images/{f}' not in open(f'{out}/index.html', encoding='utf-8').read(): os.remove(f'{out}/images/{f}')
print('ok shop')

# ---- nemunoha ----
d = 'nemunoha'; out = f'{ROOT}/samples/{d}'; cf = f'{out}/site.json'
c = json.load(open(cf, encoding='utf-8')); c['layout'] = 'cards'
json.dump(c, open(cf, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
build(d)
ms = open(f'{ROOT}/tools/mihon/make_samples.py', encoding='utf-8').read()
css = ms.split("MIHON_CSS='''", 1)[1].split("'''", 1)[0]
p = f'{out}/index.html'; s = open(p, encoding='utf-8').read()
if 'class="mihon"' not in s:
    s = s.replace('</style>', css + '</style>', 1)
    s = s.replace('</body>', '<a class="mihon" href="../index.html">デザイン見本（架空のお店）｜見本帳にもどる</a>\n</body>', 1)
    open(p, 'w', encoding='utf-8').write(s)
print('ok nemunoha')
