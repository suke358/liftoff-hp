#!/usr/bin/env python3
# photo_fuuki.py — 見本帳の「雰囲気の見本」6つ（手書きのページ）の絵（../img/ph-*.svg）を、ページごとの写真に置きかえる
# 作成: 2026/11/11（見本帳の作り直し）
# 使い方: python3 tools/mihon/photo_fuuki.py [~/src/liftoff-hp] [homey,luxury,...]
# 写真は ~/src/_素材写真/ から、img の width・height の比で真ん中を切って samples/<名前>/images/ に書き出す（元の写真は動かさない）
# 直すのは index.html の img の src と alt だけ。字・色・並びは触らない。絵（../img/）は消さない（ほかで使うかもしれないため）
import os, re, sys
from PIL import Image, ImageOps

ROOT = os.path.abspath(os.path.expanduser(sys.argv[1])) if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PHOTO_ROOT = os.path.join(os.path.dirname(ROOT), '_素材写真')
Y, Z = 'よもぎ蒸し', '造園'
# ページごと：絵の名前 → 写真。同じ名前の絵が2回出るときは出てくる順に並べる
MAP = {
 'homey':  {'ph-hero': [f'{Y}/yomo_int2.jpg'], 'ph-owner': [f'{Y}/yomo_owner1.jpg'], 'ph-room': [f'{Y}/yomo_int1.jpg'],
            'ph-lounge': [f'{Y}/yomo_int5.jpg'], 'ph-menu1': [f'{Y}/yomo_steam.jpg'], 'ph-menu2': [f'{Y}/yomo_facial1.jpg'],
            'ph-menu3': [f'{Y}/yomo_towel1.jpg']},
 'luxury': {'ph-hero': [f'{Y}/yomo_int3.jpg'], 'ph-owner': [f'{Y}/yomo_owner2.jpg'],
            'ph-menu1': [f'{Y}/yomo_herb2.jpg'], 'ph-menu2': [f'{Y}/yomo_facial2.jpg']},
 'pop':    {'ph-hero': [f'{Y}/yomo_int4.jpg'], 'ph-owner': [f'{Y}/yomo_owner3.jpg'],
            'ph-menu1': [f'{Y}/yomo_herb3.jpg'], 'ph-menu2': [f'{Y}/yomo_towel2.jpg']},
 'chic':   {'ph-owner': [f'{Y}/yomo_owner4.jpg'], 'ph-menu1': [f'{Y}/yomo_herb1.jpg'], 'ph-menu2': [f'{Y}/yomo_facial1.jpg']},
 'photo':  {'ph-top-photo': [f'{Y}/yomo_steam.jpg'], 'ph-owner': [f'{Y}/yomo_owner5.jpg'],  # 上は白い字が乗るので暗い写真
            'ph-menu1': [f'{Y}/yomo_herb1.jpg'], 'ph-menu2': [f'{Y}/yomo_facial2.jpg']},
 'wa':     {'ph-wa-hero': [f'{Z}/wa_hero.jpg'], 'ph-wa-before': [f'{Z}/wa_before.jpg', f'{Z}/wa_before2.jpg'],
            'ph-wa-after': [f'{Z}/wa_after.jpg'], 'ph-wa-after2': [f'{Z}/wa_after2.jpg'], 'ph-wa-owner': [f'{Z}/wa_owner.jpg']},
}

def write(src, dst, w, h):
    im = ImageOps.exif_transpose(Image.open(os.path.join(PHOTO_ROOT, src))).convert('RGB')
    W, H = im.size; r = w / h
    if W / H > r: nw = int(H * r); im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
    else: nh = int(W / r); im = im.crop((0, (H - nh) // 2, W, (H - nh) // 2 + nh))
    k = min(2.0, 1600 / w)  # 画面の大きさの2倍まで（横1600まで）
    im = im.resize((int(w * k), int(h * k)), Image.LANCZOS)
    im.save(dst, 'JPEG', quality=80, optimize=True, progressive=True)

only = sys.argv[2].split(',') if len(sys.argv) > 2 else list(MAP)
for d in only:
    p = f'{ROOT}/samples/{d}/index.html'; s = open(p, encoding='utf-8').read()
    os.makedirs(f'{ROOT}/samples/{d}/images', exist_ok=True)
    used = {}
    def rep(m):
        tag = m.group(0); name = m.group(1)
        lst = MAP[d].get(name)
        if not lst: return tag
        i = used.get(name, 0); used[name] = i + 1
        src = lst[min(i, len(lst) - 1)]
        out = os.path.splitext(os.path.basename(src))[0] + '.jpg'
        w = re.search(r'width="(\d+)"', tag); h = re.search(r'height="(\d+)"', tag)
        w, h = (int(w.group(1)), int(h.group(1))) if (w and h) else (1200, 900)
        write(src, f'{ROOT}/samples/{d}/images/{out}', w, h)
        tag = tag.replace(f'../img/{name}.svg', f'images/{out}')
        tag = re.sub(r'alt="([^"]*?)の写真が入ります"', r'alt="\1のイメージ写真（見本）"', tag)
        return tag
    s2 = re.sub(r'<img[^>]*?src="\.\./img/(ph-[\w-]+)\.svg"[^>]*>', rep, s)
    open(p, 'w', encoding='utf-8').write(s2)
    print(d, '置きかえ', sum(used.values()), '枚', used)
