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
    screens_html.append(f'<!-- ===== 画面 {i+1}：{name} ===== -->\n<div class="scr" id="{sid}" data-name="{name}">\n{body}{nxt}\n</div>')
s = s[:main_start] + '\n' + '\n'.join(screens_html) + '\n' + s[main_end:]

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
  var IDS = ['home', 'dekiru', 'ryokin', 'nagare', 'soudan'], cur = null;
  var bar = document.getElementById('tabbar'), prog = document.getElementById('prog'), pbar = document.getElementById('prog-bar');
  function el(id){ return document.getElementById(id); }
  function screenOf(node){ while (node && node !== document.body) { if (node.className && String(node.className).indexOf('scr') === 0) return node.id; node = node.parentNode; } return null; }
  for (var k = 1; k < IDS.length; k++) { var seg = document.createElement('i'); seg.className = 'prog-seg'; seg.style.left = (k / IDS.length * 100) + '%'; prog.appendChild(seg); }
  function render(id){
    for (var i = 0; i < IDS.length; i++) { var sc = el(IDS[i]); if (sc) sc.className = IDS[i] === id ? 'scr on' : 'scr'; }
    var links = bar.querySelectorAll('a'); for (i = 0; i < links.length; i++) links[i].className = links[i].getAttribute('data-scr') === id ? 'on' : '';
    cur = id;
    setTf(pbar, 'scaleX(' + ((IDS.indexOf(id) + 1) / IDS.length).toFixed(3) + ')'); // 上の線：今の画面の所まで黄色
    if (window.jetGo) window.jetGo(IDS.indexOf(id));
    if (id === 'ryokin' && window.layoutPlan) setTimeout(window.layoutPlan, 0);
  }
  function go(id, push){
    if (IDS.indexOf(id) < 0) id = 'home';
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
    if (IDS.indexOf(id) >= 0) { go(id, true); return; }
    var target = el(id); if (!target) return;
    var sid = screenOf(target) || cur;
    if (sid !== cur) go(sid, true);
    setTimeout(function(){ if (window.revealTarget) window.revealTarget(id); else { try { target.scrollIntoView(); } catch (err) {} } }, 30);
  });
  window.addEventListener('popstate', function(){ var id = location.hash.replace('#', ''); if (IDS.indexOf(id) < 0) { var t = id && el(id); id = (t && screenOf(t)) || 'home'; } if (id !== cur) { render(id); window.scrollTo(0, 0); } });
  // 最初の画面：URL の # で決める（#option のような中の場所なら、その画面を出してから開く）
  var first = location.hash.replace('#', ''), inner = null;
  if (IDS.indexOf(first) < 0) { var t0 = first && el(first); inner = t0 ? first : null; first = (t0 && screenOf(t0)) || 'home'; }
  render(first);
  if (inner) setTimeout(function(){ if (window.revealTarget) window.revealTarget(inner); }, 120);
  window.addEventListener('resize', function(){ if (window.jetGo) window.jetGo(IDS.indexOf(cur)); });
})();
// ===== 飛行機は1機だけ：ヘッダーのすぐ下の線の上を、ゆっくり一定の速さ（1秒に 60px）で飛ぶ =====
// 開いたときは1回だけ、画面の右下の外からなめらかなカーブで斜めに上がって入り、線に近づいたら向きを線にそろえて乗り、今の画面のタブの位置で止まる（3秒以内。文字より手前を飛ぶ）
// 画面を切りかえると、いまの位置から続けて、その画面の位置（5つに区切った線のまん中）へ。位置は変数 pos に持つ
// 右へ飛ぶときは線の高さ、左へ飛ぶときはその 22px 下（余白の中。文字やボタンの上には来ない）。折り返しは半円を描いて、機首は進む向きに
// 動かすのは transform と requestAnimationFrame だけ。動きを減らす設定の人には、その画面の位置に止めて置く
(function(){
  var jet = document.getElementById('nav-jet'); if (!jet) return;
  var N = 5, Y_R = 68, Y_L = 90, R = 11, SPEED = 60;
  var pos = { x: -200, y: -200, a: 0 }, path = [], last = null, raf = 0, entered = false, speed = SPEED;
  function xOf(i){ return (i + .5) / N * document.documentElement.clientWidth; }
  // 向き a で回したあと、上下を cos(a) 倍にする：右向き 1（そのまま）、左向き -1（上下反転＝背中が上・機首が進む向き）。
  // 半円の途中（真下向き＝90度）は 0 に近づいて、旋回して傾いているように見える。急にパッと切りかわらない
  function apply(){ var f = Math.cos(pos.a * Math.PI / 180); if (Math.abs(f) < .2) f = f < 0 ? -.2 : .2; /* 真横でも薄く見えるように、0 にはしない */ setTf(jet, 'translate3d(' + pos.x.toFixed(1) + 'px,' + pos.y.toFixed(1) + 'px,0) rotate(' + pos.a.toFixed(1) + 'deg) scaleY(' + f.toFixed(3) + ')'); }
  window.jetPose = function(x, y, a){ pos = { x: x, y: y, a: a }; path = []; apply(); }; // 確認画像を撮る用：好きな位置・向きに置く
  window.jetState = function(){ return { x: pos.x, y: pos.y, a: pos.a, speed: speed, left: path.length, next: path[0] || null, end: path[path.length - 1] || null }; }; // 確かめる用
  function heading(){ return (pos.a > 90 || pos.a < -90) ? -1 : 1; } // 今の向き：1 右、-1 左
  // いまの位置・向きから目標の x まで、なめらかな道筋を作る
  function plan(tx){
    path = [];
    var dir = heading(), need = tx >= pos.x ? 1 : -1, y0 = pos.y, y1 = need > 0 ? Y_R : Y_L, i;
    if (Math.abs(tx - pos.x) < 1 && Math.abs(y1 - y0) < 1) return;
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
  }
  function step(ts){
    raf = 0;
    if (last === null) last = ts;
    var d = speed * Math.min(50, ts - last) / 1000; last = ts;
    while (d > 0 && path.length) {
      var p = path[0], dx = p[0] - pos.x, dy = p[1] - pos.y, L = Math.sqrt(dx * dx + dy * dy);
      if (L < .01) { path.shift(); continue; }
      var ang = Math.atan2(dy, dx) * 180 / Math.PI, da = ang - pos.a;
      while (da > 180) da -= 360; while (da < -180) da += 360;
      pos.a += da * Math.min(1, d / 6); // 向きは進む方向へ少しずつ（6px 進むあいだに合わせる）
      if (L <= d) { pos.x = p[0]; pos.y = p[1]; d -= L; path.shift(); }
      else { pos.x += dx / L * d; pos.y += dy / L * d; d = 0; }
    }
    apply();
    if (path.length) raf = requestAnimationFrame(step); else { last = null; speed = SPEED; }
  }
  // 開いたときの入り方：右下の外 → なめらかなカーブ（3次ベジェ）で斜めに上がる → 線の高さで水平になって乗る → 目標まで線にそって左へ
  function planEntry(tx){
    var W = document.documentElement.clientWidth, VH = window.innerHeight || 800;
    var ex = Math.max(tx + 40, W * .55); // 線に乗る所（目標より右）
    var P0 = [W + 60, VH + 40], P1 = [W + 10, VH * .55], P2 = [ex + 140, Y_L], P3 = [ex, Y_L], i, n = 40, L = 0, prev = P0;
    path = [];
    for (i = 1; i <= n; i++) {
      var t = i / n, a = 1 - t, x = a * a * a * P0[0] + 3 * a * a * t * P1[0] + 3 * a * t * t * P2[0] + t * t * t * P3[0], y = a * a * a * P0[1] + 3 * a * a * t * P1[1] + 3 * a * t * t * P2[1] + t * t * t * P3[1];
      path.push([x, y]); L += Math.sqrt((x - prev[0]) * (x - prev[0]) + (y - prev[1]) * (y - prev[1])); prev = [x, y];
    }
    path.push([tx, Y_L]); L += Math.abs(ex - tx);
    pos = { x: P0[0], y: P0[1], a: Math.atan2(P1[1] - P0[1], P1[0] - P0[0]) * 180 / Math.PI }; // 最初から進む向きを向いておく
    speed = Math.max(SPEED * 2, Math.min(420, L / 2.6)); // 全部で 2.6 秒くらい（3秒はこえない）。線の上より少し速い
  }
  window.jetGo = function(i){
    var tx = xOf(i);
    if (STILL) { pos = { x: tx, y: Y_R, a: 0 }; path = []; apply(); entered = true; return; } // 動きなし：入ってくる動きなしで、その画面の位置に置く
    if (!entered) { entered = true; planEntry(tx); apply(); if (!raf) { last = null; raf = requestAnimationFrame(step); } return; }
    plan(tx);
    if (!raf && path.length) { last = null; raf = requestAnimationFrame(step); }
  };
  apply();
  document.addEventListener('visibilitychange', function(){ if (!document.hidden && path.length && !raf) { last = null; raf = requestAnimationFrame(step); } });
})();
</script>'''
anchor = '<script>\n// ===== こんなこと：'
must(anchor, js + '\n' + anchor)
# 最初の画面の飛行機は、切りかえの JS が出す（render → jetGo）。切りかえの JS は jetGo より前に動くので、最初の1回だけあとから呼ぶ
must("  apply();\n  document.addEventListener('visibilitychange'", "  apply();\n  window.jetGo(['home', 'dekiru', 'ryokin', 'nagare', 'soudan'].indexOf(document.querySelector('.scr.on') ? document.querySelector('.scr.on').id : 'home'));\n  document.addEventListener('visibilitychange'")

os.makedirs(os.path.dirname(DST), exist_ok=True)
open(DST, 'w', encoding='utf-8').write(s)
print('作った:', os.path.relpath(DST, ROOT), '画面', len(SCREENS), '／ section', len(secs))
