#!/usr/bin/env python3
"""お店のサイトの追加部品（Lift-Off）  2026/10/30 作成（make_site.py から呼ばれる。1つのファイル＝この役目だけ）

make_site.py の部品（belt・compare・calc・cases・form・shop）に、小さなお店のサイトでよく効く部品を足す。
どれも「設定（parts）に中身が書いてあるときだけ」出る。中身が空なら何も出さない（分からない情報は作らない）。
古いスマホ対策（マニュアル 16）：JS は var・function だけ／flex の gap・aspect-ratio・inset・svh は使わない／動きは減らす設定で止める。

部品（設定の "parts" に書く。書き方の見本は templates/site_sample_extra.json、説明は templates/部品の説明書_追加分.md）
  notice      … ページの最上部の細い帯（臨時休業・繁忙期など）。1行
  credentials … 実績・資格の帯（「全国大会3位」「創業〇年」など。写真がなくても信頼が出る）
  strengths   … 選ばれる理由（番号つきカード 2〜4）
  news        … お知らせの一覧（日付つき。月の更新の成果が見える）
  voices      … お客様の声（本物だけ。consent: true が要る＝掲載の了承）
  hours       … 営業時間（受付時間）の表と「いま営業中／時間外」の表示（JS）
  areas       … 対応エリア（市町の札）
  video       … 動画（YouTube。押したときだけ読み込む＝ページが重くならない）
  lightbox    … 写真をタップすると大きく見られる（帯・施工例・メニューの写真。設定は true だけ）
"""
import re, json, html

NAMES = ['notice', 'credentials', 'strengths', 'news', 'voices', 'hours', 'areas', 'video', 'lightbox']
DAYS = [('mon', '月'), ('tue', '火'), ('wed', '水'), ('thu', '木'), ('fri', '金'), ('sat', '土'), ('sun', '日')]


def e(t):
    return html.escape(str(t or ''), quote=True)


def _head(x, eyebrow, title):
    return f'<div class="sec-head center"><i>{x["I"]()}{e(eyebrow)}</i><h2>{e(title)}</h2></div>'


def _lead(p):
    return f'<p class="sec-lead center muted">{e(p["lead"])}</p>' if p.get('lead') else ''


def _iso(d):
    m = re.match(r'\s*(\d{4})\D+(\d{1,2})\D+(\d{1,2})', str(d or ''))
    return '%s-%02d-%02d' % (m.group(1), int(m.group(2)), int(m.group(3))) if m else ''


# ---------- 設定のチェック（足りない部品は外す。本物のお店でお客様の声の了承がないときは止める） ----------
def validate(P, c):
    def drop(k, why):
        print(f'⚠️ {k}：{why}ので入れません')
        P.pop(k, None)

    if 'notice' in P and not str(P['notice'].get('text') or '').strip():
        drop('notice', '文（text）がない')
    if 'credentials' in P:
        P['credentials']['items'] = [i for i in (P['credentials'].get('items') or []) if i.get('value') and i.get('label')]
        if not P['credentials']['items']:
            drop('credentials', '項目（items の value と label）がない')
    if 'strengths' in P:
        P['strengths']['items'] = [i for i in (P['strengths'].get('items') or []) if i.get('title')]
        if not P['strengths']['items']:
            drop('strengths', '項目（items の title）がない')
    if 'news' in P:
        P['news']['items'] = [i for i in (P['news'].get('items') or []) if i.get('text')]
        if not P['news']['items']:
            drop('news', 'お知らせ（items の text）がない')
    if 'voices' in P:
        its = [i for i in (P['voices'].get('items') or []) if i.get('text')]
        P['voices']['items'] = its
        if not its:
            drop('voices', 'お客様の声（items の text）がない')
        else:
            no = [i for i in its if i.get('consent') is not True]
            if no:
                if c.get('sample_note'):
                    print('⚠️ voices：了承（consent: true）のない声があります（見本なので出します）。本物のお店では必ずお客様の了承を取る')
                else:
                    raise SystemExit('❌ voices：お客様の了承（consent: true）がない声があります。本物のお店では、実在のお客様の声で、掲載の了承を取ったものだけ載せます（作り話・無断掲載は載せない）')
    if 'hours' in P:
        sc = P['hours'].get('schedule') or {}
        if not any(k in sc for k, _ in DAYS):
            drop('hours', '曜日ごとの時間（schedule の mon〜sun）がない')
        else:
            for k, _ in DAYS:
                for part in str(sc.get(k) or '').replace(' ', '').split(','):
                    if part and not re.match(r'^\d{1,2}:\d{2}-\d{1,2}:\d{2}$', part):
                        raise SystemExit(f'❌ hours：schedule の {k} の書き方が違います（例 "09:00-18:00" または "09:00-12:00,13:00-18:00"。休みは空 ""）：{part}')
    if 'areas' in P and not (P['areas'].get('main') or P['areas'].get('also')):
        drop('areas', '市町（main か also）がない')
    if 'video' in P and not re.match(r'^[\w-]{6,20}$', str(P['video'].get('youtube') or '')):
        drop('video', 'YouTube の動画ID（youtube）がない')


# ---------- 画面（HTML） ----------
def render(x):
    P = x['P']
    out = {k: '' for k in ('notice', 'credentials', 'strengths', 'news', 'voices', 'hours', 'areas', 'video')}

    if 'notice' in P:
        p = P['notice']
        link = f'<a href="{e(p["url"])}">{e(p.get("link_label", "くわしく"))}</a>' if p.get('url') else ''
        out['notice'] = f'<p class="notice" role="note"><b>{e(p.get("label", "お知らせ"))}</b><span>{e(p["text"])}</span>{link}</p>'

    if 'credentials' in P:
        p = P['credentials']
        its = p['items'][:4]
        lis = ''
        for i in its:
            small = f'<small>{e(i["note"])}</small>' if i.get('note') else ''
            lis += f'<li><b class="cv">{e(i["value"])}</b><span class="cl">{e(i["label"])}</span>{small}</li>'
        out['credentials'] = f'''
  <section class="cred" aria-label="{e(p.get("title", "実績・資格"))}">
    <div class="wrap"><ul class="cred-list n{len(its)}">{lis}</ul></div>
  </section>'''

    if 'strengths' in P:
        p = P['strengths']
        its = p['items'][:4]
        cards = ''
        for n, i in enumerate(its, 1):
            body = f'<p>{e(i["text"])}</p>' if i.get('text') else ''
            cards += f'<li><span class="no">{n:02d}</span><h3>{e(i["title"])}</h3>{body}</li>'
        out['strengths'] = f'''
  <section id="strengths" class="sec why-sec">
    <div class="wrap">
      {_head(x, p.get("eyebrow", "point"), p.get("title", "選ばれる理由"))}
      {_lead(p)}
      <ol class="why n{len(its)}">{cards}</ol>
    </div>
  </section>'''

    if 'news' in P:
        p = P['news']
        its = p['items']
        lim = int(p.get('limit', 3))

        def li(i):
            t = e(i['text'])
            if i.get('url'):
                t = f'<a href="{e(i["url"])}">{t}</a>'
            d = i.get('date', '')
            iso = _iso(d)
            dt = ''
            if d:
                attr = f' datetime="{iso}"' if iso else ''
                dt = f'<time{attr}>{e(d)}</time>'
            tag = f'<span class="ntag">{e(i["tag"])}</span>' if i.get('tag') else ''
            return f'<li>{dt}{tag}<span class="nt">{t}</span></li>'

        first = ''.join(li(i) for i in its[:lim])
        rest = ''.join(li(i) for i in its[lim:])
        more = f'<details class="news-more"><summary>{e(p.get("more", "これまでのお知らせ"))}</summary><ul class="news-list">{rest}</ul></details>' if rest else ''
        out['news'] = f'''
  <section id="news" class="sec news-sec">
    <div class="wrap narrow">
      {_head(x, p.get("eyebrow", "news"), p.get("title", "お知らせ"))}
      <ul class="news-list">{first}</ul>{more}
    </div>
  </section>'''

    if 'voices' in P:
        p = P['voices']
        cards = ''.join(f'<li><blockquote><p>{e(i["text"])}</p></blockquote><cite>{e(i.get("who", ""))}</cite></li>' for i in p['items'][:6])
        note = f'<p class="voice-note center muted">{e(p["note"])}</p>' if p.get('note') else ''
        out['voices'] = f'''
  <section id="voices" class="sec voice-sec">
    <div class="wrap">
      {_head(x, p.get("eyebrow", "voice"), p.get("title", "お客様の声"))}
      {_lead(p)}
      <ul class="voices">{cards}</ul>{note}
    </div>
  </section>'''

    if 'hours' in P:
        p = P['hours']
        sc = p['schedule']
        rows = ''
        for k, jp in DAYS:
            v = str(sc.get(k) or '').replace(' ', '')
            cell = e(v.replace('-', '〜').replace(',', '　／　')) if v else '<span class="cl">定休日</span>'
            rows += f'<tr><th>{jp}</th><td>{cell}</td></tr>'
        word = p.get('open_word', '営業中')
        badge = '<p class="hrs-badge" id="hrs-badge" hidden data-word="%s" data-schedule="%s" data-holidays="%s"></p>' % (
            e(word), e(json.dumps(sc, ensure_ascii=False)), e(json.dumps(p.get('holidays') or [])))
        note = f'<p class="hrs-note muted">{e(p["note"])}</p>' if p.get('note') else ''
        out['hours'] = f'''
  <section id="hours" class="sec hrs-sec">
    <div class="wrap narrow">
      {_head(x, p.get("eyebrow", "hours"), p.get("title", "営業時間"))}
      {badge}
      <table class="hrs-table">{rows}</table>{note}
    </div>
  </section>'''

    if 'areas' in P:
        p = P['areas']
        main = ''.join(f'<li class="m">{e(a)}</li>' for a in (p.get('main') or []))
        also = ''.join(f'<li>{e(a)}</li>' for a in (p.get('also') or []))
        note = f'<p class="area-note center muted">{e(p["note"])}</p>' if p.get('note') else ''
        out['areas'] = f'''
  <section id="areas" class="sec area-sec">
    <div class="wrap narrow">
      {_head(x, p.get("eyebrow", "area"), p.get("title", "対応エリア"))}
      {_lead(p)}
      <ul class="areas">{main}{also}</ul>{note}
    </div>
  </section>'''

    if 'video' in P:
        p = P['video']
        vid = p['youtube']
        ttl = p.get('title', '動画')
        thumb = p.get('poster') or f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'
        cap = f'<p class="vid-cap center muted">{e(p["caption"])}</p>' if p.get('caption') else ''
        out['video'] = f'''
  <section id="video" class="sec vid-sec">
    <div class="wrap narrow">
      {_head(x, p.get("eyebrow", "movie"), ttl)}
      {_lead(p)}
      <div class="vid-box"><a class="vid-btn" id="vid-btn" href="https://www.youtube.com/watch?v={e(vid)}" target="_blank" rel="noopener" data-id="{e(vid)}" data-title="{e(ttl)}" aria-label="{e(ttl)}を再生する"><img src="{e(thumb)}" alt="" loading="lazy"><span class="vid-play" aria-hidden="true"></span></a></div>{cap}
    </div>
  </section>'''
    return out


# ---------- 見た目（CSS） ----------
CSS = {
'notice': r'''/* 部品：お知らせの帯（最上部・1行） */
.notice{margin:0;padding:0 16px;height:34px;line-height:34px;background:var(--primary-deep);color:#fff;font-size:.8rem;text-align:center;letter-spacing:.06em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.notice b{display:inline-block;margin-right:.8em;font-weight:500;line-height:1.5;border:1px solid rgba(255,255,255,.6);border-radius:999px;padding:0 .8em}
.notice a{color:#fff;margin-left:.8em}
.notice ~ .head{top:34px}
.sample-note ~ .notice ~ .head{top:68px}''',
'credentials': r'''/* 部品：実績・資格の帯 */
.cred{background:var(--bg2);border-bottom:1px solid var(--line);padding:34px 0}
.cred-list{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(4,1fr);grid-gap:12px;gap:12px}
.cred-list.n3{grid-template-columns:repeat(3,1fr)}
.cred-list.n2{grid-template-columns:repeat(2,1fr)}
.cred-list.n1{grid-template-columns:1fr}
.cred-list li{text-align:center;padding:6px 10px;border-left:1px solid var(--line)}
.cred-list li:first-child{border-left:0}
.cv{display:block;font-family:var(--head);font-weight:600;font-size:2rem;line-height:1.4;color:var(--primary-deep);letter-spacing:.06em}
.cl{display:block;font-size:.88rem;line-height:1.7;letter-spacing:.1em}
.cred-list small{display:block;font-size:.76rem;color:var(--muted);line-height:1.6;margin-top:2px}
@media (max-width:640px){.cred{padding:22px 0}.cred-list,.cred-list.n3,.cred-list.n4{grid-template-columns:1fr 1fr}.cred-list li:nth-child(odd){border-left:0}.cred-list li:last-child:nth-child(odd){grid-column:1 / -1}.cv{font-size:1.6rem}}''',
'strengths': r'''/* 部品：選ばれる理由 */
.why{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,1fr);grid-gap:22px;gap:22px}
.why.n2,.why.n4{grid-template-columns:repeat(2,1fr)}
.why li{background:#fff;border-radius:var(--r);padding:30px 26px 28px;box-shadow:0 10px 30px rgba(0,0,0,.06);position:relative}
.why .no{display:block;font-family:var(--latin);font-style:italic;font-size:2.2rem;line-height:1.2;color:var(--primary);margin-bottom:6px}
.why h3{font-size:1.15rem;letter-spacing:.1em;margin-bottom:8px}
.why p{margin:0;color:var(--muted);font-size:.92rem;line-height:1.95}
@media (max-width:760px){.why,.why.n2,.why.n4{grid-template-columns:1fr}}''',
'news': r'''/* 部品：お知らせ */
.news-sec{background:var(--bg2)}
.news-list{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}
.news-list li{display:flex;flex-wrap:wrap;align-items:baseline;padding:16px 4px;border-bottom:1px solid var(--line);line-height:1.8}
.news-list time{font-family:var(--latin);font-size:1rem;color:var(--muted);letter-spacing:.08em;margin-right:14px;white-space:nowrap}
.ntag{font-size:.74rem;letter-spacing:.1em;background:var(--pale);color:var(--primary-deep);border-radius:999px;padding:0 .9em;margin-right:14px;white-space:nowrap;line-height:1.9}
.nt{flex:1 1 14em;min-width:0}
.nt a{color:var(--ink)}
.news-more{margin-top:14px}
.news-more summary{cursor:pointer;color:var(--primary-deep);font-size:.9rem;letter-spacing:.08em;padding:6px 0}
.news-more .news-list{border-top:0}''',
'voices': r'''/* 部品：お客様の声 */
.voice-sec{background:var(--bg2)}
.voices{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));grid-gap:22px;gap:22px}
.voices li{background:#fff;border-radius:var(--r);padding:28px 26px 22px;box-shadow:0 10px 30px rgba(0,0,0,.06);position:relative}
.voices li::before{content:"\201C";position:absolute;left:18px;top:2px;font-family:var(--latin);font-size:3.4rem;line-height:1;color:var(--accent-soft)}
.voices blockquote{margin:0;padding-top:14px}
.voices blockquote p{margin:0;font-size:.95rem;line-height:2}
.voices cite{display:block;margin-top:12px;font-style:normal;font-size:.82rem;color:var(--muted);text-align:right;letter-spacing:.08em}
.voice-note{font-size:.8rem;margin:22px 0 0}''',
'hours': r'''/* 部品：営業時間 */
.hrs-badge{display:table;margin:-8px auto 22px;padding:.35em 1.4em;border-radius:999px;font-size:.92rem;letter-spacing:.08em;line-height:1.7;text-align:center}
.hrs-badge[hidden]{display:none}
.hrs-badge.on{background:#e3f2e6;color:#1e6b36}
.hrs-badge.off{background:var(--pale);color:var(--muted)}
.hrs-table{width:100%;max-width:460px;margin:0 auto;border-collapse:collapse}
.hrs-table th,.hrs-table td{padding:10px 8px;border-bottom:1px solid var(--line);font-weight:400;text-align:left;line-height:1.7}
.hrs-table th{width:4em;font-family:var(--head);letter-spacing:.12em;color:var(--primary-deep)}
.hrs-table .cl{display:inline;color:var(--muted)}
.hrs-note{max-width:460px;margin:14px auto 0;font-size:.84rem}''',
'areas': r'''/* 部品：対応エリア */
.areas{list-style:none;margin:0 -4px;padding:0;display:flex;flex-wrap:wrap;justify-content:center}
.areas li{margin:5px 4px;padding:.4em 1.3em;border:1px solid var(--line);border-radius:999px;background:#fff;font-size:.92rem;letter-spacing:.08em}
.areas li.m{background:var(--primary);border-color:var(--primary);color:#fff}
.area-note{font-size:.86rem;margin:20px 0 0}''',
'video': r'''/* 部品：動画（押したときだけ読み込む） */
.vid-box{position:relative;width:100%;padding-top:56.25%;background:#000;border-radius:var(--r);overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,.12)}
.vid-box iframe,.vid-btn{position:absolute;top:0;left:0;width:100%;height:100%;border:0;display:block}
.vid-btn img{width:100%;height:100%;object-fit:cover;opacity:.85}
.vid-play{position:absolute;top:50%;left:50%;width:76px;height:76px;margin:-38px 0 0 -38px;border-radius:50%;background:rgba(255,255,255,.92)}
.vid-play::after{content:"";position:absolute;left:30px;top:22px;border-style:solid;border-width:16px 0 16px 26px;border-color:transparent transparent transparent var(--primary-deep)}
.vid-cap{font-size:.86rem;margin:14px 0 0}''',
'lightbox': r'''/* 部品：写真の拡大 */
.b-shot img,.case figure img,.card .photo img{cursor:-webkit-zoom-in;cursor:zoom-in}
.lb{display:none;position:fixed;top:0;left:0;right:0;bottom:0;z-index:200;background:rgba(0,0,0,.88);-webkit-box-align:center;align-items:center;-webkit-box-pack:center;justify-content:center;padding:16px}
.lb.on{display:-webkit-box;display:flex}
.lb-f{margin:0;max-width:100%;text-align:center}
.lb-f img{max-width:100%;max-height:82vh;width:auto;height:auto;border-radius:6px;background:#fff}
.lb-f figcaption{color:#eee;font-size:.86rem;margin-top:10px;letter-spacing:.06em}
.lb-x{position:absolute;top:10px;right:12px;width:46px;height:46px;border:0;border-radius:50%;background:rgba(255,255,255,.18);color:#fff;font-size:1.7rem;line-height:1;cursor:pointer}''',
}

# ---------- 動き（JS。var・function だけ） ----------
JS = {
'hours': r'''// 部品：営業時間。いま（日本時間）が営業中か、時間外ならいつからかを出す。JS がないときは表だけ出る
(function(){
  var b = document.getElementById('hrs-badge'); if (!b) return;
  var sc, hol;
  try { sc = JSON.parse(b.getAttribute('data-schedule')); hol = JSON.parse(b.getAttribute('data-holidays') || '[]'); } catch (err) { return; }
  var keys = ['sun','mon','tue','wed','thu','fri','sat'], word = b.getAttribute('data-word') || '営業中';
  var now = new Date(), jst = new Date(now.getTime() + (now.getTimezoneOffset() + 540) * 60000);
  function pad(n){ return n < 10 ? '0' + n : '' + n; }
  function iso(d){ return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function hm(m){ return Math.floor(m / 60) + ':' + pad(m % 60); }
  function ranges(d){
    if (hol.indexOf(iso(d)) >= 0) return [];
    var s = sc[keys[d.getDay()]]; if (!s) return [];
    var out = [], parts = String(s).replace(/\s/g, '').split(',');
    for (var i = 0; i < parts.length; i++) {
      var m = /^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$/.exec(parts[i]);
      if (m) out.push([parseInt(m[1], 10) * 60 + parseInt(m[2], 10), parseInt(m[3], 10) * 60 + parseInt(m[4], 10)]);
    }
    return out;
  }
  var mins = jst.getHours() * 60 + jst.getMinutes(), rs = ranges(jst), msg = '', on = false, i;
  for (i = 0; i < rs.length; i++) { if (mins >= rs[i][0] && mins < rs[i][1]) { on = true; msg = 'いま' + word + '（' + hm(rs[i][1]) + 'まで）'; break; } }
  if (!on) {
    for (i = 0; i < rs.length; i++) { if (rs[i][0] > mins) { msg = 'いまは時間外です（本日 ' + hm(rs[i][0]) + 'から）'; break; } }
    for (var d = 1; !msg && d <= 8; d++) {
      var nd = new Date(jst.getTime() + d * 86400000), r = ranges(nd);
      if (r.length) msg = 'いまは時間外です（次は ' + (d === 1 ? '明日' : (nd.getMonth() + 1) + '/' + nd.getDate() + '（' + '日月火水木金土'.charAt(nd.getDay()) + '）') + ' ' + hm(r[0][0]) + 'から）';
    }
  }
  if (!msg) return;
  b.textContent = msg; b.className = 'hrs-badge ' + (on ? 'on' : 'off'); b.removeAttribute('hidden');
})();''',
'video': r'''// 部品：動画。押したときに YouTube（youtube-nocookie）を読み込む。JS がなければ、押すと YouTube が開く
(function(){
  var b = document.getElementById('vid-btn'); if (!b) return;
  b.addEventListener('click', function(ev){
    ev.preventDefault();
    var f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + b.getAttribute('data-id') + '?autoplay=1&rel=0';
    f.title = b.getAttribute('data-title') || '動画';
    f.setAttribute('allow', 'autoplay; encrypted-media; picture-in-picture');
    f.setAttribute('allowfullscreen', ''); f.setAttribute('frameborder', '0');
    b.parentNode.replaceChild(f, b);
  });
})();''',
'lightbox': r'''// 部品：写真の拡大。帯・施工例・メニューの写真を押す（Enter でも）と大きく出る。外か「×」か Esc で閉じる。見比べつまみの写真は対象外
(function(){
  var SEL = '.b-shot img, .case figure img, .card .photo img';
  var box = null, big = null, cap = null, x = null, last = null;
  function isHit(t){
    if (!t || t.tagName !== 'IMG') return false;
    var m = t.matches || t.webkitMatchesSelector || t.msMatchesSelector;
    return m ? m.call(t, SEL) : false;
  }
  function build(){
    box = document.createElement('div'); box.className = 'lb';
    box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-label', '写真の拡大');
    box.innerHTML = '<button type="button" class="lb-x" aria-label="閉じる">×</button><figure class="lb-f"><img alt=""><figcaption></figcaption></figure>';
    document.body.appendChild(box);
    big = box.getElementsByTagName('img')[0]; cap = box.getElementsByTagName('figcaption')[0]; x = box.getElementsByTagName('button')[0];
    box.addEventListener('click', function(ev){ if (ev.target === box || ev.target === x) close(); });
  }
  function open(t){
    if (!box) build();
    big.src = t.currentSrc || t.src; big.alt = t.alt || ''; cap.textContent = t.alt || '';
    box.className = 'lb on'; document.body.style.overflow = 'hidden'; last = t;
    try { x.focus(); } catch (err) {}
  }
  function close(){
    if (!box) return;
    box.className = 'lb'; document.body.style.overflow = '';
    try { if (last && last.focus) last.focus(); } catch (err) {}
  }
  document.addEventListener('click', function(ev){ if (isHit(ev.target)) open(ev.target); });
  document.addEventListener('keydown', function(ev){
    var k = ev.keyCode || ev.which;
    if (k === 27) close();
    else if (k === 13 && isHit(ev.target)) open(ev.target);
  });
  var imgs = document.querySelectorAll(SEL);
  function hidden(n){ while (n && n !== document.body) { if (n.getAttribute && n.getAttribute('aria-hidden') === 'true') return true; n = n.parentNode; } return false; }
  for (var i = 0; i < imgs.length; i++) { if (hidden(imgs[i])) continue; imgs[i].setAttribute('tabindex', '0'); imgs[i].setAttribute('role', 'button'); }
})();''',
}
