#!/usr/bin/env python3
"""配置の型（A1 の「写真の使い方・配置」をなぞる形）で 1 ページを作る（2026/11/24。想永 _8・_9 の手書きの index.html を道具に移した）
make_site.py が設定の "layout":"a1trace" のときに呼ぶ（単独では動かさない）。型の決まりは tools/templates/配置の型.md（数字は全部そこから）。
手本の写真・絵・ロゴ・文・店名・英語の 1 語・色の組そのものは使っていない（型は割合と数字だけ）。

設定（site.json）で読む物：name・short_name・kind・area／address・catch_html・lead・menu_title・menu_word・menu_lead・menu_note・menus（3 つまで）・
  flow_title・flow（3 つまで）・info_title・address・hours・holiday・tel・map_query・show_route・faq（4 つまで。答えが「お問い合わせください」の物は出さない）・
  reserve_title・reserve_lead・line_url（なければ tel・reserve_url・dm_url）・url_base・card_v・og_image・analytics_token・sample_note・業種
  "knobs_seed": 1124 … tools/kuji.py のくじ（同じ種なら同じ答え）／"knobs": {...} … つまみを 1 つずつ上書き（書かなければ既定＝_8）
  "a1_words": {"hero": "想永", "s3": "仲間たち", "s5": "一台"} … 大きな 1 語（2〜4 字）。書かなければ hero＝店名の短い形・s3＝menu_word・s5＝「お店」
  "crops": {"hero_l": ["belt_1.jpg", [左, 上, 右, 下]], ...} … 役ごとの切る範囲（元の写真の座標）。書かない役は真ん中 70％ を自動で（make_site.crop_roles）
写真の役（12）：hero_l・hero_r（1画面目）・wide1（2画面目）・sq_a〜c（正方形）・wide2（3段目）・tall_a・tall_b（5段目）・dark（3段目の文の後ろ）・foot（いちばん下）・sq_d（札）
古いスマホ対策：aspect-ratio・inset・gap・min()・svh は使わない。-webkit- の予備。JavaScript は 1 行も無い（動きなし）
check_site.py の「釣り合い」「重なり」の検査のための印：data-pair（隣り合う写真の組）・data-under-wide（全幅の写真の下の写真）・.vt（縦書き）"""
import html, os, re, json, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
import kuji

def e(t): return html.escape(str(t or ''), quote=True)

# 写真の役：(出す幅px, 縦横の比 w/h)。切る範囲を書かない役は、この比で真ん中 70％ を切る
ROLES = {'hero_l': (900, 0.67), 'hero_r': (960, 1.11), 'wide1': (960, 1.79), 'sq_a': (800, 1.0), 'sq_b': (800, 1.0), 'sq_c': (800, 1.0),
         'wide2': (960, 1.5), 'tall_a': (760, 0.8), 'tall_b': (840, 0.8), 'dark': (960, 1.6), 'foot': (960, 1.6), 'sq_d': (520, 1.0)}
ROLE_ORDER = ['hero_r', 'hero_l', 'wide1', 'sq_a', 'sq_b', 'sq_c', 'wide2', 'tall_a', 'tall_b', 'dark', 'foot', 'sq_d']  # 写真を当てる順（最初の写真＝1画面目の大きい方）

# 見出しの前の小さなしるし（18×10。黒い点のかわりに、お店らしい小さな形）。業種の言葉で選ぶ
SIGNS = {
    'car': '<path d="M1 7V5.2l3.2-.6L6.6 1.4h5l2.6 3.2L17 5.2V7z" fill="currentColor"/><circle cx="5" cy="7.6" r="1.7" fill="BG" stroke="currentColor"/><circle cx="13" cy="7.6" r="1.7" fill="BG" stroke="currentColor"/>',
    'flower': '<circle cx="9" cy="5" r="1.7" fill="currentColor"/><circle cx="5.6" cy="5" r="1.5" fill="none" stroke="currentColor"/><circle cx="12.4" cy="5" r="1.5" fill="none" stroke="currentColor"/><circle cx="9" cy="1.7" r="1.5" fill="none" stroke="currentColor"/><circle cx="9" cy="8.3" r="1.5" fill="none" stroke="currentColor"/>',
    'scissors': '<path d="M5 1l9 7M14 1L5 8" fill="none" stroke="currentColor" stroke-width="1.1"/><circle cx="3.4" cy="8.4" r="1.6" fill="none" stroke="currentColor"/><circle cx="15.6" cy="8.4" r="1.6" fill="none" stroke="currentColor"/>',
    'leaf': '<path d="M2 9C3.5 3.5 9 1 16.5 1c-.3 5.5-4 8.5-10 8.5-1.4 0-2.8-.2-4.5-.5z" fill="currentColor"/><path d="M2 9l7-5" fill="none" stroke="BG" stroke-width=".9"/>',
    'cup': '<path d="M3 1.5h9v4a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3z" fill="currentColor"/><path d="M12 2.6h1.6a1.6 1.6 0 0 1 0 3.2H12" fill="none" stroke="currentColor" stroke-width="1.1"/><path d="M3 9.4h9" stroke="currentColor" stroke-width="1"/>',
    'dot': '<rect x="7" y="3" width="4" height="4" fill="currentColor"/>',
}
SIGN_WORDS = [('car', ['おもちゃ', '車', 'ミニカー', '整備']), ('flower', ['花', 'フラワー']), ('scissors', ['美容', 'ヘア', 'ネイル', 'まつげ', 'トリミング', '理容']),
              ('leaf', ['造園', '庭', 'よもぎ', '整体', '農', '古民家', 'リトリート', '介護']), ('cup', ['カフェ', '喫茶', 'パン', '居酒屋', 'バー', '食'])]

def sign_for(c):
    words = ' '.join(str(c.get(k) or '') for k in ('業種', 'kind', 'name'))
    for key, ws in SIGN_WORDS:
        if any(w in words for w in ws): return key
    return 'dot'

def knobs_for(c):
    """既定（_8）← くじ（knobs_seed）← 設定の knobs の順に重ねる。決まりの外の値は ValueError"""
    k = dict(kuji.DEFAULT)
    if c.get('knobs_seed') is not None: k.update(kuji.draw(c['knobs_seed']))
    if isinstance(c.get('knobs'), dict): k.update(c['knobs'])
    bad = kuji.validate(k)
    if bad: raise ValueError('knobs（つまみ）が決まりの外：' + '／'.join(bad))
    return k

def plain(t):
    """HTML の一言（catch_html）を文だけに（<br> は改行に）"""
    t = re.sub(r'<br\s*/?>', '\n', str(t or '')); t = re.sub(r'<[^>]+>', '', t)
    return html.unescape(t).strip()

def city_of(c):
    a = str(c.get('area') or '')
    if a: return re.sub(r'^.*?[都道府県]', '', a) or a
    m = re.search(r'([^\s〒0-9-]{1,8}[市区町村])', str(c.get('address') or ''))
    return m.group(1) if m else ''

def short_word(c):
    s = str(c.get('short_name') or c.get('name') or '')
    s = re.sub(r'[\s（(].*$', '', s)
    if 2 <= len(s) <= 4: return s
    return s[:2] if len(s) > 4 else s

def img(role, roles, cls='cover', extra=''):
    """役の写真の <img>（出どころの札つき）。役が無ければ空"""
    o = roles.get(role)
    if not o: return ''
    src = o.get('source')
    ds = f' data-source="{e(src)}"' if src in ('own', 'stock') else ''
    tag = f'<img class="{cls}" src="{e(o["image"])}" width="{o.get("w", "")}" height="{o.get("h", "")}" alt="{e(o.get("alt", ""))}"{ds}{extra}>'
    if src == 'stock': tag += '<span class="img-note" aria-hidden="true">写真はイメージです</span>'
    return tag

def build(c, roles, extras=None):
    """設定 c と、役ごとの写真 roles（make_site.crop_roles の戻り）から index.html の中身を返す"""
    x = extras or {}
    k = knobs_for(c)
    name = c['name']; short = c.get('short_name') or name
    words = c.get('a1_words') or {}
    w_hero = words.get('hero') or short_word(c)
    w_s3 = words.get('s3') or c.get('menu_word') or (c.get('menu_title') or '商品')[:4]
    w_s5 = words.get('s5') or 'お店'
    sign_body = SIGNS[sign_for(c)]
    def sign(bg): return f'<svg class="sg" viewBox="0 0 18 10" aria-hidden="true">{sign_body.replace("BG", bg)}</svg>'
    # 連絡の入口（LINE が本線。無ければ電話・ネット予約・インスタの DM）
    line = c.get('line_url'); tel = c.get('tel') or ''; tel_d = ''.join(ch for ch in tel if ch.isdigit())
    if line: cta_href, cta_word, cta_small = line, 'LINE で<wbr>相談する', 'LINE での<wbr>ご相談'
    elif tel: cta_href, cta_word, cta_small = 'tel:' + tel_d, '電話で<wbr>相談する', 'お電話での<wbr>ご相談'
    elif c.get('reserve_url'): cta_href, cta_word, cta_small = c['reserve_url'], 'ネットで<wbr>予約する', 'ご予約'
    else: cta_href, cta_word, cta_small = c.get('dm_url') or '#line', 'メッセージで<wbr>相談する', 'ご相談'
    ext = '' if cta_href.startswith(('#', 'tel:')) or cta_href.endswith('.html') else ' target="_blank" rel="noopener"'
    # 文
    catch = plain(c.get('catch_html') or c.get('catch') or '')
    lines = [l for l in catch.split('\n') if l.strip()] or [short]
    vt_ok = len(lines) <= 3 and all(len(l) <= 12 for l in lines)  # 縦書きは 12 字まで・3 列まで。長ければ横書き 2 行（型の「はみ出さない 3」）
    catch_1 = ''.join(lines)
    lead = str(c.get('lead') or '')
    sents = [s for s in re.split(r'(?<=。)', lead) if s.strip()]
    head2 = c.get('a1_head2') or (sents[0] if sents else catch_1)
    small2 = ''.join(sents[1:]) if len(sents) > 1 else (c.get('menu_lead') or '')
    menus = [m for m in (c.get('menus') or []) if m.get('name')][:3]
    flow = (c.get('flow') or [])[:3]
    flow_title = c.get('flow_title') or 'はじめての方へ'
    faq = [q for q in (c.get('faq') or []) if q.get('q') and q.get('a') and not str(q['a']).startswith(('お問い合わせ', 'くわしくは'))][:4]
    city = city_of(c); kind = str(c.get('kind') or '').split('｜')[0]
    tag = ' ・ '.join(t for t in (city, kind) if t)
    menu_title = c.get('menu_title') or '商品'; menu_word = c.get('menu_word') or '商品'
    rows = [('店名', name)]
    if c.get('address'): rows.append(('住所', c['address']))
    for key, lab in (('hours', '営業時間'), ('holiday', '定休日')):
        v = str(c.get(key) or '')
        if v and not v.startswith('お問い合わせ'): rows.append((lab, v))
    if tel: rows.append(('電話', tel))
    route = ''
    if c.get('map_query') and c.get('show_route', True):
        route = f'<a class="btn" href="https://www.google.com/maps/search/?api=1&amp;query={e(urllib.parse.quote(c["map_query"]))}" target="_blank" rel="noopener">Googleマップで<wbr>道順を<wbr>見る</a>'
    # つまみ → 数字
    p1, gap = k['p1'], k['gap']; p2 = 100 - p1 - gap
    close_right = k['close'] == '右'
    sq_two_s2 = k['squares'].startswith('2画面目2枚')
    a_ratio, b_ratio = (43, 45) if k['stag_ratio'] == '43／45' else (45, 43)
    stag_b_top = k['stag_top'] == '右'
    items_first = k['order'].startswith('商品')
    tr = k['tracking']
    bg, gapc, band, ink = k['bg'], k['gapc'], k['band'], k['ink']
    # 写真の alt の予備
    for r in roles.values():
        if not r.get('alt'): r['alt'] = short + 'の写真'
    for r in ('dark', 'foot'):
        if roles.get(r): roles[r]['alt'] = roles[r].get('alt') or ''
    note = f'<p class="sample-note" role="note">{e(c["sample_note"])}</p>' if c.get('sample_note') else ''
    # 1画面目
    p1_pos = 'right:0' if close_right else 'left:0'; p2_pos = 'left:0' if close_right else 'right:0'
    if vt_ok: vt2 = f'<p class="vt mi">{"<br>".join(e(l) for l in lines)}</p>'
    else: vt2 = f'<p class="yoko mi">{"<br>".join(e(l) for l in lines[:2])}</p>'
    toc = [('#about', lines[0]), ('#first', flow_title), ('#items', menu_title), ('#shop', 'お店と質問')]
    card_word = menus[0]['name'] if menus else short
    hero = f'''
<header>
<section class="hero">
 <div class="p1" data-pair="hero">{img('hero_l', roles)}</div>
 <div class="p2" data-pair="hero">{img('hero_r', roles)}</div>
 <p class="word mi" aria-hidden="true">{e(w_hero)}</p>
 <h1 class="name mi">{e(name)}</h1>
 <ul class="toc">
{''.join(f'  <li><a href="{h}">{e(t)}</a></li>' + chr(10) for h, t in toc)} </ul>
 <p class="guide">{e(lead)}</p>
 <div class="card">
  {img('sq_d', roles, cls='ph')}
  <p class="mi">{e(card_word)}</p>
  <a class="btn" href="#items">{e(menu_word)}を見る</a>
 </div>
</section>
<div class="bar">
 <div class="l"><b class="mi">お店</b>{e(c.get('address') or city)}<br>{e(catch_1)}</div>
 <div class="r"><span>{cta_small}</span><a class="btn" href="{e(cta_href)}"{ext}>{cta_word}</a></div>
</div>
</header>'''
    # 2画面目
    if sq_two_s2:
        rc = f'<div class="rc"><div class="sqs"><div class="a" data-pair="sq2" data-under-wide>{img("sq_a", roles)}</div><div class="b" data-pair="sq2" data-under-wide>{img("sq_b", roles)}</div></div></div>'
    else:
        rc = f'<div class="rc one"><div class="sq" data-under-wide>{img("sq_a", roles)}</div></div>'
    s2 = f'''
<section class="s2" id="about">
 <div class="wide">{img('wide1', roles)}{vt2}</div>
 <div class="band">
  <div class="lc">
   <p class="tag">{e(tag)}</p>
   <h2 class="mi">{e(head2)}</h2>
   <a class="btn" href="#items">{e(menu_title)}</a>
   <p class="small">{e(small2)}</p>
  </div>
  {rc}
 </div>
</section>'''
    # 3段目（商品）
    groups = ''.join(f'   <div class="g"><h3 class="mi">{e(m["name"])}</h3><p>{e(m.get("text") or "")}</p></div>\n' for m in menus)
    lk = c.get('menu_note') or 'どれにすればいいか迷うときも、お気軽にご相談ください。'
    s3 = f'''
<section class="s3" id="items">
 <div class="wide">{img('wide2', roles)}</div>
 <p class="vt mi">{e(w_s3)}</p>
 <p class="fuda mi">{sign(gapc)}{e(menu_title)}</p>
 <div class="txt">
  {img('dark', roles, cls='bgi')}
  <div class="col">
{groups}   <a class="lk" href="{e(cta_href)}"{ext}>{e(lk)}</a>
  </div>
 </div>
</section>'''
    # 4段目（はじめて）
    flow_t = ' '.join(str(f.get('text') or '') for f in flow[:2])
    if sq_two_s2:
        rt = f'<div class="rt"><div class="sq" data-pair="sq4">{img("sq_c", roles)}</div></div>'
    else:
        rt = f'<div class="rt"><div class="two"><div class="a" data-pair="sq4">{img("sq_b", roles)}</div><div class="b" data-pair="sq4">{img("sq_c", roles)}</div></div></div>'
    flow_li = ''.join(f'  <li><p class="n">(0{i + 1})</p><h3 class="mi">{e(f.get("title") or "")}</h3><p>{e(f.get("text") or "")}</p></li>\n' for i, f in enumerate(flow))
    s4 = f'''
<section class="s4" id="first">
 <div class="top">
  <div class="lt">
   <p class="lab">{sign(bg)}{e(c.get('flow_label') or 'はじめての方へ')}</p>
   <h2 class="mi">{e(flow_title)}</h2>
   <p class="t">{e(flow_t)}</p>
  </div>
  {rt}
 </div>
 <ul class="flow">
{flow_li} </ul>
</section>'''
    # 5段目（お店のこと・質問）
    faq_li = ''.join(f'    <li><p class="q"><span class="n">(0{i + 1})</span>{e(q["q"])}</p><p class="a">{e(q["a"])}</p></li>\n' for i, q in enumerate(faq))
    faq_html = f'''  <div class="rt">
   <p class="lab">よくある質問</p>
   <ul class="faq">
{faq_li}   </ul>
  </div>''' if faq else ''
    s5 = f'''
<section class="s5" id="shop">
 <div class="stag">
  <div class="a" data-pair="stag">{img('tall_a', roles)}</div>
  <div class="b" data-pair="stag">{img('tall_b', roles)}</div>
  <p class="vt mi" aria-hidden="true">{e(w_s5)}</p>
 </div>
 <div class="two">
  <div class="lt">
   <p class="lab">{sign(bg)}{e(c.get('info_title') or 'お店のこと')}</p>
   <h2 class="mi">{e(name)}</h2>
   <table>
{''.join(f'    <tr><th>{e(a)}</th><td>{e(b)}</td></tr>' + chr(10) for a, b in rows)}   </table>
   {route}
  </div>
{faq_html}
 </div>
</section>'''
    s6 = f'''
<section class="s6" id="line">
 <h2 class="mi">{e(c.get('reserve_title') or 'ご相談')}</h2>
 <p>{e(c.get('reserve_lead') or 'お気軽にどうぞ。')}</p>
 <a class="btn" href="{e(cta_href)}"{ext} style="border-color:#fff">{cta_word}</a>
</section>'''
    foot = f'''
<footer class="foot">
 {img('foot', roles)}
 <p class="w mi">{e(w_hero)}</p>
 <p class="c">&copy; {e(short)}</p>
</footer>
<nav class="fixbar" aria-label="下のメニュー">
 <a href="{e(cta_href)}"{ext}>{cta_word.replace('する', '')}</a><a href="#items">{e(menu_word)}</a><a href="#shop">お店</a>
</nav>
<a class="totop" href="#top" aria-label="上へ">&uarr;</a>'''
    body = hero + '\n<main>' + s2 + (s3 + s4 if items_first else s4 + s3) + s5 + s6 + '\n</main>' + foot
    # <head>
    desc = c.get('description') or f'{name}のホームページです。'
    base = c.get('url_base') or ''
    card_v = c.get('card_v')
    og_img = c.get('og_image') or (roles.get('hero_r') or {}).get('image') or ''
    if og_img and base and not og_img.startswith('http'): og_img = base + og_img
    meta = [f'<meta property="og:title" content="{e(name)}">', f'<meta property="og:description" content="{e(desc)}">', '<meta property="og:type" content="website">']
    if og_img: meta.append(f'<meta property="og:image" content="{e(og_img)}">')
    card_js = ''
    if base:
        u = base + (f'?v={card_v}' if card_v else '')
        meta += [f'<link rel="canonical" href="{e(u)}">', f'<meta property="og:url" content="{e(u)}">']
        if card_v:
            card_js = ('\n<script>(function () { try {\n  var q = location.search || "";\n  if (/[?&]v=/.test(q)) return;\n'
                       f'  history.replaceState(history.state, "", location.pathname + (q ? q + "&" : "?") + "v={card_v}" + (location.hash || ""));\n'
                       '} catch (e) {} })();</script>')
    tok = str(c.get('analytics_token') or '').strip()
    analytics = ('<!-- Cloudflare Web Analytics --><script defer src=\'https://static.cloudflareinsights.com/beacon.min.js\' data-cf-beacon=\'{"token": "' + e(tok) + '"}\'></script><!-- End Cloudflare Web Analytics -->') if tok else ''
    ld = {"@context": "https://schema.org", "@type": c.get('schema_type', 'LocalBusiness'), "name": name}
    if base: ld["url"] = base
    if tel: ld["telephone"] = '+81-' + tel.lstrip('0')
    if c.get('address'): ld["address"] = {"@type": "PostalAddress", "addressCountry": "JP", "streetAddress": c['address']}
    css = CSS
    for key, v in {'BG': bg, 'GAPC': gapc, 'BAND': band, 'INK': ink, 'P1': str(p1), 'P2': str(p2), 'P1POS': p1_pos, 'P2POS': p2_pos,
                   'WORDX': str(k['word_x']), 'WORDREM': str(k['word_rem']), 'TR': str(tr),
                   'VT2': ('right:5%' if k['vt2'] == '右' else 'left:5%'), 'VT3': ('left:6%' if k['vt3'] == '左' else 'right:6%'),
                   'VT5': (f'left:{3 + a_ratio}%;margin-left:-.7em' if k['vt5'] == '間' else 'right:3%'),
                   'STA': str(a_ratio), 'STB': str(b_ratio), 'DROP': str(k['stag_drop']),
                   'A_TOP': (str(k['stag_drop']) + 'px' if stag_b_top else '0'), 'B_TOP': ('0' if stag_b_top else str(k['stag_drop']) + 'px'),
                   'B_LEFT': str(3 + a_ratio)}.items():  # 右の写真の左端＝左の写真の右端（3％＋左の幅）。1 語（間）はこの線の上
        css = css.replace('{{' + key + '}}', v)
    out = f'''<!doctype html>
<html lang="ja" data-layout="a1trace">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<!-- 本公開前は検索に出さない設定。本公開のときに tools/launch.py で外す -->
<meta name="robots" content="noindex,nofollow">
<title>{e(name)}{('｜' + e(c['title_place'])) if c.get('title_place') else ''}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="{ink}">
{chr(10).join(meta)}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@400;500&family=Zen+Kaku+Gothic+New:wght@300;400&display=swap" rel="stylesheet">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False)}
</script>
<style>
{css}
</style>{card_js}
</head>
<body id="top" class="a1trace">
<!-- このページは tools/make_site.py で作った（設定：{e(c.get('slug', ''))}.json・道具の版 {e(x.get('version', ''))}・配置の型 a1trace・つまみの種 {e(k.get('seed', '既定'))}）。直すときは設定を直して作り直す -->{note}
{body}
{analytics}
{x.get('pv_band', '')}
</body>
</html>
'''
    return out

# 型の CSS（数字は tools/templates/配置の型.md。{{…}} はつまみで入れかわる）。1rem＝14px
CSS = r'''
:root{--bg:{{BG}};--gap:{{GAPC}};--band:{{BAND}};--ink:{{INK}}}
*{box-sizing:border-box}
html{font-size:14px;scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:{{BG}};color:{{INK}};font-family:"Zen Kaku Gothic New","Hiragino Kaku Gothic ProN",sans-serif;font-weight:300;font-size:1rem;line-height:2;letter-spacing:.06em;word-break:keep-all;overflow-wrap:break-word;overflow-x:hidden}
img{display:block;max-width:100%}
.ph{-webkit-filter:saturate(.78);filter:saturate(.78)}
.mi{font-family:"Shippori Mincho B1","Hiragino Mincho ProN",serif;font-weight:400}
a{color:inherit;text-decoration:none}
h1,h2,h3,p,ul,dl,dd,dt{margin:0;padding:0}
ul{list-style:none}
.sg{display:inline-block;vertical-align:middle;margin-right:.7em;width:18px;height:10px}
.btn{display:inline-block;border:1px solid currentColor;border-radius:999px;padding:.35em 1.6em;font-size:.82rem;letter-spacing:.14em;line-height:1.9}
.cover{position:absolute;left:0;top:0;width:100%;height:100%;-o-object-fit:cover;object-fit:cover}
.img-note{position:absolute;left:8px;bottom:8px;z-index:3;font-size:.62rem;line-height:1;letter-spacing:.08em;color:#fff;background:rgba(0,0,0,.42);padding:.45em .7em;border-radius:999px;pointer-events:none;white-space:nowrap}
.sample-note{position:fixed;left:0;right:0;top:0;z-index:30;margin:0;text-align:center;font-size:.72rem;line-height:1.8;background:rgba(0,0,0,.6);color:#fff}

/* 1画面目 */
.hero{position:relative;height:92vh;min-height:620px;max-height:820px;overflow:hidden;background:{{GAPC}}}
.hero .p1{position:absolute;{{P1POS}};top:0;bottom:0;width:{{P1}}%;overflow:hidden}
.hero .p2{position:absolute;{{P2POS}};top:0;bottom:0;width:{{P2}}%;overflow:hidden}
.hero .p1 img,.hero .p2 img{-webkit-filter:saturate(.78) brightness(.84);filter:saturate(.78) brightness(.84)}
.hero .word{position:absolute;left:{{WORDX}}%;top:50%;margin:0;-webkit-transform:translate(-50%,-50%);transform:translate(-50%,-50%);font-size:{{WORDREM}}rem;letter-spacing:.22em;text-indent:.22em;line-height:1.2;color:#fff;text-shadow:0 1px 10px rgba(0,0,0,.4);white-space:nowrap}
.hero .name{position:absolute;left:30px;top:30px;font-size:.86rem;letter-spacing:.24em;color:#fff;text-shadow:0 1px 6px rgba(0,0,0,.5);line-height:1.6}
.hero .toc{position:absolute;left:30px;bottom:30px;font-size:.86rem;line-height:2.1;color:#fff;text-shadow:0 1px 6px rgba(0,0,0,.55)}
.hero .guide{position:absolute;right:30px;bottom:192px;width:300px;text-align:right;font-size:.74rem;line-height:1.9;color:#fff;text-shadow:0 1px 6px rgba(0,0,0,.6)}
.hero .card{position:absolute;right:30px;bottom:30px;width:300px;background:{{INK}};color:#fff;border-radius:8px;padding:14px;overflow:hidden}
.hero .card img{float:left;width:62px;height:62px;margin-right:14px;-o-object-fit:cover;object-fit:cover}
.hero .card .img-note{display:none}
.hero .card p{font-size:.95rem;line-height:1.6;margin-bottom:6px;letter-spacing:.12em}
.hero .card .btn{font-size:.7rem;padding:.1em 1.1em}
.card:after{content:"";display:block;clear:both}
.bar{height:72px;background:{{BG}};border-top:1px solid {{INK}};padding:0 30px;overflow:hidden}
.bar .l{float:left;padding-top:12px;font-size:.78rem;line-height:1.75}
.bar .l b{font-weight:400;letter-spacing:.2em;margin-right:1em}
.bar .r{float:right;padding-top:20px;font-size:.78rem}
.bar .r span{margin-right:1.2em;letter-spacing:.14em}

/* 2画面目 */
.s2{position:relative}
.s2 .wide{position:relative;height:0;padding-bottom:42%;overflow:hidden}
.s2 .wide img{-webkit-filter:saturate(.78);filter:saturate(.78)}
.vt{position:absolute;-webkit-writing-mode:vertical-rl;writing-mode:vertical-rl;color:#fff;text-shadow:0 1px 8px rgba(0,0,0,.55)}
.s2 .vt{{{VT2}};top:7%;font-size:2.1rem;letter-spacing:.3em;line-height:1.7}
.s2 .yoko{position:absolute;right:6%;top:10%;margin:0;text-align:right;color:#fff;font-size:2.1rem;line-height:1.75;letter-spacing:.2em;text-shadow:0 1px 8px rgba(0,0,0,.55)}
.s2 .band{background:{{BAND}};color:#fff;padding:48px 0 96px 6%;overflow:hidden}
.s2 .lc{float:left;width:56%}
.s2 .rc{float:right;width:38%;margin-right:6%;padding-top:60px}
.s2 .rc.one{width:34%;padding-top:150px}
.s2 .tag{text-align:right;font-size:.8rem;letter-spacing:.2em;margin-bottom:10px}
.s2 h2{font-size:2.4rem;line-height:1.7;letter-spacing:{{TR}}em;margin-bottom:18px}
.s2 .small{font-size:.8rem;margin-top:110px}
.s2 .sqs{overflow:hidden}
.s2 .sqs .a{float:left;width:48%}
.s2 .sqs .b{float:right;width:48%;margin-top:40px}
.sqs .a,.sqs .b,.s2 .rc .sq{position:relative;height:0;padding-bottom:48%;overflow:hidden}
.s2 .rc .sq{padding-bottom:100%}
.s2 .rc img{-webkit-filter:saturate(.78);filter:saturate(.78)}

/* 4段目 はじめて */
.s4{background:{{BG}};padding:120px 0 110px;overflow:hidden}
.s4 .top{overflow:hidden;padding:0 6%}
.s4 .lt{float:left;width:52%}
.s4 .lab{font-size:.78rem;letter-spacing:.3em;margin-bottom:14px}
.s4 h2{font-size:1.7rem;font-weight:500;line-height:1.8;letter-spacing:{{TR}}em;margin-bottom:18px}
.s4 .lt p.t{font-size:.92rem;line-height:2.2}
.s4 .rt{float:right;width:40%}
.s4 .rt .sq{position:relative;height:0;padding-bottom:78%;width:78%;margin-left:auto;overflow:hidden}
.s4 .rt .two{overflow:hidden}
.s4 .rt .two .a{float:left;width:46%}
.s4 .rt .two .b{float:right;width:46%;margin-top:40px}
.s4 .rt .two .a,.s4 .rt .two .b{position:relative;height:0;padding-bottom:46%;overflow:hidden}
.s4 .rt img{-webkit-filter:saturate(.78);filter:saturate(.78)}
.s4 .flow{margin-top:96px;padding:0 6%;overflow:hidden}
.s4 .flow li{float:left;width:29%;margin-right:6.5%;border-top:1px solid {{INK}};padding-top:26px}
.s4 .flow li:last-child{margin-right:0}
.flow .n{font-size:.72rem;letter-spacing:.2em}
.flow h3{font-size:1.08rem;line-height:1.7;margin:4px 0 6px;letter-spacing:{{TR}}em}
.flow p{font-size:.88rem;line-height:2}

/* 3段目 商品 */
.s3{position:relative}
.s3 .wide{position:relative;height:0;padding-bottom:40%;overflow:hidden}
.s3 .wide img{-webkit-filter:saturate(.78);filter:saturate(.78)}
.s3 .vt{{{VT3}};top:3%;z-index:2;font-size:4.2rem;letter-spacing:.3em;line-height:1.3}
.s3 .fuda{background:{{GAPC}};text-align:right;padding:14px 6%;font-size:1rem;letter-spacing:{{TR}}em;line-height:2}
.s3 .txt{position:relative;background:{{INK}};color:#fff;padding:120px 0 130px;overflow:hidden}
.s3 .txt .bgi{position:absolute;left:0;top:0;width:100%;height:100%;opacity:.42;-o-object-fit:cover;object-fit:cover}
.s3 .txt .img-note{left:16px;bottom:16px}
.s3 .col{position:relative;width:560px;max-width:92%;margin:0 auto;border-left:1px solid rgba(255,255,255,.6);padding-left:40px}
.s3 .col h3{font-size:1.25rem;line-height:1.7;letter-spacing:{{TR}}em;margin-bottom:2px}
.s3 .col p{font-size:.9rem;line-height:2}
.s3 .col .g{margin-bottom:34px}
.s3 .col .lk{display:inline-block;border-bottom:1px solid #fff;font-size:.9rem;line-height:1.9}

/* 5段目 */
.s5{padding:130px 0 120px;overflow:hidden}
.s5 .stag{position:relative;height:0;padding-bottom:66%;margin-bottom:236px}
.s5 .stag .a{position:absolute;left:3%;top:{{A_TOP}};width:{{STA}}%;height:81.8%;overflow:hidden}
.s5 .stag .b{position:absolute;left:{{B_LEFT}}%;top:{{B_TOP}};width:{{STB}}%;height:100%;overflow:hidden}
.s5 .stag img{-webkit-filter:saturate(.78);filter:saturate(.78)}
.s5 .stag .vt{{{VT5}};top:46%;z-index:2;color:{{INK}};font-size:3rem;letter-spacing:.3em;line-height:1.3;text-shadow:0 0 14px rgba(255,255,255,.95),0 0 4px rgba(255,255,255,.9)}
.s5 .two{margin-top:0;padding:0 6%;overflow:hidden}
.s5 .two .lt{float:left;width:44%}
.s5 .two .rt{float:right;width:48%}
.s5 h2{font-size:1.6rem;font-weight:500;line-height:1.8;letter-spacing:{{TR}}em;margin-bottom:14px}
.s5 .lab{font-size:.78rem;letter-spacing:.3em;margin-bottom:14px}
.s5 table{border-collapse:collapse;width:100%;margin:10px 0 22px;font-size:.88rem}
.s5 th,.s5 td{border-top:1px solid {{INK}};border-bottom:1px solid {{INK}};padding:8px 0;text-align:left;vertical-align:top;font-weight:300;line-height:1.8}
.s5 th{width:5em;font-weight:400;letter-spacing:.2em}
.faq li{border-top:1px solid {{INK}};padding:14px 0}
.faq li:last-child{border-bottom:1px solid {{INK}}}
.faq .q{font-size:.92rem;font-weight:400}
.faq .n{display:inline-block;width:3.2em;font-size:.72rem;letter-spacing:.14em}
.faq .a{font-size:.88rem;padding-left:3.2em}

/* 6段目 */
.s6{background:{{INK}};color:#fff;text-align:center;padding:110px 6% 120px}
.s6 h2{font-size:1.8rem;letter-spacing:.2em;margin-bottom:12px}
.s6 p{font-size:.88rem;margin-bottom:24px}

/* 最後 */
.foot{position:relative;height:380px;overflow:hidden;background:{{INK}}}
.foot img{-webkit-filter:saturate(.78) brightness(.85);filter:saturate(.78) brightness(.85)}
.foot .w{position:absolute;left:30px;bottom:50px;font-size:5rem;line-height:1.2;letter-spacing:.2em;color:#fff;text-shadow:0 1px 8px rgba(0,0,0,.4)}
.foot .c{position:absolute;left:30px;bottom:16px;font-size:.72rem;color:rgba(255,255,255,.75);letter-spacing:.1em}
.fixbar,.totop{display:none}

@media (max-width:899px){
 body{padding-bottom:56px}
 .hero{height:auto;min-height:0;max-height:none;padding-bottom:0;overflow:hidden}
 .hero .p1,.hero .p2{position:relative;left:auto;right:auto;top:auto;bottom:auto;width:100%}
 .hero .p1{height:225px}
 .hero .p2{height:460px;margin-top:40px}
 .hero .word{left:26px;top:150px;margin:0;-webkit-transform:none;transform:none;-webkit-writing-mode:vertical-rl;writing-mode:vertical-rl;font-size:3.3rem;text-indent:0;text-shadow:0 1px 6px rgba(0,0,0,.55)}
 .hero .name{left:20px;top:20px;font-size:.8rem}
 .hero .toc{display:none}
 .hero .guide{right:22px;bottom:206px;width:230px;font-size:.68rem}
 .hero .card{left:22px;right:auto;bottom:22px;width:auto;min-width:176px;max-width:230px}  /* 札は左下（右下の「↑」と重ねない）。min-width が無いと札が縮んで一言が 1 字ずつ割れる */
 .hero .card img{width:52px;height:52px}
 .s2 .yoko{right:16px;top:14px;font-size:1rem;letter-spacing:.08em;line-height:1.6;white-space:nowrap}
 .s2 .yoko br{display:none}
 .bar{height:auto;padding:12px 20px;min-height:52px}
 .bar .r{display:none}
 .bar .l{float:none;padding-top:0}
 .s2 .wide{padding-bottom:62%}
 .s2 .vt{font-size:1.25rem;top:6%;line-height:1.7}
 .s2 .band{padding:34px 0 60px 6%}
 .s2 .lc{float:none;width:auto;margin-right:6%}
 .s2 h2{font-size:1.75rem;letter-spacing:.2em}
 .s2 .small{margin-top:30px}
 .s2 .rc,.s2 .rc.one{float:none;width:88%;margin:40px 6% 0 0;padding-top:0}
 .s2 .sqs .a{float:none;width:62%}
 .s2 .sqs .b{float:none;width:62%;margin:-30px 0 0 auto}
 .sqs .a,.sqs .b{padding-bottom:62%}
 .s2 .rc .sq{width:70%;padding-bottom:70%;margin-left:auto}
 .s4{padding:80px 0 70px}
 .s4 .lt,.s4 .rt{float:none;width:auto}
 .s4 .rt{margin-top:26px}
 .s4 .rt .sq{width:92%;padding-bottom:70%}
 .s4 .rt .two{width:92%;margin-left:auto}
 .s4 .flow{margin-top:50px}
 .s4 .flow li{float:none;width:auto;margin:0 0 34px}
 .s4 h2{font-size:1.5rem;letter-spacing:.2em}
 .s3 .wide{padding-bottom:88%}
 .s3 .vt{font-size:3rem;left:22px;right:auto}
 .s3 .txt{padding:70px 0 80px}
 .s3 .col{padding-left:24px}
 .s5{padding:70px 0 80px}
 .s5 .stag{height:auto;padding-bottom:0;margin-bottom:60px;position:relative}
 .s5 .stag .a,.s5 .stag .b{position:relative;left:auto;top:auto;height:0;overflow:hidden}
 .s5 .stag .a{width:74%;padding-bottom:70%;margin-left:32px}
 .s5 .stag .b{width:60%;padding-bottom:72%;margin:-40px 15% 0 auto}
 .s5 .stag .vt{left:auto;right:19%;top:auto;bottom:18px;margin-left:0;color:#fff;font-size:2.4rem;text-shadow:0 1px 8px rgba(0,0,0,.6)}
 .s5 .two{margin-top:0}
 .s5 .two .lt,.s5 .two .rt{float:none;width:auto}
 .s5 .two .rt{margin-top:40px}
 .s5 h2{font-size:1.4rem;letter-spacing:.2em}
 .s6{padding:70px 6% 80px}
 .foot{height:280px}
 .foot .w{font-size:3.6rem}
 .fixbar{display:block;position:fixed;left:0;right:0;bottom:0;z-index:20;background:{{INK}};color:#fff;height:56px;overflow:hidden;border-top:1px solid rgba(255,255,255,.25)}
 .fixbar a{float:left;width:33.33%;text-align:center;font-size:.8rem;letter-spacing:.14em;line-height:56px}
 .totop{display:block;position:fixed;right:14px;bottom:70px;z-index:21;width:36px;height:36px;border:1px solid {{INK}};border-radius:50%;background:rgba(255,255,255,.8);text-align:center;line-height:34px;font-size:.9rem}
}
'''
