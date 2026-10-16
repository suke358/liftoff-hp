#!/usr/bin/env python3
"""進行台本を作る。使い方: python3 make_daihon.py お店の設定.json 出力.html
- 部品は daihon_parts.json（同じフォルダ）。並べる順は設定の "order"（か "groups"）、時間を変えたい部品は "min": {"部品名": 分}
- 部品の文の {owner} {shop} などは、設定の同じ名前の値に置きかわる
- 予定の時刻は "start" と各部品の分数から自動で計算する
- 手順書（tejun_parts.json）を中に埋めこむ。画像（gazou/印つき）も埋めこむので、1つのファイルで開ける（2026/10/12）
- パスワードを打つ欄があったら止まる（2026/10/12 の決まり）"""
import json, sys, re, pathlib
here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here))
from make_tejun import embed
cfg = json.load(open(sys.argv[1], encoding='utf-8'))
lib = json.load(open(here / 'daihon_parts.json', encoding='utf-8'))
tpl = (here / 'daihon_template.html').read_text(encoding='utf-8')
def fill(x):
    if isinstance(x, str):
        def r(m):
            k = m.group(1)
            if k not in cfg: raise SystemExit('設定に「%s」がありません' % k)
            return str(cfg[k])
        return re.sub(r'\{(\w+)\}', r, x)
    if isinstance(x, list): return [fill(i) for i in x]
    if isinstance(x, dict): return {k: fill(v) for k, v in x.items()}
    return x
cfg.setdefault('pwgroup', 'Lift-Off ' + cfg['name'])
h, m = map(int, cfg['start'].split(':')); t = h * 60 + m
steps = []
groups = cfg.get('groups') or [{'label': '', 'order': cfg['order']}]
plan = [(k, gi, g) for gi, g in enumerate(groups) for k in g['order']]
for k, gi, g in plan:
    if k not in lib: raise SystemExit('部品「%s」がありません。daihon_parts.json の名前: %s' % (k, ', '.join(lib)))
    s = fill(lib[k]); s['min'] = cfg.get('min', {}).get(k, s['min'])
    s['at'] = '%d:%02d' % (t // 60, t % 60); t += s['min']
    s['grp'] = gi; s['glabel'] = g.get('label', ''); s['extra'] = bool(g.get('extra')); steps.append(s)
shop = {k: cfg[k] for k in ('key', 'name', 'owner', 'date', 'start')}
shop['pwgroup'] = cfg['pwgroup']
# パスワードを打つ欄は作らない
bad = [x for s in steps for x in s.get('vals', []) if 'パスワード' in x]
if bad: raise SystemExit('❌ 「パスワード」という言葉の入った欄があります。言い方を変えてください：' + '／'.join(bad))
tj = {}
tp = here / 'tejun_parts.json'
if tp.exists():
    allp = json.loads(tp.read_text(encoding='utf-8'))
    need = {x[0] for s in steps for x in s.get('tejun', [])} | {'KUMI'}
    tj = {k: {'title': v['title'], 'short': v['short'], 'html': embed(v['html'])} for k, v in allp.items() if k in need}
    miss = [x[1] for s in steps for x in s.get('tejun', []) if x[1] and ('id="%s"' % x[1]) not in tj.get(x[0], {}).get('html', '')]
    if miss: print('⚠️ 手順書に見出しがありません（ボタンは出るが飛べない）:', '／'.join(miss))
# 題名はお店の名前から（前は colore と書いてあった。2026/10/17）
out = tpl.replace('__TITLE__', cfg['name'] + ' 当日の進行台本').replace('__SHOP__', json.dumps(shop, ensure_ascii=False)).replace('__STEPS__', json.dumps(steps, ensure_ascii=False)).replace('__TEJUN__', json.dumps(tj, ensure_ascii=False).replace('</', '<\\/'))
if re.search(r'<(input|textarea)[^>]*(type="password"|パスワード)', out): raise SystemExit('❌ 出来上がりにパスワードの欄があります')
p = pathlib.Path(sys.argv[2]); p.write_text(out, encoding='utf-8')
print('作りました: %s（%d 手順・終わり予定 %d:%02d・%.1f MB）' % (sys.argv[2], len(steps), t // 60, t % 60, p.stat().st_size / 1048576))
