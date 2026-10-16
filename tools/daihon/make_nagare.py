#!/usr/bin/env python3
"""実行までの流れ（A4・1枚）を作る。使い方: python3 make_nagare.py お店の設定.json 出力.html
台本と同じ部品（daihon_parts.json）と並び（order）から作る。"""
import json, sys, re, pathlib, html as H
here = pathlib.Path(__file__).resolve().parent
cfg = json.load(open(sys.argv[1], encoding='utf-8'))
lib = json.load(open(here / 'daihon_parts.json', encoding='utf-8'))
fill = lambda s: re.sub(r'\{(\w+)\}', lambda m: str(cfg.get(m.group(1), m.group(0))), s)
e = lambda s: H.escape(fill(s))
h, m = map(int, cfg['start'].split(':')); t = h*60+m
rows, prep, after = '', [], []
groups = cfg.get('groups') or [{'label': '', 'order': cfg['order']}]
for g in groups:
  if g.get('label'): rows += '<tr><td colspan="3" class="gh%s">%s</td></tr>' % (' ex' if g.get('extra') else '', e(g['label']))
  for k in g['order']:
    s = lib[k]; mn = cfg.get('min', {}).get(k, s['min'])
    own = '<span class="o">%s</span>' % e(s['oshort']) if s.get('oshort') else ''
    rows += '<tr><td class="tm">%d:%02d</td><td><b>%s</b>%s</td><td class="p">%s</td></tr>' % (t//60, t%60, e(s['title']), (' '+own) if own else '', e(s['part']))
    t += mn; prep += s.get('prep', [])
    if s.get('after'): after.append(s['after'])
end = '%d:%02d' % (t//60, t%60)
li = lambda xs: ''.join('<li>□ %s</li>' % e(x) for x in xs)
out = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>{e(cfg["name"])} 実行までの流れ</title><style>
@page{{size:A4;margin:0}}*{{box-sizing:border-box}}
body{{margin:0;font-family:"Noto Sans CJK JP","Hiragino Sans",sans-serif;color:#1f2a37;font-size:8.9pt;line-height:1.42}}
.page{{width:210mm;height:297mm;padding:9mm 14mm 7mm;display:flex;flex-direction:column}}
h1{{font-size:15pt;margin:0}}.lead{{color:#5d6875;font-size:8.6pt;margin:.6mm 0 2.5mm}}
.flow{{display:flex;gap:2mm;margin-bottom:2.5mm}}.flow div{{flex:1;background:#e8f1fb;color:#0c447c;border-radius:2mm;padding:1.6mm 2.4mm;font-size:8.6pt}}.flow b{{display:block;font-size:9.6pt}}
h2{{font-size:10.2pt;margin:2mm 0 1mm;border-left:1.2mm solid #185fa5;padding-left:2.6mm}}
ul{{list-style:none;margin:0;padding:0;columns:2;column-gap:6mm}}li{{margin:.25mm 0;break-inside:avoid}}
table{{width:100%;border-collapse:collapse}}td{{border-bottom:.25mm solid #e3e6ea;padding:.45mm 1.5mm;vertical-align:top}}
td.gh{{background:#185fa5;color:#fff;font-weight:700;font-size:8.6pt;padding:.6mm 2mm}}td.gh.ex{{background:#e8f1fb;color:#0c447c}}td.tm{{width:13mm;font-weight:700;color:#185fa5}}td.p{{width:30mm;color:#5d6875;font-size:8pt}}
.o{{display:inline-block;background:#fdf3dc;color:#6b4300;border-radius:1mm;padding:0 1.4mm;font-size:7.8pt;margin-left:1mm}}
.note{{background:#f6f7f9;border-radius:2mm;padding:1.8mm 3mm;font-size:8.6pt;margin-top:2mm}}
footer{{margin-top:auto;font-size:7.6pt;color:#999;display:flex;justify-content:space-between;border-top:.25mm solid #ddd;padding-top:1.6mm}}
</style></head><body><div class="page">
<h1>{e(cfg["name"])}さん　実行までの流れ（{e(cfg["date"])}）</h1>
<p class="lead">こちら用。当日は「進行台本」（Mac で開く）を上から進めるだけ。くわしい押し方は「手順書（部品A〜G）」</p>
<div class="flow"><div><b>① 前日まで</b>準備・印刷・持ち物の LINE</div><div><b>② 当日 {e(cfg["start"])}〜{end}</b>進行台本のとおり</div><div><b>③ その日の夜</b>待ちの続き・仕上げ</div><div><b>④ 後日</b>確かめ・記録</div></div>
<h2>① 前日までに（こちらだけで）</h2><ul>{li(prep)}</ul>
<h2>② 当日（黄色＝{e(cfg["owner"])}にしてもらうこと）</h2>
<table>{rows}</table>
<div class="note">時間が足りないとき：「時間があれば」は飛ばして「最後に必ず」へ（台本の「最後に必ずへ飛ぶ」）。<b>その日に必ず</b>やるのは、メール・ドメイン・予約の登録と、各サービスに Lift-Off を入れること（ほかは帰ったあとにこちらでできる）</div>
<h2>③ その日の夜（こちらだけで）</h2><ul>{li(after)}<li>□ 台本の「Claudeに渡す用にコピー」をチャットに貼る（作業時間の記録・資料の更新）</li></ul>
<h2>④ 後日</h2><ul><li>□ {e(cfg["owner"])}に公開のお知らせとお礼の LINE</li><li>□ 「あとに回した」手順を片づける</li><li>□ 手順書の ⚠️ を、やった画面の言葉に直す</li><li>□ 顧客管理シート：段階・ドメインの期限日・公開日</li></ul>
<footer><span>Lift-Off　作り方：make_nagare.py（台本と同じ部品と並び）</span><span>{e(cfg.get("made","2026年10月9日版"))}</span></footer>
</div></body></html>'''
pathlib.Path(sys.argv[2]).write_text(out, encoding='utf-8'); print('作りました:', sys.argv[2], '終わり予定', end)
