#!/usr/bin/env python3
"""毎月の報告を作る（Lift-Off）  2026/10/22 作成（claude/商品/毎月の報告.md）

お店の名前・月・数字・来月やること を入れると、LINE 用の画像（縦 1080×1350）と 紙用の A4 PDF を同じ中身で作る。

使い方:
  python3 make_report.py <お店のフォルダ名> <月>        例）python3 make_report.py hiyori 2026-11
  python3 make_report.py <お店のフォルダ名> <月> --auto … 「サイトを見た人」が空なら、Cloudflare Web Analytics の数（fetch_cf.py）を入れて数字.csv に書き戻す（2026/10/22）
      そのお店のホスト名は ~/src/houkoku/<お店>/サイト.txt（1行。例 colore-yomogi.com）。ほかの数字は今までどおり手で入れる
  数字の元は1か所：~/src/houkoku/<お店>/数字.csv（月ごとに1行。1行目は見出し）
    月,サイトを見た人,検索に出た回数,押された回数,地図_電話,地図_道順,地図_サイト,来月やること
    2026-10,120,900,45,6,14,9,写真を3枚足す
  お店の表示名は ~/src/houkoku/<お店>/お店.txt（1行）。なければフォルダ名
  できるもの：~/src/houkoku/<お店>/<月>.png と <月>.pdf（liftoff-hp の外。公開しない）

決まり:
  - 数字が空・その月の行がない → 作らずにエラーで止める
  - 先月の行があれば「先月より +◯」を出す。なければ「初めての報告」
  - 「売上が増えた」のような、数字から言えない文は入れない。少ない月もそのまま出す
  - 見た目は Lift-Off の紺（#17283A）と黄色（#F2C230）。文字は大きく
  - 作り方：HTML を1つ作り、Chrome（headless）で画像（1080×1350）と PDF（A4）にする
"""
import sys, os, csv, html, subprocess, re, datetime

HOME = os.path.expanduser('~')
BASE = os.path.join(HOME, 'src', 'houkoku')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
COLS = ['サイトを見た人', '検索に出た回数', '押された回数', '地図_電話', '地図_道順', '地図_サイト']
LABELS = {'サイトを見た人': 'ホームページを見た人', '検索に出た回数': 'Google 検索に出た回数', '押された回数': '検索から押された回数',
          '地図_電話': 'Googleマップから電話', '地図_道順': 'Googleマップで道順', '地図_サイト': 'Googleマップからサイトへ'}
UNITS = {'サイトを見た人': '人', '検索に出た回数': '回', '押された回数': '回', '地図_電話': '回', '地図_道順': '回', '地図_サイト': '回'}

def e(t): return html.escape(str(t), quote=True)
def die(msg): sys.exit('❌ ' + msg)

def read_rows(path):
    if not os.path.exists(path): die(f'数字のファイルがありません：{path}')
    with open(path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows: die('数字.csv に行がありません')
    for need in ['月'] + COLS:
        if need not in rows[0]: die(f'数字.csv の1行目（見出し）に「{need}」がありません')
    return rows

def to_int(v, col, month):
    v = str(v or '').strip().replace(',', '')
    if v == '': die(f'{month} の「{col}」が空です（数字を入れてから作る）')
    if not re.fullmatch(r'-?\d+', v): die(f'{month} の「{col}」が数字ではありません：{v}')
    return int(v)

def prev_month(m):
    y, mo = int(m[:4]), int(m[5:7])
    return f'{y - 1}-12' if mo == 1 else f'{y}-{mo - 1:02d}'

def jp_month(m): return f'{int(m[:4])}年{int(m[5:7])}月'

def diff_text(now, before):
    if before is None: return ''
    d = now - before
    if d > 0: return f'先月より +{d:,}'
    if d < 0: return f'先月より −{abs(d):,}'
    return '先月と同じ'

def build_html(shop, month, cur, prev, todo):
    first = prev is None
    cards = ''
    for col in COLS:
        n = cur[col]
        sub = '初めての報告' if first else diff_text(n, prev[col])
        cls = ''
        if not first:
            d = n - prev[col]
            cls = ' up' if d > 0 else (' down' if d < 0 else '')
        cards += f'''
      <div class="card{cls}">
        <div class="lab">{e(LABELS[col])}</div>
        <div class="num">{n:,}<small>{UNITS[col]}</small></div>
        <div class="sub">{e(sub)}</div>
      </div>'''
    note = '※ 数字は Cloudflare（ホームページ）・Google 検索・Googleマップの集計です。少ない月もそのまま載せています。'
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>{e(shop)} {e(jp_month(month))}の報告</title>
<style>
:root{{--ink:#17283A;--signal:#F2C230;--paper:#FBF9F4;--mu:#6B7A8C;--line:#DCE1E8;--up:#2F7A42;--down:#5A6B82}}  /* 減った月は赤にせず、落ち着いた青灰色（責めない）2026/10/22 */
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Hiragino Sans","Noto Sans CJK JP","Yu Gothic",sans-serif;color:var(--ink);background:#fff;-webkit-font-smoothing:antialiased}}
/* LINE 用：1080×1350（px） */
.sheet{{width:1080px;height:1350px;background:var(--paper);position:relative;overflow:hidden;display:flex;flex-direction:column}}
.head{{background:var(--ink);color:#fff;padding:44px 56px 36px}}
.head .k{{font-size:26px;letter-spacing:.2em;color:var(--signal);font-weight:700}}
.head h1{{font-size:54px;line-height:1.25;margin-top:10px;font-weight:800;letter-spacing:.02em}}
.head .shop{{font-size:30px;margin-top:10px;opacity:.9}}
.body{{padding:40px 56px 0;flex:1;display:flex;flex-direction:column}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}
.card{{background:#fff;border:3px solid var(--line);border-radius:22px;padding:24px 26px 22px;min-height:190px}}
.card .lab{{font-size:26px;color:var(--mu);font-weight:700;line-height:1.3}}
.card .num{{font-size:74px;font-weight:800;line-height:1.1;margin-top:8px;letter-spacing:-.01em}}
.card .num small{{font-size:28px;margin-left:8px;font-weight:700;color:var(--mu)}}
.card .sub{{font-size:26px;margin-top:6px;font-weight:700;color:var(--mu)}}
.card.up .sub{{color:var(--up)}}
.card.down .sub{{color:var(--down)}}
.todo{{margin-top:28px;background:var(--signal);border-radius:22px;padding:26px 30px}}
.todo .k{{font-size:26px;font-weight:800;letter-spacing:.12em}}
.todo p{{font-size:40px;font-weight:800;line-height:1.35;margin-top:6px}}
.foot{{margin-top:auto;padding:0 0 36px;display:flex;justify-content:space-between;align-items:flex-end}}
.foot .n{{font-size:24px;color:var(--mu);line-height:1.5;max-width:760px}}
.foot .lo{{font-size:30px;font-weight:800;letter-spacing:.08em}}
/* 紙用：A4 は同じ中身を縮めて1枚に（印刷のときだけ） */
@page{{size:210mm 297mm;margin:0}}
@media print{{
  html,body{{width:210mm;height:297mm;overflow:hidden;background:#fff}}
  .sheet{{transform:scale(0.7349);transform-origin:0 0;width:1080px;height:1350px;position:absolute;left:0;top:0}}  /* 1080px → 210mm（793.7px）。高さは 1350×0.7349＝992px≒262mm で A4 に収まる */
  .wrapA4{{position:absolute;left:0;top:0;width:210mm;height:297mm;background:#FBF9F4;overflow:hidden}}  /* 縮めた元の箱（1080×1350px）が紙の外に出て2ページ目を作らないように */
}}
</style>
</head>
<body>
<div class="wrapA4"><div class="sheet">
  <div class="head">
    <div class="k">毎月の報告</div>
    <h1>{e(jp_month(month))}の<br>ホームページとGoogleマップ</h1>
    <div class="shop">{e(shop)}</div>
  </div>
  <div class="body">
    <div class="grid">{cards}
    </div>
    <div class="todo"><div class="k">来月やること</div><p>{e(todo)}</p></div>
    <div class="foot"><div class="n">{e(note)}</div><div class="lo">Lift-Off</div></div>
  </div>
</div></div>
</body>
</html>
'''

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    key, month = sys.argv[1], sys.argv[2]
    if not re.fullmatch(r'\d{4}-\d{2}', month): die('月は 2026-11 のように書く')
    d = os.path.join(BASE, key)
    rows = read_rows(os.path.join(d, '数字.csv'))
    by = {r['月'].strip(): r for r in rows}
    if month not in by: die(f'{month} の行が 数字.csv にありません（月ごとに1行。見出しは「月」）')
    if '--auto' in sys.argv and not str(by[month].get('サイトを見た人') or '').strip():
        site_file = os.path.join(d, 'サイト.txt')
        if not os.path.exists(site_file): die(f'--auto には {site_file}（ホスト名を1行）が要ります')
        host = open(site_file, encoding='utf-8').read().strip().split('\n')[0].strip()
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import fetch_cf
        n = fetch_cf.counts(host, month)['visits']
        by[month]['サイトを見た人'] = str(n)
        # 数字.csv に書き戻す（元は1か所）
        csv_path = os.path.join(d, '数字.csv')
        with open(csv_path, encoding='utf-8-sig', newline='') as f: rd = csv.DictReader(f); fields = rd.fieldnames; allrows = list(rd)
        for r in allrows:
            if r['月'].strip() == month: r['サイトを見た人'] = str(n)
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(allrows)
        print(f'Cloudflare から「サイトを見た人」を入れました：{host} {month} → {n:,} 人（数字.csv に書き戻し）')
    cur = {c: to_int(by[month][c], c, month) for c in COLS}
    pm = prev_month(month)
    prev = {c: to_int(by[pm][c], c, pm) for c in COLS} if pm in by else None
    todo = str(by[month].get('来月やること') or '').strip()
    if not todo: die(f'{month} の「来月やること」が空です（1つ書く）')
    shop_file = os.path.join(d, 'お店.txt')
    shop = open(shop_file, encoding='utf-8').read().strip() if os.path.exists(shop_file) else key
    html_path = os.path.join(d, f'{month}.html')
    png, pdf = os.path.join(d, f'{month}.png'), os.path.join(d, f'{month}.pdf')
    open(html_path, 'w', encoding='utf-8').write(build_html(shop, month, cur, prev, todo))
    if not os.path.exists(CHROME): die('Google Chrome が見つかりません（画像と PDF を作るのに使う）')
    prof = os.path.join(d, '.chrome-prof')
    base = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--user-data-dir=' + prof]
    subprocess.run(base + ['--window-size=1080,1350', '--force-device-scale-factor=1', '--screenshot=' + png, 'file://' + html_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(base + ['--no-pdf-header-footer', '--print-to-pdf=' + pdf, 'file://' + html_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for p in (png, pdf):
        if not os.path.exists(p) or os.path.getsize(p) < 1000: die('作れませんでした：' + p)
    print('作りました：', png, '（LINE 用 1080×1350）')
    print('作りました：', pdf, '（紙用 A4）')
    print('先月：', ('あり（' + pm + '）' if prev else 'なし → 「初めての報告」'))

if __name__ == '__main__':
    main()
