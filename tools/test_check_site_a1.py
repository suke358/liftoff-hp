#!/usr/bin/env python3
"""check_site.py の「釣り合い」「重なり」（配置の型 a1trace だけ。2026/11/24）の検査
使い方: python3 tools/test_check_site_a1.py
  手で作った小さなページで確かめる：
  1. 縦書き 13 字 → ⚠️ 重なり（ブラウザなし）。12 字なら出ない
  2. data-pair の 2 枚が幅 100px と 300px → ⚠️ 釣り合い（ブラウザ）。同じ幅なら出ない
  3. 縦書きが写真の真ん中 → ⚠️ 重なり。写真の左端 5％ なら出ない
  4. data-layout="a1trace" の無いページでは何も出ない
  合格：全部 OK"""
import io, os, re, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
ok = True
def check(cond, msg, extra=''):
    global ok
    print(('OK ' if cond else 'NG ') + msg + ('' if cond else '  ' + str(extra)))
    ok = ok and cond

def page(a1, vt, widths, vt_left):
    from PIL import Image
    d = tempfile.mkdtemp(prefix='chk_a1_'); os.makedirs(os.path.join(d, 'images'))
    Image.new('RGB', (400, 300), (120, 130, 140)).save(os.path.join(d, 'images', 'a.jpg'), quality=80)
    io.open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(f'''<!doctype html>
<html lang="ja"{' data-layout="a1trace"' if a1 else ''}><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>試し</title><style>body{{margin:0;word-break:keep-all}}.wide{{position:relative;width:100%;height:200px;overflow:hidden}}.wide img{{width:100%;height:100%;display:block}}
.vt{{position:absolute;top:10px;left:{vt_left};-webkit-writing-mode:vertical-rl;writing-mode:vertical-rl;margin:0}}
.row{{overflow:hidden}}.row div{{float:left;height:80px;overflow:hidden;background:#ccc}}</style></head><body>
<div class="wide"><img src="images/a.jpg" alt="試し"><p class="vt mi">{vt}</p></div>
<div class="row"><div data-pair="x" style="width:{widths[0]}px"></div><div data-pair="x" style="width:{widths[1]}px"></div></div>
<p>試しの<wbr>ページ</p></body></html>''')
    return d

def run(d, browser=True):
    r = subprocess.run([sys.executable, os.path.join(here, 'check_site.py'), d] + ([] if browser else ['--no-browser']), capture_output=True, text=True, timeout=600)
    return r.stdout

o = run(page(True, '一二三四五六七八九十一二三', (100, 100), '5%'), browser=False)
check('重なり' in o and '12 字' in o, '1 縦書き 13 字 → ⚠️ 重なり（ブラウザなし）', o[-300:])
o = run(page(True, '一二三四五六七八九十一二', (100, 100), '5%'), browser=False)
check('重なり' not in o, '1 縦書き 12 字なら出ない', o[-300:])
try:
    import playwright  # noqa
    o = run(page(True, '試し', (100, 300), '5%'))
    check('釣り合い' in o and '1：3.0' in o, '2 幅 100 と 300 の組 → ⚠️ 釣り合い', [l for l in o.splitlines() if '釣り合い' in l])
    o = run(page(True, '試し', (100, 100), '5%'))
    check('⚠️ [釣り合い]' not in o and '✅ [釣り合い]' in o, '2 同じ幅なら ✅ 釣り合い', [l for l in o.splitlines() if '釣り合い' in l])
    o = run(page(True, '試し', (100, 100), '48%'))
    check('重なり' in o and '主役' in o, '3 縦書きが写真の真ん中 → ⚠️ 重なり', [l for l in o.splitlines() if '重なり' in l])
    o = run(page(True, '試し', (100, 100), '5%'))
    check('⚠️ [重なり]' not in o, '3 縦書きが左端 5％ なら出ない', [l for l in o.splitlines() if '重なり' in l])
    o = run(page(False, '一二三四五六七八九十一二三', (100, 300), '48%'))
    check('釣り合い' not in o and '重なり' not in o, '4 a1trace でないページでは何も出ない', [l for l in o.splitlines() if '釣り合い' in l or '重なり' in l])
except ImportError:
    print('（Playwright が無いので 2〜4 は飛ばしました）')
print('合格' if ok else '不合格')
sys.exit(0 if ok else 1)
