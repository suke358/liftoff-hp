#!/usr/bin/env python3
"""色の組み合わせ（THEMES）の見本を 6 つ作り、幅 390・1280 で撮って 1 枚の一覧画像にする  2026/10/31 作成

使い方: python3 tools/mihon/make_theme_samples.py <作るフォルダ> [--shots <画像を置くフォルダ>]
  ・架空のお店（templates/site_sample.json の松葉造園）を、雰囲気ごと（salon・wa・fresh・simple・jouhin・genki）に作る
  ・この Mac の Chrome（画面なし）で撮る。幅 390 は make_thumbs.py と同じく枠（iframe）に入れて撮る
  ・一覧画像：<画像を置くフォルダ>/色の組み合わせ6種.jpg（--shots を省くと <作るフォルダ>/_shots/）
  ・check_site.py の「色」の検査（❌/⚠️）も、作るときに出る
"""
import json, os, subprocess, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)
from make_site import THEMES, THEME_LABELS
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
FONT_OF = {'salon': 'mincho', 'wa': 'mincho', 'jouhin': 'mincho', 'fresh': 'gothic', 'simple': 'gothic', 'genki': 'gothic'}
MARK_OF = {'salon': 'heart', 'wa': 'leaf', 'fresh': 'leaf', 'simple': 'dot', 'jouhin': 'heart', 'genki': 'dot'}

args = [a for a in sys.argv[1:]]
shots = None
if '--shots' in args:
    i = args.index('--shots'); shots = os.path.expanduser(args[i + 1]); del args[i:i + 2]
if not args: sys.exit(__doc__)
OUT = os.path.expanduser(args[0]); shots = shots or os.path.join(OUT, '_shots')
os.makedirs(shots, exist_ok=True)


def shot(url, w, h, out):
    if w < 500:  # Chrome（画面なし）は窓の幅が 500 より小さくならないので、枠に入れて撮って切り出す
        host = os.path.join(shots, f'_host_{w}.html')
        open(host, 'w', encoding='utf-8').write(f'<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:#fff"><iframe src="{url}" style="display:block;border:0;width:{w}px;height:{h}px"></iframe></body></html>')
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size=500,{h}', '--virtual-time-budget=8000', f'--screenshot={out}', 'file://' + host], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        from PIL import Image
        im = Image.open(out); im.crop((0, 0, w, h)).save(out); return
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size={w},{h}', '--virtual-time-budget=8000', f'--screenshot={out}', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


base = json.load(open(os.path.join(TOOLS, 'templates', 'site_sample.json'), encoding='utf-8'))
made = []
for t in THEMES:
    c = dict(base); c.pop('theme', None)
    c['theme_base'] = t; c['font'] = FONT_OF.get(t, 'mincho'); c['mark'] = MARK_OF.get(t, 'dot')
    c['sample_note'] = f'※色の組み合わせ「{THEME_LABELS.get(t, t)}」（{t}）の見本。架空のお店'
    c['tel'] = '0000-00-0000'; c['line_url'] = '#reserve'  # ボタンが全部出るように（見本）
    d = os.path.join(OUT, t); os.makedirs(d, exist_ok=True)
    sj = os.path.join(d, 'site.json'); json.dump(c, open(sj, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'\n===== {t}（{THEME_LABELS.get(t, t)}）')
    subprocess.call([sys.executable, os.path.join(TOOLS, 'make_site.py'), sj, d])
    url = 'file://' + os.path.join(d, 'index.html')
    pc, sp = os.path.join(shots, f'{t}_1280.png'), os.path.join(shots, f'{t}_390.png')
    shot(url, 1280, 1800, pc); shot(url, 390, 1400, sp)  # トップ（dark）だけでなく、その下のメニュー（bg・白のカード・札）まで入る高さ
    made.append((t, pc, sp))

# 一覧画像（2列×3行。左が PC、右がスマホ。半分の大きさに縮める）
from PIL import Image, ImageDraw, ImageFont
CW, CH = 900, 960
W, H = CW * 2 + 60, CH * 3 + 80
im = Image.new('RGB', (W, H), '#f2f2f0'); d = ImageDraw.Draw(im)
try: font = ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc', 22)
except Exception:
    try: font = ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 22)
    except Exception: font = ImageFont.load_default()
for n, (t, pc, sp) in enumerate(made):
    x0 = 20 + (n % 2) * (CW + 20); y0 = 20 + (n // 2) * (CH + 20)
    d.rectangle((x0, y0, x0 + CW, y0 + CH), fill='#ffffff', outline='#d8d8d4')
    d.text((x0 + 16, y0 + 10), f'{THEME_LABELS.get(t, t)}（{t}）  primary {THEMES[t]["primary"]} / dark {THEMES[t]["dark"]} / bg {THEMES[t]["bg"]}', fill='#222', font=font)
    p = Image.open(pc).convert('RGB').resize((640, 900)); im.paste(p, (x0 + 16, y0 + 44))
    s = Image.open(sp).convert('RGB').resize((195, 700)); im.paste(s, (x0 + 676, y0 + 44))
out = os.path.join(shots, '色の組み合わせ6種.jpg'); im.save(out, quality=88)
print('\n一覧画像：', out)
