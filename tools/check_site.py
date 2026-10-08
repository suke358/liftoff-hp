#!/usr/bin/env python3
"""公開前チェック（Lift-Off）  2026/10/8 作成

使い方:
  python3 check_site.py <サイトのフォルダ>            … 全部（ブラウザでのはみ出しチェックは Playwright があるときだけ）
  python3 check_site.py <サイトのフォルダ> --no-browser
  python3 check_site.py <サイトのフォルダ> --all          … 見比べ用の別ページ（v1/ など）も全部調べる（ふつうはトップだけ）

調べること:
  1. 古いスマホで崩れる書き方（マニュアル16）
  2. 電話番号がページ内でそろっているか
  3. 使ってはいけない言葉（効果を言い切る・一番だと言い切る）
  4. 画像・リンク先のファイルがあるか／ページ内リンク（#〜）の行き先があるか
  5. 画像の説明（alt）・外部リンクの rel・noindex・シェア用画像・文の折り返し
  6. 横にはみ出していないか（幅 320・360・390・768・1280）
結果: ✅ 問題なし ／ ⚠️ 確かめる ／ ❌ 直す
"""
import sys, os, re, glob, html
from html.parser import HTMLParser

# ---- 設定 -------------------------------------------------------------
NG_WORDS = {  # 言葉: 理由
    'デトックス': '効果をうたう言葉', '痩せる': '効果の断定', '痩せます': '効果の断定', '治る': '効果の断定',
    '治ります': '効果の断定', '解消': '効果の断定になりやすい', '改善します': '効果の断定',
    '必ず': '断定（文脈を確認）', '確実': '断定', '絶対': '断定', '効果抜群': '効果の断定',
    '極上': '一番だと言い切る', 'No.1': '一番だと言い切る', 'NO.1': '一番だと言い切る', 'ナンバーワン': '一番だと言い切る',
    '日本一': '一番だと言い切る', '地域一': '一番だと言い切る', '最高級': '一番だと言い切る',
    '一番人気': '根拠のない表現（「おすすめ」にする）', 'いちばん人気': '根拠のない表現（「おすすめ」にする）',
    '人気No': '根拠のない表現', '永久': '「永久脱毛」などは使わない',
}
OLD_CSS = [  # (正規表現, 名前, 予備の書き方)
    (r'aspect-ratio\s*:', 'aspect-ratio（縦横比）', '画像そのものの縦横比で高さを決める（img を height:auto）'),
    (r'\b\d*\.?\d+(cqw|cqh|cqi|cqb)\b', 'cqw（枠の幅に合わせた大きさ）', '先に vw で同じくらいの大きさを書く'),
    (r'\b\d*\.?\d+(svh|dvh|lvh|svw|dvw)\b', 'svh / dvh（スマホの画面の高さ）', '先に vh で書く'),
    (r'(?<![-\w])inset\s*:', 'inset（上下左右まとめて）', '先に top / left / right / bottom を書く'),
    (r'margin-inline\s*:|margin-block\s*:|padding-inline\s*:|padding-block\s*:', 'margin-inline など（まとめ書き）', '先に margin-left / margin-right などを書く'),
    (r':has\(', ':has()（新しい選び方）', '使わない（JavaScript かクラスで代わりに）'),
    (r'text-wrap\s*:', 'text-wrap', '効かなくても崩れないか確かめる'),
]
FALLBACK = {  # 同じ { } の中にこれがあれば「予備あり」とみなす
    'inset': r'\btop\s*:', 'margin-inline': r'margin-left\s*:', 'padding-inline': r'padding-left\s*:',
    'margin-block': r'margin-top\s*:', 'padding-block': r'padding-top\s*:',
}
WIDTHS = [320, 360, 390, 768, 1280]

# ---- 下ごしらえ -------------------------------------------------------
class TextAndTags(HTMLParser):
    def __init__(s):
        super().__init__(); s.text=[]; s.skip=0; s.tags=[]; s.ids=set()
    def handle_starttag(s, t, a):
        d=dict(a); s.tags.append((t, d, s.getpos()[0]))
        if d.get('id'): s.ids.add(d['id'])
        if t in ('script','style','svg','title','noscript'): s.skip+=1
    def handle_endtag(s, t):
        if t in ('script','style','svg','title','noscript') and s.skip: s.skip-=1
    def handle_data(s, d):
        if not s.skip: s.text.append((d, s.getpos()[0]))

def norm_tel(t): return re.sub(r'\D', '', t.replace('+81', '0'))

results = []  # (mark, area, message)
OLD_HITS = {}  # (file, name, fallback) -> [lines]
ROOT = '.'
def add(mark, area, msg): results.append((mark, area, msg))

def check_css(path, css, base_line=0):
    found = False
    for rx, name, fb in OLD_CSS:
        for m in re.finditer(rx, css):
            line = css.count('\n', 0, m.start()) + 1 + base_line
            a = css.rfind('{', 0, m.start()); b = css.find('}', m.start())
            block = css[a+1:b] if a != -1 and b != -1 else ''
            before = css[a+1:m.start()] if a != -1 else ''
            key = name.split('（')[0].strip()
            ok = False
            for k, frx in FALLBACK.items():
                if key.startswith(k) and re.search(frx, before): ok = True
            if key.startswith('svh') or key.startswith('cqw'):
                prop = re.search(r'([\w-]+)\s*:[^;{}]*$', css[a+1:m.end()])
                if prop and re.search(re.escape(prop.group(1)) + r'\s*:[^;]*\b\d*\.?\d+(vh|vw|px|rem|em|%)', before): ok = True
            # @supports not (aspect-ratio…) で古いスマホ用の書き方を別に用意してあれば OK
            if key.startswith('aspect-ratio') and re.search(r'@supports\s+not\s*\(\s*aspect-ratio', css): ok = True
            if ok: continue
            found = True
            OLD_HITS.setdefault((path, name, fb), []).append(line)
    return found

def run_static(root):
    pages = sorted(glob.glob(os.path.join(root, '**', '*.html'), recursive=True))
    pages = [p for p in pages if '/tools/' not in p and '/.git/' not in p and '/node_modules/' not in p]
    top = os.path.join(root, 'index.html')
    if '--all' not in sys.argv: pages = [p for p in pages if p == top]
    if not os.path.exists(top): add('❌', 'ファイル', 'index.html がありません'); return []
    add('✅', 'ファイル', f'調べたページ：{len(pages)} ページ（{", ".join(os.path.relpath(p, root) for p in pages[:8])}{" ほか" if len(pages)>8 else ""}）')

    old_found = False
    css_files = set()
    for p in pages:
        src0 = open(p, encoding='utf-8', errors='ignore').read()
        for m in re.finditer(r'<link[^>]+href=["\']([^"\']+\.css)["\']', src0):
            u = m.group(1)
            if not re.match(r'(https?:|//)', u): css_files.add(os.path.normpath(os.path.join(os.path.dirname(p), u)))
    for css_path in sorted(css_files):
        if os.path.exists(css_path):
            old_found |= check_css(css_path, open(css_path, encoding='utf-8', errors='ignore').read())

    for p in pages:
        rel = os.path.relpath(p, root)
        src = open(p, encoding='utf-8', errors='ignore').read()
        par = TextAndTags(); par.feed(src)
        text = ''.join(t for t, _ in par.text)
        is_top = (p == top)

        for m in re.finditer(r'<style[^>]*>(.*?)</style>', src, re.S):
            old_found |= check_css(p, m.group(1), src.count('\n', 0, m.start(1)))

        # 電話番号
        tels = set()
        for t, d, _ in par.tags:
            if t == 'a' and d.get('href', '').startswith('tel:'): tels.add(norm_tel(d['href'][4:]))
        for m in re.finditer(r'0\d{1,4}-\d{1,4}-\d{3,4}', text): tels.add(norm_tel(m.group()))
        for m in re.finditer(r'"telephone"\s*:\s*"([^"]+)"', src): tels.add(norm_tel(m.group(1)))
        tels = {t for t in tels if t and not set(t) <= {'0'}}
        if len(tels) > 1: add('❌', '電話番号', f'{rel}：番号が {len(tels)} 種類あります → ' + '／'.join(sorted(tels)))
        elif tels and is_top: add('✅', '電話番号', f'{rel}：{next(iter(tels))} でそろっています')

        # 使ってはいけない言葉
        flat = re.sub(r'\s+', '', text)
        for w, why in NG_WORDS.items():
            for m in re.finditer(re.escape(w), flat):
                ctx = flat[max(0, m.start()-14): m.end()+14]
                add('⚠️', '言葉', f'{rel}：「{w}」（{why}）… …{ctx}…')

        # 画像・リンク
        for t, d, line in par.tags:
            for attr in ('src', 'href'):
                u = d.get(attr, '')
                if not u or t == 'a' and attr == 'src': continue
                if re.match(r'(https?:|mailto:|tel:|data:|#|//|javascript:)', u): continue
                if t == 'link' and d.get('rel') in ('preconnect', 'dns-prefetch'): continue
                f = os.path.normpath(os.path.join(os.path.dirname(p), u.split('#')[0].split('?')[0]))
                if f.endswith(os.sep) or os.path.isdir(f): f = os.path.join(f, 'index.html')
                if not os.path.exists(f): add('❌', 'ファイル', f'{rel} {line}行目：{u} がありません')
            if t == 'a' and d.get('href', '').startswith('#') and len(d['href']) > 1 and d['href'][1:] not in par.ids:
                add('❌', 'リンク', f'{rel} {line}行目：{d["href"]} の行き先がページ内にありません')
            if t == 'a' and re.match(r'https?:', d.get('href', '')) and d.get('target') == '_blank' and 'noopener' not in d.get('rel', ''):
                add('⚠️', 'リンク', f'{rel} {line}行目：外部リンクに rel="noopener" がありません')
            if t == 'img' and 'alt' not in d:
                add('⚠️', '画像', f'{rel} {line}行目：画像の説明（alt）がありません → {d.get("src","")}')

        if is_top:
            if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', src):
                add('⚠️', '検索', 'noindex が入っています（試作ならOK。本公開のときに外す）')
            else:
                add('✅', '検索', 'noindex なし（検索に出る状態）')
            og = re.search(r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)', src)
            if not og: add('⚠️', 'シェア', 'シェア用の画像（og:image）がありません')
            else:
                u = og.group(1); local = re.sub(r'^https?://[^/]+/[^/]*?/?', '', u) if u.startswith('http') else u
                cand = [os.path.join(root, u)] + [os.path.join(root, u.split('/', 3)[-1])] + [os.path.join(root, '/'.join(u.split('/')[-2:]))]
                add('✅' if any(os.path.exists(c) for c in cand) else '⚠️', 'シェア', f'og:image：{u}' + ('' if any(os.path.exists(c) for c in cand) else '（ファイルが見つかりません）'))
                if 'github.io' in u: add('⚠️', 'シェア', 'og:image が github.io を指しています（本公開のときに、独自ドメインか Cloudflare 版のURLに直す）')
            if 'keep-all' in src and '<wbr>' in src: add('✅', '折り返し', f'言葉の切れ目で折り返す設定あり（<wbr> {src.count("<wbr>")} 個）')
            else: add('⚠️', '折り返し', '文の折り返しの調整（BudouX）がまだです（マニュアル 06）')
            soon = src.count('準備中')
            if soon: add('⚠️', '準備中', f'「準備中」が {soon} か所あります（本公開までにURLを入れる）')
    for (path, name, fb), lines in OLD_HITS.items():
        ls = sorted(set(lines))
        add('⚠️', '古いスマホ', f'{os.path.relpath(path, root)}：{name} が {len(ls)} か所（{"・".join(map(str, ls[:8]))}{"…" if len(ls)>8 else ""}行目）… 予備：{fb}')
    if not old_found: add('✅', '古いスマホ', '崩れやすい書き方は見つかりませんでした（予備ありのものは除く）')
    return pages

def run_browser(root):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        add('⚠️', 'はみ出し', 'ブラウザが使えないので、はみ出しは調べていません（Claude の作業場所で調べる）'); return
    top = 'file://' + os.path.abspath(os.path.join(root, 'index.html'))
    bad = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for w in WIDTHS:
            pg = b.new_page(viewport={'width': w, 'height': 800}, is_mobile=w < 760, has_touch=w < 760)
            pg.goto(top); pg.wait_for_timeout(600)
            sw = pg.evaluate('document.documentElement.scrollWidth')
            if sw > w + 1:
                who = pg.evaluate("""(w)=>[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();const cs=getComputedStyle(e);return r.right>w+1&&cs.position!=='fixed'&&r.width>0}).slice(0,3).map(e=>e.tagName.toLowerCase()+(e.className?'.'+String(e.className).split(' ')[0]:'')).join(' / ')""", w)
                bad.append(f'幅{w}：{sw}px（{who}）')
            pg.close()
        b.close()
    if bad: add('❌', 'はみ出し', '横にはみ出しています → ' + '、'.join(bad))
    else: add('✅', 'はみ出し', '幅 ' + '・'.join(map(str, WIDTHS)) + ' ではみ出しなし')

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    root = sys.argv[1].rstrip('/')
    run_static(root)
    if '--no-browser' not in sys.argv: run_browser(root)
    order = {'❌': 0, '⚠️': 1, '✅': 2}
    print(f'【公開前チェック】{os.path.basename(os.path.abspath(root))}')
    n = {k: sum(1 for r in results if r[0] == k) for k in order}
    print(f'❌ 直す {n["❌"]}　⚠️ 確かめる {n["⚠️"]}　✅ 問題なし {n["✅"]}\n')
    for mark, area, msg in sorted(results, key=lambda r: order[r[0]]):
        print(f'{mark} [{area}] {msg}')
    sys.exit(1 if n['❌'] else 0)

if __name__ == '__main__':
    main()
