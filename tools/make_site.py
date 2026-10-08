#!/usr/bin/env python3
"""お店のサイトのひな形を作る（Lift-Off）  2026/10/8 作成

設定ファイル（JSON）に店名・色・写真・メニューなどを書くと、1ページのサイト（index.html）を作る。
colore で作った「最初から入れる UI/UX の標準」（決定事項）が全部入る：
  予約・相談の入口（いま使える窓口を先に）／目次とスマホのメニュー／メニューごとの LINE 相談（下書き入り）／
  見やすい料金表／よくある質問／道順ボタン／上へ戻る・「もどる」で見ていた場所へ／文の折り返し（BudouX）／
  古いスマホ対策（予備の書き方つき）／LINE のカード画像の設定／検索用のお店情報（JSON-LD）／noindex（試作）

使い方:
  python3 make_site.py <設定.json> <作るフォルダ>
    例）python3 make_site.py ~/src/liftoff-hp/tools/templates/site_sample.json ~/src/yamaguchi-zouteisha
  ・作るフォルダに index.html を書く（前の index.html があれば index.old.html に残す）
  ・画像は設定に書いた場所（images/〜）に自分で入れる。ないときは「写真が入ります」の仮画像を入れる
  ・最後に check_site.py（公開前チェック）を自動で走らせる
設定の書き方は templates/site_sample.json（山口造庭舎のデモ）を見る。分からない情報は書かない（空にすると、その行は出ない）
"""
import sys, os, json, html, shutil, subprocess, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))

def e(t): return html.escape(str(t or ''), quote=True)

THEMES = {  # 色の組み合わせ。設定の "theme" で上書きできる
    'salon': dict(primary='#fe97b2', primary_deep='#ef6386', accent='#c4a466', accent_soft='#e2cf9f', pale='#fdeef2', dark='#24342b', dark2='#2d4136', bg='#faf5ee', bg2='#f3ebe0', ink='#3a3330', muted='#75695f', line='#e6dccd'),
    'wa':    dict(primary='#a8432a', primary_deep='#8f3822', accent='#3e5640', accent_soft='#c9b98f', pale='#efe6d6', dark='#23221f', dark2='#33312c', bg='#f3eee3', bg2='#e9e2d3', ink='#23221f', muted='#6d675c', line='#cfc6b4'),
    'fresh': dict(primary='#2f8f6f', primary_deep='#22735a', accent='#f2b84b', accent_soft='#f7d99a', pale='#e6f3ee', dark='#1f3b33', dark2='#2a4a41', bg='#f7faf8', bg2='#eaf2ee', ink='#22302b', muted='#5d6e67', line='#d5e2dc'),
}
LINE_ICON = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 3C6.5 3 2 6.6 2 11c0 3.9 3.5 7.2 8.3 7.9.3.1.8.2.9.5.1.3.1.7 0 1l-.1.9c0 .3-.2 1 .9.5s5.9-3.5 8-6C21.4 14.3 22 12.7 22 11c0-4.4-4.5-8-10-8z"/></svg>'
PIN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>'
MARKS = {
    'heart': '<path d="M12 21s-7.6-4.6-9.6-9.4C1 8.2 3 4.5 6.6 4.5c2.2 0 3.7 1.3 5.4 3.3 1.7-2 3.2-3.3 5.4-3.3 3.6 0 5.6 3.7 4.2 7.1C19.6 16.4 12 21 12 21z"/>',
    'leaf':  '<path d="M20 4C10 4 4 9 4 16c0 1.6.4 3 1 4 1-4 4-8 9-10-4 3-6 6-7 10 1 .3 2 .5 3 .5 7 0 10-7 10-16z"/>',
    'dot':   '<circle cx="12" cy="12" r="6"/>',
}

def line_url(c, msg=None):
    oid = c.get('line_id')  # 例 "@224ybmlu"。あれば下書き入りで開く
    if msg and oid:
        return 'https://line.me/R/oaMessage/' + urllib.parse.quote(oid) + '/?' + urllib.parse.quote(msg)
    return c.get('line_url') or ''

def ext(url): return f'href="{e(url)}" target="_blank" rel="noopener"'

def build(c):
    t = dict(THEMES[c.get('theme_base', 'salon')]); t.update(c.get('theme', {}))
    name, short = c['name'], c.get('short_name', c['name'])
    mark = MARKS.get(c.get('mark', 'heart'), MARKS['heart'])
    head_font = 'var(--mincho)' if c.get('font', 'mincho') == 'mincho' else 'var(--gothic)'
    base = c.get('url_base', '')
    has_line = bool(c.get('line_url'))
    has_rsv = bool(c.get('reserve_url'))
    tel = c.get('tel', ''); tel_d = ''.join(ch for ch in tel if ch.isdigit())
    I = lambda: '<svg class="mk"><use href="#mk"/></svg>'

    # ---------- 予約・相談の入口（いま使えるものを先に） ----------
    first_btns = []
    if has_rsv: first_btns.append(f'<a class="btn btn-main" {ext(c["reserve_url"])}>ネットで<wbr>予約する</a>')
    if has_line: first_btns.append(f'<a class="btn btn-line" {ext(c["line_url"])}>{LINE_ICON}LINEで<wbr>相談する</a>')
    if tel: first_btns.append(f'<a class="btn btn-ghost" href="tel:{tel_d}">電話する <span class="nw">{e(tel)}</span></a>')
    if not first_btns: first_btns.append('<a class="btn btn-main" href="#reserve">お問い合わせ</a>')

    secs = [('menu', c.get('menu_title', 'メニュー・料金'))]
    if c.get('flow'): secs.append(('flow', c.get('flow_title', 'ご依頼の流れ')))
    secs += [('reserve', c.get('reserve_title', 'ご予約・ご相談')), ('access', c.get('info_title', '店舗情報')), ('faq', 'よくある質問')]
    if c.get('greeting'): secs.insert(0, ('greeting', 'ごあいさつ'))
    nav = ''.join(f'<a href="#{k}">{e(v)}</a>' for k, v in secs if k != 'reserve')
    toc = ''.join(f'<li><a href="#{k}">{e(v)}</a></li>' for k, v in secs)

    # ---------- トップ ----------
    hero = c.get('hero') or {}
    if hero.get('image'):
        hero_vis = f'<figure class="poster"><img src="{e(hero["image"])}" alt="{e(hero.get("alt","イメージ"))}" width="{hero.get("w",1600)}" height="{hero.get("h",1000)}" fetchpriority="high"></figure>'
    else:
        hero_vis = f'<div class="poster plain"><p class="plain-name">{e(short)}</p></div>'
    hero_html = f'''
  <section class="hero">
    <div class="wrap">
      {hero_vis}
      <div class="hero-info">
        <p class="eyebrow">{e(c.get("kind",""))}</p>
        <h1>{c.get("catch_html") or e(c.get("catch",""))}</h1>
        <p class="lead">{e(c.get("lead",""))}</p>
        {f'<p class="addr">{PIN}<span>{e(c.get("area") or c.get("address",""))}</span></p>' if (c.get("area") or c.get("address")) else ''}
        <div class="hero-btns">{''.join(first_btns)}</div>
        <ul class="toc" aria-label="このページの案内">{toc}</ul>
      </div>
    </div>
  </section>'''

    # ---------- ごあいさつ ----------
    g = c.get('greeting')
    greet = ''
    if g:
        img = f'<div class="photo"><img src="{e(g["image"])}" alt="{e(g.get("alt",""))}" width="{g.get("w",800)}" height="{g.get("h",1000)}" loading="lazy"></div>' if g.get('image') else ''
        greet = f'''
  <section id="greeting" class="sec owner{' noimg' if not img else ''}">
    <div class="wrap">
      {img}
      <div>
        <div class="sec-head"><i>{I()}greeting</i><h2>ごあいさつ</h2></div>
        {f'<span class="role">{e(g["role"])}</span>' if g.get("role") else ''}
        <h3>{e(g.get("title",""))}</h3>
        {''.join(f'<p class="muted">{e(p)}</p>' for p in g.get("text",[]))}
      </div>
    </div>
  </section>'''

    # ---------- メニュー・料金 ----------
    menus = c.get('menus', [])
    tabs = ''.join(f'<a href="#m-{e(m["id"])}">{e(m["name"])}</a>' for m in menus)
    if c.get('price_table'): tabs += f'<a href="#m-table">{e(c["price_table"].get("title","料金表"))}</a>'
    cards = []
    for m in menus:
        img = f'<div class="photo"><img src="{e(m["image"])}" alt="{e(m.get("alt", m["name"]))}" width="{m.get("w",1000)}" height="{m.get("h",750)}" loading="lazy"></div>' if m.get('image') else ''
        price = f'<div class="price"><small>{e(m.get("price_note",""))}</small><b>{e(m["price"])}</b></div>' if m.get('price') else '<div class="price"><span class="ask">料金は<wbr>お問い合わせください</span></div>'
        sub = ''.join(f'<li>{e(x)}</li>' for x in m.get('items', []))
        ask = ''
        if has_line:
            msg = c.get('line_msg', 'ホームページを見ました。{name}について相談したいです。').replace('{name}', m['name'])
            ask = f'<a class="ask-line" {ext(line_url(c, msg))}>{LINE_ICON}<span class="nw">この{e(c.get("menu_word","メニュー"))}を<wbr>LINEで相談</span></a>'
        elif tel:
            ask = f'<a class="ask-line tel" href="tel:{tel_d}"><span class="nw">電話で相談する</span></a>'
        cards.append(f'''
        <article class="card" id="m-{e(m["id"])}">
          {img}
          <div class="card-body">
            <h3>{e(m["name"])}</h3>
            {f'<ul class="sub-items">{sub}</ul>' if sub else ''}
            <p>{e(m.get("text",""))}</p>
            {price}
            {ask}
          </div>
        </article>''')
    pt = c.get('price_table')
    table = ''
    if pt:
        rows = ''.join(f'<tr{" class=first" if r.get("tag") else ""}><th>{e(r["label"])}{f"<span class=tag>{e(r[chr(116)+chr(97)+chr(103)])}</span>" if r.get("tag") else ""}</th><td>{e(r.get("text",""))}</td><td class="yen">{e(r["price"])}</td></tr>' for r in pt.get('rows', []))
        opts = ''.join(f'<tr><th>{e(o["label"])}</th><td class="yen">{e(o["price"])}</td></tr>' for o in pt.get('options', []))
        table = f'''
      <div class="ptable" id="m-table">
        <h3>{I()}{e(pt.get("title","料金表"))}</h3>
        {f'<p class="lead">{e(pt["lead"])}</p>' if pt.get("lead") else ''}
        <div class="cols{' one' if not opts else ''}">
          <table class="tbl course">{rows}</table>
          {f'<div class="opt"><h4>オプション</h4><table class="tbl">{opts}</table></div>' if opts else ''}
        </div>
        {f'<p class="extra">{e(pt["note"])}</p>' if pt.get("note") else ''}
      </div>'''
    menu_html = f'''
  <section id="menu" class="sec menu">
    <div class="wrap">
      <div class="sec-head center"><i>{I()}menu</i><h2>{e(c.get("menu_title","メニュー・料金"))}</h2></div>
      {f'<p class="sec-lead center muted">{e(c["menu_lead"])}</p>' if c.get("menu_lead") else ''}
      <nav class="menu-tabs" aria-label="メニューの種類">{tabs}</nav>
      <div class="menu-cards n{len(cards)}">{''.join(cards)}
      </div>{table}
      <p class="price-note muted center">{e(c.get("menu_note","どれにすればいいか迷うときも、お気軽にご相談ください。"))}</p>
    </div>
  </section>'''

    # ---------- 流れ ----------
    flow_html = ''
    if c.get('flow'):
        steps = ''.join(f'<li><h3>{e(s["title"])}</h3><p>{e(s.get("text",""))}</p></li>' for s in c['flow'])
        flow_html = f'''
  <section id="flow" class="sec flow">
    <div class="wrap">
      <div class="sec-head center"><i>{I()}flow</i><h2>{e(c.get("flow_title","ご依頼の流れ"))}</h2></div>
      <ol class="steps">{steps}</ol>
    </div>
  </section>'''

    # ---------- 予約・相談 ----------
    ways = []
    if has_line:
        ways.append(f'<div class="way"><h3>LINE</h3><p>{e(c.get("line_text","友だち追加して、メッセージでご相談ください。"))}</p><a class="btn btn-line" {ext(c["line_url"])}>{LINE_ICON}友だち追加</a></div>')
    if tel:
        ways.append(f'<div class="way"><h3>お電話</h3><p>{e(c.get("tel_note","作業中は出られないことがあります。折り返しご連絡いたします。"))}</p><a class="tel" href="tel:{tel_d}">{e(tel)}</a></div>')
    if has_rsv:
        ways.append(f'<div class="way"><h3>ネット予約</h3><p>空いている日時を見て、24時間いつでもご予約いただけます。</p><a class="btn btn-main" {ext(c["reserve_url"])}>ネットで<wbr>予約する</a></div>')
    if c.get('form_url'):
        ways.append(f'<div class="way"><h3>フォーム</h3><p>24時間いつでも送れます。</p><a class="btn btn-main" {ext(c["form_url"])}>フォームを開く</a></div>')
    if not ways:
        ways.append(f'<div class="way"><h3>準備中</h3><p>{e(c.get("pending_text","連絡先は準備中です。"))}</p></div>')
    rules = ''.join(f'<li>{e(x)}</li>' for x in c.get('rules', []))
    reserve_html = f'''
  <section id="reserve" class="sec reserve dark">
    <div class="wrap">
      <div class="sec-head center"><i>{I()}contact</i><h2>{e(c.get("reserve_title","ご予約・ご相談"))}</h2></div>
      {f'<p class="muted center" style="margin-bottom:40px">{e(c["reserve_lead"])}</p>' if c.get("reserve_lead") else ''}
      <div class="ways n{len(ways)}">{''.join(ways)}</div>
      {f'<div class="rules"><h4>{e(c.get("rules_title","ご予約について"))}</h4><ul>{rules}</ul></div>' if rules else ''}
    </div>
  </section>'''

    # ---------- 店舗情報 ----------
    info_rows = [('店名', name), ('住所', c.get('address')), ('アクセス', c.get('access_note')), ('営業時間', c.get('hours')), ('定休日', c.get('holiday')),
                 ('対応エリア', c.get('service_area')), ('駐車場', c.get('parking')), ('お支払い', c.get('payment'))] + [(k, v) for k, v in c.get('info_extra', [])]
    info = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in info_rows if v)
    if tel: info += f'<div><dt>電話</dt><dd><a href="tel:{tel_d}">{e(tel)}</a></dd></div>'
    mq = c.get('map_query')
    route = f'<a class="route" {ext("https://www.google.com/maps/dir/?api=1&destination=" + urllib.parse.quote(mq))}>{PIN}Googleマップで<wbr>道順を見る</a>' if mq and c.get('show_route', True) else ''
    mapf = f'<div class="map"><iframe src="https://maps.google.com/maps?q={urllib.parse.quote(mq)}&amp;z=15&amp;output=embed" title="{e(short)}の地図" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>' if mq else ''
    access_html = f'''
  <section id="access" class="sec access">
    <div class="wrap{' nomap' if not mapf else ''}">
      <div>
        <div class="sec-head"><i>{I()}{e(c.get("info_eyebrow","access"))}</i><h2>{e(c.get("info_title","店舗情報"))}</h2></div>
        <dl class="info">{info}</dl>
        {route}
      </div>
      {mapf}
    </div>
  </section>'''

    # ---------- よくある質問 ----------
    faq = ''.join(f'<details><summary><span class="q">Q</span><span>{e(f["q"])}</span></summary><p><span class="a">A</span><span>{e(f["a"])}</span></p></details>' for f in c.get('faq', []))
    faq_html = f'''
  <section id="faq" class="sec faq">
    <div class="wrap">
      <div class="sec-head center"><i>{I()}q &amp; a</i><h2>よくある<wbr>ご質問</h2></div>
      <div class="faq-list">{faq}</div>
    </div>
  </section>'''

    # ---------- SNS ----------
    sns = c.get('sns', [])
    sns_html = ''
    if sns:
        sns_html = f'''
  <section id="contact" class="sec sns center">
    <div class="wrap">
      <div class="sec-head center"><i>{I()}follow us</i><h2>SNS</h2></div>
      <div class="sns-list">{''.join(f'<a {ext(s["url"])}>{e(s["name"])}</a>' for s in sns)}</div>
    </div>
  </section>'''

    # ---------- スマホの下のボタン ----------
    bar = []
    if tel: bar.append(f'<a href="tel:{tel_d}">電話する</a>')
    if has_line: bar.append(f'<a class="l" {ext(c["line_url"])}>LINEで相談</a>')
    bar.append(f'<a class="r" {ext(c["reserve_url"])}>ネット予約</a>' if has_rsv else '<a class="r" href="#menu">メニュー</a>')

    # ---------- 頭 ----------
    desc = c.get('description', c.get('lead', ''))
    og = ''
    if base:
        og = f'''<meta property="og:url" content="{e(base)}">
<meta property="og:image" content="{e(base + c.get('og_image','images/og.jpg'))}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">'''
    ld = {"@context": "https://schema.org", "@type": c.get('schema_type', 'LocalBusiness'), "name": name}
    if base: ld["url"] = base
    if tel: ld["telephone"] = '+81-' + tel.lstrip('0')
    if c.get('address'): ld["address"] = {"@type": "PostalAddress", "addressCountry": "JP", "streetAddress": c['address']}
    if c.get('area_served'): ld["areaServed"] = c['area_served']
    if c.get('opening_hours'): ld["openingHours"] = c['opening_hours']
    if sns: ld["sameAs"] = [s['url'] for s in sns]

    css = CSS
    for k, v in t.items(): css = css.replace('{{' + k + '}}', v)
    css = css.replace('{{head_font}}', head_font)

    out = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(name)}{('｜' + e(c['title_place'])) if c.get('title_place') else ''}</title>
<meta name="description" content="{e(desc)}">
<!-- 本公開前は検索に出さない設定。本公開のときに tools/launch.py で外す -->
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="{t['dark']}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(name)}">
<meta property="og:title" content="{e(name)}">
<meta property="og:description" content="{e(desc)}">
{og}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,500&family=Shippori+Mincho+B1:wght@500;600;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False)}
</script>
<style>
{css}
</style>
</head>
<body>
<!-- このページは tools/make_site.py で作った（設定：{e(c.get('slug',''))}.json）。直すときは設定を直して作り直すか、このファイルを直接直す -->
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="mk" viewBox="0 0 24 24">{mark}</symbol></svg>
<header class="head">
  <div class="wrap">
    <a href="#top" class="brand" aria-label="{e(short)} トップへ">{f'<img src="{e(c["logo"])}" alt="{e(short)}" width="46" height="46">' if c.get('logo') else ''}<span class="bn">{e(short)}</span>{f'<span class="bk">{e(c["kind"])}</span>' if c.get('kind') else ''}</a>
    <nav class="nav" id="gnav" aria-label="ページ内">{nav}<a href="#reserve" class="rsv">{e(c.get("nav_cta","ご相談"))}</a></nav>
    <button type="button" class="menubtn" aria-expanded="false" aria-controls="gnav"><i aria-hidden="true"></i>メニュー</button>
  </div>
</header>
<main id="top">{hero_html}{greet}{menu_html}{flow_html}{reserve_html}{access_html}{faq_html}{sns_html}
</main>
<footer class="foot">
  <div class="wrap">
    <p class="fname">{e(name)}</p>
    {f'<p>{e(c["address"])}</p>' if c.get('address') else ''}
    {f'<p>TEL <a href="tel:{tel_d}">{e(tel)}</a>{("　／　" + e(c["hours"])) if c.get("hours") else ""}</p>' if tel else ''}
    <nav aria-label="フッター">{nav}</nav>
    <p class="copy">© {e(short)}</p>
  </div>
</footer>
{f'<nav class="spbar n{len(bar)}" aria-label="ご予約・ご相談">' + ''.join(bar) + '</nav>' if (tel or has_line or has_rsv) else ''}
<a class="totop" href="#top" aria-label="ページの上へ">↑</a>
<script>
{JS}
</script>
</body>
</html>
'''
    return out

CSS = r'''/* 言葉の切れ目で折り返す（<wbr> は BudouX で入れる） */
.nw{white-space:nowrap}
body{word-break:keep-all;overflow-wrap:anywhere;line-break:strict}
:root{
  --primary:{{primary}};--primary-deep:{{primary_deep}};--accent:{{accent}};--accent-soft:{{accent_soft}};--pale:{{pale}};
  --dark:{{dark}};--dark2:{{dark2}};--bg:{{bg}};--bg2:{{bg2}};--ink:{{ink}};--muted:{{muted}};--line:{{line}};
  --r:18px;
  --mincho:"Shippori Mincho B1","Hiragino Mincho ProN","Yu Mincho","Noto Serif CJK JP",serif;
  --gothic:"Zen Kaku Gothic New","Hiragino Sans","Yu Gothic","Noto Sans CJK JP",sans-serif;
  --latin:"Cormorant Garamond","Shippori Mincho B1",serif;
  --head:{{head_font}};
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--gothic);font-size:16px;line-height:2;letter-spacing:.06em}
img{max-width:100%;height:auto;display:block}
a{color:inherit}
:focus-visible{outline:2px solid var(--primary);outline-offset:4px}
.wrap{width:min(1100px,100% - 40px);margin-left:auto;margin-right:auto}
h1,h2,h3{font-family:var(--head);font-weight:500;margin:0;line-height:1.7}
p{margin:0 0 1.2em}
.muted{color:var(--muted)}
.center{text-align:center}
.mk{display:inline-block;width:.9em;height:.9em;vertical-align:-.05em;fill:var(--primary-deep)}
.photo{border-radius:var(--r);overflow:hidden;background:var(--bg2)}
.photo img{width:100%;height:auto}
.btn{display:inline-flex;align-items:center;justify-content:center;text-decoration:none;font-weight:500;letter-spacing:.12em;padding:.95em 1.8em;border-radius:999px;line-height:1.4;text-align:center;-webkit-transition:background .2s;transition:background .2s}
.btn svg{width:1.25em;height:1.25em;flex:none;margin-right:.5em}
.btn-main{background:var(--primary);color:#fff}
.btn-main:hover{background:var(--primary-deep)}
.btn-line{background:#06c755;color:#fff}
.btn-line:hover{background:#05b04b}
.btn-ghost{border:1px solid rgba(255,255,255,.45);color:#fff}
.btn-ghost:hover{border-color:#fff}
/* ヘッダー */
.head{position:absolute;top:0;left:0;right:0;z-index:30}
.head .wrap{display:flex;justify-content:space-between;align-items:center;height:84px;color:#f3efe6}
.brand{display:flex;align-items:center;text-decoration:none}
.brand img{width:46px;height:46px;border-radius:10px;margin-right:12px}
.bn{font-family:var(--head);font-size:1.15rem;letter-spacing:.14em}
.bk{font-size:.74rem;letter-spacing:.18em;color:var(--accent-soft);margin-left:12px}
.nav{display:flex;align-items:center;font-size:.86rem}
.nav a{text-decoration:none;opacity:.9;margin-left:24px}
.nav a:hover{opacity:1;color:var(--accent-soft)}
.nav .rsv{background:var(--primary);color:#fff;padding:.5em 1.4em;border-radius:999px;opacity:1}
.menubtn{display:none}
@media (max-width:860px){
  .nav a{display:none}.bk{display:none}
  .menubtn{display:inline-flex;align-items:center;background:rgba(0,0,0,.35);color:#f3efe6;border:1px solid rgba(255,255,255,.4);border-radius:999px;padding:.45em .95em;font:inherit;font-size:.8rem;letter-spacing:.1em;cursor:pointer}
  .menubtn i{display:block;width:14px;height:10px;border-top:1.5px solid currentColor;border-bottom:1.5px solid currentColor;position:relative;margin-right:6px}
  .menubtn i::after{content:"";position:absolute;left:0;right:0;top:3.5px;border-top:1.5px solid currentColor}
  .head.open .nav{display:flex;position:absolute;top:76px;right:12px;flex-direction:column;align-items:stretch;background:var(--dark);border:1px solid rgba(255,255,255,.2);border-radius:14px;padding:6px;min-width:210px;box-shadow:0 12px 30px rgba(0,0,0,.35)}
  .head.open .nav a{display:block;margin:0;padding:.85em 1em;border-radius:10px;font-size:.92rem}
  .head.open .nav .rsv{margin-top:4px;text-align:center}
}
/* トップ */
.hero{background:var(--dark);color:#f3efe6;position:relative;overflow:hidden}
.hero .wrap{width:100%;display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);align-items:stretch;min-height:100vh;min-height:min(100vh,940px)}
.poster{margin:0;position:relative;overflow:hidden}
.poster img{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover}
.poster::after{content:"";position:absolute;top:0;right:0;bottom:0;width:30%;background:linear-gradient(90deg,rgba(0,0,0,0),var(--dark));pointer-events:none}
.poster.plain{display:flex;align-items:center;justify-content:center;background:radial-gradient(70% 60% at 50% 45%,var(--dark2),var(--dark))}
.plain-name{font-family:var(--head);font-size:3rem;letter-spacing:.3em;color:var(--accent-soft);margin:0;padding:0 20px;text-align:center}
.hero-info{align-self:center;padding:130px clamp(28px,6vw,90px) 90px clamp(24px,3vw,48px);max-width:640px}
.eyebrow{font-family:var(--head);color:var(--accent-soft);letter-spacing:.2em;font-size:.95rem;margin-bottom:18px;display:flex;align-items:center}
.eyebrow::before{content:"";width:36px;height:1px;background:var(--accent-soft);margin-right:14px;flex:none}
.hero h1{font-size:2.1rem;font-size:clamp(1.6rem,3.2vw,2.5rem);letter-spacing:.14em;line-height:1.75;margin-bottom:22px}
.hero .lead{color:#ddd8cc;line-height:2.1}
.addr{display:flex;font-size:.9rem;color:#e9e4d8;border-top:1px solid rgba(255,255,255,.18);padding-top:22px;margin-top:26px}
.addr svg{width:1.1em;height:1.1em;flex:none;margin:.4em .6em 0 0;fill:var(--primary)}
.hero-btns{display:flex;flex-wrap:wrap;margin:8px -6px 0}
.hero-btns .btn{margin:6px}
.toc{display:flex;flex-wrap:wrap;margin:18px -4px 0;padding:0;list-style:none}
.toc li{margin:4px}
.toc a{display:inline-block;text-decoration:none;font-size:.82rem;letter-spacing:.1em;color:#efeadf;border:1px solid rgba(255,255,255,.3);border-radius:999px;padding:.45em 1.1em}
.toc a:hover{border-color:var(--accent-soft);color:var(--accent-soft)}
@media (max-width:860px){
  .hero{padding-bottom:48px}
  .hero .wrap{grid-template-columns:1fr;min-height:0}
  .poster img{position:static;height:auto}
  .poster::after{display:none}
  .poster.plain{min-height:220px;padding-top:70px}
  .plain-name{font-size:2.2rem}
  .hero-info{width:auto;max-width:none;margin:28px 20px 0;padding:0}
  .hero-btns .btn{flex:1 1 100%}
}
/* 見出し */
.sec{padding:110px 0}
.sec-head{margin-bottom:48px}
.sec-head i{display:flex;align-items:center;font-family:var(--latin);font-style:italic;font-size:1.1rem;color:var(--primary-deep);letter-spacing:.08em;margin-bottom:4px}
.sec-head i .mk{margin-right:.45em}
.sec-head.center i{justify-content:center}
.sec-head h2{font-size:1.75rem;font-size:clamp(1.5rem,2.8vw,2rem);letter-spacing:.16em}
.dark{background:var(--dark);color:#efeadf}
.dark .muted{color:#cfcabd}
.dark .sec-head i{color:var(--primary)}
.sec-lead{max-width:40em;margin:-24px auto 32px}
@media (max-width:860px){.sec{padding:80px 0}.sec-head{margin-bottom:34px}}
/* ごあいさつ */
.owner .wrap{display:grid;grid-template-columns:340px 1fr;grid-gap:72px;gap:72px;align-items:center;max-width:1000px}
.owner.noimg .wrap{grid-template-columns:1fr;max-width:760px}
.role{display:inline-block;font-size:.8rem;letter-spacing:.2em;background:var(--pale);color:var(--primary-deep);padding:.3em 1.1em;border-radius:999px;margin-bottom:16px}
.owner h3{font-size:1.4rem;letter-spacing:.12em;margin-bottom:22px}
@media (max-width:860px){.owner .wrap{grid-template-columns:1fr;grid-gap:40px;gap:40px}.owner .photo{max-width:300px;margin:0 auto}}
/* メニュー */
.menu-tabs{display:flex;flex-wrap:wrap;justify-content:center;margin:-8px auto 36px;max-width:700px}
.menu-tabs a{margin:4px;text-decoration:none;font-size:.86rem;letter-spacing:.08em;color:var(--ink);background:#fff;border:1px solid var(--line);border-radius:999px;padding:.5em 1.2em}
.menu-tabs a:hover{border-color:var(--primary);color:var(--primary-deep)}
.menu-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));grid-gap:24px;gap:24px}
.menu-cards.n4{grid-template-columns:repeat(4,1fr)}
@media (max-width:1100px){.menu-cards.n4{grid-template-columns:1fr 1fr}}
@media (max-width:600px){.menu-cards.n4{grid-template-columns:1fr}}
.card{background:#fff;border-radius:var(--r);overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,.06);display:flex;flex-direction:column;scroll-margin-top:16px}
.card .photo{border-radius:0}
.card-body{padding:24px 24px 26px;display:flex;flex-direction:column;flex:1}
.card h3{font-size:1.25rem;letter-spacing:.12em;margin-bottom:6px}
.card p{color:var(--muted);font-size:.92rem;line-height:1.9;margin-bottom:14px}
.sub-items{display:flex;flex-wrap:wrap;margin:0 -3px 12px;padding:0;list-style:none}
.sub-items li{margin:3px;font-size:.78rem;background:var(--pale);color:var(--primary-deep);border-radius:999px;padding:.15em .9em}
.price{margin-top:auto;border-top:1px dashed var(--line);padding-top:12px;font-family:var(--head);display:flex;justify-content:space-between;align-items:baseline}
.price b{font-size:1.35rem;font-weight:500;color:var(--dark);letter-spacing:.04em}
.price small{font-family:var(--gothic);font-size:.8rem;color:var(--muted)}
.price .ask{font-size:.9rem;color:var(--muted)}
.ask-line{display:flex;align-items:center;justify-content:center;margin-top:14px;text-decoration:none;font-size:.85rem;letter-spacing:.06em;color:#06a447;border:1.5px solid #06c755;border-radius:999px;padding:.6em 1em}
.ask-line:hover{background:#06c755;color:#fff}
.ask-line svg{width:1.1em;height:1.1em;margin-right:.45em;flex:none}
.ask-line.tel{color:var(--primary-deep);border-color:var(--primary)}
.ptable{margin-top:56px;background:#fff;border-radius:var(--r);padding:44px clamp(18px,5vw,52px);scroll-margin-top:16px}
.ptable h3{font-size:1.3rem;letter-spacing:.14em;margin-bottom:6px;display:flex;align-items:center}
.ptable h3 .mk{margin-right:.45em}
.ptable .lead{color:var(--muted);font-size:.92rem;margin-bottom:20px}
.tbl{width:100%;border-collapse:collapse}
.tbl th,.tbl td{padding:14px 4px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
.tbl th{font-family:var(--head);font-weight:500;letter-spacing:.08em;font-size:1.05rem;width:9em}
.tbl td{color:var(--muted);font-size:.9rem;line-height:1.8}
.tbl td.yen{text-align:right;white-space:nowrap;font-family:var(--head);color:var(--dark);font-size:1.2rem;width:7em}
.tbl .tag{display:inline-block;margin-left:.6em;font-family:var(--gothic);font-size:.68rem;background:var(--pale);color:var(--primary-deep);border-radius:999px;padding:.1em .7em;vertical-align:.15em;white-space:nowrap}
.tbl tr.first{background:linear-gradient(90deg,var(--pale),rgba(255,255,255,0))}
.cols{display:grid;grid-template-columns:1.4fr 1fr;grid-gap:44px;gap:44px}
.cols.one{grid-template-columns:1fr}
.opt h4{font-family:var(--head);font-weight:500;letter-spacing:.14em;margin:0 0 6px}
.opt .tbl th{width:auto;font-size:.95rem}
.extra{margin:20px 0 0;background:var(--bg);border-radius:12px;padding:14px 18px;font-size:.88rem;color:var(--muted)}
.price-note{margin-top:28px;font-size:.88rem}
@media (max-width:860px){.cols{grid-template-columns:1fr;grid-gap:30px;gap:30px}}
@media (max-width:640px){
  .menu-tabs{margin:-12px -4px 26px}.menu-tabs a{font-size:.8rem;padding:.45em .95em}
  .card-body{padding:16px 16px 18px}.card h3{font-size:1.08rem}.card p{font-size:.84rem;line-height:1.75;margin-bottom:10px}
  .ptable{padding:30px 18px}
  .tbl.course tr{display:grid;grid-template-columns:1fr auto;border-bottom:1px solid var(--line);padding:12px 0}
  .tbl.course th,.tbl.course td{border:none;padding:0;width:auto}
  .tbl.course td.yen{grid-column:2;grid-row:1}
  .tbl.course td:not(.yen){grid-column:1 / -1;margin-top:4px;font-size:.84rem}
}
/* 流れ */
.steps{list-style:none;margin:0 auto;padding:0;max-width:860px;counter-reset:s}
.steps li{position:relative;padding:0 0 30px 64px;counter-increment:s}
.steps li::before{content:counter(s);position:absolute;left:0;top:0;width:44px;height:44px;border-radius:50%;background:var(--primary);color:#fff;display:flex;align-items:center;justify-content:center;font-family:var(--latin);font-size:1.2rem}
.steps li::after{content:"";position:absolute;left:21px;top:48px;bottom:4px;border-left:2px dotted var(--line)}
.steps li:last-child::after{display:none}
.steps h3{font-size:1.15rem;letter-spacing:.1em;margin:4px 0 4px}
.steps p{color:var(--muted);font-size:.92rem;margin:0}
/* 予約・相談 */
.reserve .wrap{max-width:1000px}
.ways{display:grid;grid-template-columns:repeat(3,1fr);grid-gap:18px;gap:18px}
.ways.n1{grid-template-columns:1fr;max-width:460px;margin:0 auto}
.ways.n2{grid-template-columns:1fr 1fr;max-width:760px;margin:0 auto}
.way{background:var(--dark2);border:1px solid rgba(255,255,255,.14);border-radius:var(--r);padding:32px 22px;text-align:center;display:flex;flex-direction:column;align-items:center}
.way h3{font-size:1rem;letter-spacing:.2em;color:var(--accent-soft);margin-bottom:6px}
.way p{font-size:.9rem;color:#d9d4c8;margin-bottom:18px}
.way .btn{width:100%;margin-top:auto}
.tel{font-family:var(--latin);font-size:2rem;letter-spacing:.06em;text-decoration:none;color:#fff;margin-top:auto}
.rules{max-width:760px;margin:36px auto 0;border:1px solid rgba(255,255,255,.18);border-radius:var(--r);padding:24px 26px}
.rules h4{font-family:var(--head);font-weight:500;color:var(--accent-soft);letter-spacing:.16em;margin:0 0 8px}
.rules ul{margin:0;padding-left:1.2em;font-size:.9rem}
@media (max-width:860px){.ways,.ways.n2{grid-template-columns:1fr}}
/* 店舗情報 */
.access .wrap{display:grid;grid-template-columns:1fr 1fr;grid-gap:56px;gap:56px}
.access .wrap.nomap{grid-template-columns:1fr;max-width:760px}
.info{margin:0;background:#fff;border-radius:var(--r);padding:6px 26px}
.info div{display:grid;grid-template-columns:7em 1fr;padding:14px 0;border-bottom:1px solid var(--line)}
.info div:last-child{border-bottom:none}
.info dt{color:var(--muted);font-size:.9rem}
.info dd{margin:0}
.route{display:flex;align-items:center;justify-content:center;margin-top:18px;text-decoration:none;background:var(--dark);color:#fbf7ef;border-radius:999px;padding:.95em 1.4em;letter-spacing:.12em;font-size:.92rem}
.route svg{width:1.1em;height:1.1em;fill:var(--primary);margin-right:.5em}
.map{border-radius:var(--r);overflow:hidden;min-height:400px;background:var(--bg2)}
.map iframe{width:100%;height:100%;min-height:400px;border:0;display:block}
@media (max-width:860px){.access .wrap{grid-template-columns:1fr;grid-gap:36px;gap:36px}.info{padding:4px 18px}.info div{grid-template-columns:5.5em 1fr}.map,.map iframe{min-height:280px}}
/* よくある質問 */
.faq{background:var(--bg2)}
.faq-list{max-width:820px;margin:0 auto}
.faq details{background:#fff;border-radius:14px;margin-bottom:12px}
.faq summary{list-style:none;cursor:pointer;display:flex;align-items:center;padding:18px 48px 18px 20px;position:relative;font-family:var(--head);letter-spacing:.06em;line-height:1.7}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";position:absolute;right:20px;top:50%;-webkit-transform:translateY(-50%);transform:translateY(-50%);color:var(--primary-deep);font-size:1.3rem;font-family:var(--gothic)}
.faq details[open] summary::after{content:"−"}
.faq p{margin:0;padding:0 20px 20px;display:flex;color:var(--muted);font-size:.93rem;line-height:1.9}
.faq .q,.faq .a{flex:none;display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:50%;font-family:var(--latin);font-style:italic;margin-right:14px}
.faq .q{background:var(--primary);color:#fff}
.faq .a{background:var(--pale);color:var(--primary-deep)}
/* SNS・下 */
.sns{background:var(--pale)}
.sns-list{display:flex;flex-wrap:wrap;justify-content:center}
.sns-list a{margin:6px;background:#fff;border-radius:14px;padding:16px 26px;text-decoration:none}
.foot{background:var(--dark);color:#e9e4d8;padding:56px 0 110px;font-size:.88rem}
.foot .fname{font-family:var(--head);font-size:1.1rem;letter-spacing:.14em;color:#fff}
.foot nav{display:flex;flex-wrap:wrap;margin:20px -10px}
.foot nav a{margin:4px 10px;text-decoration:none;opacity:.85}
.foot .copy{font-family:var(--latin);font-style:italic;opacity:.7;margin:0}
.spbar{display:none}
@media (max-width:860px){
  .spbar{display:grid;grid-template-columns:repeat(3,1fr);position:fixed;left:0;right:0;bottom:0;z-index:50;background:var(--dark);border-top:1px solid var(--accent-soft);padding-bottom:env(safe-area-inset-bottom)}
  .spbar.n2{grid-template-columns:1fr 1fr}.spbar.n1{grid-template-columns:1fr}
  .spbar a{text-align:center;text-decoration:none;color:#fbf7ef;padding:1em .3em;font-size:.86rem;letter-spacing:.1em}
  .spbar a.l{background:#06c755}.spbar a.r{background:var(--primary)}
}
.totop{position:fixed;right:14px;bottom:18px;z-index:40;width:44px;height:44px;border-radius:50%;background:var(--dark);color:#fff;display:flex;align-items:center;justify-content:center;text-decoration:none;opacity:0;visibility:hidden;-webkit-transition:opacity .3s;transition:opacity .3s;box-shadow:0 4px 12px rgba(0,0,0,.25)}
.totop.show{opacity:.92;visibility:visible}
@media (max-width:860px){.totop{bottom:76px;right:12px}}'''

JS = r'''// スマホのメニュー（開く・閉じる）と、上へ戻るボタン
(function(){
  var head = document.querySelector('.head'), btn = document.querySelector('.menubtn'), nav = document.getElementById('gnav');
  if (head && btn && nav) {
    function set(open){ head.className = open ? 'head open' : 'head'; btn.setAttribute('aria-expanded', open ? 'true' : 'false'); }
    btn.addEventListener('click', function(e){ e.stopPropagation(); set(head.className.indexOf('open') < 0); });
    nav.addEventListener('click', function(e){ if (e.target.tagName === 'A') set(false); });
    document.addEventListener('click', function(e){ if (head.className.indexOf('open') >= 0 && !nav.contains(e.target)) set(false); });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape') set(false); });
  }
  var up = document.querySelector('.totop');
  if (up) { var f = function(){ up.className = (window.pageYOffset || 0) > 900 ? 'totop show' : 'totop'; }; window.addEventListener('scroll', f); f(); }
})();
// 戻ったときに、見ていた場所に戻す
(function(){
  var key = 'y:' + location.pathname;
  try {
    window.addEventListener('pagehide', function(){ sessionStorage.setItem(key, String(window.pageYOffset || 0)); });
    var nav = performance.getEntriesByType ? performance.getEntriesByType('navigation')[0] : null;
    var back = nav ? nav.type === 'back_forward' : (performance.navigation && performance.navigation.type === 2);
    if (back) window.addEventListener('load', function(){ var y = parseInt(sessionStorage.getItem(key) || '0', 10); if (y > 0 && (window.pageYOffset || 0) < 10) window.scrollTo(0, y); });
  } catch (err) {}
})();'''

def placeholder(path, w, h, label):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ece5da"/><stop offset="1" stop-color="#d9cfc0"/></linearGradient></defs>
<rect width="{w}" height="{h}" fill="url(#g)"/>
<text x="{w/2}" y="{h/2}" text-anchor="middle" font-family="'Hiragino Sans','Noto Sans CJK JP',sans-serif" font-size="{max(28, w//28)}" letter-spacing="3" fill="#8a7d6a">{html.escape(label)}</text>
</svg>
''')

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    conf, outdir = sys.argv[1], os.path.expanduser(sys.argv[2])
    c = json.load(open(conf, encoding='utf-8'))
    os.makedirs(outdir, exist_ok=True)
    # 写真がまだないところは「写真が入ります」の仮画像（.svg）を入れる
    def need(obj, label, w, h):
        if obj and obj.get('image') and not os.path.exists(os.path.join(outdir, obj['image'])):
            if obj['image'].endswith('.svg'): placeholder(os.path.join(outdir, obj['image']), w, h, label)
            else: print('⚠️ 写真がありません：', obj['image'])
    need(c.get('hero'), 'トップの写真が入ります', c.get('hero', {}).get('w', 1600), c.get('hero', {}).get('h', 1000))
    need(c.get('greeting'), 'ごあいさつの写真が入ります', 800, 1000)
    for m in c.get('menus', []): need(m, m['name'] + 'の写真が入ります', m.get('w', 1000), m.get('h', 750))
    s = build(c)
    try:
        sys.path.insert(0, HERE); import wbr
        s, n = wbr.add_wbr(s); print(f'文の折り返し：{n}か所')
    except SystemExit:
        print('⚠️ budoux がないので文の折り返しを入れていません（pip3 install budoux）')
    p = os.path.join(outdir, 'index.html')
    if os.path.exists(p): shutil.copy(p, os.path.join(outdir, 'index.old.html'))
    open(p, 'w', encoding='utf-8').write(s)
    print('作りました：', p)
    # 設定はサイトのフォルダに一緒に置く（次に作り直すときはこれを直す）
    keep = os.path.join(outdir, 'site.json')
    if os.path.abspath(conf) != os.path.abspath(keep): shutil.copy(conf, keep); print('設定を置きました：', keep)
    chk = os.path.join(HERE, 'check_site.py')
    if os.path.exists(chk): subprocess.call([sys.executable, chk, outdir, '--no-browser'])

if __name__ == '__main__':
    main()
