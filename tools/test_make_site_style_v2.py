#!/usr/bin/env python3
"""見た目の型 "style": "v2"（2026/11/26 いいサイト49 に合わせた新しい型）の検査
使い方: python3 tools/test_make_site_style_v2.py
  1. "style" を書かない・"classic" は、今までと 1 字も同じ（版の印だけ除く）
  2. "v2"：最初の画面のボタンは 1 つ（entry_order があってもなくても）。下の帯は 2 つまで。ご予約の欄の入口は減らさない（フォームの箱はフォームがすぐ下にあるので出さない）
  3. "v2"：見出しは明朝が基本。"font_heading": "gothic" で細いゴシック、"hand" で手書き風。手書き風は既定にしない
  4. "v2"：角丸・白いカードの影・丸い目次・大きい薄い英字・背景の模様を使わない（V2_CSS が入り、DESIGN_CSS は入らない）
  5. 使えない値（"style": "v3"・"font_heading": "pop"）は止まる
合格：全部 OK"""
import json, os, re, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import make_site as ms

ok = True
def check(cond, msg):
    global ok
    print(('OK ' if cond else 'NG ') + msg)
    ok = ok and cond

def build(c, expect_fail=False):
    d = tempfile.mkdtemp(prefix='style_v2_')
    p = os.path.join(d, 'site.json'); json.dump(c, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    r = subprocess.run([sys.executable, os.path.join(here, 'make_site.py'), p, d], capture_output=True, text=True)
    if expect_fail: return r
    if r.returncode: print(r.stdout[-800:], r.stderr[-800:])
    return open(os.path.join(d, 'index.html'), encoding='utf-8').read()

def hero_count(s):
    m = re.search(r'<div class="hero-btns">(.*?)</div>', s, re.S)
    return len(re.findall(r'<a\b', m.group(1))) if m else -1

strip = lambda s: re.sub(r'道具の版 [^）\s]+', '道具の版 X', s)
base = json.load(open(os.path.join(here, 'templates', 'site_sample.json'), encoding='utf-8'))
base.update(reserve_url='https://example.com/yoyaku', line_url='https://line.me/R/ti/p/@example', tel='0000-00-0000')
base.setdefault('parts', {}); base['parts']['form'] = base['parts'].get('form') or {}

# 1
s0 = build(json.loads(json.dumps(base)))
c = json.loads(json.dumps(base)); c['style'] = 'classic'
check(strip(build(c)) == strip(s0), '"style": "classic" は書かないときと同じ')
check('V2' not in s0 and '新しい型' not in s0, '書かないときは新しい型の CSS が入らない')
# 2
for eo in (None, ['reserve', 'line', 'tel', 'form']):
    c = json.loads(json.dumps(base)); c['style'] = 'v2'
    if eo: c['entry_order'] = eo
    s = build(c)
    check(hero_count(s) == 1, f'v2・entry_order {"あり" if eo else "なし"} → 最初の画面のボタン 1 つ（{hero_count(s)}）')
    bar = re.search(r'<nav class="spbar n(\d)"', s)
    check(bar and int(bar.group(1)) <= 2, f'下の帯は 2 つまで（{bar.group(1) if bar else "なし"}）')
    hb = re.search(r'<div class="hero-btns">(.*?)</div>', s, re.S).group(1)
    check('example.com/yoyaku' in hb, '最初の画面のボタンはネット予約（いま使える窓口を先に）')
    ways = re.search(r'<div class="ways n(\d)">', s)
    check(ways and ways.group(1) == '3', f'ご予約の欄はネット予約・LINE・電話（フォームの箱はフォームのすぐ上なので出さない）（{ways.group(1) if ways else "なし"}）')
    check('id="form"' in s, 'フォームそのものは残る')
# 3
c = json.loads(json.dumps(base)); c['style'] = 'v2'
s = build(c)
check('--head:var(--mincho)' in s and 'family=Klee' not in s and '--hand:var(--head)' in s, 'v2 の見出しは明朝・手書き風は読まない')
c['font_heading'] = 'gothic'; s = build(c)
check('--head:var(--gothic)' in s, '"font_heading": "gothic" → 細いゴシック')
c['font_heading'] = 'hand'; s = build(c)
check(re.search(r'--hand:"[^"]+",var\(--head\)', s) is not None and 'family=' + ms.HAND_FONTS[ms.hand_font(c, None)].split(':')[0] in s, '"font_heading": "hand" → 手書き風')
# 4
c = json.loads(json.dumps(base)); c['style'] = 'v2'
s = build(c)
check('新しい型（"style": "v2"' in s and '背景のデザイン（⑥-2 5周目）' not in s and 'data-en=' not in s and 'bgv-' not in s, 'v2 は V2_CSS だけ（模様・大きい英字・区画の模様なし）')
check('--r:0' in s and '.toc a,.hero.ov .hero-under .toc a' in s, '角丸 0・目次は文字のリンク')
# 5
c = json.loads(json.dumps(base)); c['style'] = 'v3'
r = build(c, expect_fail=True)
check(r.returncode != 0 and '"style"' in (r.stdout + r.stderr), '"style": "v3" は止まる')
c = json.loads(json.dumps(base)); c['style'] = 'v2'; c['font_heading'] = 'pop'
r = build(c, expect_fail=True)
check(r.returncode != 0 and '"font_heading"' in (r.stdout + r.stderr), '"font_heading": "pop" は止まる')

print('合格' if ok else '不合格')
sys.exit(0 if ok else 1)
