#!/usr/bin/env python3
"""make_site.py の A1 の素材入れ（fill_photos → fill_a1）の検査（2026/11/24 想永 05:41 の不具合から）
使い方: python3 tools/test_make_site_a1_stock.py
  仮の素材フォルダ（hero 入りの名前 1 枚＋ほか 2 枚）と仮のお店で、素材入れを 2 回（2 回目は 1 回目の images/ を写してから＝完成図の係が周を重ねるときと同じ）回して確かめる：
  1. 1画面目の後ろ（hero.bg）は、1 回目も 2 回目も名前に hero の入った素材（前は 2 回目に「もう images/ にある」で除かれ、別の素材が入った）
  2. 同じ素材を 1 回の作成で 2 回使わない（fill_photos が sec-about.jpg に使った物を、fill_a1 が band に使わない）
  3. 素材の写真には source:stock が付く
  合格：3つ全部 OK"""
import io, os, shutil, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import make_site
try:
    from PIL import Image
except ImportError:
    sys.exit('Pillow が要ります（pip3 install pillow）')

ok = True
def check(cond, msg, extra=''):
    global ok
    print(('OK ' if cond else 'NG ') + msg + ('' if cond else '  ' + str(extra)))
    ok = ok and cond

root = tempfile.mkdtemp(prefix='make_site_a1_stock_')
stock = os.path.join(root, '_素材写真'); gy = 'ためし'; os.makedirs(os.path.join(stock, gy))
names = ['tameshi_hero_bright.jpg', 'tameshi_a.jpg', 'tameshi_b.jpg']
for i, n in enumerate(names):
    Image.new('RGB', (1200, 800), (240 - i * 60, 240 - i * 60, 200)).save(os.path.join(stock, gy, n), quality=85)
io.open(os.path.join(stock, '素材一覧.md'), 'w', encoding='utf-8').write(
    '| ファイル | 出どころ | 元のページ | 利用条件 | 取った日 | 最初に使った店 |\n|---|---|---|---|---|---|\n' +
    ''.join('| %s/%s | 試し | - | Unsplash License(商用可・表記不要) | 2026-11-24 | 試し |\n' % (gy, n) for n in names))
make_site.STOCK_ROOT = stock

copied = []
_orig = make_site.copy_photo
def spy(src, dst, ratio=None):
    copied.append((os.path.basename(src), os.path.relpath(dst, root))); return _orig(src, dst, ratio)
make_site.copy_photo = spy

def build(outdir, images_from=None, src='stock'):
    """仮のお店で fill_photos → fill_a1（make_site の main と同じ順）。images_from があれば先にその images/ を写す（完成図の係の周の重ね方）。src＝1画面目の写真の出どころ"""
    os.makedirs(os.path.join(outdir, 'images'), exist_ok=True)
    if images_from: shutil.copytree(os.path.join(images_from, 'images'), os.path.join(outdir, 'images'), dirs_exist_ok=True)
    Image.new('RGB', (900, 1200), (90, 90, 90)).save(os.path.join(outdir, 'images', 'hero.jpg'), quality=85)
    c = {'name': 'ためしの店', 'hero': {'image': 'images/hero.jpg', 'source': src}, 'menus': [], 'photo_style': 'a1', '業種': gy}
    make_site.STOCK_USED.clear(); del copied[:]
    make_site.fill_photos(c, outdir); make_site.fill_a1(c, outdir)
    return c, list(copied)

d1 = os.path.join(root, '周1'); c1, cp1 = build(d1)
d2 = os.path.join(root, '周2'); c2, cp2 = build(d2, images_from=d1)
bg1 = os.path.basename(((c1.get('hero') or {}).get('bg') or {}).get('image') or ''); bg2 = os.path.basename(((c2.get('hero') or {}).get('bg') or {}).get('image') or '')
check(bg1 == names[0] and bg2 == names[0], '1 1画面目の後ろは 1 回目も 2 回目も hero 入りの名前の素材（1画面目が見本の写真のとき）', (bg1, bg2))
# 1画面目がお店の写真（source own）なら、後ろの素材は入れない＝お店の写真が大きな写真になる（2026/11/24 通し試験 本人の決め 1）
d3 = os.path.join(root, '周own'); c3, cp3 = build(d3, src='own')
check(not ((c3.get('hero') or {}).get('bg') or {}).get('image'), '1b 1画面目がお店の写真なら後ろの素材は入れない', (c3.get('hero') or {}).get('bg'))
srcs1 = [s for s, _ in cp1]
check(len(srcs1) == len(set(srcs1)) and len(make_site.STOCK_USED) == len(set(srcs1)), '2 同じ素材を 1 回の作成で 2 回使わない', (srcs1, sorted(make_site.STOCK_USED)))
stocks = []
def walk(o):
    if isinstance(o, dict):
        if o.get('source') == 'stock': stocks.append(o.get('image'))
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(c1)
check(len(stocks) >= 2 and all(s for s in stocks), '3 素材の写真には source:stock が付く', stocks)
print('合格' if ok else '不合格'); sys.exit(0 if ok else 1)
