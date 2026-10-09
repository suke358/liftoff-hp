#!/usr/bin/env python3
"""shian/index.html から、切りかえ式の shian2/index.html を作る  2026/10/9

shian/ と同じ中身を、画面の下の5つのボタン（ホーム／できること／料金／流れ／相談）で切りかえる形にする（ファイルは1つ）。
shian/ を直したら、もう一度これを動かして shian2/ を作り直す。

使い方:  python3 tools/mihon/make_shian2.py
"""
import re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'shian', 'index.html')
DST = os.path.join(ROOT, 'shian2', 'index.html')

# 画面の割り当て（左から順）。値は shian の <section> の id か class（先頭の class 名）
SCREENS = [
    ('home',   'ホーム',     ['hero', 'worry', 'update', 'work']),
    ('dekiru', 'できること', ['can', 'trust']),
    ('ryokin', '料金',       ['price']),
    ('nagare', '流れ',       ['flow', 'faq', 'other']),
    ('soudan', '相談',       ['contact']),
]

s = open(SRC, encoding='utf-8').read()

# ---- <section> を切り出す（shian は section を入れ子にしていない）
secs = {}
for m in re.finditer(r'<section\b[^>]*>.*?</section>', s, re.S):
    tag = m.group(0)
    mid = re.search(r'\bid="([^"]+)"', tag[:tag.index('>')])
    mcl = re.search(r'\bclass="([^"]+)"', tag[:tag.index('>')])
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

# ---- 目印・題名・noindex はそのまま。og:url と注釈だけ変える
s = s.replace('content="https://liftoff-hp.liftoff-358.workers.dev/shian/"', 'content="https://liftoff-hp.liftoff-358.workers.dev/shian2/"')
s = s.replace('<!-- 試しの版（2026/10/9）。本番に入れかえるまで検索に出さない -->',
              '<!-- 試しの版・切りかえ式（2026/10/9）。tools/mihon/make_shian2.py が shian/ から作る。直すときは shian/ を直して作り直す -->')
s = s.replace('<body>', '<body class="switch">', 1)

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
/* 切りかえのときに飛ぶ飛行機（上の線の飛行機が、押したボタンへ飛んで、次の画面の位置へ戻る） */
.fly-jet{position:fixed;left:0;top:0;width:100%;height:100%;pointer-events:none;overflow:visible;z-index:40;display:none}
.fly-jet.on{display:block}
.fly-jet .trail{fill:none;stroke:#F2C230;stroke-width:3;stroke-dasharray:6 9;stroke-linecap:round;opacity:.85}
</style>'''
s = s.replace('</style>', css, 1)

# ---- 飛ぶ飛行機の SVG（固定）
s = s.replace('<a class="skip" href="#main">本文へ</a>',
              '<a class="skip" href="#main">本文へ</a>\n<svg class="fly-jet" id="fly-jet" aria-hidden="true" focusable="false"><path class="trail" id="fly-trail" d=""/><g id="fly-plane"><use href="#jet" xlink:href="#jet" x="-32" y="-16" width="64" height="32"/></g></svg>', 1)

# ---- 切りかえの JS（ほかの JS より先に動かして、最初の画面を出しておく）
js = r'''
<script>
// ===== 切りかえ式：画面を1つずつ見せる。URL の #ryokin などで画面を覚え、スマホの「戻る」で前の画面に戻る =====
(function(){
  var IDS = ['home', 'dekiru', 'ryokin', 'nagare', 'soudan'], cur = null, busy = false;
  var bar = document.getElementById('tabbar'), prog = document.getElementById('prog'), pbar = document.getElementById('prog-bar'), pjet = document.getElementById('prog-jet');
  var fsvg = document.getElementById('fly-jet'), fplane = document.getElementById('fly-plane'), ftrail = document.getElementById('fly-trail');
  var STILL2 = (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) || !window.requestAnimationFrame;
  function el(id){ return document.getElementById(id); }
  function screenOf(node){ while (node && node !== document.body) { if (node.className && String(node.className).indexOf('scr') === 0) return node.id; node = node.parentNode; } return null; }
  // 上の線：5つに区切って、今の画面の所まで黄色。飛行機は今の画面の位置
  function progAt(i){
    var W = document.documentElement.clientWidth, x = (i + .5) / IDS.length * W;
    pbar.style.width = ((i + 1) / IDS.length * 100).toFixed(1) + '%';
    if (pjet) pjet.style.left = (x - 9).toFixed(1) + 'px';
    return x;
  }
  for (var k = 1; k < IDS.length; k++) { var seg = document.createElement('i'); seg.className = 'prog-seg'; seg.style.left = (k / IDS.length * 100) + '%'; prog.appendChild(seg); }
  function render(id){
    for (var i = 0; i < IDS.length; i++) { var sc = el(IDS[i]); if (sc) sc.className = IDS[i] === id ? 'scr on' : 'scr'; }
    var links = bar.querySelectorAll('a'); for (i = 0; i < links.length; i++) links[i].className = links[i].getAttribute('data-scr') === id ? 'on' : '';
    cur = id; progAt(IDS.indexOf(id));
    if (id === 'home' && window.heroStart) setTimeout(window.heroStart, 50);
    if (id === 'ryokin' && window.layoutPlan) setTimeout(window.layoutPlan, 0);
    if (window.requestAnimationFrame) requestAnimationFrame(function(){ window.dispatchEvent(document.createEvent('Event').initEvent ? (function(){ var e = document.createEvent('Event'); e.initEvent('resize', true, false); return e; })() : new Event('resize')); });
  }
  // 切りかえの動き：上の線の飛行機が、押したボタンへ飛び（黄色い飛行機雲）、次の画面が出てから新しい位置へ戻る
  function fly(toId, btn, done){
    if (STILL2 || !fsvg || !btn) { done(); return; }
    var W = document.documentElement.clientWidth, H = window.innerHeight, b = btn.getBoundingClientRect();
    fsvg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); fsvg.setAttribute('class', 'fly-jet on');
    var x0 = parseFloat(pjet.style.left || '0') + 9, y0 = 68, x1 = b.left + b.width / 2, y1 = b.top + 10, x2 = (IDS.indexOf(toId) + .5) / IDS.length * W, y2 = 68;
    if (pjet) pjet.style.visibility = 'hidden';
    var pts = [];
    function seg(a, b2, c, ms, next){
      tween(ms, function(u){
        var av = 1 - u, x = av * av * a[0] + 2 * av * u * b2[0] + u * u * c[0], y = av * av * a[1] + 2 * av * u * b2[1] + u * u * c[1];
        var dx = 2 * av * (b2[0] - a[0]) + 2 * u * (c[0] - b2[0]), dy = 2 * av * (b2[1] - a[1]) + 2 * u * (c[1] - b2[1]);
        fplane.setAttribute('transform', 'translate(' + x.toFixed(1) + ' ' + y.toFixed(1) + ') rotate(' + (Math.atan2(dy, dx) * 180 / Math.PI).toFixed(1) + ') scale(.6)');
        if (pts.length > 40) pts.shift(); pts.push([x, y]);
        var d = ''; for (var i = 0; i < pts.length; i++) d += (i ? ' L' : 'M') + pts[i][0].toFixed(1) + ' ' + pts[i][1].toFixed(1); ftrail.setAttribute('d', d);
      }, next, easeInOut);
    }
    seg([x0, y0], [(x0 + x1) / 2 + 60, (y0 + y1) / 2], [x1, y1], 420, function(){
      done();
      seg([x1, y1], [(x1 + x2) / 2 - 60, (y1 + y2) / 2], [x2, y2], 420, function(){ fsvg.setAttribute('class', 'fly-jet'); if (pjet) pjet.style.visibility = ''; });
    });
  }
  function go(id, push, btn){
    if (IDS.indexOf(id) < 0) id = 'home';
    if (push) { try { history.pushState(null, '', '#' + id); } catch (e) { location.hash = id; } }
    if (id === cur) return;
    if (busy) return; busy = true;
    fly(id, btn, function(){ render(id); window.scrollTo(0, 0); busy = false; });
  }
  // ページの中のリンク（#price-zero・#option・#contact など）：その場所がある画面に切りかえてから、開く・飛ぶ
  document.addEventListener('click', function(e){
    var a = e.target.closest ? e.target.closest('a') : null; if (!a) return;
    var h = a.getAttribute('href'); if (!h || h.charAt(0) !== '#') return;
    e.preventDefault();
    var id = h.slice(1);
    if (!id) { go('home', true, bar.querySelector('[data-scr=home]')); return; }
    if (IDS.indexOf(id) >= 0) { go(id, true, bar.querySelector('[data-scr=' + id + ']')); return; }
    var target = el(id); if (!target) return;
    var sid = screenOf(target) || cur;
    var after = function(){ if (window.revealTarget) window.revealTarget(id); else { try { target.scrollIntoView(); } catch (err) {} } };
    if (sid !== cur) { go(sid, true, bar.querySelector('[data-scr=' + sid + ']')); setTimeout(after, STILL2 ? 30 : 500); } else after();
  });
  window.addEventListener('popstate', function(){ var id = location.hash.replace('#', ''); if (IDS.indexOf(id) < 0) { var t = id && el(id); id = (t && screenOf(t)) || 'home'; } if (id !== cur) { render(id); window.scrollTo(0, 0); } });
  // 最初の画面：URL の # で決める（#option のような中の場所なら、その画面を出してから開く）
  var first = location.hash.replace('#', ''), inner = null;
  if (IDS.indexOf(first) < 0) { var t0 = first && el(first); inner = t0 ? first : null; first = (t0 && screenOf(t0)) || 'home'; }
  render(first);
  if (inner) setTimeout(function(){ if (window.revealTarget) window.revealTarget(inner); }, 120);
  window.addEventListener('resize', function(){ progAt(IDS.indexOf(cur)); });
})();
</script>'''
# 共通の道具（tween など）の次に入れる
anchor = '<script>\n// ===== 最初：'
if anchor not in s: sys.exit('入れる場所が見つからない')
s = s.replace(anchor, js + '\n' + anchor, 1)

os.makedirs(os.path.dirname(DST), exist_ok=True)
open(DST, 'w', encoding='utf-8').write(s)
print('作った:', os.path.relpath(DST, ROOT), '画面', len(SCREENS), '／ section', len(secs))
