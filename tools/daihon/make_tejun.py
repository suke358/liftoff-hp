#!/usr/bin/env python3
"""手順書を「部品ごと」に分けて管理する道具（Lift-Off）2026/10/9 作成・2026/10/12 画像入りに

使い方:
  置き場所：~/src/liftoff-hp/tools/daihon/（2026/10/17 に colore の「進行台本の道具」と liftoff-buhin/tools から引っ越し）
  部品の .md と画像は ~/src/liftoff-buhin/（daihon_settei.json の "buhin"。お店の情報が入るので公開リポジトリには置かない）
  1) 部品に分ける（.md を直したら毎回）
     python3 make_tejun.py split ~/src/liftoff-buhin/buhin/   → tejun_parts.json（.md の「画像：」の行は印だけ入れる）
     python3 make_tejun.py split 手順書.html              → tejun_parts.json（まとめた HTML から分けるとき）
  2) 1つだけ出す      python3 make_tejun.py one C 出力.html
  3) 組み合わせて出す  python3 make_tejun.py mix A,B,C,D 出力.html   （上のタブで切りかえ・印刷すると全部）
  4) 全部の単品を一度に python3 make_tejun.py all 出力フォルダ
部品の名前: KUMI（組み立て表）, A（Gmail）, B（Googleマップ）, C（ドメイン）, D（Cloudflare）, E（RESERVA）, F（公式LINE）, G（フォーム）, H（パスワード）
台本（make_daihon.py）は tejun_parts.json があれば、手順ごとに「くわしい手順」を自動で付ける（画像も中に埋めこむ）。

画像のしくみ（2026/10/12）：
  .md の手順の下に「   画像：C-B-05_検索の欄.png」の行を書く → gazou/印つき/C-B-05_検索の欄.jpg（make_gazou.py が marks.json の印を重ねたもの）を、
  出すときに手順の下に埋めこむ（1つのファイルで開けるよう data: で入れる）。「画像：あとで（…）」と書くと、その文をそのまま薄く出す。
"""
import json, re, sys, os, pathlib, html as H, base64

HERE = pathlib.Path(__file__).resolve().parent

def buhin_root():
    """部品（buhin/*.md）と画像（gazou/）の置き場所。お店の情報が入るので公開リポジトリ（liftoff-hp）には置かない（2026/10/17 引っ越し）
    決め方：環境変数 LIFTOFF_BUHIN → 同じフォルダの daihon_settei.json の "buhin" → ~/src/liftoff-buhin"""
    p = os.environ.get('LIFTOFF_BUHIN')
    cfg = HERE / 'daihon_settei.json'
    if not p and cfg.exists(): p = json.loads(cfg.read_text(encoding='utf-8')).get('buhin')
    return pathlib.Path(p or '~/src/liftoff-buhin').expanduser()

ROOT = buhin_root()
PARTS_FILE = HERE / 'tejun_parts.json'   # 作った部品の写し（お店の情報が混ざるので git には入れない。.gitignore）
GAZOU = ROOT / 'gazou' / '印つき'
MARKS = ROOT / 'gazou' / 'marks.json'
SHORT = {'KUMI': '組み立て表', 'A': 'Gmail', 'B': 'Googleマップ', 'C': 'ドメイン', 'D': 'Cloudflare', 'E': 'RESERVA', 'F': '公式LINE', 'G': 'フォーム', 'H': 'パスワード'}

def key_of(title):
    m = re.match(r'部品([A-H])', title)
    return m.group(1) if m else ('KUMI' if '組み立て表' in title else None)

def add_anchors(key, body):
    """h3 の頭の番号（B-2・3-1・E. など）から id を付ける。台本から飛ぶのに使う"""
    def rep(m):
        txt = re.sub(r'<[^>]+>', '', m.group(2))
        code = txt.split(' ')[0].split('　')[0].rstrip('.．')
        aid = f'{key}:{code}' if re.match(r'^[0-9A-Z][0-9A-Z\-]*$', code) else ''
        return f'<h3{(" id=" + chr(34) + aid + chr(34)) if aid else ""}>{m.group(2)}</h3>'
    body = re.sub(r'<h3([^>]*)>(.*?)</h3>', rep, body, flags=re.S)
    n = [0]
    def num(m):
        n[0] += 1
        return f'<h3 id="{key}:h{n[0]}">' if 'id=' not in m.group(0) else m.group(0)
    return re.sub(r'<h3(?: id="[^"]*")?>', num, body)

GZ_LINE = re.compile(r'^([ \t]*)画像：(.+?)\s*$', re.M)
def md_gazou(md):
    """「画像：〜」の行を印（<span class="gz" data-gz="…">）にする。出すときに embed() が画像に置きかえる"""
    def rep(m):
        ind, what = m.group(1), m.group(2).strip()
        if what.startswith('あとで'):
            return f'{ind}<span class="gz-later" data-gz-later="{H.escape(what)}"></span>'
        return f'{ind}<span class="gz" data-gz="{H.escape(what)}"></span>'
    return GZ_LINE.sub(rep, md)

def split_html(src):
    t = src.read_text(encoding='utf-8')
    out = {}
    for sec in re.findall(r'<section>(.*?)</section>', t, flags=re.S):
        m = re.search(r'<h1>(.*?)</h1>', sec, flags=re.S)
        title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        k = key_of(title)
        if not k: continue
        body = sec[m.end():]
        out[k] = {'title': title, 'short': SHORT.get(k, k), 'html': add_anchors(k, body)}
    return out

def split_md(folder):
    import markdown
    out = {}
    for p in sorted(pathlib.Path(folder).glob('*.md')):
        md = p.read_text(encoding='utf-8')
        m = re.search(r'^# (.+)$', md, flags=re.M)
        if not m: continue
        title = m.group(1).strip(); k = key_of(title)
        if not k: continue
        body = markdown.markdown(md_gazou(md[m.end():]), extensions=['tables', 'sane_lists'])
        out[k] = {'title': title, 'short': SHORT.get(k, k), 'html': add_anchors(k, body), 'file': p.name}
    return out

def gazou_list(parts):
    """部品ごとの画像の一覧（撮れた／あとで）。作業メモ用"""
    res = {}
    for k, v in parts.items():
        got = re.findall(r'data-gz="([^"]+)"', v['html']); later = re.findall(r'data-gz-later="([^"]+)"', v['html'])
        res[k] = {'撮れた': [H.unescape(x) for x in got], 'あとで': [H.unescape(x) for x in later]}
    return res

_cache = {}
def embed(html):
    """印（data-gz）を、印つきの画像（data: URI）に置きかえる。ないときは「（画像はまだ）」"""
    marks = json.loads(MARKS.read_text(encoding='utf-8')).get('画像', {}) if MARKS.exists() else {}
    def rep(m):
        name = H.unescape(m.group(1)); jpg = GAZOU / (pathlib.Path(name).stem + '.jpg')
        if not jpg.exists():
            print(f'⚠️ 画像がありません：{name}（make_gazou.py で作る）')
            return f'<span class="gz-later">画像：{H.escape(name)}（まだ）</span>'
        if name not in _cache: _cache[name] = base64.b64encode(jpg.read_bytes()).decode()
        cap = ''.join(f'<b>{i + 1}</b> {H.escape(x["一言"])}　' for i, x in enumerate(marks.get(name, {}).get('印', [])))
        note = marks.get(name, {}).get('注', '')
        day = marks.get(name, {}).get('撮った日', '')
        return (f'<span class="gz"><img src="data:image/jpeg;base64,{_cache[name]}" alt="{H.escape(name)}">'
                f'<span class="gzc">{cap}{("<i>" + H.escape(note) + "</i>") if note else ""}<small>{H.escape(pathlib.Path(name).stem)}{("・" + day) if day else ""}</small></span></span>')
    html = re.sub(r'<span class="gz" data-gz="([^"]+)"></span>', rep, html)
    html = re.sub(r'<span class="gz-later" data-gz-later="([^"]+)"></span>', lambda m: f'<span class="gz-later">画像：{m.group(1)}</span>', html)
    return html

CSS = """:root{--ink:#17283a;--sub:#5d6875;--line:#cfd5dc;--bg:#ffffff;--card:#f6f7f9;--th:#eef1f4;--acc:#185fa5;--pink:#f4a0b4;--code:#f2f4f6}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ink:#e6e9ee;--sub:#a3acb7;--line:#38414c;--bg:#14181d;--card:#1c2229;--th:#232a33;--acc:#5b9be0;--pink:#c0607a;--code:#232a33;color-scheme:dark}}
:root[data-theme="dark"]{--ink:#e6e9ee;--sub:#a3acb7;--line:#38414c;--bg:#14181d;--card:#1c2229;--th:#232a33;--acc:#5b9be0;--pink:#c0607a;--code:#232a33;color-scheme:dark}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Hiragino Sans","Noto Sans CJK JP","Noto Sans JP",sans-serif;font-size:15px;line-height:1.7;word-break:break-word;overflow-wrap:anywhere}
.wrap{max-width:860px;margin:0 auto;padding-inline:16px;padding-block:12px 40px}
.tabs{position:sticky;top:0;z-index:3;background:var(--bg);display:flex;flex-wrap:wrap;gap:6px;padding-block:10px;border-bottom:1px solid var(--line)}
.tabs button{font:inherit;font-size:14px;padding:6px 12px;border:1px solid var(--line);border-radius:99px;background:var(--card);color:var(--ink);cursor:pointer}
.tabs button[aria-pressed="true"]{background:var(--acc);border-color:var(--acc);color:#fff}
h1{font-size:21px;line-height:1.4;margin:18px 0 6px;text-wrap:balance}
h2{font-size:17px;border-left:4px solid var(--pink);padding-left:8px;margin:22px 0 6px}
h3{font-size:15.5px;margin:16px 0 4px;scroll-margin-top:70px}h4{font-size:15px;margin:12px 0 4px}
.tbl{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;margin:6px 0}
th,td{border:1px solid var(--line);padding:4px 7px;vertical-align:top;text-align:left}th{background:var(--th)}
code{background:var(--code);padding:0 3px;border-radius:3px;font-size:13.5px}
ol,ul{padding-left:22px}li{margin:2px 0}a{color:var(--acc);word-break:break-all}
.part[hidden]{display:none}
.gz{display:block;margin:6px 0 10px}.gz img{display:block;width:300px;max-width:100%;border:1px solid var(--line);border-radius:8px}
.gzc{display:block;font-size:13px;color:var(--sub);margin-top:3px;max-width:600px}.gzc b{display:inline-block;background:#dc2626;color:#fff;border-radius:99px;min-width:18px;text-align:center;font-size:12px;margin-right:2px}
.gzc i{display:block;font-style:normal;font-size:12.5px}.gzc small{display:block;font-size:11px;opacity:.7}
.gz-later{display:block;font-size:12.5px;color:var(--sub);background:var(--card);border:1px dashed var(--line);border-radius:6px;padding:2px 8px;margin:4px 0 6px;width:fit-content}
@media print{.tabs{display:none}.part{display:block!important;break-before:page}.part:first-of-type{break-before:auto}body{font-size:10pt}.gz img{width:60mm;break-inside:avoid}}"""

def wrap_tables(h):
    return re.sub(r'(<table.*?</table>)', r'<div class="tbl">\1</div>', h, flags=re.S)

def page(keys, parts, title):
    tabs = '' if len(keys) == 1 else '<nav class="tabs">' + ''.join(
        f'<button type="button" data-k="{k}" aria-pressed="{"true" if i == 0 else "false"}">{"部品" + k + " " if k != "KUMI" else ""}{H.escape(parts[k]["short"])}</button>' for i, k in enumerate(keys)) + '</nav>'
    secs = ''.join(f'<section class="part" id="part-{k}"{"" if i == 0 else " hidden"}><h1>{H.escape(parts[k]["title"])}</h1>{embed(wrap_tables(parts[k]["html"]))}</section>' for i, k in enumerate(keys))
    js = """<script>var b=document.querySelectorAll('.tabs button');b.forEach(function(x){x.onclick=function(){b.forEach(function(y){y.setAttribute('aria-pressed',y===x?'true':'false')});document.querySelectorAll('.part').forEach(function(s){s.hidden=s.id!=='part-'+x.dataset.k});scrollTo(0,0)}});</script>""" if len(keys) > 1 else ''
    return f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{H.escape(title)}</title><style>{CSS}</style></head><body><div class="wrap">{tabs}{secs}</div>{js}</body></html>'

def load():
    return json.loads(PARTS_FILE.read_text(encoding='utf-8'))

if __name__ == '__main__':
    if len(sys.argv) < 3: raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == 'split':
        src = pathlib.Path(sys.argv[2])
        parts = split_md(src) if src.is_dir() else split_html(src)
        PARTS_FILE.write_text(json.dumps(parts, ensure_ascii=False, indent=1), encoding='utf-8')
        print('分けました:', ', '.join(f'{k}（{v["short"]}）' for k, v in parts.items()))
        for k, g in gazou_list(parts).items(): print(f'  {k}: 画像 {len(g["撮れた"])} 枚・あとで {len(g["あとで"])}')
    elif cmd in ('one', 'mix'):
        parts = load(); keys = [k.strip() for k in sys.argv[2].split(',')]
        for k in keys:
            if k not in parts: raise SystemExit('部品「%s」がありません: %s' % (k, ', '.join(parts)))
        title = '手順書 ' + '・'.join(parts[k]['short'] for k in keys)
        pathlib.Path(sys.argv[3]).write_text(page(keys, parts, title), encoding='utf-8'); print('作りました:', sys.argv[3])
    elif cmd == 'all':
        parts = load(); d = pathlib.Path(sys.argv[2]); d.mkdir(parents=True, exist_ok=True)
        for k, v in parts.items():
            name = ('手順書_' + ('' if k == 'KUMI' else k + '_') + v['short'] + '.html')
            (d / name).write_text(page([k], parts, '手順書 ' + v['short']), encoding='utf-8')
        print('作りました:', d, len(parts), '枚')
    else:
        raise SystemExit(__doc__)
