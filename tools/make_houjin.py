#!/usr/bin/env python3
"""法人の型：複数ページの会社サイトを作る（Lift-Off）  2026/11/13 作成（段2a）

make_site.py から呼ばれる（設定に "pages" があるとき）。単独では動かさない：
  python3 make_site.py <設定.json> <作るフォルダ>   ← 今までと同じ命令。設定に "pages" がなければ今までどおり1ページのお店の型

1つの役目：法人（会社）向けの「複数ページ」の HTML を作る。見た目（CSS）・ページの組み立てはこのファイルだけが持つ。
共通の部品（色の辞書 THEMES・e()・JS・404・Cloudflare の設定ファイル・部品 form の JS）は make_site.py から借りる（コピーしない）。

作るもの（作るフォルダの中）：
  index.html                     トップ（最初の画面・お知らせの新着3件・信頼の帯・会社紹介・事業内容・実績の新着3件・採用・お問い合わせ）
  business/index.html            事業内容（事業ごとの区画・ご依頼の流れ）
  works/index.html               実績の一覧（種類の札・カード）         works/<id>/index.html  実績1件（写真・本文・前後・一覧へ）
  news/index.html                お知らせの一覧（年・分類）             news/<id>/index.html   お知らせ1件
  company/index.html             会社概要・沿革（表・年表・地図と道順・あいさつ）
  recruit/index.html             採用（募集要項の表・働き方・よくある質問・応募の方法）
  contact/index.html             お問い合わせ（電話・メール・フォーム・よくある質問）
  privacy/index.html             プライバシーポリシー
  404.html  sitemap.xml  robots.txt  site.json（設定の控え）  wrangler.jsonc・.assetsignore（別のリポジトリの中でなければ）
  _tpl/                          2b（CMS）の Worker が使うひな形。同じ関数に差し込みの印（{{title}} など）を渡して作る。見た目はここにしかない

設定（JSON）の書き方：templates/site_sample_houjin.json（架空の会社・写真なし）。分からない情報は書かない（空なら出ない）
  "pages": { "business": {...}, "works": {...}, "news": {...}, "company": {...}, "recruit": {...}, "contact": {...}, "privacy": {...} }
  お知らせ・実績は pages.news.items / pages.works.items に1件足せば、一覧・1件ページ・トップの新着・sitemap.xml が全部増える
  "cms": {"enabled": true, "approve": false}  … 2b で Worker が /works/ /news/ とトップの新着を D1 から出す（2a では印を残すだけ）

標準7点（~/src/CLAUDE.md）は全ページに：①電話・お問い合わせ（スマホは下に固定）②全ページ共通の案内＋スマホの「メニュー」＋パンくず
  ③事業内容の区画（料金は出さず「お見積もり」）④よくある質問（お問い合わせ・採用）⑤「Googleマップで道順を見る」（会社概要）
  ⑥「↑上へ」と、もどると見ていた場所に戻る ⑦折り返し（BudouX）・古いスマホ対策・ページごとの og:image
言葉の検査（check_site.py の NG_WORDS）は全サイト共通のまま。法人の文で ⚠️ が出たら文を直す（設計書 02 の 5）
"""
import sys, os, re, json, html, shutil, subprocess, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_site as ms  # 共通の部品を借りる（e・THEMES・JS・PARTS_JS['form']・build_404・write_cloudflare_files）

e = ms.e

# 法人向けの色（お店の THEMES には足さない＝お店の出力を変えないため）。会社の色1つ＋差し色1つ＋黒白
THEMES = {
    'navy':  dict(primary='#1f3a5f', primary_deep='#16294a', accent='#d9731a', accent_soft='#f3c88a', pale='#e8eef5', dark='#0e1722', dark2='#1d2c3e', bg='#f7f8f9', bg2='#eef1f4', ink='#1e252d', muted='#5c6670', line='#d9dee4'),
    'steel': dict(primary='#3b4a5a', primary_deep='#2a3642', accent='#c9a227', accent_soft='#ecd98a', pale='#eaeef1', dark='#141b22', dark2='#222c36', bg='#f7f8f8', bg2='#eef0f2', ink='#20262c', muted='#5f6870', line='#d8dde2'),
}
EYEBROW = {'news': 'News', 'works': 'Works', 'business': 'Business', 'company': 'Company', 'recruit': 'Recruit', 'contact': 'Contact', 'about': 'About us', 'privacy': 'Privacy policy'}
MARK_SVG = '<svg class="mark" viewBox="0 0 36 36" aria-hidden="true"><rect width="36" height="36" rx="4" fill="{{primary}}"/><path d="M8 24h7V12h6v12h7" fill="none" stroke="{{accent_soft}}" stroke-width="3"/></svg>'


def esc_lines(lines):
    """文の配列を <p> に。1つの文字列なら1つの <p>"""
    if isinstance(lines, str): lines = [lines]
    return ''.join(f'<p>{e(x)}</p>' for x in (lines or []) if x)


class Site:
    """設定を読み、全ページを作る"""

    def __init__(self, c, outdir):
        self.c = c
        self.out = outdir
        self.P = c.get('pages') or {}
        self.t = dict(THEMES.get(c.get('theme_base', 'navy'), THEMES['navy'])); self.t.update(c.get('theme', {}))
        self.name, self.short = c['name'], c.get('short_name', c['name'])
        self.tel = c.get('tel', ''); self.tel_d = ''.join(ch for ch in self.tel if ch.isdigit())
        self.base = c.get('url_base', '')
        self.cms = bool((c.get('cms') or {}).get('enabled'))
        self.written = []  # (ページの道, 見出し)

    # ---------- 道（相対）。深さ 0＝トップ、1＝/works/、2＝/works/<id>/ ----------
    def rel(self, depth): return '../' * depth

    # ---------- 全ページ共通：頭・ヘッダー・フッター・下の固定ボタン ----------
    def nav_items(self):
        P = self.P
        items = []
        if 'business' in P: items.append(('business/', '事業内容'))
        if 'works' in P: items.append(('works/', '施工実績'))
        if 'company' in P: items.append(('company/', '会社概要'))
        if 'recruit' in P: items.append(('recruit/', '採用情報'))
        if 'news' in P: items.append(('news/', 'お知らせ'))
        return items

    def page(self, depth, path, title, desc, body, current='', og_image=None, crumbs=None):
        """1ページ分の HTML。body は <main> の中身。current は案内で印を付けるページ（'works' など）。crumbs は [(道, 名前), ...]（最後は名前だけ）"""
        c, t, r = self.c, self.t, self.rel(depth)
        nav = ''.join(f'<a href="{r}{e(p)}"{chr(32) + chr(99)+chr(108)+chr(97)+chr(115)+chr(115) + "=" + chr(34) + "on" + chr(34) + " aria-current=" + chr(34) + "page" + chr(34) if p.split("/")[0] == current else ""}>{e(n)}</a>' for p, n in self.nav_items())
        if 'contact' in self.P: nav += f'<a href="{r}contact/" class="cta">お問い合わせ</a>'
        sample = f'<p class="sample-note" role="note">{e(c["sample_note"])}</p>' if c.get('sample_note') else ''
        latin = f'<span class="bk">{e(c["latin"])}</span>' if c.get('latin') else ''
        logo = f'<img class="mark" src="{r}{e(c["logo"])}" alt="" width="36" height="36">' if c.get('logo') else MARK_SVG
        crumb = ''
        if crumbs:
            lis = ''.join(f'<li><a href="{r}{e(p)}">{e(n)}</a></li>' if p is not None else f'<li>{e(n)}</li>' for p, n in crumbs)
            crumb = f'<div class="wrap"><ol class="crumb" aria-label="現在地"><li><a href="{r}">トップ</a></li>{lis}</ol></div>'
        # 頭：ページごとの title・description・og。url_base があれば canonical（トップだけ LINE のカードの番号 ?v=）
        full_title = e(title) + ('' if depth == 0 else f'｜{e(self.name)}')
        if depth == 0: full_title = e(self.name) + (f'｜{e(c["title_place"])}' if c.get('title_place') else '')
        og_img = og_image or c.get('og_image', '')
        og = ''
        card_js = ''
        if self.base:
            url = self.base.rstrip('/') + '/' + path
            if depth == 0:
                v = int(c.get('card_v', 1))
                og += f'<meta property="og:url" content="{e(url)}?v={v}">\n<link rel="canonical" href="{e(url)}?v={v}">\n'
                card_js = ms_card_js(v)
            else:
                og += f'<meta property="og:url" content="{e(url)}">\n<link rel="canonical" href="{e(url)}">\n'
            if og_img: og += f'<meta property="og:image" content="{e(self.base.rstrip("/") + "/" + og_img)}">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n<meta name="twitter:card" content="summary_large_image">\n'
        elif og_img:
            og += f'<meta property="og:image" content="{r}{e(og_img)}">\n'
        ld = ''
        if depth == 0:
            d = {"@context": "https://schema.org", "@type": c.get('schema_type', 'Organization'), "name": self.name}
            if self.base: d["url"] = self.base
            if self.tel: d["telephone"] = '+81-' + self.tel.lstrip('0')
            if c.get('address'): d["address"] = {"@type": "PostalAddress", "addressCountry": "JP", "streetAddress": c['address']}
            if c.get('founded'): d["foundingDate"] = str(c['founded'])
            ld = f'<script type="application/ld+json">\n{json.dumps(d, ensure_ascii=False)}\n</script>\n'
        tok = str(c.get('analytics_token') or '').strip()
        analytics = ('<!-- Cloudflare Web Analytics --><script defer src=\'https://static.cloudflareinsights.com/beacon.min.js\' data-cf-beacon=\'{"token": "' + e(tok) + '"}\'></script><!-- End Cloudflare Web Analytics -->') if tok else ''
        css = CSS
        for k, v in t.items(): css = css.replace('{{' + k + '}}', v)
        logo = logo.replace('{{primary}}', t['primary']).replace('{{accent_soft}}', t['accent_soft'])
        head_font = 'var(--mincho)' if c.get('font') == 'mincho' else 'var(--gothic)'
        css = css.replace('{{head_font}}', head_font)
        js = ms.JS + ('\n' + ms.PARTS_JS['form'] if 'id="cform"' in body else '')
        foot_nav1 = ''.join(f'<a href="{r}{e(p)}">{e(n)}</a>' for p, n in self.nav_items()[:4])
        foot_nav2 = ''.join(f'<a href="{r}{e(p)}">{e(n)}</a>' for p, n in self.nav_items()[4:])
        if 'contact' in self.P: foot_nav2 += f'<a href="{r}contact/">お問い合わせ</a>'
        if 'privacy' in self.P: foot_nav2 += f'<a href="{r}privacy/">プライバシーポリシー</a>'
        lic = ''.join(f'<p class="lic">{e(x)}</p>' for x in c.get('licenses', []))
        bar = []
        if self.tel: bar.append(f'<a href="tel:{self.tel_d}">電話する</a>')
        if 'contact' in self.P: bar.append(f'<a class="c" href="{r}contact/">お問い合わせ</a>')
        elif c.get('line_url'): bar.append(f'<a class="c" {ms.ext(c["line_url"])}>LINEで相談</a>')
        spbar = f'<nav class="spbar n{len(bar)}" aria-label="お問い合わせ">{"".join(bar)}</nav>' if bar else ''
        return f'''<!DOCTYPE html>
<html lang="ja" class="no-js">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{e(desc)}">
<!-- 本公開前は検索に出さない設定。本公開のときに tools/launch.py で外す -->
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="{t['primary_deep']}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(self.name)}">
<meta property="og:title" content="{full_title}">
<meta property="og:description" content="{e(desc)}">
{og}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Shippori+Mincho+B1:wght@500;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
{ld}<style>
{css}
</style>
<script>document.documentElement.className = 'js';</script>{card_js}
</head>
<body>
<!-- このページは tools/make_site.py（法人の型 make_houjin.py）で作った（設定：{e(c.get('slug', ''))}.json）。直すときは設定を直して作り直す -->{sample}
<header class="head">
  <div class="wrap">
    <a href="{r if depth else './'}" class="brand" aria-label="{e(self.short)} トップへ">{logo}<span class="bn">{e(self.short)}{latin}</span></a>
    <nav class="nav" id="gnav" aria-label="サイトの案内">{nav}</nav>
    <button type="button" class="menubtn" aria-expanded="false" aria-controls="gnav"><i aria-hidden="true"></i>メニュー</button>
  </div>
</header>
<main id="top">{crumb}{body}
</main>
<footer class="foot">
  <div class="wrap">
    <div class="cols">
      <div>
        <p class="fname">{e(self.name)}</p>
        {f'<p>{e(c["address"])}</p>' if c.get('address') else ''}
        {f'<p>TEL <a href="tel:{self.tel_d}">{e(self.tel)}</a>{("　受付 " + e(c["tel_hours"])) if c.get("tel_hours") else ""}</p>' if self.tel else ''}
        {lic}
      </div>
      <nav aria-label="フッター">{foot_nav1}</nav>
      <nav aria-label="フッター2">{foot_nav2}</nav>
    </div>
    <p class="copy">© {e(c.get('copyright', self.name))}</p>
  </div>
</footer>
{spbar}
<a class="totop" href="#top" aria-label="ページの上へ">↑</a>
<script>
{js}
</script>
{analytics}
</body>
</html>
'''

    def write(self, path, s, title):
        p = os.path.join(self.out, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(s)
        self.written.append((path, title))

    # ---------- 小さな部品 ----------
    def sec_head(self, key, title, more=None, center=False):
        m = f'<a class="more" href="{e(more[0])}">{e(more[1])}</a>' if more else ''
        return f'<div class="sec-head{" center" if center else ""}">{m}<i>{e(EYEBROW.get(key, key))}</i><h2>{e(title)}</h2></div>'

    def page_head(self, key, title):
        return f'<div class="page-head"><div class="wrap"><i>{e(EYEBROW.get(key, key))}</i><h1>{e(title)}</h1></div></div>'

    def img(self, o, depth, alt='', w=1200, h=800, lazy=True):
        if not o or not o.get('image'): return ''
        return f'<img src="{self.rel(depth)}{e(o["image"])}" alt="{e(o.get("alt") or alt)}" width="{o.get("w", w)}" height="{o.get("h", h)}"{" loading=lazy" if lazy else ""}>'

    def contact_band(self, depth, title='お問い合わせ・お見積もり', lead=None):
        c, r = self.c, self.rel(depth)
        if 'contact' not in self.P and not self.tel: return ''
        lead = lead if lead is not None else (self.P.get('contact') or {}).get('band_lead', '')
        tel = f'<a class="tel" href="tel:{self.tel_d}">{e(self.tel)}<small>{("受付 " + e(c["tel_hours"])) if c.get("tel_hours") else ""}</small></a>' if self.tel else ''
        btn = f'<a class="btn btn-navy" href="{r}contact/">フォームで問い合わせる<span class="ar">→</span></a>' if 'contact' in self.P and depth >= 0 and self.P['contact'].get('form') is not None else ''
        return f'''
  <section class="sec contact-band" id="contact">
    <div class="wrap">
      <div>{self.sec_head('contact', title)}{f'<p>{e(lead)}</p>' if lead else ''}</div>
      <div class="telbox">{tel}{btn}</div>
    </div>
  </section>'''

    def faq_html(self, items):
        if not items: return ''
        return '<div class="faq-list">' + ''.join(f'<details><summary><span class="q">Q</span><span>{e(f["q"])}</span></summary><p><span class="a">A</span><span>{e(f["a"])}</span></p></details>' for f in items) + '</div>'

    # ---------- お知らせ・実績の「1件」を HTML にする（静的ページと _tpl で同じ関数） ----------
    def news_li(self, it, depth, big=False):
        r = self.rel(depth)
        d = it.get('date', '')
        iso = _iso(d)
        dt = f'<time{f" datetime={chr(34)}{iso}{chr(34)}" if iso else ""}>{e(d)}</time>' if d else ''
        cat = f'<span class="cat">{e(it["cat"])}</span>' if it.get('cat') else ''
        href = it.get('_href') or f'{r}news/{e(it["id"])}/'
        ex = f'<span class="ex">{e(it["ex"])}</span>' if (big and it.get('ex')) else ''
        return f'<li>{dt}{cat}<span class="nt"><a href="{href}">{e(it["title"])}</a></span>{ex}</li>'

    def work_card(self, it, depth):
        r = self.rel(depth)
        href = it.get('_href') or f'{r}works/{e(it["id"])}/'
        cat = f'<span class="cat">{e(it["cat"])}</span>' if it.get('cat') else ''
        meta = ''
        if it.get('place') or it.get('ym'): meta = f'<span class="meta">{f"<b>{e(it[chr(112)+chr(108)+chr(97)+chr(99)+chr(101)])}</b>" if it.get("place") else ""}{e(it.get("ym", ""))}</span>'
        tags = ''.join(f'<span>{e(x)}</span>' for x in it.get('tags', []))
        img = self.img(it, depth, alt=it.get('title', ''), w=1200, h=800) if it.get('image') else '<span class="noimg">写真はありません</span>'
        return f'<a class="wcard" href="{href}"><div class="ph">{img}{cat}</div><div class="bd"><h3>{e(it["title"])}</h3>{meta}{f"<div class={chr(34)}tags tg{chr(34)}>{tags}</div>" if tags else ""}</div></a>'

    # ---------- トップ ----------
    def build_top(self):
        c, P, r = self.c, self.P, ''
        depth = 0
        hero = c.get('hero') or {}
        btns = []
        if 'contact' in P: btns.append('<a class="btn btn-main" href="contact/">お問い合わせ・お見積もり<span class="ar">→</span></a>')
        elif self.tel: btns.append(f'<a class="btn btn-main" href="tel:{self.tel_d}">電話で問い合わせる</a>')
        if 'business' in P: btns.append('<a class="btn btn-line-w" href="business/">事業内容を見る</a>')
        hero_html = f'''
  <section class="hero">
    <div class="ph">{self.img(hero, 0, alt='トップの写真', w=1600, h=1000, lazy=False) if hero.get('image') else ''}</div>
    <div class="wrap">
      {f'<p class="eyebrow">{e(hero["eyebrow"])}</p>' if hero.get('eyebrow') else ''}
      <h1>{hero.get('catch_html') or e(hero.get('catch', self.name))}</h1>
      {f'<p class="lead">{e(hero["lead"])}</p>' if hero.get('lead') else ''}
      <div class="hero-btns">{''.join(btns)}</div>
    </div>
  </section>'''
        # お知らせの新着（目印のコメントの中だけ、2b の Worker が差しかえる）
        news_html = ''
        if 'news' in P and P['news'].get('items'):
            lim = int(P['news'].get('top_limit', 3))
            lis = ''.join(self.news_li(it, 0) for it in P['news']['items'][:lim])
            news_html = f'''
  <section class="news-strip" aria-labelledby="news-h">
    <div class="wrap">
      <div><h2 id="news-h"><i>News</i>{e(P['news'].get('title', 'お知らせ'))}</h2><a class="more" href="news/">お知らせ一覧へ</a></div>
      <ul class="news-list"><!--news:start-->{lis}<!--news:end--></ul>
    </div>
  </section>'''
        trust = ''
        if c.get('trust'):
            lis = ''.join(f'<li><b>{e(x["value"])}<small>{e(x.get("unit", ""))}</small></b><span>{e(x["label"])}</span></li>' for x in c['trust'][:4])
            trust = f'<section class="trust" aria-label="数字で見る{e(self.short)}"><div class="wrap"><ul class="n{min(len(c["trust"]), 4)}">{lis}</ul></div></section>'
        about = ''
        a = c.get('about')
        if a:
            ph = f'<div class="ph">{self.img(a, 0, alt=a.get("title", ""))}</div>' if a.get('image') else ''
            link = f'<a class="btn btn-line-n" href="company/">会社概要・沿革<span class="ar">→</span></a>' if 'company' in P else ''
            about = f'''
  <section class="sec about" id="about">
    <div class="wrap{' noimg' if not ph else ''}">
      <div>{self.sec_head('about', a.get('heading', f'{self.short}について'))}{f'<h3>{nl2br(a["title"])}</h3>' if a.get('title') else ''}{esc_lines(a.get('text'))}{link}</div>
      {ph}
    </div>
  </section>'''
        biz = ''
        B = P.get('business')
        if B and B.get('items'):
            cards = ''
            for i, it in enumerate(B['items'], 1):
                tags = ''.join(f'<span>{e(x)}</span>' for x in it.get('targets', []))
                ph = f'<div class="ph">{self.img(it, 0, alt=it["name"])}</div>' if it.get('image') else ''
                cards += f'<a class="card" href="business/#{e(it["id"])}">{ph}<div class="bd"><h3><small>{e(it.get("no", f"{i:02d}"))}</small>{e(it["name"])}</h3><p>{e(it.get("text", ""))}</p>{f"<div class={chr(34)}tags{chr(34)}>{tags}</div>" if tags else ""}</div><span class="go">くわしく →</span></a>'
            biz = f'''
  <section class="sec biz" id="business">
    <div class="wrap">
      {self.sec_head('business', B.get('title', '事業内容'), ('business/', '事業内容をくわしく'))}
      <div class="cards n{min(len(B['items']), 4)}">{cards}</div>
    </div>
  </section>'''
        works = ''
        W = P.get('works')
        if W and W.get('items'):
            lim = int(W.get('top_limit', 3))
            cards = ''.join(self.work_card(it, 0) for it in W['items'][:lim])
            works = f'''
  <section class="sec works-sec" id="works">
    <div class="wrap">
      {self.sec_head('works', W.get('title', '施工実績'), ('works/', '施工実績の一覧へ'))}
      <div class="wcards"><!--works:start-->{cards}<!--works:end--></div>
    </div>
  </section>'''
        rec = ''
        R = P.get('recruit')
        if R:
            bg = f'<div class="bgph">{self.img(R, 0, alt="")}</div>' if R.get('image') else ''
            rec = f'''
  <section class="recruit" id="recruit">
    {bg}
    <div class="wrap">
      <p class="eyebrow">Recruit</p>
      <h2>{e(R.get('top_title', '一緒に働く仲間を募集しています'))}</h2>
      {f'<p>{e(R["top_text"])}</p>' if R.get('top_text') else ''}
      <a class="btn btn-main" href="recruit/">募集要項を見る<span class="ar">→</span></a>
    </div>
  </section>'''
        body = hero_html + news_html + trust + about + biz + works + rec + self.contact_band(0)
        desc = c.get('description', (hero.get('lead') or ''))
        self.write('index.html', self.page(0, '', self.name, desc, body, current='', og_image=c.get('og_image')), 'トップ')

    # ---------- 事業内容 ----------
    def build_business(self):
        B = self.P.get('business')
        if not B: return
        d = 1
        secs = ''
        for i, it in enumerate(B.get('items', []), 1):
            ph = f'<div class="ph">{self.img(it, d, alt=it["name"])}</div>' if it.get('image') else ''
            tags = ''.join(f'<span>{e(x)}</span>' for x in it.get('targets', []))
            subs = ''.join(f'<li>{e(x)}</li>' for x in it.get('items', []))
            secs += f'''
      <article class="bizsec" id="{e(it["id"])}">
        {ph}
        <div class="bd">
          <h2><small>{e(it.get("no", f"{i:02d}"))}</small>{e(it["name"])}</h2>
          {f'<div class="tags">{tags}</div>' if tags else ''}
          {esc_lines(it.get('body') or it.get('text'))}
          {f'<ul class="subs">{subs}</ul>' if subs else ''}
        </div>
      </article>'''
        flow = ''
        if B.get('flow'):
            steps = ''.join(f'<li><h3>{e(s["title"])}</h3><p>{e(s.get("text", ""))}</p></li>' for s in B['flow'])
            flow = f'''
  <section class="sec flow" id="flow">
    <div class="wrap">{self.sec_head('business', B.get('flow_title', 'ご依頼の流れ'), center=True)}<ol class="steps">{steps}</ol></div>
  </section>'''
        body = self.page_head('business', B.get('title', '事業内容')) + f'''
  <section class="sec tight">
    <div class="wrap">
      {f'<p class="lead-p">{e(B["lead"])}</p>' if B.get('lead') else ''}
      <div class="bizlist">{secs}</div>
      {f'<p class="note-p muted">{e(B["note"])}</p>' if B.get('note') else ''}
    </div>
  </section>''' + flow + self.contact_band(d, lead=B.get('contact_lead'))
        self.write('business/index.html', self.page(d, 'business/', B.get('title', '事業内容'), B.get('description', f'{self.name}の事業内容'), body, current='business', og_image=self.c.get('og_image'), crumbs=[(None, B.get('title', '事業内容'))]), '事業内容')

    # ---------- 実績（一覧・1件・_tpl） ----------
    def build_works(self):
        W = self.P.get('works')
        if not W: return
        items = [it for it in W.get('items', []) if it.get('id') and it.get('title')]
        title = W.get('title', '施工実績')
        cats = W.get('categories') or sorted({it['cat'] for it in items if it.get('cat')})
        per = int(W.get('per_page', 12))

        def list_page(cards_html, count_text, pager_html, depth=1, href_all='./'):
            fl = f'<li><span class="chip all">すべて {len(items)}件</span></li>' + ''.join(f'<li><span class="chip">{e(cat)}（{sum(1 for it in items if it.get("cat") == cat)}）</span></li>' for cat in cats)
            return self.page_head('works', title) + f'''
  <section class="sec tight">
    <div class="wrap">
      {f'<p class="lead-p">{e(W["lead"])}</p>' if W.get('lead') else ''}
      {f'<ul class="filter" aria-label="施工場所の内わけ（件数）">{fl}</ul>' if cats else ''}
      <p class="count">{count_text}</p>
      <div class="wcards">{cards_html}</div>
      {pager_html}
    </div>
  </section>''' + self.contact_band(depth, title=W.get('contact_title', '同じような工事のご相談'), lead=W.get('contact_lead'))
        # 一覧（12件ずつ。2ページ目からは works/page/2/）
        pages = [items[i:i + per] for i in range(0, len(items), per)] or [[]]
        for n, chunk in enumerate(pages, 1):
            depth = 1 if n == 1 else 3
            path = 'works/' if n == 1 else f'works/page/{n}/'
            cards = ''.join(self.work_card(it, depth) for it in chunk)
            first = (n - 1) * per + 1
            count = f'{len(items)}件中 {first}〜{first + len(chunk) - 1}件を表示' if items else '実績はまだありません'
            pager = ''
            if len(pages) > 1:
                lis = ''
                for k in range(1, len(pages) + 1):
                    href = (self.rel(depth) + 'works/') if k == 1 else (self.rel(depth) + f'works/page/{k}/')
                    lis += f'<li><span aria-current="page">{k}</span></li>' if k == n else f'<li><a href="{href}">{k}</a></li>'
                pager = f'<ul class="pager" aria-label="ページ">{lis}</ul>'
            crumbs = [(None, title)] if n == 1 else [('works/', title), (None, f'{n}ページ目')]
            self.write(path + 'index.html', self.page(depth, path, title if n == 1 else f'{title}（{n}ページ目）', W.get('description', f'{self.name}の{title}'), list_page(cards, count, pager, depth, href_all=self.rel(depth) + 'works/'), current='works', og_image=self.c.get('og_image'), crumbs=crumbs), f'{title} {n}')
        # 1件
        for i, it in enumerate(items):
            prev_it = items[i - 1] if i > 0 else None
            next_it = items[i + 1] if i + 1 < len(items) else None
            self.write(f'works/{it["id"]}/index.html', self.work_item_page(it, prev_it, next_it, W), it['title'])
        # 2b の Worker 用のひな形（同じ関数に差し込みの印を渡す）
        ph = dict(id='{{id}}', title='{{title}}', cat='{{cat}}', place='{{place}}', ym='{{ym}}', tags=['{{tags}}'], image='{{image}}', alt='{{alt}}', body=['{{body}}'], images=[], _href='{{href}}')
        self.write('_tpl/works_card.html', self.work_card(ph, 1), '_tpl')
        self.write('_tpl/works_list.html', self.page(1, 'works/', title, W.get('description', ''), list_page('{{items}}', '{{count}}', '{{pager}}'), current='works', crumbs=[(None, title)]), '_tpl')
        self.write('_tpl/works_item.html', self.work_item_page(ph, {'id': '{{prev_id}}', 'title': '{{prev_title}}'}, {'id': '{{next_id}}', 'title': '{{next_title}}'}, W, tpl=True), '_tpl')

    def work_item_page(self, it, prev_it, next_it, W, tpl=False):
        d = 2
        r = self.rel(d)
        title = W.get('title', '施工実績')
        meta = []
        if it.get('cat'): meta.append((W.get('cat_label', '種別'), it['cat']))
        if it.get('place'): meta.append(('場所', it['place']))
        if it.get('ym'): meta.append(('時期', it['ym']))
        for k, v in it.get('rows', []): meta.append((k, v))
        dl = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in meta)
        tags = ''.join(f'<span>{e(x)}</span>' for x in it.get('tags', []))
        main_img = f'<figure class="wmain">{self.img(it, d, alt=it["title"], lazy=False)}</figure>' if it.get('image') else ''
        figs = ''
        for im in it.get('images', []):
            cap = f'<figcaption>{e(im["caption"])}</figcaption>' if im.get('caption') else ''
            figs += f'<figure>{self.img(im, d, alt=im.get("alt", ""))}{cap}</figure>'
        if tpl: figs = '{{images}}'
        body_html = '{{body}}' if tpl else esc_lines(it.get('body'))
        pn = ''
        if prev_it: pn += f'<a class="pn prev" href="{r}works/{e(prev_it["id"])}/"><small>前の実績</small>{e(prev_it["title"])}</a>'
        if next_it: pn += f'<a class="pn next" href="{r}works/{e(next_it["id"])}/"><small>次の実績</small>{e(next_it["title"])}</a>'
        if tpl: pn = '{{prevnext}}'
        body = self.page_head('works', it['title']) + f'''
  <section class="sec tight item">
    <div class="wrap narrow">
      {f'<div class="tags">{tags}</div>' if tags else ''}
      {main_img}
      {f'<dl class="meta">{dl}</dl>' if dl else ''}
      <div class="body">{body_html}</div>
      {f'<div class="figs">{figs}</div>' if figs else ''}
      <div class="pn-wrap">{pn}</div>
      <p class="back"><a href="{r}works/">← {e(title)}の一覧へ</a></p>
    </div>
  </section>''' + self.contact_band(d, title=W.get('contact_title', '同じような工事のご相談'), lead=W.get('contact_lead'))
        return self.page(d, f'works/{it["id"]}/', it['title'], first_line(it.get('body')) if not tpl else '{{description}}', body, current='works', og_image=it.get('og_image') or it.get('image') or self.c.get('og_image'), crumbs=[('works/', title), (None, it['title'])])

    # ---------- お知らせ（一覧・1件・_tpl） ----------
    def build_news(self):
        N = self.P.get('news')
        if not N: return
        items = [it for it in N.get('items', []) if it.get('id') and it.get('title')]
        title = N.get('title', 'お知らせ')
        years = []
        for it in items:
            y = (_iso(it.get('date', '')) or '')[:4]
            if y and y not in years: years.append(y)
        cats = N.get('categories') or sorted({it['cat'] for it in items if it.get('cat')})

        def list_page(content_html, depth=1):
            yn = ''.join(f'<li><span class="chip">{e(y)}</span></li>' for y in years)
            fl = ''.join(f'<li><span class="chip">{e(cat)}</span></li>' for cat in cats)
            return self.page_head('news', title) + f'''
  <section class="sec tight">
    <div class="wrap">
      {f'<p class="lead-p">{e(N["lead"])}</p>' if N.get('lead') else ''}
      {f'<ul class="year-nav" aria-label="年">{yn}</ul>' if years else ''}
      {f'<ul class="filter" aria-label="分類">{fl}</ul>' if cats else ''}
      {content_html}
    </div>
  </section>''' + self.contact_band(depth)
        # 年ごとに見出し＋一覧
        groups = []
        for it in items:
            y = (_iso(it.get('date', '')) or '')[:4] or 'その他'
            if not groups or groups[-1][0] != y: groups.append((y, []))
            groups[-1][1].append(it)
        inner = ''.join(f'<h2 class="news-year">{e(y)}</h2><ul class="news-list news-big">' + ''.join(self.news_li(it, 1, big=True) for it in its) + '</ul>' for y, its in groups)
        if not items: inner = '<p class="count">お知らせはまだありません</p>'
        page_body = list_page(inner)
        self.write('news/index.html', self.page(1, 'news/', title, N.get('description', f'{self.name}からの{title}'), page_body, current='news', og_image=self.c.get('og_image'), crumbs=[(None, title)]), title)
        for i, it in enumerate(items):
            prev_it = items[i - 1] if i > 0 else None
            next_it = items[i + 1] if i + 1 < len(items) else None
            self.write(f'news/{it["id"]}/index.html', self.news_item_page(it, prev_it, next_it, N), it['title'])
        ph = dict(id='{{id}}', title='{{title}}', cat='{{cat}}', date='{{date}}', ex='{{ex}}', body=['{{body}}'], _href='{{href}}')
        self.write('_tpl/news_li.html', self.news_li(ph, 1, big=True), '_tpl')
        self.write('_tpl/news_list.html', self.page(1, 'news/', title, N.get('description', ''), list_page('{{items}}'), current='news', crumbs=[(None, title)]), '_tpl')  # {{items}} には <h2 class="news-year">年</h2><ul class="news-list news-big">news_li…</ul> を年ごとに並べる
        self.write('_tpl/news_item.html', self.news_item_page(ph, {'id': '{{prev_id}}', 'title': '{{prev_title}}'}, {'id': '{{next_id}}', 'title': '{{next_title}}'}, N, tpl=True), '_tpl')

    def news_item_page(self, it, prev_it, next_it, N, tpl=False):
        d = 2
        r = self.rel(d)
        title = N.get('title', 'お知らせ')
        dt = it.get('date', '')
        iso = _iso(dt)
        head = f'<p class="nmeta">{f"<time datetime={chr(34)}{iso}{chr(34)}>{e(dt)}</time>" if dt else ""}{f"<span class={chr(34)}cat{chr(34)}>{e(it[chr(99)+chr(97)+chr(116)])}</span>" if it.get("cat") else ""}</p>'
        img = f'<figure class="wmain">{self.img(it, d, alt=it["title"], lazy=False)}</figure>' if it.get('image') else ('{{image}}' if tpl else '')
        body_html = '{{body}}' if tpl else esc_lines(it.get('body') or it.get('ex'))
        pn = ''
        if prev_it: pn += f'<a class="pn prev" href="{r}news/{e(prev_it["id"])}/"><small>前のお知らせ</small>{e(prev_it["title"])}</a>'
        if next_it: pn += f'<a class="pn next" href="{r}news/{e(next_it["id"])}/"><small>次のお知らせ</small>{e(next_it["title"])}</a>'
        if tpl: pn = '{{prevnext}}'
        body = self.page_head('news', it['title']) + f'''
  <section class="sec tight item">
    <div class="wrap narrow">
      {head}
      {img}
      <div class="body">{body_html}</div>
      <div class="pn-wrap">{pn}</div>
      <p class="back"><a href="{r}news/">← {e(title)}の一覧へ</a></p>
    </div>
  </section>''' + self.contact_band(d)
        return self.page(d, f'news/{it["id"]}/', it['title'], (it.get('ex') or first_line(it.get('body'))) if not tpl else '{{description}}', body, current='news', og_image=it.get('image') or self.c.get('og_image'), crumbs=[('news/', title), (None, it['title'])])

    # ---------- 会社概要・沿革 ----------
    def build_company(self):
        C = self.P.get('company')
        if not C: return
        d = 1
        c = self.c
        rows = list(C.get('rows', []))
        if not rows:
            rows = [('社名', self.name), ('所在地', c.get('address')), ('電話', self.tel)]
        dl = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in rows if v)
        hist = ''.join(f'<li><time>{e(y)}</time><span>{e(x)}</span></li>' for y, x in C.get('history', []))
        mq = c.get('map_query')
        route = f'<a class="route" {ms.ext("https://www.google.com/maps/dir/?api=1&destination=" + urllib.parse.quote(mq))}>{ms.PIN}Googleマップで<wbr>道順を見る</a>' if mq and c.get('show_route', True) else ''
        mapf = f'<div class="map"><iframe src="https://maps.google.com/maps?q={urllib.parse.quote(mq)}&amp;z=15&amp;output=embed" title="{e(self.short)}の地図" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>' if mq and c.get('show_map', True) else ''
        g = C.get('greeting')
        greet = ''
        if g:
            ph = f'<div class="ph">{self.img(g, d, alt=g.get("name", ""))}</div>' if g.get('image') else ''
            greet = f'''
  <section class="sec greet" id="greeting">
    <div class="wrap{' noimg' if not ph else ''}">
      {ph}
      <div>{self.sec_head('company', g.get('heading', 'ごあいさつ'))}{f'<h3>{nl2br(g["title"])}</h3>' if g.get('title') else ''}{esc_lines(g.get('text'))}{f'<p class="sign">{e(g.get("role", ""))} {e(g["name"])}</p>' if g.get('name') else ''}</div>
    </div>
  </section>'''
        body = self.page_head('company', C.get('title', '会社概要')) + f'''
  <section class="sec tight" id="outline">
    <div class="wrap">
      {self.sec_head('company', C.get('outline_title', '会社概要'))}
      <dl class="info">{dl}</dl>
    </div>
  </section>
  {f'<section class="sec history" id="history"><div class="wrap">{self.sec_head("company", C.get("history_title", "沿革"))}<ol class="hist">{hist}</ol></div></section>' if hist else ''}
  {greet}
  <section class="sec access" id="access">
    <div class="wrap{' nomap' if not mapf else ''}">
      <div>{self.sec_head('company', C.get('access_title', 'アクセス'))}{f'<p>{e(c["address"])}</p>' if c.get('address') else ''}{f'<p class="muted">{e(C["access_note"])}</p>' if C.get('access_note') else ''}{route}</div>
      {mapf}
    </div>
  </section>''' + self.contact_band(d)
        self.write('company/index.html', self.page(d, 'company/', C.get('title', '会社概要'), C.get('description', f'{self.name}の会社概要・沿革'), body, current='company', og_image=c.get('og_image'), crumbs=[(None, C.get('title', '会社概要'))]), '会社概要')

    # ---------- 採用 ----------
    def build_recruit(self):
        R = self.P.get('recruit')
        if not R: return
        d = 1
        pts = ''
        if R.get('points'):
            pts = '<ol class="why n%d">' % min(len(R['points']), 4) + ''.join(f'<li><span class="no">{n:02d}</span><h3>{e(p["title"])}</h3>{f"<p>{e(p[chr(116)+chr(101)+chr(120)+chr(116)])}</p>" if p.get("text") else ""}</li>' for n, p in enumerate(R['points'][:4], 1)) + '</ol>'
        jobs = ''
        for j in R.get('jobs', []):
            dl = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in j.get('rows', []) if v)
            jobs += f'<article class="job" id="{e(j.get("id", ""))}"><h3>{e(j["title"])}</h3><dl class="info">{dl}</dl></article>'
        ap = R.get('apply') or {}
        ways = []
        if ap.get('tel', True) and self.tel: ways.append(f'<div class="way"><h3>お電話</h3><p>{e(ap.get("tel_text", "採用担当あてにお電話ください。"))}</p><a class="tel" href="tel:{self.tel_d}">{e(self.tel)}</a></div>')
        if ap.get('email'): ways.append(f'<div class="way"><h3>メール</h3><p>{e(ap.get("email_text", "お名前・ご連絡先・希望の職種を書いてお送りください。"))}</p><a class="btn btn-navy" href="mailto:{e(ap["email"])}">{e(ap["email"])}</a></div>')
        if ap.get('form_url'): ways.append(f'<div class="way"><h3>応募フォーム</h3><p>{e(ap.get("form_text", "フォームからもご応募いただけます。"))}</p><a class="btn btn-navy" {ms.ext(ap["form_url"])}>応募フォームを開く</a></div>')
        if 'contact' in self.P and not ways: ways.append(f'<div class="way"><h3>お問い合わせフォーム</h3><p>ご用件で「採用について」を選んでお送りください。</p><a class="btn btn-navy" href="{self.rel(d)}contact/">お問い合わせへ</a></div>')
        faq = self.faq_html(R.get('faq'))
        body = self.page_head('recruit', R.get('title', '採用情報')) + f'''
  <section class="sec tight">
    <div class="wrap">
      {f'<p class="lead-p">{e(R["lead"])}</p>' if R.get('lead') else ''}
      {pts}
    </div>
  </section>
  {f'<section class="sec jobs" id="jobs"><div class="wrap">{self.sec_head("recruit", R.get("jobs_title", "募集要項"))}<div class="joblist">{jobs}</div>{f"<p class={chr(34)}note-p muted{chr(34)}>{e(R[chr(106)+chr(111)+chr(98)+chr(115)+chr(95)+chr(110)+chr(111)+chr(116)+chr(101)])}</p>" if R.get("jobs_note") else ""}</div></section>' if jobs else ''}
  {f'<section class="sec faq" id="faq"><div class="wrap">{self.sec_head("recruit", "よくあるご質問", center=True)}{faq}</div></section>' if faq else ''}
  <section class="sec apply" id="apply">
    <div class="wrap">{self.sec_head('recruit', ap.get('title', 'ご応募・お問い合わせ'))}{f'<p>{e(ap["lead"])}</p>' if ap.get('lead') else ''}<div class="ways n{len(ways)}">{''.join(ways)}</div>{f'<p class="note-p muted">{e(ap["privacy_note"])}</p>' if ap.get('privacy_note') else ''}</div>
  </section>'''
        self.write('recruit/index.html', self.page(d, 'recruit/', R.get('title', '採用情報'), R.get('description', f'{self.name}の採用情報・募集要項'), body, current='recruit', og_image=R.get('og_image') or self.c.get('og_image'), crumbs=[(None, R.get('title', '採用情報'))]), '採用情報')

    # ---------- お問い合わせ ----------
    def build_contact(self):
        K = self.P.get('contact')
        if K is None: return
        d = 1
        c = self.c
        ways = []
        if self.tel: ways.append(f'<div class="way"><h3>お電話</h3><p>{e(K.get("tel_text", "受付時間内におかけください。現場に出ていて出られないときは折り返します。"))}</p><a class="tel" href="tel:{self.tel_d}">{e(self.tel)}</a>{f"<small>受付 {e(c[chr(116)+chr(101)+chr(108)+chr(95)+chr(104)+chr(111)+chr(117)+chr(114)+chr(115)])}</small>" if c.get("tel_hours") else ""}</div>')
        if c.get('email'): ways.append(f'<div class="way"><h3>メール</h3><p>{e(K.get("email_text", "図面や写真を添えて送れます。"))}</p><a class="btn btn-navy" href="mailto:{e(c["email"])}">{e(c["email"])}</a></div>')
        if c.get('line_url'): ways.append(f'<div class="way"><h3>LINE</h3><p>{e(c.get("line_text", "写真を送ってご相談いただけます。"))}</p><a class="btn btn-line" {ms.ext(c["line_url"])}>{ms.LINE_ICON}友だち追加</a></div>')
        form = ''
        F = K.get('form')
        if F is not None:
            F = F or {}
            endpoint = F.get('endpoint') or ''
            if not endpoint: print('⚠️ contact.form：送り先（endpoint。Formspree の URL）がまだありません。送るボタンを押すと「準備中」と出ます')
            topics = F.get('topics') or ['お見積もりの依頼', '工事のご相談', '保守・点検について', '採用について', 'そのほか']
            chips = ''.join(f'<label class="chip"><input type="radio" name="ご用件" value="{e(v)}"><span>{e(v)}</span></label>' for v in topics)
            form = f'''
      <div class="formbox" id="form">
        <div class="form-top"><span>{e(F.get("title", "お問い合わせフォーム"))}</span><span class="form-sub">{e(F.get("sub", "24時間受付"))}</span></div>
        <form id="cform" action="{e(endpoint)}" method="POST" data-endpoint="{e(endpoint)}">
          <p class="form-lead">{e(F.get("lead", "下の欄に入れて送るだけで大丈夫です。内容を確かめて、こちらからご連絡します。"))}</p>
          <label class="f-row"><span>会社名・団体名<span class="opt-label">個人の方は空欄で可</span></span><input name="会社名" autocomplete="organization"></label>
          <label class="f-row"><span>お名前<span class="req">必須</span></span><input name="お名前" required autocomplete="name"></label>
          <label class="f-row"><span>ご連絡先（電話番号かメール）<span class="req">必須</span></span><input name="ご連絡先" required autocomplete="tel" placeholder="例：0835-00-0000"></label>
          <fieldset><legend>ご用件</legend><div class="chips">{chips}</div></fieldset>
          <label class="f-row"><span>ご相談の内容<span class="opt-label">分かる範囲で</span></span><textarea name="ご相談の内容" placeholder="例：工場の給水配管から水もれ。来週中に見てほしい"></textarea></label>
          <input type="hidden" name="_subject" value="【{e(self.name)}】ホームページからのお問い合わせ">
          <input type="text" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true" class="gotcha">
          <button class="btn btn-main" type="submit">この<wbr>内容で<wbr>送る</button>
          <p class="formnote" id="formnote" role="status">{e(F.get("note", "送信後、こちらから折り返しご連絡します。"))}</p>
          <p class="formnote">{e(F.get("privacy", "いただいた内容は、お問い合わせへの返事のためだけに使います。"))}{f' <a href="{self.rel(d)}privacy/">プライバシーポリシー</a>' if 'privacy' in self.P else ''}</p>
        </form>
      </div>'''
        faq = self.faq_html(K.get('faq'))
        body = self.page_head('contact', K.get('title', 'お問い合わせ')) + f'''
  <section class="sec tight">
    <div class="wrap">
      {f'<p class="lead-p">{e(K["lead"])}</p>' if K.get('lead') else ''}
      <div class="ways n{len(ways)}">{''.join(ways)}</div>
      {form}
    </div>
  </section>
  {f'<section class="sec faq" id="faq"><div class="wrap">{self.sec_head("contact", "よくあるご質問", center=True)}{faq}</div></section>' if faq else ''}'''
        self.write('contact/index.html', self.page(d, 'contact/', K.get('title', 'お問い合わせ'), K.get('description', f'{self.name}へのお問い合わせ・お見積もりのご依頼'), body, current='contact', og_image=c.get('og_image'), crumbs=[(None, K.get('title', 'お問い合わせ'))]), 'お問い合わせ')

    # ---------- プライバシーポリシー ----------
    def build_privacy(self):
        V = self.P.get('privacy')
        if V is None: return
        V = V or {}
        d = 1
        c = self.c
        items = V.get('items') or [
            ('取得する情報', 'お問い合わせ・ご応募のときにいただく、お名前・ご連絡先（電話番号・メールアドレス）・会社名・ご相談の内容。'),
            ('使いみち', 'お問い合わせへの返事、お見積もりとご連絡、採用の選考のためだけに使います。ほかの目的には使いません。'),
            ('第三者への提供', 'ご本人の同意がある場合と、法令で求められた場合を除き、第三者に渡しません。'),
            ('保存する期間', 'お問い合わせの内容は、用件が済んでから1年を目安に消します。ご応募の書類は、選考が終わってから相当の期間の後に返却または廃棄します。'),
            ('フォームの送信', 'ホームページのフォームは外部のフォーム送信サービスを通じて届きます。送信された内容はそのサービスの規約のもとで扱われます。'),
            ('アクセスの集計', 'ホームページの表示回数などを、個人を特定しない形で集計することがあります。'),
            ('お問い合わせ先', f'{self.name}' + (f'　TEL {self.tel}' if self.tel else '') + (f'　{c["email"]}' if c.get('email') else '')),
        ]
        secs = ''.join(f'<section><h2>{e(k)}</h2><p>{e(v)}</p></section>' for k, v in items)
        body = self.page_head('privacy', V.get('title', 'プライバシーポリシー')) + f'''
  <section class="sec tight">
    <div class="wrap narrow prose">
      <p class="lead-p">{e(V.get('lead', f'{self.name}（以下「当社」）は、お客さま・ご応募の方からお預かりする個人情報を、次のとおり扱います。'))}</p>
      {secs}
      {f'<p class="muted">制定日：{e(V["date"])}</p>' if V.get('date') else ''}
    </div>
  </section>'''
        self.write('privacy/index.html', self.page(d, 'privacy/', V.get('title', 'プライバシーポリシー'), f'{self.name}の個人情報の扱いについて', body, current='privacy', og_image=c.get('og_image'), crumbs=[(None, V.get('title', 'プライバシーポリシー'))]), 'プライバシーポリシー')

    # ---------- まとめて ----------
    def build_all(self):
        self.build_top(); self.build_business(); self.build_works(); self.build_news(); self.build_company(); self.build_recruit(); self.build_contact(); self.build_privacy()
        # sitemap.xml・robots.txt（url_base があるときだけ中身に住所が入る）
        pages = [p for p, _ in self.written if not p.startswith('_tpl/')]
        if self.base:
            b = self.base.rstrip('/')
            urls = ''.join(f'  <url><loc>{e(b + "/" + p[:-len("index.html")])}</loc></url>\n' for p in pages)
            open(os.path.join(self.out, 'sitemap.xml'), 'w', encoding='utf-8').write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
            open(os.path.join(self.out, 'robots.txt'), 'w', encoding='utf-8').write(f'User-agent: *\nAllow: /\nDisallow: /_tpl/\nSitemap: {b}/sitemap.xml\n')
        else:
            open(os.path.join(self.out, 'robots.txt'), 'w', encoding='utf-8').write('User-agent: *\nAllow: /\nDisallow: /_tpl/\n')
        # 2b 用の説明
        open(os.path.join(self.out, '_tpl', 'README.md'), 'w', encoding='utf-8').write(TPL_README)
        return pages


def ms_card_js(v):
    return f'''
<!-- LINE のカードの番号 ?v={v}（設定の card_v。og:url・canonical・この JS の3か所でそろえる） -->
<script>
(function(){{ try {{
  var q = location.search || '';
  if (/[?&]v=/.test(q)) return;
  history.replaceState(history.state, '', location.pathname + (q ? q + '&' : '?') + 'v={v}' + (location.hash || ''));
}} catch (e) {{}} }})();
</script>'''


def _iso(d):
    m = re.match(r'\s*(\d{4})\D+(\d{1,2})\D+(\d{1,2})', str(d or ''))
    return '%s-%02d-%02d' % (m.group(1), int(m.group(2)), int(m.group(3))) if m else ''


def first_line(b):
    """本文（文字列か配列）の最初の文を、説明文（description）に使う"""
    if isinstance(b, str): return b
    return (b or [''])[0]


def nl2br(s):
    return '<br>'.join(e(x) for x in str(s).split('\n'))


def build_404(c, t):
    """404 は make_site.py の build_404 を借り、お店向けの言葉（メニュー）だけ法人向けに置きかえる"""
    s = ms.build_404(dict(c, theme_base='salon', theme=t))
    return s.replace('href="/menu">メニューを<wbr>見る', 'href="/business/">事業内容を<wbr>見る')


TPL_README = '''# _tpl/（2b の CMS 用のひな形。make_houjin.py が作る。手で直さない）

- 見た目はここにしかない。直すときは tools/make_houjin.py を直して make_site.py で作り直す（静的のページと同時に変わる）
- Worker は、差し込みの印を記事の中身で置きかえるだけ（印：{{id}} {{title}} {{cat}} {{place}} {{ym}} {{tags}} {{image}} {{alt}} {{body}} {{images}} {{date}} {{ex}} {{href}} {{description}} {{items}} {{count}} {{pager}} {{prevnext}} {{prev_id}} {{prev_title}} {{next_id}} {{next_title}}）
- works_card.html・news_li.html … 一覧とトップの新着に並べる1件分。works_list.html・news_list.html … 一覧ページ（{{items}} に1件分を並べる）。works_item.html・news_item.html … 1件ページ
- トップ index.html の <!--news:start-->…<!--news:end--> と <!--works:start-->…<!--works:end--> の中だけを、Worker が news_li / works_card で作った最新3件で差しかえる
- {{body}} は Worker が <p>…</p> にして入れる（HTML は許さない。文字は必ずエスケープ）。{{tags}} は <span>…</span> の並び
- 検索エンジンに出さない：robots.txt で /_tpl/ を Disallow。公開しても中身は印だけ
'''


# ============================== 見た目（CSS）。色は {{primary}} などの印で、設定の theme から入れる ==============================
CSS = r'''/* 法人の型（make_houjin.py）。色は会社の色1つ＋差し色1つ＋黒白。角は小さく。古いスマホ対策：flex の gap・aspect-ratio・inset・svh を使わない。min()・clamp() の前に予備を1行 */
.nw{white-space:nowrap}
body{word-break:keep-all;overflow-wrap:anywhere;line-break:strict}
:root{
  --primary:{{primary}};--primary-deep:{{primary_deep}};--accent:{{accent}};--accent-soft:{{accent_soft}};--pale:{{pale}};
  --dark:{{dark}};--dark2:{{dark2}};--bg:{{bg}};--bg2:{{bg2}};--ink:{{ink}};--muted:{{muted}};--line:{{line}};
  --r:8px;
  --mincho:"Shippori Mincho B1","Hiragino Mincho ProN","Yu Mincho","Noto Serif CJK JP",serif;
  --gothic:"Zen Kaku Gothic New","Hiragino Sans","Yu Gothic","Noto Sans CJK JP",sans-serif;
  --latin:"Inter","Helvetica Neue",Arial,sans-serif;
  --head:{{head_font}};
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{-webkit-transition:none!important;transition:none!important;-webkit-animation:none!important;animation:none!important}}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--gothic);font-size:16px;line-height:1.9;letter-spacing:.04em}
img{max-width:100%;height:auto;display:block}
a{color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.wrap{width:92%;width:min(1140px,100% - 40px);margin-left:auto;margin-right:auto}
.wrap.narrow{max-width:800px}
h1,h2,h3,h4{font-family:var(--head);font-weight:700;margin:0;line-height:1.5}
p{margin:0 0 1.1em}
.muted{color:var(--muted)}
.center{text-align:center}
.sample-note{margin:0;padding:0 16px;height:32px;line-height:32px;background:#333;color:#fff;font-size:.76rem;text-align:center;letter-spacing:.04em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lead-p{max-width:40em;margin-bottom:28px}
.note-p{font-size:.9rem;margin-top:24px}
/* ボタン（角 6px の四角） */
.btn{display:-webkit-inline-box;display:-ms-inline-flexbox;display:inline-flex;-webkit-box-align:center;-ms-flex-align:center;align-items:center;-webkit-box-pack:center;-ms-flex-pack:center;justify-content:center;text-decoration:none;font-weight:700;letter-spacing:.08em;padding:.85em 1.7em;border-radius:6px;line-height:1.4;text-align:center;min-height:48px;-webkit-transition:background .2s,color .2s;transition:background .2s,color .2s;font:inherit;font-weight:700;cursor:pointer}
.btn svg{width:1.25em;height:1.25em;-ms-flex:none;flex:none;margin-right:.5em}
.btn-main{background:var(--accent);color:#fff;border:0}
.btn-main:hover{opacity:.9}
.btn-navy{background:var(--primary);color:#fff}
.btn-navy:hover{background:var(--primary-deep)}
.btn-line{background:#06c755;color:#fff}
.btn-line-w{border:2px solid #fff;color:#fff;background:transparent}
.btn-line-w:hover{background:#fff;color:var(--primary-deep)}
.btn-line-n{border:2px solid var(--primary);color:var(--primary-deep);background:#fff}
.btn-line-n:hover{background:var(--primary);color:#fff}
.btn .ar{display:inline-block;margin-left:.6em;font-family:var(--latin)}
/* ヘッダー（白地・上に固定） */
.head{position:-webkit-sticky;position:sticky;top:0;z-index:30;background:rgba(255,255,255,.96);border-bottom:1px solid var(--line)}
.head .wrap{display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-pack:justify;-ms-flex-pack:justify;justify-content:space-between;-webkit-box-align:center;-ms-flex-align:center;align-items:center;height:72px}
.brand{display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-align:center;-ms-flex-align:center;align-items:center;text-decoration:none;color:var(--primary-deep)}
.brand .mark{width:36px;height:36px;margin-right:10px;-ms-flex:none;flex:none;border-radius:4px}
.brand .bn{font-weight:700;font-size:1.1rem;letter-spacing:.1em;line-height:1.2}
.brand .bk{display:block;font-size:.66rem;font-weight:400;letter-spacing:.14em;color:var(--muted);font-family:var(--latin)}
.nav{display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-align:center;-ms-flex-align:center;align-items:center;font-size:.9rem}
.nav a{text-decoration:none;margin-left:26px;white-space:nowrap;padding:6px 0;border-bottom:2px solid transparent}
.nav a:hover,.nav a.on{border-bottom-color:var(--accent);color:var(--primary-deep)}
.nav .cta{background:var(--primary);color:#fff;padding:.55em 1.3em;border-radius:6px;border:0;margin-left:22px}
.nav .cta:hover{background:var(--primary-deep);color:#fff}
.menubtn{display:none}
@media (min-width:861px) and (max-width:1100px){.nav a{margin-left:16px;font-size:.84rem}.brand .bk{display:none}}
@media (max-width:860px){
  .head .wrap{height:60px}
  .nav a{display:none}
  .menubtn{display:-webkit-inline-box;display:-ms-inline-flexbox;display:inline-flex;-webkit-box-align:center;-ms-flex-align:center;align-items:center;background:#fff;color:var(--primary-deep);border:1px solid var(--line);border-radius:6px;padding:.5em .9em;font:inherit;font-size:.8rem;font-weight:700;letter-spacing:.1em;cursor:pointer;min-height:44px}
  .menubtn i{display:block;width:16px;height:12px;border-top:2px solid currentColor;border-bottom:2px solid currentColor;position:relative;margin-right:8px}
  .menubtn i::after{content:"";position:absolute;left:0;right:0;top:3px;border-top:2px solid currentColor}
  .head.open .nav{display:-webkit-box;display:-ms-flexbox;display:flex;position:absolute;top:60px;left:0;right:0;-webkit-box-orient:vertical;-webkit-box-direction:normal;-ms-flex-direction:column;flex-direction:column;-webkit-box-align:stretch;-ms-flex-align:stretch;align-items:stretch;background:#fff;border-bottom:1px solid var(--line);padding:8px 16px 16px;box-shadow:0 14px 30px rgba(0,0,0,.12)}
  .head.open .nav a{display:block;margin:0;padding:.9em 4px;border-bottom:1px solid var(--line);font-size:.98rem}
  .head.open .nav a.on{color:var(--primary-deep);font-weight:700;border-bottom-color:var(--line)}
  .head.open .nav .cta{margin-top:12px;text-align:center;border-radius:6px;border-bottom:0}
}
/* トップの最初の画面（全幅の写真＋大きな見出し） */
.hero{position:relative;background:var(--dark);color:#fff;overflow:hidden;min-height:520px;height:84vh;max-height:860px}
.hero .ph{position:absolute;top:0;left:0;width:100%;height:100%}
.hero .ph img{width:100%;height:100%;-o-object-fit:cover;object-fit:cover;-o-object-position:center;object-position:center}
@media (max-width:860px){.hero .ph img{-o-object-position:68% center;object-position:68% center}}
.hero .ph::after{content:"";position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.45);background:-webkit-gradient(linear,left top,right top,from(rgba(0,0,0,.66)),color-stop(60%,rgba(0,0,0,.34)),to(rgba(0,0,0,.18)));background:linear-gradient(90deg,rgba(0,0,0,.66) 0%,rgba(0,0,0,.34) 60%,rgba(0,0,0,.18) 100%)}
.hero .wrap{position:relative;z-index:2;height:100%;display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-orient:vertical;-webkit-box-direction:normal;-ms-flex-direction:column;flex-direction:column;-webkit-box-pack:center;-ms-flex-pack:center;justify-content:center;padding:40px 20px 56px}
.eyebrow{font-family:var(--latin);font-size:.8rem;letter-spacing:.3em;color:var(--accent-soft);margin:0 0 14px;text-transform:uppercase}
.hero h1{font-size:3rem;font-size:clamp(2.2rem,5.4vw,4.4rem);letter-spacing:.12em;line-height:1.35;margin-bottom:22px;text-shadow:0 3px 24px rgba(0,0,0,.45)}
.hero .lead{max-width:32em;color:#eef2f6;font-size:1.05rem;font-size:clamp(1rem,1.3vw,1.15rem);margin-bottom:30px;text-shadow:0 1px 10px rgba(0,0,0,.4)}
.hero-btns .btn{margin:0 10px 10px 0}
@media (max-width:860px){.hero{height:78vh;min-height:520px}.hero .wrap{padding:30px 20px 40px}.hero h1{font-size:2.2rem;line-height:1.4}.hero-btns .btn{width:100%;margin:0 0 10px}}
/* 区画の見出し */
.sec{padding:88px 0}
.sec.tight{padding:56px 0}
.sec-head{margin-bottom:36px}
.sec-head i{display:block;font-family:var(--latin);font-style:normal;font-size:.78rem;letter-spacing:.3em;color:var(--accent);margin-bottom:6px;text-transform:uppercase}
.sec-head h2{font-size:1.7rem;font-size:clamp(1.45rem,2.6vw,2rem);letter-spacing:.12em;color:var(--primary-deep)}
.sec-head h2::after{content:"";display:block;width:40px;height:3px;background:var(--primary);margin-top:14px}
.sec-head.center{text-align:center}
.sec-head.center h2::after{margin-left:auto;margin-right:auto}
.sec-head .more{float:right;font-size:.88rem;text-decoration:none;color:var(--primary-deep);border-bottom:1px solid var(--primary);margin-top:28px}
.sec-head .more:hover{color:var(--accent);border-bottom-color:var(--accent)}
@media (max-width:860px){.sec{padding:64px 0}.sec.tight{padding:40px 0}.sec-head{margin-bottom:26px;display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-orient:vertical;-webkit-box-direction:normal;-ms-flex-direction:column;flex-direction:column;-webkit-box-align:start;-ms-flex-align:start;align-items:flex-start}.sec-head.center{-webkit-box-align:center;-ms-flex-align:center;align-items:center}.sec-head .more{float:none;display:inline-block;margin-top:14px;-webkit-box-ordinal-group:4;-ms-flex-order:3;order:3}}
/* 新着（トップ） */
.news-strip{background:#fff;border-bottom:1px solid var(--line)}
.news-strip .wrap{display:grid;grid-template-columns:200px 1fr;grid-gap:0 40px;padding:28px 20px}
.news-strip h2{font-size:1rem;letter-spacing:.12em;color:var(--primary-deep)}
.news-strip h2 i{display:block;font-family:var(--latin);font-style:normal;font-size:.74rem;letter-spacing:.3em;color:var(--accent);text-transform:uppercase}
.news-strip .more{display:inline-block;margin-top:8px;font-size:.84rem;text-decoration:none;color:var(--primary-deep);border-bottom:1px solid var(--primary)}
.news-list{list-style:none;margin:0;padding:0}
.news-list li{display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-align:baseline;-ms-flex-align:baseline;align-items:baseline;-ms-flex-wrap:wrap;flex-wrap:wrap;padding:10px 0;border-bottom:1px solid var(--line);font-size:.95rem}
.news-list li:last-child{border-bottom:0}
.news-list time{font-family:var(--latin);color:var(--muted);font-size:.9rem;letter-spacing:.06em;margin-right:14px;white-space:nowrap}
.news-list .cat,.nmeta .cat{display:inline-block;font-size:.72rem;letter-spacing:.1em;background:var(--pale);color:var(--primary-deep);border-radius:3px;padding:0 .7em;line-height:1.9;margin-right:14px;white-space:nowrap}
.news-list a{text-decoration:none}
.news-list a:hover{color:var(--accent)}
@media (max-width:860px){.news-strip .wrap{grid-template-columns:1fr;grid-gap:10px;padding:22px 0}.news-list li{font-size:.92rem;padding:10px 0}.news-list .nt{width:100%;margin-top:2px}}
/* 信頼の帯 */
.trust{background:var(--primary);color:#fff}
.trust ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,1fr)}
.trust ul.n2{grid-template-columns:repeat(2,1fr)}
.trust ul.n4{grid-template-columns:repeat(4,1fr)}
.trust li{text-align:center;padding:30px 10px;border-left:1px solid rgba(255,255,255,.18)}
.trust li:first-child{border-left:0}
.trust b{display:block;font-family:var(--latin);font-size:2.2rem;font-weight:700;line-height:1.2;letter-spacing:.02em}
.trust b small{font-family:var(--gothic);font-size:1rem;margin-left:.15em}
.trust span{display:block;font-size:.84rem;letter-spacing:.14em;color:var(--accent-soft);margin-top:4px}
@media (max-width:600px){.trust b{font-size:1.6rem}.trust li{padding:20px 4px}.trust span{font-size:.74rem;letter-spacing:.08em}.trust ul.n4{grid-template-columns:1fr 1fr}.trust ul.n4 li:nth-child(3){border-left:0}}
/* 会社紹介・ごあいさつ */
.about .wrap,.greet .wrap{display:grid;grid-template-columns:1fr 1fr;grid-gap:60px;-webkit-box-align:center;-ms-flex-align:center;align-items:center}
.about .wrap.noimg,.greet .wrap.noimg{grid-template-columns:1fr;max-width:800px}
.about .ph,.greet .ph{position:relative;padding-top:72%;overflow:hidden;border-radius:var(--r);background:var(--bg2)}
.about .ph img,.greet .ph img{position:absolute;top:0;left:0;width:100%;height:100%;-o-object-fit:cover;object-fit:cover}
.about h3,.greet h3{font-size:1.35rem;letter-spacing:.08em;margin-bottom:16px;color:var(--primary-deep)}
.greet .sign{text-align:right;font-weight:700;margin-top:8px}
@media (max-width:860px){.about .wrap,.greet .wrap{grid-template-columns:1fr;grid-gap:28px}}
/* 事業内容：トップのカード */
.biz{background:#fff}
.cards{display:grid;grid-template-columns:repeat(4,1fr);grid-gap:22px}
.cards.n3{grid-template-columns:repeat(3,1fr)}
.cards.n2{grid-template-columns:repeat(2,1fr);max-width:760px}
.card{background:#fff;border:1px solid var(--line);border-radius:var(--r);overflow:hidden;text-decoration:none;display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-orient:vertical;-webkit-box-direction:normal;-ms-flex-direction:column;flex-direction:column;-webkit-transition:box-shadow .2s;transition:box-shadow .2s}
.card:hover{box-shadow:0 12px 30px rgba(0,0,0,.12)}
.card .ph,.wcard .ph{position:relative;padding-top:66%;overflow:hidden;background:var(--bg2)}
.card .ph img,.wcard .ph img{position:absolute;top:0;left:0;width:100%;height:100%;-o-object-fit:cover;object-fit:cover}
.card .bd{padding:18px 20px 20px;-webkit-box-flex:1;-ms-flex:1;flex:1}
.card h3{font-size:1.08rem;letter-spacing:.08em;color:var(--primary-deep);margin-bottom:6px}
.card h3 small,.bizsec h2 small{display:block;font-family:var(--latin);font-weight:400;font-size:.7rem;letter-spacing:.24em;color:var(--accent);margin-bottom:4px;text-transform:uppercase}
.card p{font-size:.9rem;color:var(--muted);line-height:1.8;margin:0 0 10px}
.tags span{display:inline-block;font-size:.72rem;letter-spacing:.08em;border:1px solid var(--line);border-radius:3px;padding:0 .6em;line-height:1.9;margin:0 6px 4px 0;color:var(--muted);background:#fff}
.card .go{display:block;margin-top:auto;padding:12px 20px;border-top:1px solid var(--line);font-size:.84rem;color:var(--primary-deep);text-align:right}
@media (max-width:1000px){.cards,.cards.n3{grid-template-columns:1fr 1fr}}
@media (max-width:560px){.cards,.cards.n3,.cards.n2{grid-template-columns:1fr}}
/* 事業内容のページ */
.bizlist{display:grid;grid-gap:48px}
.bizsec{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);grid-gap:36px;-webkit-box-align:start;-ms-flex-align:start;align-items:start;padding-bottom:48px;border-bottom:1px solid var(--line);scroll-margin-top:80px}
.bizsec:last-child{border-bottom:0}
.bizsec .ph{position:relative;padding-top:68%;overflow:hidden;border-radius:var(--r);background:var(--bg2)}
.bizsec .ph img{position:absolute;top:0;left:0;width:100%;height:100%;-o-object-fit:cover;object-fit:cover}
.bizsec h2{font-size:1.5rem;letter-spacing:.1em;color:var(--primary-deep);margin-bottom:12px}
.bizsec .subs{margin:8px 0 0;padding:0;list-style:none}
.bizsec .subs li{position:relative;padding-left:1.2em;font-size:.95rem}
.bizsec .subs li::before{content:"";position:absolute;left:0;top:.85em;width:.5em;height:.5em;background:var(--accent);border-radius:1px}
@media (max-width:860px){.bizsec{grid-template-columns:1fr;grid-gap:18px}}
/* 流れ */
.flow{background:#fff}
.steps{list-style:none;margin:0 auto;padding:0;max-width:860px;counter-reset:s}
.steps li{position:relative;padding:0 0 30px 64px;counter-increment:s}
.steps li::before{content:counter(s);position:absolute;left:0;top:0;width:44px;height:44px;border-radius:6px;background:var(--primary);color:#fff;display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-align:center;-ms-flex-align:center;align-items:center;-webkit-box-pack:center;-ms-flex-pack:center;justify-content:center;font-family:var(--latin);font-weight:700;font-size:1.1rem}
.steps li::after{content:"";position:absolute;left:21px;top:48px;bottom:4px;border-left:2px dotted var(--line)}
.steps li:last-child::after{display:none}
.steps h3{font-size:1.15rem;letter-spacing:.1em;margin:4px 0 4px}
.steps p{color:var(--muted);font-size:.92rem;margin:0}
/* 実績のカード・一覧 */
.works-sec{background:var(--bg2)}
.wcards{display:grid;grid-template-columns:repeat(3,1fr);grid-gap:22px}
.wcard{background:#fff;border-radius:var(--r);overflow:hidden;text-decoration:none;display:block;border:1px solid var(--line)}
.wcard .ph{padding-top:62%}
.wcard .ph .cat{position:absolute;left:0;top:0;background:var(--primary);color:#fff;font-size:.72rem;letter-spacing:.12em;padding:.3em 1em;border-radius:0 0 6px 0}
.wcard .ph .noimg{position:absolute;left:0;top:0;width:100%;height:100%;display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-align:center;-ms-flex-align:center;align-items:center;-webkit-box-pack:center;-ms-flex-pack:center;justify-content:center;color:var(--muted);font-size:.85rem}
.wcard .bd{padding:16px 18px 18px}
.wcard h3{font-size:1rem;letter-spacing:.06em;color:var(--primary-deep);line-height:1.6}
.wcard .meta{display:block;font-size:.8rem;color:var(--muted);margin-top:6px}
.wcard .meta b{font-weight:400;margin-right:1em}
.wcard .tg{margin-top:8px}
@media (max-width:860px){.wcards{grid-template-columns:1fr 1fr}}
@media (max-width:560px){.wcards{grid-template-columns:1fr}}
.filter,.year-nav{display:-webkit-box;display:-ms-flexbox;display:flex;-ms-flex-wrap:wrap;flex-wrap:wrap;margin:0 -4px 20px;padding:0;list-style:none}
.filter li,.year-nav li{margin:4px}
.filter a{display:inline-block;text-decoration:none;font-size:.86rem;letter-spacing:.06em;padding:.5em 1.1em;border:1px solid var(--line);border-radius:6px;background:#fff;min-height:44px;line-height:2}
.filter .chip,.year-nav .chip{display:inline-block;font-size:.8rem;letter-spacing:.06em;padding:.2em .8em;border-radius:3px;background:var(--pale);color:var(--primary-deep);line-height:1.9;cursor:default}  /* 内わけの札（押せない。2b で絞り込みを付けたら a に） */
.year-nav .chip{font-family:var(--latin)}
.filter a.on,.filter .chip.all{background:var(--primary);color:#fff;border-color:var(--primary)}
.count{font-size:.86rem;color:var(--muted);margin:0 0 18px}
.pager{display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-pack:center;-ms-flex-pack:center;justify-content:center;margin:40px 0 0;padding:0;list-style:none}
.pager li{margin:0 4px}
.pager a,.pager span{display:inline-block;min-width:44px;min-height:44px;line-height:42px;text-align:center;border:1px solid var(--line);border-radius:6px;text-decoration:none;background:#fff;padding:0 .6em}
.pager span{background:var(--primary);color:#fff;border-color:var(--primary)}
/* お知らせの一覧 */
.news-year{font-family:var(--latin);font-size:1.3rem;color:var(--primary-deep);letter-spacing:.06em;margin:36px 0 6px;padding-bottom:6px;border-bottom:2px solid var(--primary)}
.news-year:first-of-type{margin-top:0}
.news-big li{padding:18px 4px;font-size:1rem}
.news-big .nt{display:block;width:100%;margin-top:4px}
.news-big .nt a{font-weight:700;color:var(--primary-deep)}
.news-big .ex{display:block;width:100%;font-size:.88rem;color:var(--muted);margin-top:4px;line-height:1.7}
/* 1件ページ（実績・お知らせ） */
.page-head{background:var(--primary-deep);color:#fff;padding:54px 0 46px}
.page-head i{display:block;font-family:var(--latin);font-style:normal;font-size:.8rem;letter-spacing:.3em;color:var(--accent-soft);margin-bottom:6px;text-transform:uppercase}
.page-head h1{font-size:1.8rem;font-size:clamp(1.5rem,2.8vw,2.1rem);letter-spacing:.14em}
.crumb{list-style:none;margin:0;padding:12px 0;font-size:.8rem;color:var(--muted);display:-webkit-box;display:-ms-flexbox;display:flex;-ms-flex-wrap:wrap;flex-wrap:wrap}
.crumb li{margin-right:.5em}
.crumb li::after{content:"›";margin-left:.5em}
.crumb li:last-child::after{content:""}
.crumb a{text-decoration:none}
.item .nmeta{font-size:.9rem;color:var(--muted);margin-bottom:18px}
.item .nmeta time{font-family:var(--latin);margin-right:14px}
.item .wmain{margin:0 0 24px;border-radius:var(--r);overflow:hidden;background:var(--bg2)}
.item .meta{margin:0 0 28px;background:#fff;border:1px solid var(--line);border-radius:var(--r);padding:4px 22px}
.item .meta div{display:grid;grid-template-columns:7em 1fr;padding:10px 0;border-bottom:1px solid var(--line);font-size:.95rem}
.item .meta div:last-child{border-bottom:0}
.item .meta dt{color:var(--muted)}
.item .meta dd{margin:0}
.item .body p{margin-bottom:1.2em}
.item .figs{display:grid;grid-template-columns:1fr 1fr;grid-gap:18px;margin:28px 0}
.item .figs figure{margin:0}
.item .figs img{border-radius:var(--r);background:var(--bg2)}
.item .figs figcaption{font-size:.85rem;color:var(--muted);padding:8px 2px 0;background:var(--bg)}
.pn-wrap{display:grid;grid-template-columns:1fr 1fr;grid-gap:14px;margin:40px 0 20px}
.pn{display:block;text-decoration:none;border:1px solid var(--line);border-radius:var(--r);padding:14px 18px;background:#fff;font-size:.92rem;line-height:1.6}
.pn small{display:block;font-size:.72rem;color:var(--accent);letter-spacing:.1em}
.pn.next{text-align:right;grid-column:2}
.pn:hover{border-color:var(--primary)}
.back a{text-decoration:none;color:var(--primary-deep);border-bottom:1px solid var(--primary)}
@media (max-width:600px){.item .figs{grid-template-columns:1fr}.pn-wrap{grid-template-columns:1fr}.pn.next{grid-column:1}.item .meta div{grid-template-columns:5.5em 1fr}}
/* 会社概要・沿革・アクセス */
.info{margin:0;background:#fff;border:1px solid var(--line);border-radius:var(--r);padding:6px 26px}
.info div{display:grid;grid-template-columns:9em 1fr;padding:14px 0;border-bottom:1px solid var(--line)}
.info div:last-child{border-bottom:none}
.info dt{color:var(--muted);font-size:.9rem}
.info dd{margin:0}
.history{background:#fff}
.hist{list-style:none;margin:0;padding:0;max-width:800px;border-left:2px solid var(--line)}
.hist li{position:relative;padding:0 0 22px 28px;display:grid;grid-template-columns:8em 1fr}
.hist li::before{content:"";position:absolute;left:-7px;top:.6em;width:12px;height:12px;border-radius:50%;background:var(--accent);border:2px solid #fff}
.hist time{font-family:var(--latin);font-weight:700;color:var(--primary-deep)}
.access .wrap{display:grid;grid-template-columns:1fr 1fr;grid-gap:56px}
.access .wrap.nomap{grid-template-columns:1fr;max-width:760px}
.route{display:-webkit-inline-box;display:-ms-inline-flexbox;display:inline-flex;-webkit-box-align:center;-ms-flex-align:center;align-items:center;margin-top:10px;text-decoration:none;background:var(--primary);color:#fff;border-radius:6px;padding:.9em 1.4em;letter-spacing:.08em;font-size:.92rem;min-height:48px}
.route svg{width:1.1em;height:1.1em;fill:var(--accent-soft);margin-right:.5em}
.map{border-radius:var(--r);overflow:hidden;min-height:360px;background:var(--bg2)}
.map iframe{width:100%;height:100%;min-height:360px;border:0;display:block}
@media (max-width:860px){.access .wrap{grid-template-columns:1fr;grid-gap:30px}.info{padding:4px 18px}.info div{grid-template-columns:6em 1fr}.map,.map iframe{min-height:260px}.hist li{grid-template-columns:1fr}}
/* 採用 */
.why{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,1fr);grid-gap:22px}
.why.n2{grid-template-columns:repeat(2,1fr)}
.why.n4{grid-template-columns:repeat(4,1fr)}
.why li{background:#fff;border:1px solid var(--line);border-radius:var(--r);padding:24px 22px}
.why .no{display:block;font-family:var(--latin);font-weight:700;color:var(--accent);letter-spacing:.1em;margin-bottom:6px}
.why h3{font-size:1.08rem;letter-spacing:.06em;color:var(--primary-deep);margin-bottom:8px}
.why p{font-size:.92rem;color:var(--muted);margin:0}
@media (max-width:860px){.why,.why.n4{grid-template-columns:1fr 1fr}}
@media (max-width:560px){.why,.why.n2,.why.n4{grid-template-columns:1fr}}
.jobs{background:#fff}
.joblist{display:grid;grid-gap:28px}
.job h3{font-size:1.2rem;letter-spacing:.08em;color:var(--primary-deep);margin-bottom:12px;padding-left:12px;border-left:4px solid var(--accent)}
.ways{display:grid;grid-template-columns:repeat(3,1fr);grid-gap:18px}
.ways.n1{grid-template-columns:1fr;max-width:520px}
.ways.n2{grid-template-columns:1fr 1fr;max-width:820px}
.way{background:#fff;border:1px solid var(--line);border-radius:var(--r);padding:28px 22px;text-align:center;display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-orient:vertical;-webkit-box-direction:normal;-ms-flex-direction:column;flex-direction:column;-webkit-box-align:center;-ms-flex-align:center;align-items:center}
.way h3{font-size:1rem;letter-spacing:.2em;color:var(--primary-deep);margin-bottom:6px}
.way p{font-size:.9rem;color:var(--muted);margin-bottom:16px}
.way .btn{width:100%;margin-top:auto;word-break:break-all}
.way .tel{font-family:var(--latin);font-size:1.7rem;font-weight:700;letter-spacing:.03em;text-decoration:none;color:var(--primary-deep);margin-top:auto}
.way small{font-size:.8rem;color:var(--muted)}
@media (max-width:860px){.ways,.ways.n2{grid-template-columns:1fr}}
/* よくある質問 */
.faq{background:var(--bg2)}
.faq-list{max-width:820px;margin:0 auto}
.faq details{background:#fff;border-radius:var(--r);margin-bottom:12px;border:1px solid var(--line)}
.faq summary{list-style:none;cursor:pointer;display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-align:center;-ms-flex-align:center;align-items:center;padding:16px 48px 16px 18px;position:relative;font-weight:700;letter-spacing:.04em;line-height:1.7;min-height:48px}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";position:absolute;right:20px;top:50%;-webkit-transform:translateY(-50%);transform:translateY(-50%);color:var(--primary-deep);font-size:1.3rem}
.faq details[open] summary::after{content:"−"}
.faq p{margin:0;padding:0 18px 18px;display:-webkit-box;display:-ms-flexbox;display:flex;color:var(--muted);font-size:.93rem;line-height:1.9}
.faq .q,.faq .a{-ms-flex:none;flex:none;display:-webkit-inline-box;display:-ms-inline-flexbox;display:inline-flex;-webkit-box-align:center;-ms-flex-align:center;align-items:center;-webkit-box-pack:center;-ms-flex-pack:center;justify-content:center;width:30px;height:30px;border-radius:6px;font-family:var(--latin);font-weight:700;margin-right:14px}
.faq .q{background:var(--primary);color:#fff}
.faq .a{background:var(--pale);color:var(--primary-deep)}
/* フォーム（明るい地） */
.formbox{max-width:800px;margin:40px 0 0;background:#fff;border:1px solid var(--line);border-radius:var(--r);overflow:hidden;scroll-margin-top:16px}
.form-top{display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-pack:justify;-ms-flex-pack:justify;justify-content:space-between;-webkit-box-align:baseline;-ms-flex-align:baseline;align-items:baseline;padding:12px 24px;background:var(--primary);color:#fff;font-weight:700;letter-spacing:.1em}
.form-sub{font-size:.78rem;font-weight:400;letter-spacing:.1em;opacity:.9}
.formbox form{display:grid;grid-gap:18px;padding:24px 24px 28px}
.formbox .form-lead{margin:0;font-size:.92rem;color:var(--muted)}
.f-row{display:block;font-size:.9rem}
.f-row > span{display:block;margin-bottom:6px;font-weight:700;letter-spacing:.04em}
.formbox input,.formbox textarea{font:inherit;font-size:16px;padding:12px 14px;border-radius:6px;border:1px solid var(--line);background:var(--bg);color:var(--ink);width:100%;min-height:50px;display:block}
.formbox input:focus,.formbox textarea:focus{border-color:var(--primary);outline:none;background:#fff}
.formbox textarea{min-height:140px;resize:vertical}
.formbox fieldset{border:none;margin:0;padding:0;min-width:0}
.formbox legend{padding:0;margin-bottom:8px;font-weight:700;letter-spacing:.04em;font-size:.9rem}
.req,.opt-label{display:inline-block;margin-left:8px;font-weight:400;font-size:.7rem;letter-spacing:.05em;border-radius:3px;padding:0 6px;vertical-align:.15em;line-height:1.7}
.req{background:var(--accent);color:#fff}
.opt-label{border:1px solid var(--line);color:var(--muted)}
.chips{display:-webkit-box;display:-ms-flexbox;display:flex;-ms-flex-wrap:wrap;flex-wrap:wrap;margin:-4px}
.chip{position:relative;margin:4px;font-size:.92rem;cursor:pointer}
.formbox .chip input{position:absolute;left:0;top:0;width:1px;height:1px;min-height:0;padding:0;opacity:0}
.formbox .chip span{display:block;margin:0;padding:9px 16px;border-radius:6px;border:1px solid var(--line);color:var(--ink);line-height:1.5;min-height:44px;background:#fff}
.formbox .chip input:checked + span{background:var(--primary);border-color:var(--primary);color:#fff}
.formbox .chip input:focus-visible + span{outline:2px solid var(--accent);outline-offset:2px}
.formbox .btn{width:100%;font-size:1.05rem}
.formnote{font-size:.82rem;color:var(--muted);margin:0;line-height:1.7}
.formbox .gotcha{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}
.form-sent{text-align:center;padding:20px 0}
.form-sent h3{font-size:1.3rem;letter-spacing:.14em;margin-bottom:10px}
@media (max-width:640px){.form-top{padding:11px 18px}.formbox form{padding:18px 18px 22px}.form-sub{display:none}}
/* 採用・お問い合わせの帯 */
.recruit{position:relative;background:var(--dark);color:#fff;overflow:hidden}
.recruit .bgph{position:absolute;top:0;left:0;width:100%;height:100%;opacity:.28}
.recruit .bgph img{width:100%;height:100%;-o-object-fit:cover;object-fit:cover}
.recruit .wrap{position:relative;z-index:2;padding:80px 20px;max-width:760px;text-align:center}
.recruit h2{font-size:1.6rem;letter-spacing:.12em;margin-bottom:14px}
.recruit p{color:#dfe5ec;margin-bottom:26px}
.contact-band{background:var(--pale)}
.contact-band .wrap{display:grid;grid-template-columns:1fr 1fr;grid-gap:30px;-webkit-box-align:center;-ms-flex-align:center;align-items:center}
.contact-band .telbox{background:#fff;border-radius:var(--r);padding:26px 28px;border:1px solid var(--line)}
.contact-band .tel{display:block;font-family:var(--latin);font-size:2rem;font-weight:700;color:var(--primary-deep);text-decoration:none;letter-spacing:.03em;line-height:1.3}
.contact-band .tel small{display:block;font-family:var(--gothic);font-size:.8rem;font-weight:400;color:var(--muted);letter-spacing:.08em}
.contact-band .telbox .btn{width:100%;margin-top:16px}
@media (max-width:860px){.contact-band .wrap{grid-template-columns:1fr}}
@media (max-width:360px){.contact-band .tel{font-size:1.55rem}}
/* 文章のページ */
.prose section{margin-bottom:28px}
.prose h2{font-size:1.15rem;letter-spacing:.08em;color:var(--primary-deep);margin-bottom:8px;padding-left:12px;border-left:4px solid var(--accent)}
.prose p{font-size:.95rem}
/* 下 */
.foot{background:var(--dark);color:#cfd6de;padding:56px 0 120px;font-size:.88rem}
.foot .fname{font-weight:700;font-size:1.1rem;letter-spacing:.12em;color:#fff;margin-bottom:6px}
.foot .cols{display:grid;grid-template-columns:1.3fr 1fr 1fr;grid-gap:30px}
.foot nav a{display:block;text-decoration:none;padding:4px 0;opacity:.9}
.foot nav a:hover{color:#fff;opacity:1}
.foot .lic{font-size:.8rem;opacity:.85}
.foot .copy{font-family:var(--latin);opacity:.6;margin:30px 0 0;font-size:.8rem;border-top:1px solid rgba(255,255,255,.14);padding-top:18px}
.foot p{margin:0 0 6px}
@media (max-width:860px){.foot .cols{grid-template-columns:1fr 1fr}.foot .cols > div:first-child{grid-column:1 / -1}}
/* スマホの下の固定ボタン・上へ */
.spbar{display:none}
@media (max-width:860px){
  .spbar{display:grid;grid-template-columns:1fr 1fr;position:fixed;left:0;right:0;bottom:0;z-index:50;background:#fff;border-top:1px solid var(--line);padding-bottom:env(safe-area-inset-bottom)}
  .spbar.n1{grid-template-columns:1fr}
  .spbar a{text-align:center;text-decoration:none;padding:.95em .3em;font-size:.9rem;font-weight:700;letter-spacing:.08em;min-height:48px;color:var(--primary-deep)}
  .spbar a.c{background:var(--accent);color:#fff}
}
.totop{position:fixed;right:14px;bottom:18px;z-index:40;width:44px;height:44px;border-radius:6px;background:var(--primary);color:#fff;display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-align:center;-ms-flex-align:center;align-items:center;-webkit-box-pack:center;-ms-flex-pack:center;justify-content:center;text-decoration:none;opacity:0;visibility:hidden;-webkit-transition:opacity .3s;transition:opacity .3s;box-shadow:0 4px 12px rgba(0,0,0,.25)}
.totop.show{opacity:.92;visibility:visible}
@media (max-width:860px){.totop{bottom:76px;right:12px}}'''


def main(conf, outdir):
    """make_site.py の main() から呼ばれる（設定に "pages" があるとき）"""
    c = json.load(open(conf, encoding='utf-8'))
    outdir = os.path.expanduser(outdir)
    os.makedirs(outdir, exist_ok=True)
    s = Site(c, outdir)
    pages = s.build_all()
    # 折り返しの印（全ページ・_tpl も）
    try:
        import wbr
        n_all = 0
        for p, _ in s.written:
            fp = os.path.join(outdir, p)
            txt, n = wbr.add_wbr(open(fp, encoding='utf-8').read()); n_all += n
            open(fp, 'w', encoding='utf-8').write(txt)
        print(f'文の折り返し：{n_all}か所（{len(s.written)} ファイル）')
    except SystemExit:
        print('⚠️ budoux がないので文の折り返しを入れていません（pip3 install budoux）')
    # 404
    open(os.path.join(outdir, '404.html'), 'w', encoding='utf-8').write(build_404(c, s.t))
    print(f'作りました：{len(pages)} ページ（' + '、'.join(p for p in pages[:6]) + ('…' if len(pages) > 6 else '') + '）＋ 404.html＋_tpl/')
    keep = os.path.join(outdir, 'site.json')
    if os.path.abspath(conf) != os.path.abspath(keep): shutil.copy(conf, keep); print('設定を置きました：', keep)
    ms.write_cloudflare_files(outdir)
    if s.cms: print('cms.enabled: true → 2b の Worker が /works/ /news/ とトップの新着（<!--news:start--> の中）を D1 から出す。2a では静的のページと _tpl/ を作っただけ')
    chk = os.path.join(HERE, 'check_site.py')
    if os.path.exists(chk): subprocess.call([sys.executable, chk, outdir, '--all', '--no-browser'])


if __name__ == '__main__':
    sys.exit('このファイルは単独では動かしません。python3 make_site.py <設定.json> <作るフォルダ>（設定に "pages" があると法人の型になります）')
