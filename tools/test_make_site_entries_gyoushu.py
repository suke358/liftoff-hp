#!/usr/bin/env python3
"""最初の画面の入口の数（整備の箱 34）と、業種を 2 つ書く（整備の箱 31）の検査（2026/11/25 夜）
使い方: python3 tools/test_make_site_entries_gyoushu.py
  1. entry_order に 4 つ書くと、最初の画面のボタンは 2 つ（先頭の 2 つ）。"hero_entries": 1 なら 1 つ。ご予約の欄には 4 つとも残る
  2. entry_order が無いお店は今までどおり（ボタンの数を減らさない）
  3. "業種" の並び：gyoushu_list・電話の文・手書きフォントは先（主）から。1 つの文字は今までどおり
  4. 業種が 2 つのとき、メニューの名前に近いフォルダの素材がカードに入る（伐採→伐採・草刈り/、修繕→家の修繕/）。1 つのときは今までどおり
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

def build(c):
    d = tempfile.mkdtemp(prefix='entries_')
    p = os.path.join(d, 'site.json'); json.dump(c, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    r = subprocess.run([sys.executable, os.path.join(here, 'make_site.py'), p, d], capture_output=True, text=True)
    if r.returncode: print(r.stdout[-800:], r.stderr[-800:])
    return open(os.path.join(d, 'index.html'), encoding='utf-8').read()

def hero_count(s):
    m = re.search(r'<div class="hero-btns">(.*?)</div>', s, re.S)
    return len(re.findall(r'<a\b', m.group(1))) if m else -1

base = json.load(open(os.path.join(here, 'templates', 'site_sample.json'), encoding='utf-8'))
base.update(reserve_url='https://example.com/yoyaku', line_url='https://line.me/R/ti/p/@example', tel='0000-00-0000')
base.setdefault('parts', {}); base['parts']['form'] = base['parts'].get('form') or {}

# 1
c = json.loads(json.dumps(base)); c['entry_order'] = ['reserve', 'line', 'tel', 'form']
s = build(c)
check(hero_count(s) == 2, f'entry_order 4 つ → 最初の画面のボタン 2 つ（{hero_count(s)}）')
hb = re.search(r'<div class="hero-btns">(.*?)</div>', s, re.S).group(1)
check('example.com/yoyaku' in hb and 'line.me' in hb and 'tel:' not in hb, '残るのは先頭の 2 つ（ネット予約・LINE）')
ways = re.search(r'<div class="ways n(\d)">', s)
check(ways and ways.group(1) == '4', 'ご予約の欄には 4 つとも残る')
c['hero_entries'] = 1
s = build(c)
check(hero_count(s) == 1, f'"hero_entries": 1 → 1 つ（{hero_count(s)}）')
# 2
c = json.loads(json.dumps(base)); c.pop('entry_order', None)
s = build(c)
check(hero_count(s) >= 3, f'entry_order なし → 今までどおり減らさない（{hero_count(s)}）')
# 3
check(ms.gyoushu_list({'業種': '造園'}) == ['造園'] and ms.gyoushu_list({'業種': ['伐採・草刈り', '家の修繕']}) == ['伐採・草刈り', '家の修繕'] and ms.gyoushu_list({}) == [], 'gyoushu_list')
check(ms.tel_note_default({'業種': ['伐採・草刈り', '家の修繕']}) == ms.tel_note_default({'業種': '伐採・草刈り'}), '電話の文は主の業種から')
check(ms.hand_font({'業種': ['なにか', '居酒屋']}, None) == 'Yusei Magic' and ms.hand_font({'業種': '居酒屋'}, None) == 'Yusei Magic', '手書きフォントは並びの中で当たる業種から')
check(ms.is_kaigo({'業種': ['介護']}) and not ms.is_kaigo({'業種': ['居酒屋']}), '介護の判定も並びで')
# 4
menus = [{'name': '庭木の伐採'}, {'name': '草刈り・除草'}, {'name': '家の修繕・リフォーム'}]
photos = [('bassai_climb.jpg', ''), ('kusakari_trimmer.jpg', ''), ('bassai_saw_log.jpg', ''), ('shuzen_plaster.jpg', '')]
fo = {'bassai_climb.jpg': '伐採・草刈り', 'kusakari_trimmer.jpg': '伐採・草刈り', 'bassai_saw_log.jpg': '伐採・草刈り', 'shuzen_plaster.jpg': '家の修繕'}
got = {m['name']: p[0] for m, p, _ in ms.match_menus(menus, photos, fo)}
check(got['家の修繕・リフォーム'] == 'shuzen_plaster.jpg', f'業種 2 つ：修繕のカード ← {got["家の修繕・リフォーム"]}')
check(got['庭木の伐採'].startswith('bassai') and got['草刈り・除草'].startswith('kusakari'), f'業種 2 つ：伐採・草刈りのカード ← {got["庭木の伐採"]}・{got["草刈り・除草"]}')
one = {m['name']: p[0] for m, p, _ in ms.match_menus(menus, photos[:3])}
one2 = {m['name']: p[0] for m, p, _ in ms.match_menus(menus, photos[:3], None)}
check(one == one2, '業種 1 つ（folder_of なし）は今までどおり')
check(ms.menu_folder({'name': 'ふつうの相談'}, ['伐採・草刈り', '家の修繕']) is None, '名前が近くないカードはフォルダを決めない')

print('合格' if ok else '不合格')
sys.exit(0 if ok else 1)
