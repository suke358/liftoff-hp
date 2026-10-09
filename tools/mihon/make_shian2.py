#!/usr/bin/env python3
"""shian/index.html から、切りかえ式の shian2/index.html を作る  2026/10/9（10/10 表示を速く・飛行機の動きを直した）

shian/ と同じ中身を、画面の下の5つのボタン（ホーム／できること／料金／流れ／相談）で切りかえる形にする（ファイルは1つ）。
shian/ を直したら、もう一度これを動かして shian2/ を作り直す。

shian2 だけの違い（この道具が書きかえる）：
  - 見出しの文字は最初から見える（JS で隠さない）。トップの飛行機の横切りはなし
  - Google Fonts は BIZ UDPGothic（400/700）だけ。見出しの書体は端末の Hiragino Sans
  - 飛行機は1機だけ、ヘッダーのすぐ下の線の上を、ゆっくり一定の速さで飛ぶ。画面を切りかえると、いまの位置から続けて次の画面の位置へ
    （位置は変数に持つ。動かすのは transform と requestAnimationFrame だけ。向きは進む方向。折り返しは半円を描く）

使い方:  python3 tools/mihon/make_shian2.py
"""
import re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'shian', 'index.html')
DST = os.path.join(ROOT, 'shian2', 'index.html')

# 画面の割り当て（左から順）。値は shian の <section> の id か class
SCREENS = [
    ('home',   'ホーム',     ['hero', 'worry', 'update', 'work']),
    ('dekiru', 'できること', ['can', 'trust']),
    ('ryokin', '料金',       ['price']),
    ('nagare', '流れ',       ['flow', 'faq', 'other']),
    ('soudan', '相談',       ['contact']),
]

s = open(SRC, encoding='utf-8').read()

def must(old, new, count=1):
    """必ずある文字列を置きかえる（なければ止まる。shian が変わったときに気づけるように）"""
    global s
    if old not in s: sys.exit('見つからない: ' + old[:60])
    s = s.replace(old, new, count)

# ---- <section> を切り出す（shian は section を入れ子にしていない）
secs = {}
for m in re.finditer(r'<section\b[^>]*>.*?</section>', s, re.S):
    tag = m.group(0)
    head = tag[:tag.index('>')]
    mid = re.search(r'\bid="([^"]+)"', head)
    mcl = re.search(r'\bclass="([^"]+)"', head)
    if mid: secs[mid.group(1)] = tag
    elif mcl:
        for c in mcl.group(1).split():
            if c not in ('sec', 'alt'): secs[c] = tag
missing = [k for _, _, ks in SCREENS for k in ks if k not in secs]
if missing: sys.exit('section が見つからない: ' + ', '.join(missing))

# ---- 修正依頼（2026/10/10 決定）：ご契約中のお店の入口。送り方は今までと同じメール（liftoff.358@gmail.com あて）。写真はメールに付けてもらう
IRAI_BAND = '<a class="irai-band" id="irai-band" href="#irai"><span class="in">ご契約中の<wbr>お店へ<span class="sep">｜</span>修正の<wbr>ご依頼は<wbr>こちら →</span></a>'
IRAI_SCREEN = """<!-- ===== 画面：修正のご依頼（#irai。下のタブには出さない。ホームの帯・メニューの「修正依頼」・相談の下・フッターから） ===== -->
<div class="scr" id="irai" data-name="修正のご依頼">
<section class="sec irai" aria-labelledby="irai-h">
  <div class="wrap">
    <div class="sec-head">
      <h2 id="irai-h">修正の<wbr>ご依頼<wbr><span class="nw">（ご契約中のお店）</span></h2>
      <p>直したい<wbr>所を<wbr>選んで<wbr>「メールを作る」を<wbr>押すと、<wbr>内容の<wbr>入った<wbr>メールの<wbr>画面が<wbr>開きます。<wbr>そのまま<wbr>送信してください。</p>
    </div>
    <div class="formbox irai-box" id="irai-box">
      <svg class="send-plane" id="irai-plane" aria-hidden="true" focusable="false"><path class="trail" id="irai-trail" d=""/><g class="plane" id="irai-jet"><use href="#jet" xlink:href="#jet" x="-32" y="-16" width="64" height="32"/></g></svg>
      <div class="form-top"><span>修正のご依頼票</span><span class="left" id="irai-top"></span></div>
      <form id="irai-form" action="" method="POST" novalidate>
        <label><span>お店の<wbr>名前<span class="req">必須</span></span><input name="shop" id="irai-shop" autocomplete="organization" placeholder="例：〇〇サロン"></label>
        <fieldset><legend>直したい<wbr>所<span class="opt-label">いくつでも</span></legend>
          <div class="chips">
            <label class="chip"><input type="checkbox" name="what" value="お休み・営業時間"><span>お休み・営業時間</span></label>
            <label class="chip"><input type="checkbox" name="what" value="メニュー・料金"><span>メニュー・料金</span></label>
            <label class="chip"><input type="checkbox" name="what" value="写真"><span>写真</span></label>
            <label class="chip"><input type="checkbox" name="what" value="文の直し"><span>文の直し</span></label>
            <label class="chip"><input type="checkbox" name="what" value="そのほか"><span>そのほか</span></label>
          </div>
        </fieldset>
        <label><span>ひと言<span class="opt-label">自由に</span></span><textarea name="note" id="irai-note-in" placeholder="例：来週の水曜はお休みにします"></textarea></label>
        <p class="formnote irai-photo">写真が<wbr>あるときは、<wbr>次に<wbr>開く<wbr>メールに<wbr>付けて<wbr>送ってください。</p>
        <button class="btn signal" type="submit" id="irai-btn">メールを<wbr>作る</button>
        <p class="formnote" id="irai-msg" role="status"></p>
        <p class="formnote irai-small">ご依頼には<wbr>原則<wbr>3営業日以内に<wbr>対応します。<wbr>回数は<wbr>月の<wbr>回数の<wbr>中で<wbr>数えます。</p>
      </form>
    </div>
    <!-- 最近できるようになったこと：お知らせとして並べるだけ（あおる言葉は使わない） -->
    <div class="news" id="news">
      <h3>最近<wbr>できるように<wbr>なったこと</h3>
      <ul>
        <li><b>商品ページ<wbr>（ネットで<wbr>売る）</b><p>1ページ・<wbr>商品5点までの<wbr>商品ページを<wbr>作れるように<wbr>なりました。<wbr>「購入する」<wbr>ボタン付きで、<wbr>支払いは<wbr>Square の<wbr>しくみです。<wbr><a href="#option">料金の表</a></p></li>
        <li><b>動きの<wbr>演出</b><p>お店の<wbr>ロゴや<wbr>絵に<wbr>合わせた<wbr>オリジナルの<wbr>動きを、<wbr>1か所から<wbr>付けられます。<wbr><a href="#option">料金の表</a></p></li>
        <li><b>ロゴ・<wbr>名刺・<wbr>チラシ</b><p>ホームページと<wbr>同じ<wbr>色・言葉で<wbr>そろえて<wbr>作れます。<wbr>印刷用の<wbr>データで<wbr>お渡しします。<wbr><a href="#option">料金の表</a></p></li>
      </ul>
    </div>
    <p class="next-btn"><a class="btn" href="#home">← ホームへ</a></p>
  </div>
</section>
</div>"""

# ---- 画面を組み立てる
main_start = s.index('<main id="main">') + len('<main id="main">')
main_end = s.index('</main>')
screens_html = []
for i, (sid, name, keys) in enumerate(SCREENS):
    body = '\n'.join(secs[k] for k in keys)
    nxt = ''
    if i + 1 < len(SCREENS):
        nid, nname = SCREENS[i + 1][0], SCREENS[i + 1][1]
        nxt = f'\n<p class="next-btn"><a class="btn primary" href="#{nid}">次へ：{nname} →</a></p>'
    if sid == 'soudan': nxt = '\n<p class="irai-line"><a href="#irai">ご契約中の<wbr>お店：<wbr>修正の<wbr>ご依頼 →</a></p>'
    screens_html.append(f'<!-- ===== 画面 {i+1}：{name} ===== -->\n<div class="scr" id="{sid}" data-name="{name}">\n{body}{nxt}\n</div>')
screens_html.append(IRAI_SCREEN)
s = s[:main_start] + '\n' + '\n'.join(screens_html) + '\n' + s[main_end:]

# 帯はヘッダー（固定の部分）の中、線より下。ホームの画面のときだけ出す（body の class scr-home）
must('  </div>\n</header>', '  </div>\n  ' + IRAI_BAND + '\n</header>')
# メニューの「修正依頼」は、メールを開くリンクから修正依頼の画面へ。フッターにも1行
s = re.sub(r'<a class="nav-m" href="mailto:[^"]*">修正依頼</a>', '<a class="nav-m" href="#irai">修正依頼</a>', s, count=1)
must('    <p class="copy">', '    <p class="foot-irai"><a href="#irai">ご契約中のお店：修正のご依頼 →</a></p>\n    <p class="copy">')

# ---- 下の5つのボタン（固定ボタンの代わり）
tabbar = '<nav class="tabbar" id="tabbar" aria-label="画面の切りかえ">\n' + ''.join(
    f'  <a href="#{sid}" data-scr="{sid}">{name}</a>\n' for sid, name, _ in SCREENS) + '</nav>'
s = re.sub(r'<div class="fixbar" id="fixbar">.*?</div>\n', tabbar + '\n', s, count=1, flags=re.S)

# ---- 題名・noindex はそのまま。og:url と注釈だけ変える
must('content="https://liftoff-hp.liftoff-358.workers.dev/shian/"', 'content="https://liftoff-hp.liftoff-358.workers.dev/shian2/"')
must('<!-- 試しの版（2026/10/9）。本番に入れかえるまで検索に出さない -->',
     '<!-- 試しの版・切りかえ式（2026/10/9）。tools/mihon/make_shian2.py が shian/ から作る。直すときは shian/ か、その道具を直して作り直す -->')
must('<body>', '<body class="switch">')

# ---- 【1】最初の表示を速く
# Google Fonts は BIZ UDPGothic だけ（Zen Kaku Gothic Antique・Michroma は外す）。preconnect はそのまま
s = re.sub(r'<link href="https://fonts\.googleapis\.com/css2\?[^"]*" rel="stylesheet">',
           '<link href="https://fonts.googleapis.com/css2?family=BIZ+UDPGothic:wght@400;700&display=swap" rel="stylesheet">', s, count=1)
must('--head:"Zen Kaku Gothic Antique","Hiragino Sans",sans-serif;', '--head:"Hiragino Sans","BIZ UDPGothic","Yu Gothic",sans-serif;')
s = s.replace('font-family:"Michroma",var(--head)', 'font-family:var(--head)')
# 見出しの文字を JS で隠す仕組みをやめる（最初から見える）
must('.anim .hero .rv{opacity:0}\n', '')
# トップの飛行機の横切り（SVG と JS）はなくす。飛行機は下の「1機だけ」のものに
s = re.sub(r'  <svg class="hero-plane" id="hero-plane".*?</svg>\n', '', s, count=1, flags=re.S)
s = re.sub(r'<script>\n// ===== 最初：.*?</script>\n', '', s, count=1, flags=re.S)
# 上の線の飛行機（SVG・left で動かす）→ 1機だけの飛行機（div・transform で動かす）に。使わなくなった CSS も消す
s = re.sub(r'\.hero-plane[^\n]*\n', '', s)
s = re.sub(r'\.prog-jet[^\n]*\n|\.anim \.prog-jet[^\n]*\n', '', s)
s = re.sub(r'<svg class="prog-jet" id="prog-jet".*?</svg>', '', s, count=1, flags=re.S)
must('.prog-bar{position:absolute;left:0;top:0;height:4px;width:0;background:var(--signal);border-radius:0 2px 2px 0}',
     '.prog-bar{position:absolute;left:0;top:0;height:4px;width:100%;background:var(--signal);border-radius:0 2px 2px 0;-webkit-transform-origin:0 0;transform-origin:0 0;-webkit-transform:scaleX(0);transform:scaleX(0)}')
must('<a class="skip" href="#main">本文へ</a>',
     '<a class="skip" href="#main">本文へ</a>\n'
     '<!-- 飛行機は1機だけ。ヘッダーのすぐ下の線の上を飛ぶ。位置は JS の変数に持ち、transform で動かす（top/left は動かさない） -->\n'
     '<div class="jet-sky" aria-hidden="true"></div>\n'
     '<div class="nav-jet" id="nav-jet" aria-hidden="true"><svg viewBox="-44 -10 60 20" width="60" height="20"><path d="M-42 0 H-19" stroke="#F2C230" stroke-width="2.4" stroke-dasharray="4 5" stroke-linecap="round" fill="none"/><use href="#jet" xlink:href="#jet" x="-16" y="-8" width="32" height="16"/></svg></div>')

# ---- 【診断の飛行機】shian2 では、3問そろったらその高さのまま右へまっすぐ飛んで右はしで止まる（着地しない）。答えを変えても下がらない
quiz_js = r"""// ===== 「どのプランが合う？」3問の診断（shian2 の飛び方）：答えるたびに少し上がり、3つそろったら、その高さのまま右へまっすぐ飛んで右はしで止まる =====
// 高さは答えた数で決める（どのプランでも同じ高さ・同じ飛び方）。答えを変えても下がらず、今の位置からなめらかにつなぐ。動きを減らす設定の人には最後の位置に置く
// 目安の決め方：更新が月3回以上 か Googleマップの投稿も任せたい → WEB担当者代行／初期費用をおさえたい → 初期0円プラン／それ以外 → スタンダード
(function(){
  var q = document.getElementById('quiz'), svg = document.getElementById('quiz-sky'); if (!q || !svg) return;
  var jet = document.getElementById('q-jet'), trail = document.getElementById('q-trail'), label = document.getElementById('q-label'), out = document.getElementById('quiz-out');
  var NAME = { std: 'スタンダード', zero: '初期0円プラン', web: 'WEB担当者代行' }, ID = { std: 'price-std', zero: 'price-zero', web: 'price-web' }, TAB = { std: 'pt-std', zero: 'pt-zero', web: 'pt-web' };
  var W = 0, H = 74, cur = [0, 0], pts = [], landed = null, stage = 0, busy = false, seg = [];
  function val(n){ var el = q.querySelector('input[name=' + n + ']:checked'); return el ? el.value : null; }
  function setup(){
    W = Math.round(svg.getBoundingClientRect().width) || 300; svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    var g = document.getElementById('q-ground'), l = document.getElementById('q-lights');
    g.setAttribute('x1', 12); g.setAttribute('y1', H - 10); g.setAttribute('x2', W - 12); g.setAttribute('y2', H - 10);
    l.setAttribute('x1', 16); l.setAttribute('y1', H - 14); l.setAttribute('x2', W - 16); l.setAttribute('y2', H - 14);
    label.setAttribute('x', W - 14); label.setAttribute('y', H - 32);
    // 止まる所：出発 → 1問目 → 2問目 → 3問目（少しずつ上がる）→ 右はし（同じ高さのまま）
    pts = [[28, H - 22], [W * .28, H - 36], [W * .46, H - 48], [W * .62, H - 58], [W - 52, H - 58]];
  }
  function put(p, a){ jet.setAttribute('transform', 'translate(' + p[0].toFixed(1) + ' ' + p[1].toFixed(1) + ') rotate(' + (a || 0) + ') scale(.75)'); }
  function drawTrail(){ var d = '', i; for (i = 0; i < seg.length; i++) d += (i ? ' L' : 'M') + seg[i][0].toFixed(1) + ' ' + seg[i][1].toFixed(1); trail.setAttribute('d', d); }
  function flyTo(p, done){
    var from = cur.slice(); busy = true;
    tween(500, function(u){
      var x = from[0] + (p[0] - from[0]) * u, y = from[1] + (p[1] - from[1]) * u;
      cur = [x, y]; put(cur, Math.atan2(p[1] - from[1], p[0] - from[0]) * 180 / Math.PI * .5);
      if (seg.length > 60) seg.shift(); seg.push([x, y]); drawTrail();
    }, function(){ cur = p.slice(); put(cur, 0); busy = false; if (done) done(); }, easeInOut);
  }
  function pick(k){
    var tabs = document.querySelectorAll('#ptabs [role=tab]'), i;
    for (i = 0; i < tabs.length; i++) tabs[i].className = tabs[i].id === TAB[k] ? 'fit-on' : '';
    if (window.pickPlan) window.pickPlan(ID[k], true);
    label.textContent = NAME[k];
    out.innerHTML = '<b>目安</b>' + NAME[k] + 'が合いそうです。相談で一緒に決めます。';
  }
  function update(){
    if (busy) { setTimeout(update, 120); return; }
    var a = val('q1'), b = val('q2'), c = val('q3'), n = (a ? 1 : 0) + (b ? 1 : 0) + (c ? 1 : 0);
    if (n < 3) { out.textContent = n ? 'あと' + (3 - n) + 'つ' : ''; if (n !== stage) { stage = n; flyTo(pts[n]); } return; }
    var k = (a === '4' || b === 'yes') ? 'web' : (c === 'yes' ? 'zero' : 'std');
    if (landed) { landed = k; pick(k); return; } // 3問そろったあとに答えを変えた：位置はそのまま、プラン名だけ変える
    landed = k; stage = 4;
    flyTo(pts[3], function(){ flyTo(pts[4], function(){ pick(k); }); });
  }
  setup(); cur = pts[0].slice(); seg = [cur.slice()]; put(cur, 0);
  q.addEventListener('change', update);
  window.addEventListener('resize', function(){ setTimeout(function(){ setup(); cur = pts[stage].slice(); seg = [cur.slice()]; put(cur, 0); drawTrail(); }, 80); });
})();
"""
s = re.sub(r'// ===== 「どのプランが合う？」3問の診断：.*?\n\}\)\(\);\n(?=// ===== 上の細い進み具合の線)', quiz_js, s, count=1, flags=re.S)
if 'shian2 の飛び方' not in s: sys.exit('診断の JS を差しかえられなかった')

# ---- 【商品ページ】別料金のメニューに「商品ページの追加」を足す（2026/10/10 決定。今の本番トップには入れない。shian2 を本体にするときに入る）
# 料金の表に1行（通常の列は「—」。動きの演出と同じ扱い）
must('<tr><td>ホームページの<wbr>動きの<wbr>演出<wbr><span class="nw">（1か所）</span></td><td>—</td><td><b>16,500円〜</b></td></tr>',
     '<tr><td>ホームページの<wbr>動きの<wbr>演出<wbr><span class="nw">（1か所）</span></td><td>—</td><td><b>16,500円〜</b></td></tr>\n'
     '            <tr><td>商品ページの<wbr>追加<wbr><span class="nw">（1ページ・</span><wbr><span class="nw">商品5点まで）</span></td><td>—</td><td><b>22,000円〜</b></td></tr>')
# 表の下の注に1つ
s = re.sub(r'(<li>動きの<wbr>演出は、.*?</li>)',
           r'\1\n          <li>商品ページは、<wbr>「購入する」<wbr>ボタンと<wbr>特定商取引法の<wbr>表示の<wbr>ページ込みです。<wbr>ホームページを<wbr>ご契約の<wbr>お店だけの<wbr>メニューです。<wbr>商品の<wbr>追加・<wbr>入れかえは<wbr>更新1回です。<wbr>6点以上や、<wbr>配送・<wbr>在庫の<wbr>管理が<wbr>要るときは、<wbr>作る<wbr>前に<wbr>金額を<wbr>お伝えします。</li>',
           s, count=1, flags=re.S)
if '商品ページは、' not in s: sys.exit('注を足せなかった')
# よくある質問「あわせて頼めること」に1つ
s = re.sub(r'(<details class="acc"><summary>ロゴや<wbr>名刺、<wbr>チラシも.*?</details>)',
           r'\1\n        <details class="acc"><summary>ネットで<wbr>商品を<wbr>売れますか？<i class="pm" aria-hidden="true"><b></b><b></b></i></summary><div class="acc-body"><div class="acc-in"><p>できます。<wbr>商品ページ<wbr>1ページ・<wbr>商品5点までで<wbr>22,000円〜<wbr>（ホームページを<wbr>ご契約の<wbr>お店）です。<wbr>支払いは<wbr>Square の<wbr>しくみで、<wbr>手数料は<wbr>お店から<wbr>Square へ<wbr>お支払い<wbr>いただきます。<wbr>売る<wbr>物や<wbr>点数を<wbr>うかがって、<wbr>作る<wbr>前に<wbr>金額を<wbr>お伝えします。</p></div></div></details>',
           s, count=1, flags=re.S)
if 'ネットで<wbr>商品を<wbr>売れますか' not in s: sys.exit('質問を足せなかった')

# ---- 切りかえ式だけの CSS
css = '''
/* ---------- 切りかえ式（shian2）：画面を1つずつ見せる。下の5つのボタンで切りかえる ---------- */
.scr{display:none}
.scr.on{display:block}
.next-btn{text-align:center;padding:8px 20px 56px}
.next-btn .btn{min-width:260px}
.tabbar{position:fixed;left:0;right:0;bottom:0;z-index:30;display:flex;background:rgba(255,255,255,.97);border-top:1px solid var(--line);padding-bottom:env(safe-area-inset-bottom)}
.tabbar a{flex:1 1 0;text-align:center;text-decoration:none;color:var(--muted);font-family:var(--head);font-weight:700;font-size:13px;padding:12px 2px 10px;min-height:56px;border-top:3px solid transparent;line-height:1.3}
.tabbar a.on{color:var(--ink);border-top-color:var(--signal)}
.tabbar a[data-scr="soudan"]{color:var(--ink);background:#FFF4CC}
.tabbar a[data-scr="soudan"].on{background:var(--signal)}
footer{padding-bottom:96px}
@media (max-width:760px){footer{padding-bottom:96px}.top .top-right .btn{display:inline-flex}}
/* 修正依頼（ご契約中のお店の入口）：帯は控えめ（相談の入口より目立たせない） */
.irai-band{display:none;color:var(--ink);font-family:var(--head);font-weight:700;font-size:15px;text-decoration:none;padding:34px 0 0;line-height:1.5}
/* ヘッダーの中、線（66〜70px）のすぐ下。上の 34px は飛行機が通る所（透明。右向き 70px・左向き 80px、機体の一番下は中心＋6px → 86px まで）。
   文字の行（.in）は白い地で、飛行機（z-index 22）より手前（ヘッダー全体が z-index 24）。入ってくる途中の飛行機は文字の行の後ろを通って隠れる。文字は 100px から（飛行機の一番下との間 14px 以上） */
.irai-band .in{display:block;text-align:center;background:#fff;padding:6px 16px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.scr-home .irai-band{display:block}
/* ヘッダーの帯（0〜66px）の地色は ::before に移し（飛行機は帯の中を飛ばない）、ヘッダー自体は透明にして、飛行機が通る所に地色が付かないようにする */
.top{position:fixed;left:0;right:0;top:0;background:transparent;-webkit-backdrop-filter:none;backdrop-filter:none;border-bottom:none;z-index:24}
/* ヘッダーは固定（本文に重ねる）。本文の上の空きは JS がヘッダーの実際の高さを測って main の padding-top に入れる（sticky だと iPhone の Safari で、帯が出たあとの高さが本文に反映されないことがあった） */
main{padding-top:66px}
@media (max-width:760px){.hero{padding-top:24px}} /* 帯の下と見出しの間：スマホは 24px */
.top::before{content:"";position:absolute;left:0;right:0;top:0;height:66px;background:rgba(255,255,255,.95);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);z-index:-1}
/* 飛行機が通る所の白い地（ホームの画面だけ。飛行機より後ろ、本文より手前） */
.jet-sky{position:fixed;left:0;right:0;top:66px;height:34px;background:#fff;z-index:19;display:none}
.scr-home .jet-sky{display:block}
html{scroll-padding-top:130px}
.irai-band .in::before{content:"";display:inline-block;width:10px;height:10px;border-radius:3px;background:var(--signal);margin-right:8px;vertical-align:1px}
.irai-band .sep{color:#9fb6c6;margin:0 4px;font-weight:400}
.irai-band:hover{color:var(--sea)}
.irai-line{text-align:center;padding:0 20px 24px;font-size:15px}
.irai-line a{color:var(--sea)}
.foot-irai{grid-column:1 / -1;font-size:14px}
.foot-irai a{color:#dbe6ee;text-decoration:underline}
.irai .sec-head h2{padding-top:18px}
.irai-box{max-width:560px;color:#fff} /* 紺の地なので、項目の名前（お店の名前・直したい所・ひと言）も白に。相談の画面は .contact{color:#fff} で同じになっている */
.irai-photo{background:rgba(242,194,48,.14);color:#fff;border-radius:10px;padding:10px 14px}
.irai-small{color:#c3d2dd}
.news{max-width:560px;margin-top:28px;border:2px solid var(--ink);border-radius:18px;padding:18px 20px 8px;background:var(--paper)}
.news h3{font-size:18px;margin-bottom:6px}
.news ul{list-style:none}
.news li{padding:10px 0 12px;border-top:1px solid var(--line)}
.news li b{display:block;font-family:var(--head);font-size:16px;margin-bottom:2px}
.news li p{font-size:15px;color:var(--ink-2);line-height:1.75}
.news li a{color:var(--sea)}
@media (max-width:760px){.irai-band{font-size:14px}.irai-band .in{padding:6px 12px}}
.totop{bottom:84px}
.prog-seg{position:absolute;top:0;height:4px;width:1px;background:rgba(23,40,58,.25)}
/* 1機だけの飛行機：画面に固定。左上を原点にして transform で動かす。中の絵は機体の中心が原点に来るようにずらす */
.nav-jet{position:fixed;left:0;top:0;width:0;height:0;z-index:22;pointer-events:none;will-change:transform;-webkit-transform:translate3d(-200px,-200px,0);transform:translate3d(-200px,-200px,0)}
.nav-jet svg{display:block;width:60px;max-width:none;margin:-10px 0 0 -44px;overflow:visible}
</style>'''
must('</style>', css)

# ---- 切りかえの JS（共通の道具 tween などの次に入れて、最初の画面をすぐ出す）
js = r'''
<script>
// ===== 切りかえ式：画面を1つずつ見せる。URL の #ryokin などで画面を覚え、スマホの「戻る」で前の画面に戻る =====
(function(){
  var IDS = ['home', 'dekiru', 'ryokin', 'nagare', 'soudan'], ALL = IDS.concat(['irai']), cur = null; // irai：タブのない画面（修正のご依頼）。飛行機と線はホームの位置
  function tabIndex(id){ var i = IDS.indexOf(id); return i < 0 ? 0 : i; }
  var bar = document.getElementById('tabbar'), prog = document.getElementById('prog'), pbar = document.getElementById('prog-bar');
  function el(id){ return document.getElementById(id); }
  function screenOf(node){ while (node && node !== document.body) { if (node.className && String(node.className).indexOf('scr') === 0) return node.id; node = node.parentNode; } return null; }
  for (var k = 1; k < IDS.length; k++) { var seg = document.createElement('i'); seg.className = 'prog-seg'; seg.style.left = (k / IDS.length * 100) + '%'; prog.appendChild(seg); }
  function render(id){
    for (var i = 0; i < ALL.length; i++) { var sc = el(ALL[i]); if (sc) sc.className = ALL[i] === id ? 'scr on' : 'scr'; }
    var links = bar.querySelectorAll('a'); for (i = 0; i < links.length; i++) links[i].className = links[i].getAttribute('data-scr') === id ? 'on' : '';
    cur = id; document.body.className = 'switch scr-' + id;
    setTf(pbar, 'scaleX(' + ((tabIndex(id) + 1) / IDS.length).toFixed(3) + ')'); // 上の線：今の画面の所まで黄色
    if (window.jetGo) window.jetGo(tabIndex(id));
    if (id === 'ryokin' && window.layoutPlan) setTimeout(window.layoutPlan, 0);
    fitHome();
  }
  // ヘッダーは固定（本文に重ねる）ので、本文の上の空きはヘッダーの実際の高さ（帯があるときは帯込み）を測って付ける（決め打ちの数字にしない）
  // ホームの画面：帯の下と見出しの間は hero の padding-top（スマホ 24px・パソコン 64px）
  function fitHome(){
    var top = document.querySelector('.top'), main = el('main'); if (!top || !main) return;
    var h = top.offsetHeight;
    main.style.paddingTop = h + 'px';
    document.documentElement.style.scrollPaddingTop = (h + 16) + 'px';
  }
  window.fitHome = fitHome;
  function go(id, push){
    if (ALL.indexOf(id) < 0) id = 'home';
    if (push) { try { history.pushState(null, '', '#' + id); } catch (e) { location.hash = id; } }
    if (id === cur) return;
    render(id); window.scrollTo(0, 0);
  }
  // ページの中のリンク（#price-zero・#option・#contact など）：その場所がある画面に切りかえてから、開く・飛ぶ
  document.addEventListener('click', function(e){
    var a = e.target.closest ? e.target.closest('a') : null; if (!a) return;
    var h = a.getAttribute('href'); if (!h || h.charAt(0) !== '#') return;
    e.preventDefault();
    var id = h.slice(1);
    if (!id) { go('home', true); return; }
    if (ALL.indexOf(id) >= 0) { go(id, true); return; }
    var target = el(id); if (!target) return;
    var sid = screenOf(target) || cur;
    if (sid !== cur) go(sid, true);
    setTimeout(function(){ if (window.revealTarget) window.revealTarget(id); else { try { target.scrollIntoView(); } catch (err) {} } }, 30);
  });
  window.addEventListener('popstate', function(){ var id = location.hash.replace('#', ''); if (ALL.indexOf(id) < 0) { var t = id && el(id); id = (t && screenOf(t)) || 'home'; } if (id !== cur) { render(id); window.scrollTo(0, 0); } });
  // 最初の画面：URL の # で決める（#option のような中の場所なら、その画面を出してから開く）
  var first = location.hash.replace('#', ''), inner = null;
  if (ALL.indexOf(first) < 0) { var t0 = first && el(first); inner = t0 ? first : null; first = (t0 && screenOf(t0)) || 'home'; }
  render(first);
  if (inner) setTimeout(function(){ if (window.revealTarget) window.revealTarget(inner); }, 120);
  window.addEventListener('resize', function(){ if (window.jetGo) window.jetGo(tabIndex(cur)); fitHome(); });
  window.addEventListener('load', fitHome); setTimeout(fitHome, 300); // 書体が読み込まれて帯の高さが変わったあとにも合わせる
})();
// ===== 修正のご依頼（#irai）：選んだ内容とひと言の入ったメールを開く（liftoff.358@gmail.com あて。件名は今までと同じ「ホームページの修正のご依頼」。店名は本文の1行目） =====
// URL に ?shop=〇〇 のように付いていたら、その文字をそのままお店の名前の欄に入れる（日本語も可。実在のお店の名前はソースに書かない。長すぎる・おかしな文字は入れない）
(function(){
  var form = document.getElementById('irai-form'); if (!form) return;
  var MAIL = 'liftoff.358@gmail.com', SUBJECT_HEAD = 'ホームページの修正のご依頼';
  var shop = document.getElementById('irai-shop'), msg = document.getElementById('irai-msg'), btn = document.getElementById('irai-btn'), box = document.getElementById('irai-box');
  var m = /[?&]shop=([^&#]+)/.exec(location.search || '');
  if (m) { var k = ''; try { k = decodeURIComponent(m[1].replace(/\+/g, ' ')); } catch (err) { k = ''; }
    k = k.replace(/[\x00-\x1f<>"'`\\]/g, '').replace(/^\s+|\s+$/g, ''); if (k.length > 40) k = ''; shop.value = k; }
  function build(){
    var what = [], els = form.querySelectorAll('input[name=what]'), i;
    for (i = 0; i < els.length; i++) if (els[i].checked) what.push(els[i].value);
    var name = shop.value.replace(/^\s+|\s+$/g, ''), note = document.getElementById('irai-note-in').value.replace(/^\s+|\s+$/g, '');
    var body = 'お店：' + name + '\n直したい所：' + (what.length ? what.join('、') : '（未選択）') + '\nひと言：' + (note || '（なし）') + '\n\n写真があるときは、このメールに付けて送ってください。';
    return 'mailto:' + MAIL + '?subject=' + encodeURIComponent(SUBJECT_HEAD) + '&body=' + encodeURIComponent(body);
  }
  // 送るときの飛行機：相談のフォームと同じ動き（右上へ飛んで黄色い飛行機雲）。動きを減らす設定の人には飛ばさない
  function fly(done){
    var svg = document.getElementById('irai-plane'), jet = document.getElementById('irai-jet'), trail = document.getElementById('irai-trail');
    if (STILL || !svg || !jet) { done(); return; }
    var r = box.getBoundingClientRect(), W = Math.round(r.width), H = Math.round(r.height), b = btn.getBoundingClientRect();
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); svg.style.height = H + 'px'; svg.setAttribute('class', 'send-plane on');
    var x0 = b.left - r.left + b.width / 2, y0 = b.top - r.top, x1 = W + 80, y1 = -60, cx = x0 + (x1 - x0) * .25, cy = y0 - (y0 - y1) * .02;
    function at(u){ var a = 1 - u; return [a * a * x0 + 2 * a * u * cx + u * u * x1, a * a * y0 + 2 * a * u * cy + u * u * y1]; }
    tween(1000, function(u){
      var p = at(u), a = 1 - u, dx = 2 * a * (cx - x0) + 2 * u * (x1 - cx), dy = 2 * a * (cy - y0) + 2 * u * (y1 - cy);
      jet.setAttribute('transform', 'translate(' + p[0].toFixed(1) + ' ' + p[1].toFixed(1) + ') rotate(' + (Math.atan2(dy, dx) * 180 / Math.PI).toFixed(1) + ') scale(' + (.9 + u * .5).toFixed(2) + ')');
      var d = 'M' + x0 + ' ' + y0, k, n = Math.max(2, Math.round(u * 20));
      for (k = 1; k <= n; k++) { var t = at(u * k / n); d += ' L' + t[0].toFixed(1) + ' ' + t[1].toFixed(1); }
      trail.setAttribute('d', d);
    }, function(){ svg.setAttribute('class', 'send-plane'); done(); }, easeInOut);
  }
  form.addEventListener('submit', function(e){
    e.preventDefault();
    if (!shop.value.replace(/\s/g, '')) { msg.textContent = 'お店の名前を入れてください。'; shop.focus(); return; }
    var href = build(); window.iraiLastMailto = href; // 確かめる用
    btn.disabled = true;
    fly(function(){
      msg.textContent = 'メールの画面を開きます。写真を付けて送信してください。「開く」を押すと、メールのアプリが開きます。';
      btn.disabled = false;
      setTimeout(function(){ location.href = href; }, 300);
    });
  });
})();
// ===== 飛行機は1機だけ：ヘッダーのすぐ下の線の上を飛ぶ。切りかえの移動は「どこへでも約1.5秒で着く」（遠いほど速い。動き出しと止まる所は少しゆっくり。折り返しの旋回も1.5秒の中） =====
// 開いたときは1回だけ、画面の右下の外から、画面の中ほどを通る大きなゆるいカーブで左上へ上がり、線に乗って今の画面のタブの位置で止まる（約3秒。動き出しと止まる所はゆっくり、途中は速め）
// 画面を切りかえると、いまの位置から続けて、その画面の位置（5つに区切った線のまん中）へ。位置は変数 pos に持つ
// 右へ飛ぶときは線の高さ、左へ飛ぶときはその 10px 下。折り返しは半円を描いて機首を 180 度なめらかに回す。向きは常に進む方向
// 上下の反転は「いま右へ進んでいるか、左へ進んでいるか」（moveDir）で決める：右へ進むときは必ず背中が上。角度は毎回 -180〜180 度にそろえる（足され続けない）
// 動かすのは transform と requestAnimationFrame だけ。動きを減らす設定の人には、その画面の位置に止めて置く
(function(){
  var jet = document.getElementById('nav-jet'); if (!jet) return;
  var N = 5, Y_R = 70, Y_L = 80, R = 5, FLY_MS = 1500, ENTRY_MS = 3000; // 右向きは線のすぐ下 70px、左向きはその 10px 下 80px（機体の一番下は中心＋6px。帯の文字 100px〜との間 14px 以上）
  var pos = { x: -200, y: -200, a: 0 }, path = [], last = null, raf = 0, entered = false, turn = 0, moveDir = 1, entry = null, fly = null;
  function norm(a){ while (a > 180) a -= 360; while (a <= -180) a += 360; return a; }
  function xOf(i){ return (i + .5) / N * document.documentElement.clientWidth; }
  // 向き a で回したあと、上下を f 倍にする：右へ進んでいれば +（そのまま）、左へ進んでいれば -（上下反転＝背中が上・機首が進む向き）。
  // 曲がっている最中（turn＝1px 進むあいだに何度向きが変わるか）は f を 0 に近づけて、旋回して傾いているように見せる。
  // 折り返しの半円は強く曲がるので、左右が入れかわる瞬間は f がほぼ 0 → パッと切りかわって見えない
  function apply(){ var f = moveDir * Math.max(.1, 1 - turn / 3.5); setTf(jet, 'translate3d(' + pos.x.toFixed(1) + 'px,' + pos.y.toFixed(1) + 'px,0) rotate(' + pos.a.toFixed(1) + 'deg) scaleY(' + f.toFixed(3) + ')'); }
  // 1歩すすめる：目標の点へ向けて d px。向きは進む方向へ少しずつ。左右の向きは実際の動きで決める
  function moveTo(p, d){
    var dx = p[0] - pos.x, dy = p[1] - pos.y, L = Math.sqrt(dx * dx + dy * dy);
    if (L < .01) return 0;
    var step = Math.min(L, d), ang = Math.atan2(dy, dx) * 180 / Math.PI, da = norm(ang - pos.a);
    var turned = da * Math.min(1, step / 6); pos.a = norm(pos.a + turned);
    turn += (Math.abs(turned) / Math.max(.5, step) - turn) * .25;
    if (Math.abs(dx) > .01) moveDir = dx > 0 ? 1 : -1;
    pos.x += dx / L * step; pos.y += dy / L * step;
    return step;
  }
  function heading(){ return moveDir; } // 今の向き：1 右、-1 左
  // いまの位置・向きから目標の x まで、なめらかな道筋を作る
  function plan(tx){
    path = [];
    var dir = heading(), need = tx >= pos.x ? 1 : -1, y0 = pos.y, y1 = need > 0 ? Y_R : Y_L, i;
    if (Math.abs(tx - pos.x) < 1) return; // もう同じ位置なら動かない（向きが左でも折り返さない。#irai でホームの位置を指すときなど）
    if (dir !== need) {
      // 折り返し：進んでいる方へふくらむ半円で、もう一方の高さへ（向きが 180 度なめらかに変わる）
      var r = Math.abs(y1 - y0) / 2 || R, n = 16;
      for (i = 1; i <= n; i++) { var t = Math.PI * i / n; path.push([pos.x + dir * Math.sin(t) * r, y0 + (y1 - y0) / 2 * (1 - Math.cos(t))]); }
    } else if (Math.abs(y1 - y0) > 1) {
      // 同じ向きのまま高さだけ違うとき：ゆるい S 字で高さを合わせる
      var n2 = 12, len = Math.min(80, Math.abs(tx - pos.x) * .5);
      for (i = 1; i <= n2; i++) { var u = i / n2; path.push([pos.x + need * len * u, y0 + (y1 - y0) * (u * u * (3 - 2 * u))]); }
    }
    path.push([tx, y1]);
    // 道のりの長さを測って、約 FLY_MS で着くようにする（時間で進める）
    var L = 0, prev = [pos.x, pos.y]; for (i = 0; i < path.length; i++) { L += Math.sqrt((path[i][0] - prev[0]) * (path[i][0] - prev[0]) + (path[i][1] - prev[1]) * (path[i][1] - prev[1])); prev = path[i]; }
    fly = { t0: null, L: L, flown: 0 };
  }
  // 線の上の飛び方：時間で進める。進み具合は「ゆっくり→速め→ゆっくり」（smoothstep）。遠いほど速く飛んで、どこへでも約1.5秒
  function advance(ts){
    if (!fly) { path = []; return false; }
    if (fly.t0 === null) fly.t0 = ts;
    var u = Math.min(1, (ts - fly.t0) / FLY_MS), e = u * u * (3 - 2 * u), d = fly.L * e - fly.flown;
    while (d > 0 && path.length) { var moved = moveTo(path[0], d); if (moved === 0) { path.shift(); continue; } fly.flown += moved; d -= moved; if (moved < .01) break; if (Math.abs(path[0][0] - pos.x) < .01 && Math.abs(path[0][1] - pos.y) < .01) path.shift(); }
    apply();
    if (u >= 1 || !path.length) { if (path.length) { var last2 = path[path.length - 1]; pos.x = last2[0]; pos.y = last2[1]; } path = []; fly = null; return false; }
    return true;
  }
  function step(ts){
    raf = 0;
    if (last === null) last = ts;
    var more;
    try { more = entry ? entryStep(ts) : advance(ts); }
    catch (err) { if (entry) entryFinish(); path = []; more = false; }
    last = ts;
    if (more) raf = requestAnimationFrame(step); else { last = null; turn = 0; if (!entry) pos.a = moveDir > 0 ? 0 : 180; apply(); } // 止まったら向きを線にぴったりそろえる
  }
  function kick(){ if (!raf) { last = null; raf = requestAnimationFrame(step); } }
  // ---- 開いたときの入り方：右下の外 → 画面の中ほど → 左上 → 線に乗って目標（3次ベジェ。長さで等分して、時間はゆっくり→速め→ゆっくり）
  function bez(P, t){ var a = 1 - t; return [a * a * a * P[0][0] + 3 * a * a * t * P[1][0] + 3 * a * t * t * P[2][0] + t * t * t * P[3][0], a * a * a * P[0][1] + 3 * a * a * t * P[1][1] + 3 * a * t * t * P[2][1] + t * t * t * P[3][1]]; }
  function planEntry(tx){
    var W = document.documentElement.clientWidth, VH = window.innerHeight || 800;
    // 画面のまん中（幅の半分・高さの半分あたり）を通るように、2つの制御点を置く。目標が左寄りなら左向きで線に乗る（その高さは Y_L）、右寄りなら右向き（Y_R）
    var leftEnd = tx < W * .32, P = [[W + 50, VH + 30], [W * .6, VH * .8], [W * .32, 60], [tx, leftEnd ? Y_L : Y_R]], pts = [], cum = [], i, L = 0;
    for (i = 0; i <= 120; i++) { var q = bez(P, i / 120); if (i) L += Math.sqrt((q[0] - pts[i - 1][0]) * (q[0] - pts[i - 1][0]) + (q[1] - pts[i - 1][1]) * (q[1] - pts[i - 1][1])); pts.push(q); cum.push(L); }
    entry = { pts: pts, cum: cum, L: L, t0: null, tx: tx, leftEnd: leftEnd };
    pos = { x: P[0][0], y: P[0][1], a: Math.atan2(P[1][1] - P[0][1], P[1][0] - P[0][0]) * 180 / Math.PI }; moveDir = -1; turn = 0;
  }
  function entryAt(u){ // 道のり u（0〜1）の点（pts[i] までの道のりが cum[i]。i は 1〜最後）
    var sL = Math.max(0, Math.min(1, u)) * entry.L, i = 1; while (i < entry.pts.length - 1 && entry.cum[i] < sL) i++;
    var a = entry.pts[i - 1], b = entry.pts[i], seg = entry.cum[i] - entry.cum[i - 1], k = seg > 0 ? (sL - entry.cum[i - 1]) / seg : 0;
    return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];
  }
  // 入り方の終わり：線の上の決まった位置に置く。入ってくる途中にタブが押されていたら（nextTx）、そのまま線にそってそこへ続けて飛ぶ
  function entryFinish(){ var d = entry.leftEnd ? -1 : 1, nx = entry.nextTx; pos = { x: entry.tx, y: d > 0 ? Y_R : Y_L, a: d > 0 ? 0 : 180 }; moveDir = d; turn = 0; entry = null; path = []; apply(); if (nx !== undefined) { plan(nx); if (path.length) kick(); } }
  function entryStep(ts){
    if (entry.t0 === null) entry.t0 = ts;
    var u = Math.min(1, (ts - entry.t0) / ENTRY_MS), e = u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; // 動き出しと止まる所はゆっくり、途中は速め
    var p = entryAt(e), q = entryAt(Math.min(1, e + .004)), dx = q[0] - p[0], dy = q[1] - p[1];
    var moved = Math.sqrt((p[0] - pos.x) * (p[0] - pos.x) + (p[1] - pos.y) * (p[1] - pos.y));
    if (dx * dx + dy * dy > .0001) { var da = norm(Math.atan2(dy, dx) * 180 / Math.PI - pos.a); var turned = da * .25; pos.a = norm(pos.a + turned); turn += (Math.abs(turned) / Math.max(.5, moved) - turn) * .15; if (Math.abs(dx) > .001) moveDir = dx > 0 ? 1 : -1; }
    pos.x = p[0]; pos.y = p[1];
    apply();
    if (u >= 1) { entryFinish(); return false; }
    return true;
  }
  window.jetGo = function(i){
    var tx = xOf(i);
    if (STILL) { pos = { x: tx, y: Y_R, a: 0 }; moveDir = 1; turn = 0; path = []; fly = null; entry = null; apply(); entered = true; return; } // 動きなし：入ってくる動きなしで、その画面の位置に置く
    if (!entered) { entered = true; planEntry(tx); apply(); kick(); return; }
    if (entry) { entry.nextTx = tx; return; } // 入ってくる途中に切りかえた：入り方は最後まで飛んで、そのあと線にそって新しい行き先へ
    plan(tx); if (path.length) kick();
  };
  // 確かめる用（確認画像・JS での確認）
  window.jetPose = function(x, y, a, t, dir){ pos = { x: x, y: y, a: a }; turn = t || 0; if (dir) moveDir = dir; path = []; fly = null; entry = null; apply(); };
  window.jetEntryPose = function(u, i){ planEntry(xOf(i || 0)); if (u >= 1) { entryFinish(); return; } var e = u, p = entryAt(e), q = entryAt(Math.min(1, e + .004)); pos = { x: p[0], y: p[1], a: Math.atan2(q[1] - p[1], q[0] - p[0]) * 180 / Math.PI }; moveDir = q[0] >= p[0] ? 1 : -1; turn = 0; entry = null; path = []; fly = null; apply(); }; // 置いたあとは入り方の動きを止める（画像を撮る用）
  window.jetSim = function(ms){ var t = 0; while (t < ms && path.length) { t += 16; advance(t); } turn = 0; apply(); return { x: Math.round(pos.x), y: Math.round(pos.y), a: Math.round(pos.a), dir: moveDir, left: path.length }; };
  window.jetTick = function(ts){ step(ts); return { raf: raf, last: last, entry: !!entry, left: path.length, x: Math.round(pos.x), y: Math.round(pos.y), a: Math.round(pos.a) }; }; // 確かめる用：描画の1コマを手で回す
  window.jetState = function(){ return { x: pos.x, y: pos.y, a: pos.a, dir: moveDir, turn: turn, left: path.length, entry: !!entry }; };
  apply();
  window.jetGo(['home', 'dekiru', 'ryokin', 'nagare', 'soudan'].indexOf(document.querySelector('.scr.on') ? document.querySelector('.scr.on').id : 'home'));
  document.addEventListener('visibilitychange', function(){ if (!document.hidden && (path.length || entry) && !raf) { last = null; if (entry) entry.t0 = null; raf = requestAnimationFrame(step); } });
})();
</script>'''
anchor = '<script>\n// ===== こんなこと：'
must(anchor, js + '\n' + anchor)
# 最初の画面の飛行機は、切りかえの JS が出す（render → jetGo）。切りかえの JS は jetGo より前に動くので、最初の1回だけあとから呼ぶ
# （最初の1回の jetGo は、飛行機の JS の中で呼ぶ）

os.makedirs(os.path.dirname(DST), exist_ok=True)
open(DST, 'w', encoding='utf-8').write(s)
print('作った:', os.path.relpath(DST, ROOT), '画面', len(SCREENS), '／ section', len(secs))
