"""見本帳の一覧画像（samples/thumbs/<名前>.jpg）を、この Mac の Chrome（画面なし）で撮って作る  2026/10/9 作成

使い方: python3 tools/mihon/make_thumbs.py [~/src/liftoff-hp] cafe,school,...
  ・samples/<名前>/index.html を 幅1280（パソコン）と 幅390（スマホ）で撮り、thumb.py で 1200×780 の一覧画像にする
  ・背景の色は samples/<名前>/site.json の theme.bg（なければ薄い灰色）
  ・ついでに、幅 390・1280 で横にはみ出していないか（scrollWidth）を調べて出す（Playwright がなくても調べられる）
  ・途中の画像（撮ったもの）は /tmp ではなく、引数 --keep <フォルダ> を付けるとそこに残す（確認画像に使う）
"""
import json, os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
keep = sys.argv[sys.argv.index('--keep') + 1] if '--keep' in sys.argv else None
args = [a for a in sys.argv[1:] if not a.startswith('--') and a != keep]
ROOT = os.path.expanduser(args[0]) if len(args) > 1 else os.path.dirname(os.path.dirname(HERE))  # 1つ目がフォルダなら、それが liftoff-hp
names = args[-1].split(',') if args else []
if not names: sys.exit(__doc__)
work = keep or tempfile.mkdtemp()
os.makedirs(work, exist_ok=True)

def shot(url, w, h, out):
    """幅 w・高さ h で撮る。Chrome（画面なし）は窓の幅が 500 より小さくならない（390 と指定しても 500 幅の画面を切り取ったものになる。2026/10/9 に判明）ので、
    500 より狭いときは、幅 w の枠（iframe）にページを入れた包み紙のページを撮り、枠の分だけ切り出す"""
    if w < 500:
        host = os.path.join(work, f'_host_{w}_{abs(hash(url)) % 100000}.html')
        open(host, 'w', encoding='utf-8').write(f'<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:#fff"><iframe src="{url}" style="display:block;border:0;width:{w}px;height:{h}px"></iframe></body></html>')
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size=500,{h}',
                        '--virtual-time-budget=8000', f'--screenshot={out}', 'file://' + host], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        from PIL import Image
        im = Image.open(out); im.crop((0, 0, w, h)).save(out)
        return
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size={w},{h}',
                    '--virtual-time-budget=6000', f'--screenshot={out}', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def overflow(page, w):
    """横にはみ出しているか。はみ出していたら画面の左上に赤い帯を出す小さな script を足した写しを撮り、左上の色で判定する
    （--dump-dom では窓の幅が 500 より小さくならないので、幅が正しく効く --screenshot で調べる。2026/10/9）
    戻り値: None＝調べられず／0＝はみ出しなし／はみ出した px 数（赤い帯の幅の割合で返す）"""
    from PIL import Image
    src = open(page, encoding='utf-8').read()
    base = 'file://' + os.path.dirname(os.path.abspath(page)) + '/'
    src = src.replace('<head>', f'<head><base href="{base}">', 1)
    js = ("<script>window.addEventListener('load',function(){setTimeout(function(){"
          "var sw=document.documentElement.scrollWidth,iw=window.innerWidth;"
          "var d=document.createElement('div');d.style.cssText='position:fixed;top:0;left:0;height:40px;z-index:99999;width:'+(sw>iw+1?Math.min(100,(sw-iw)):0)+'px;background:#ff0000';"
          "var g=document.createElement('div');g.style.cssText='position:fixed;top:40px;left:0;width:40px;height:40px;z-index:99999;background:#00ff00';"
          "document.body.appendChild(d);document.body.appendChild(g);},500);});</script></body>")
    src = src.replace('</body>', js, 1)
    tmp = os.path.join(work, f'_chk_{w}.html'); open(tmp, 'w', encoding='utf-8').write(src)
    png = os.path.join(work, f'_chk_{w}.png')
    shot('file://' + tmp, w, 400, png)
    im = Image.open(png).convert('RGB')
    if im.size[0] != w or im.getpixel((5, 60)) != (0, 255, 0): return None  # 窓の幅が違う／script が走っていない
    n = 0
    while n < 100 and im.getpixel((n, 10)) == (255, 0, 0): n += 1
    return n

check_only = '--check' in sys.argv  # 一覧画像は作らず、はみ出しだけ調べる（index と書くと見本帳の一覧 samples/index.html）
for d in names:
    page = os.path.join(ROOT, 'samples', 'index.html') if d == 'index' else os.path.join(ROOT, 'samples', d, 'index.html')
    url = 'file://' + page
    out = '（一覧画像は作っていない）'
    if not check_only:
        bg = '#f0ede8'
        sj = os.path.join(ROOT, 'samples', d, 'site.json')
        if os.path.exists(sj):
            try: bg = json.load(open(sj, encoding='utf-8')).get('theme', {}).get('bg', bg)
            except Exception: pass
        pc, sp = os.path.join(work, f'{d}_1280.png'), os.path.join(work, f'{d}_390.png')
        shot(url, 1280, 800, pc); shot(url, 390, 844, sp)
        out = os.path.join(ROOT, 'samples', 'thumbs', f'{d}.jpg')
        subprocess.run([sys.executable, os.path.join(HERE, 'thumb.py'), pc, sp, out, bg], check=True)
    over = []
    for w in (320, 390, 1280):
        n = overflow(page, w)
        if n is None: over.append(f'幅{w}：調べられず')
        elif n: over.append(f'幅{w}：はみ出し（{n}px{"以上" if n >= 100 else ""}）')
    print('ok', d, out, '／ はみ出し：' + ('、'.join(over) if over else 'なし（320・390・1280）'))
