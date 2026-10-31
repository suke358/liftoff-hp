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
  4b. 土台の 3 行（<!doctype html>・<meta charset="utf-8">・viewport）があるか（2026/10/26。無いと iPhone で文字化け・縮小表示）
  5. 画像の説明（alt）・外部リンクの rel・noindex・シェア用画像・文の折り返し
  6. 横にはみ出していないか（幅 320・360・390・768・1280）
  7. LINE のカードの番号（?v=）が、アドレスバーに足す JS・canonical・og:url の3か所でそろっているか（2026/10/10 追加。欠け・ちがい → ❌、しくみ無し → ⚠️）
     og:image の画像が同じ名前のまま中身だけ変わっていたら ⚠️（LINE が古い画像を覚えるので、名前も変える）
  10. Cloudflare Web Analytics：設定（site.json）に analytics_token があるのに一文がなければ ❌。一文があれば ✅（2026/10/22）
  9. 商品ページの「特定商取引法に基づく表示」に「お問い合わせください」が残っていたら ❌（見本は ⚠️）。2026/10/22
  8. 公開URL（canonical が独自ドメインのとき）：外に貼るリンク用の転送があるか（決定事項 08「外に貼るリンクには # を使わない」2026/10/21 colore）
     ①「ドメイン/menu」と「/menu/」が転送で「/#menu」に着く ②「ドメイン/%23menu」が 404 でない（転送で /#menu へ）→ だめなら ❌。ネットが使えないときは ⚠️
     canonical が workers.dev・github.io のサイト（まだ本公開前）は調べない。--url=https://ドメイン を付けると、そのURLで調べる
  11. 色の差（2026/10/31）：:root の --primary・--dark・--bg などから、ボタンの白い文字とボタン／ボタンと周りの背景（トップの dark・ページの bg）／
     地図の印（primary）と dark／小見出し（accent_soft）と dark／札の文字（primary_deep）と pale／本文（ink）と bg の差（WCAG のコントラスト比）を計算し、
     小さすぎたら ⚠️（10/31 に色を一部だけ上書きして「ご相談」ボタンと地図の印が背景に溶けたのを二度と起こさない）。make_site.py で作ったページだけ
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
    (r'mix-blend-mode\s*:', 'mix-blend-mode（重ねて色を混ぜる）', '使わない。iPhone の Safari で動きが止まって見えた（2026/10/8 colore の♡）。半透明の色で重ねる'),
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

# ---- 色の差（2026/10/31）-------------------------------------------------
COLOR_PAIRS = [  # (説明, 色A, 色B, 最低の比)。色は :root の変数名か、固定の色。hero＝上の部分の背景（dark か、明るいときは pale）
    ('ボタンの白い文字とボタン（primary）', '#ffffff', 'primary', 3.0),  # 大きな文字の見やすさの目安（WCAG）。2026/10/31 ユーザー決定
    ('ボタン（primary）と上の部分の背景', 'primary', 'hero', 1.5),
    ('ボタン（primary）とページの背景（bg）', 'primary', 'bg', 1.5),
    ('ボタン（primary）と相談の背景（dark）', 'primary', 'dark', 1.5),
    ('道順の印（primary）と背景（dark）', 'primary', 'dark', 1.5),
    ('上の部分の文字と背景', 'hero_ink', 'hero', 4.5),
    ('小見出しの文字と上の部分の背景', 'hero_sub', 'hero', 2.0),
    ('札の文字（primary_deep）と札の背景（pale）', 'primary_deep', 'pale', 2.0),
    ('本文の文字（ink）とページの背景（bg）', 'ink', 'bg', 4.5),
]

def _lum(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(ch * 2 for ch in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def contrast(a, b):
    """WCAG のコントラスト比（1〜21。大きいほど見分けやすい）"""
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

def check_colors(src, rel):
    """make_site.py で作ったページの :root の色（--primary など）を読み、見分けにくい組み合わせがあれば ⚠️。変数がないページ（手で作ったサイト）は調べない"""
    m = re.search(r':root\s*{([^}]*)}', src)
    if not m: return
    v = dict((k, c.lower()) for k, c in re.findall(r'--([a-z0-9_-]+)\s*:\s*(#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?)\b', m.group(1)))
    v = {k.replace('-', '_'): c for k, c in v.items()}
    if 'primary' not in v or 'dark' not in v or 'bg' not in v: return
    # 上の部分（トップ）：明るい（--hero-style:light）なら背景 pale・文字 ink・小見出し primary_deep。濃いなら dark・#f3efe6・accent_soft
    if re.search(r'--hero-style\s*:\s*light', src):
        v['hero'], v['hero_ink'], v['hero_sub'] = v.get('pale', '#ffffff'), v.get('ink', '#000000'), v.get('primary_deep', v['primary'])
    else:
        v['hero'], v['hero_ink'], v['hero_sub'] = v['dark'], '#f3efe6', v.get('accent_soft', '#ffffff')
    bad = []
    for label, a, b, need in COLOR_PAIRS:
        ca, cb = v.get(a, a), v.get(b, b)
        if not (str(ca).startswith('#') and str(cb).startswith('#')): continue  # 変数が無い・hex でない → 調べない
        r = contrast(ca, cb)
        if r < need: bad.append(f'{label}：{r:.2f}（{need} 以上にする。{ca}／{cb}）')
    if bad:
        for b in bad: add('⚠️', '色', f'{rel}：色の差が小さい → {b}。theme の色を見直す（ボタンや印が背景に溶ける）')
    else:
        add('✅', '色', f'{rel}：ボタン・印・文字の色が背景と見分けられます（コントラスト比 OK）')

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

def check_card_v(src, rel):
    """LINE のカードの番号（?v=）が3か所でそろっているか（2026/10/10 自社で再発防止。マニュアル 17）
    iPhone の Safari の共有ボタンはアドレスバーではなく canonical の URL を LINE に送る。LINE はページの URL ごとにカードを覚えるので、
    ①開いたときにアドレスバーに ?v= を足す JS ②canonical ③og:url の3つに同じ番号が要る。欠けている・番号がちがう → ❌。3つとも無い → ⚠️（しくみが入っていない）"""
    def v_of(url): m = re.search(r'[?&]v=(\d+)', url or ''); return m.group(1) if m else None
    js = re.search(r"replaceState\([^<]*?'v=(\d+)'", src)
    can = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', src) or re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', src)
    ogu = re.search(r'property=["\']og:url["\'][^>]+content=["\']([^"\']+)', src)
    got = {'アドレスバーの JS': js.group(1) if js else None, 'canonical': v_of(can.group(1)) if can else None, 'og:url': v_of(ogu.group(1)) if ogu else None}
    if not any(got.values()):
        add('⚠️', 'カード', f'{rel}：LINE のカードの番号（?v=）のしくみが入っていません（canonical・og:url・アドレスバーの JS。マニュアル 17）'); return
    miss = [k for k, v in got.items() if v is None]
    if miss: add('❌', 'カード', f'{rel}：LINE のカードの番号（?v=）が {"・".join(miss)} にありません（3か所そろえる。マニュアル 17）'); return
    if len(set(got.values())) > 1:
        add('❌', 'カード', f'{rel}：LINE のカードの番号（?v=）がそろっていません → ' + '／'.join(f'{k} v={v}' for k, v in got.items())); return
    add('✅', 'カード', f'{rel}：LINE のカードの番号 ?v={js.group(1)}（アドレスバーの JS・canonical・og:url でそろっています）')

def check_redirects(src, rel):
    """外に貼るリンク用の転送（決定事項 08。2026/10/21 colore で「Googleマップに /#menu を貼ったら #menu が消えた」の再発防止）。
    /menu・/menu/ → https://ドメイン/#menu（302 など）、/%23menu → 404 でない（同じ転送）。canonical が独自ドメインのときだけ調べる（--url で指定もできる）"""
    import urllib.request, urllib.error
    url = next((a[len('--url='):] for a in sys.argv if a.startswith('--url=')), None)
    if not url:
        can = re.search(r'rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', src)
        if not can: return
        url = can.group(1)
        if re.search(r'workers\.dev|github\.io|localhost|127\.0\.0\.1', url): return   # まだ本公開前（仮のURL）
    m = re.match(r'(https?://[^/]+)', url)
    if not m: return
    origin = m.group(1)
    want = origin + '/#menu'
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    opener = urllib.request.build_opener(NoRedirect)
    bad = []
    for path in ('/menu', '/menu/', '/%23menu'):
        try:
            r = opener.open(urllib.request.Request(origin + path, method='HEAD'), timeout=10)
            code, loc = r.status, r.headers.get('Location', '')
        except urllib.error.HTTPError as e:
            code, loc = e.code, e.headers.get('Location', '')
        except Exception as e:
            add('⚠️', '転送', f'{origin}{path} を調べられませんでした（ネットの状態を確かめる）：{e}'); return
        if code in (301, 302, 307, 308) and loc.rstrip('/') == want: continue
        bad.append(f'{path} → {code}' + (f' {loc}' if loc else ''))
    if bad: add('❌', '転送', f'{origin}：外に貼るリンク用の転送がありません → ' + '／'.join(bad) + f'（Cloudflare の転送「/menu・/menu/・/%23menu → {want}（302）」を作る。決定事項 08）')
    else: add('✅', '転送', f'{origin}：/menu・/menu/・/%23menu が {want} に転送されます（外に貼るリンクは /menu を使う）')

def check_og_image_changed(root, img_path, rel):
    """og:image の画像が、前のコミットから同じ名前のまま中身だけ変わっていたら ⚠️（まだコミットしていない変更も、直前のコミットでの変更も見る）"""
    import subprocess
    def git(*a):
        try: return subprocess.run(['git', '-C', root] + list(a), capture_output=True, text=True)
        except Exception: return None
    r = git('rev-parse', '--is-inside-work-tree')
    if not r or r.returncode != 0: return
    p = os.path.relpath(img_path, root)
    tracked = git('ls-files', '--error-unmatch', p)
    if not tracked or tracked.returncode != 0: return  # 新しい名前の画像（まだ git に無い）→ 名前を変えてある
    r = git('diff', '--quiet', 'HEAD', '--', p)
    if r and r.returncode == 1:
        add('⚠️', 'シェア', f'{rel}：og:image の画像 {p} が、同じ名前のまま中身だけ変わっています（コミット前）。LINE が古い画像を覚えるので、ファイル名も変える（例 og-日付b.jpg）'); return
    r = git('diff', '--quiet', 'HEAD~1', 'HEAD', '--', p)
    if r and r.returncode == 1:
        was = git('cat-file', '-e', f'HEAD~1:{p}')
        if was and was.returncode == 0:
            add('⚠️', 'シェア', f'{rel}：og:image の画像 {p} が、直前のコミットで同じ名前のまま中身だけ変わっています。LINE が古い画像を覚えるので、ファイル名も変える（例 og-日付b.jpg）')

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

        # 土台の 3 つ（doctype・文字コード・viewport）。2026/10/26 samples/calendar-trial/ で charset が無く iPhone で文字化けしたが ❌ 0 だったので足した
        head = src[:4000]
        base_miss = []
        if not re.search(r'<!doctype\s+html', head, re.I): base_miss.append('<!doctype html>')
        if not re.search(r'<meta[^>]+charset\s*=\s*["\']?utf-8', head, re.I): base_miss.append('<meta charset="utf-8">')
        if not re.search(r'<meta[^>]+name\s*=\s*["\']viewport["\'][^>]*width=device-width', head, re.I): base_miss.append('viewport（width=device-width）')
        if base_miss: add('❌', '土台', f'{rel}：{"・".join(base_miss)} がありません（先頭の 3 行。無いと iPhone で文字化け・縮小表示になる）')
        elif is_top: add('✅', '土台', f'{rel}：doctype・charset・viewport あり')

        for m in re.finditer(r'<style[^>]*>(.*?)</style>', src, re.S):
            old_found |= check_css(p, m.group(1), src.count('\n', 0, m.start(1)))

        if is_top: check_colors(src, rel)  # 色の差（2026/10/31）

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
                if promised_not(flat, m.start(), m.end()): continue
                ctx = flat[max(0, m.start()-14): m.end()+14]
                add('⚠️', '言葉', f'{rel}：「{w}」（{why}）… …{ctx}…')

        # パスワードを打つ欄があったら止める（2026/10/12 決定。台本・入力シート・お店のサイトにパスワードの欄は作らない）
        for t, d, line in par.tags:
            if t in ('input', 'textarea') and (d.get('type') == 'password' or 'パスワード' in ''.join(d.get(a, '') for a in ('placeholder', 'name', 'id', 'aria-label', 'data-v'))):
                add('❌', 'パスワード', f'{rel} {line}行目：パスワードを打つ欄があります（作らない決まり。言い方を変えるか欄を消す）')
        for m in re.finditer(r'<label[^>]*>([^<]*パスワード[^<]*)</label>\s*<(?:input|textarea)\b', src):
            add('❌', 'パスワード', f'{rel} {src.count(chr(10), 0, m.start()) + 1}行目：「{m.group(1).strip()[:30]}」の欄があります（パスワードの欄は作らない決まり）')
        # JS で欄を作る道具（進行台本など）：欄の名前の一覧（"vals": [...]）にパスワードがあっても止める
        for m in re.finditer(r'"vals"\s*:\s*\[([^\]]*パスワード[^\]]*)\]', src):
            add('❌', 'パスワード', f'{rel} {src.count(chr(10), 0, m.start()) + 1}行目：入力欄の名前に「パスワード」があります → {m.group(1).strip()[:40]}（言い方を変える）')

        # 画像・リンク
        for t, d, line in par.tags:
            for attr in ('src', 'href'):
                u = d.get(attr, '')
                if not u or t == 'a' and attr == 'src': continue
                if re.match(r'(https?:|mailto:|tel:|data:|#|//|javascript:)', u): continue
                if t == 'link' and d.get('rel') in ('preconnect', 'dns-prefetch'): continue
                path_only = u.split('#')[0].split('?')[0]
                if path_only.startswith('/'):
                    # サイトの根からの道（404.html など、どの深さでも同じ所を指すページで使う。2026/10/21）
                    # 「/」や「/menu」のような拡張子のない道は、トップや転送（Cloudflare）なのでファイルの有無は調べない
                    if not os.path.splitext(path_only.rstrip('/'))[1]: continue
                    f = os.path.normpath(os.path.join(root, path_only.lstrip('/')))
                else:
                    f = os.path.normpath(os.path.join(os.path.dirname(p), path_only))
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
                # 同じ名前のまま中身だけ変わっていないか（LINE は画像の URL ごとに古い画像を覚えるので、変えるときは名前も変える。2026/10/10 自社で再発防止）
                img_local = next((c for c in cand if os.path.exists(c)), None)
                if img_local: check_og_image_changed(root, img_local, rel)
            check_card_v(src, rel)
            check_redirects(src, rel)
            if 'keep-all' in src and '<wbr>' in src: add('✅', '折り返し', f'言葉の切れ目で折り返す設定あり（<wbr> {src.count("<wbr>")} 個）')
            else: add('⚠️', '折り返し', '文の折り返しの調整（BudouX）がまだです（マニュアル 06）')
            soon = src.count('準備中')
            if soon: add('⚠️', '準備中', f'「準備中」が {soon} か所あります（本公開までにURLを入れる）')
        # Cloudflare Web Analytics（2026/10/22）：設定（site.json）に analytics_token があるのに、数える一文がないページは ❌
        if is_top:
            tok = ''
            sj = os.path.join(root, 'site.json')
            if os.path.exists(sj):
                try:
                    import json as _json; tok = str(_json.load(open(sj, encoding='utf-8')).get('analytics_token') or '').strip()
                except Exception: tok = ''
            has = 'cloudflareinsights.com/beacon' in src
            if tok and not has: add('❌', '集計', f'{rel}：設定に analytics_token があるのに、Cloudflare Web Analytics の一文がありません（make_site.py で作り直す）')
            elif has: add('✅', '集計', f'{rel}：Cloudflare Web Analytics の一文あり')
        # 商品ページの「特定商取引法に基づく表示」に「お問い合わせください」が残っていないか（本物のお店は ❌・見本（sample-note あり）は ⚠️。2026/10/22 マニュアル K）
        tk = re.search(r'<details class="tokushoho".*?</details>', src, re.S)
        if tk:
            n_ask = tk.group(0).count('お問い合わせください')
            if n_ask:
                if 'class="sample-note"' in src: add('⚠️', '特商法', f'{rel}：特定商取引法の表示に「お問い合わせください」が {n_ask} か所（見本なのでOK。本物のお店では設定に書く）')
                else: add('❌', '特商法', f'{rel}：特定商取引法の表示に「お問い合わせください」が {n_ask} か所あります（送料・支払い方法・支払いの時期・お届けの時期・返品 などを設定に書いて作り直す。このまま公開しない）')
            else: add('✅', '特商法', f'{rel}：特定商取引法の表示に空の項目なし')
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

def promised_not(flat, start, end):
    """言葉が「…」の中にあり、その 」 の直後（「などの」があってもよい）が「約束はしません」なら True
    ＝「必ずお客さんが増える」などの約束はしません、のように約束しない側の文（2026/10/31 決定。このときだけ ⚠️ を出さない）"""
    o = flat.rfind('「', 0, start)
    if o < 0 or '」' in flat[o:start]: return False
    c = flat.find('」', end)
    if c < 0 or '「' in flat[end:c]: return False
    return re.match(r'(などの)?約束はしません', flat[c + 1:]) is not None

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
