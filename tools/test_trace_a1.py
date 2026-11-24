#!/usr/bin/env python3
"""配置の型（"layout":"a1trace"。tools/trace_a1.py・kuji.py・make_site.crop_roles）の検査（2026/11/24）
使い方: python3 tools/test_trace_a1.py
  見本の設定（templates/site_sample_a1trace.json）で仮のフォルダに作って確かめる：
  1. check_site.py が ❌ 0（ブラウザがあれば はみ出し 320〜1280 も ✅）
  2. 同じ種（knobs_seed）なら同じ HTML（道具の版の注釈は除く）
  3. 別の種なら、色か 1画面目の割合が違う
  4. くじ 1124 は想永 _8・_9 のつまみと同じ（p1 36・gap 7・茶灰・はじめて → 商品・寄り↔並び・ずらし 20）
  5. 決まりの外のつまみ（knobs）では止まる
  6. 素材の写真に札が付き、12 の役の写真が images/a1/ にある
  合格：全部 OK"""
import io, json, os, re, shutil, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import kuji
SAMPLE = os.path.join(here, 'templates', 'site_sample_a1trace.json')
ok = True
def check(cond, msg, extra=''):
    global ok
    print(('OK ' if cond else 'NG ') + msg + ('' if cond else '  ' + str(extra)))
    ok = ok and cond

root = tempfile.mkdtemp(prefix='trace_a1_')
def build(name, **over):
    c = json.load(io.open(SAMPLE, encoding='utf-8')); c.update(over)
    cf = os.path.join(root, name + '.json'); json.dump(c, io.open(cf, 'w', encoding='utf-8'), ensure_ascii=False)
    out = os.path.join(root, name)
    r = subprocess.run([sys.executable, os.path.join(here, 'make_site.py'), cf, out], capture_output=True, text=True, timeout=600)
    html = io.open(os.path.join(out, 'index.html'), encoding='utf-8').read() if os.path.isfile(os.path.join(out, 'index.html')) else ''
    return out, html, r.stdout + r.stderr
def strip_ver(h): return re.sub(r'道具の版 [^・）]*', '', h)

# 1 ❌ 0・はみ出し
out1, h1, log1 = build('a')
chk = subprocess.run([sys.executable, os.path.join(here, 'check_site.py'), out1], capture_output=True, text=True, timeout=600).stdout
m = re.search(r'❌ 直す (\d+)', chk)
check(m and m.group(1) == '0', '1 check_site ❌ 0', chk[-400:])
check('はみ出しなし' in chk or 'ブラウザが使えない' in chk, '1 はみ出し 320〜1280 なし（ブラウザがあるとき）', [l for l in chk.splitlines() if 'はみ出し' in l])
# 2 同じ種なら同じ HTML
out2, h2, _ = build('b')
check(h1 and strip_ver(h1) == strip_ver(h2), '2 同じ種（1124）なら同じ HTML')
# 3 別の種なら色か割合が違う
k1, k2 = kuji.draw(1124), kuji.draw(7)
out3, h3, _ = build('c', knobs_seed=7)
diff = (k1['bg'], k1['band'], k1['p1']) != (k2['bg'], k2['band'], k2['p1'])
check(diff and h3 and strip_ver(h3) != strip_ver(h1), '3 別の種（7）なら色か 1画面目の割合が違う', (k1['bg'], k1['band'], k1['p1'], k2['bg'], k2['band'], k2['p1']))
# 4 くじ 1124
check(k1['p1'] == 36 and k1['gap'] == 7 and k1['band'] == '#6b5e55' and k1['order'] == 'はじめて → 商品' and k1['swap'].startswith('寄り') and k1['shift'] == 20 and k1['squares'] == '2画面目2枚・4段目1枚', '4 くじ 1124 は想永 _8・_9 と同じつまみ', k1)
check(not kuji.validate(k1) and not kuji.validate(kuji.DEFAULT), '4 くじの答えと既定は決まりの中')
# 5 決まりの外で止まる
out5, h5, log5 = build('d', knobs={'p1': 50})
check(not h5 and 'knobs' in log5, '5 決まりの外のつまみ（p1 50）では止まる', log5[-200:])
# 6 札と役
roles = [f for f in os.listdir(os.path.join(out1, 'images', 'a1')) if f.endswith('.jpg')] if os.path.isdir(os.path.join(out1, 'images', 'a1')) else []
check(len(roles) == 12, '6 12 の役の写真が images/a1/ にある', roles)
check(h1.count('data-source="stock"') >= 12 and h1.count('class="img-note"') >= 12, '6 素材の写真に札が付く（札の文は wbr で <wbr> が入るので class で数える）', (h1.count('data-source="stock"'), h1.count('class="img-note"')))
check('data-layout="a1trace"' in h1 and 'class="vt mi"' in h1 and 'data-pair="hero"' in h1, '6 検査用の印（data-layout・.vt・data-pair）がある')
shutil.rmtree(root, ignore_errors=True)
print('合格' if ok else '不合格')
sys.exit(0 if ok else 1)
