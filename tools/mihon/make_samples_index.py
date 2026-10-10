#!/usr/bin/env python3
"""見本帳のトップ（samples/index.html）を samples_list.json から作る  2026/10/11 作成（B案：小さなカードを並べる＋業種の切りかえ）

使い方:  python3 tools/mihon/make_samples_index.py
  ・見本の一覧（番号・名前・色・雰囲気・特徴・向いているお店・業種）は tools/mihon/samples_list.json の1か所に書く。index.html は手で直さない
  ・見本を足すとき：samples/〇〇/ を作る → thumbs/〇〇.jpg（1200×780。tools/mihon/make_thumbs.py）→ samples_list.json に1つ足す → この道具を動かす
  ・業種のボタンを押すとその業種だけ並ぶ。選んだ業種は URL の #（例 …/samples/#salon）に残る。JS が動かないときは全部並ぶ
  ・前の版（縦に大きなカード）は samples/v1/
  ・文の折り返し（<wbr>）は wbr.py で入れる。動きは足さない。古いスマホ対策はマニュアル 16
"""
import json, os, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, 'samples_list.json')
DST = os.path.join(ROOT, 'samples', 'index.html')

def e(t): return html.escape(str(t or ''), quote=True)

d = json.load(open(DATA, encoding='utf-8'))
cats = d['cats']
cat_name = dict(cats)
samples = sorted(d['samples'], key=lambda s: s['num'])
for s in samples:
    bad = [c for c in s['cats'] if c not in cat_name or c == 'all']
    if bad: sys.exit(f'見本 {s["num"]}：知らない業種 {bad}')
    if not os.path.exists(os.path.join(ROOT, 'samples', s['dir'], 'index.html')): sys.exit(f'見本 {s["num"]}：samples/{s["dir"]}/index.html がない')
    if not os.path.exists(os.path.join(ROOT, 'samples', 'thumbs', s['thumb'])): sys.exit(f'見本 {s["num"]}：thumbs/{s["thumb"]} がない')

def chips(colors):
    if not colors: return ''
    return '<div class="chips" aria-label="使っている色">' + ''.join(f'<span style="background:{e(c)}"></span>' for c in colors) + '</div>'

cards = []
for s in samples:
    href = f'{e(s["dir"])}/index.html'
    cards.append(f'''
    <article class="card" data-cat="{e(" ".join(s["cats"]))}">
      <a class="shot" href="{href}" aria-label="見本 {s["num"]} {e(s["name"])} を開く"><img src="thumbs/{e(s["thumb"])}" alt="{e(s["alt"])}" width="1200" height="780" loading="lazy"></a>
      <div class="card-body">
        <span class="num">見本 {s["num"]}</span>
        <h2><a href="{href}">{e(s["name"])}</a></h2>
        {chips(s.get("colors"))}
        <details class="more">
          <summary>くわしく</summary>
          <dl>
            <dt>雰囲気</dt><dd>{e(s["mood"])}</dd>
            <dt>特徴</dt><dd>{e(s["feature"])}</dd>
            <dt>向いているお店</dt><dd>{e(s["fit"])}</dd>
          </dl>
          <a class="btn" href="{href}">見本を開く</a>
        </details>
      </div>
    </article>''')

extras = []
for x in d.get('extras', []):
    href = f'{e(x["dir"])}/index.html'
    dl = ''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k, v in x.get('dl', []))
    extras.append(f'''
    <article class="card extra">
      <a class="shot" href="{href}" aria-label="{e(x["name"])} を開く"><img src="thumbs/{e(x["thumb"])}" alt="{e(x["alt"])}" width="1200" height="780" loading="lazy"></a>
      <div class="card-body">
        <span class="num">{e(x["label"])}</span>
        <h2><a href="{href}">{e(x["name"])}</a></h2>
        <details class="more">
          <summary>くわしく</summary>
          <dl>{dl}</dl>
          <a class="btn" href="{href}">見本を開く</a>
        </details>
      </div>
    </article>''')

buttons = ''.join(f'<button type="button" data-cat="{e(k)}"{" class=on aria-pressed=true" if k == "all" else " aria-pressed=false"}>{e(v)}</button>' for k, v in cats)
# 業種ごとの表示の切りかえは CSS で（JS は .list の data-show を変えるだけ）
show_css = '\n'.join(f'.list[data-show="{k}"] .card:not([data-cat~="{k}"]){{display:none}}' for k, _ in cats if k != 'all')

# ページの型（f-string にしない：JS や CSS の { } と混ざるため。@@〇〇@@ を置きかえる）
PAGE = '''<!doctype html>
<html lang="ja" class="no-js">
<head>
<meta charset="utf-8">
<link rel="icon" href="../img/favicon.png" type="image/png">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>デザイン見本｜Lift-Off ホームページ制作</title>
<meta name="description" content="Lift-Off ホームページ制作のデザイン見本です。架空のお店で作った @@LEN@@ の見本を、業種ごとに見られます。">
<!-- 公開準備ができるまで検索に出さない。本公開時に外す -->
<meta name="robots" content="noindex">
<!-- このページは tools/mihon/make_samples_index.py が tools/mihon/samples_list.json から作る。直すときはそちらを直して作り直す（手で直さない）。前の版は v1/ -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=BIZ+UDPGothic:wght@400;700&family=Zen+Kaku+Gothic+Antique:wght@500;900&display=swap" rel="stylesheet">
<style>
/* 言葉の切れ目で折り返す（<wbr> は BudouX で入れた） */
body{word-break:keep-all;overflow-wrap:anywhere;line-break:strict}

/* 自社サイト（Lift-Off）と同じ色・文字 */
:root{
  --ink:#1B2A38;
  --sea:#2F6F8F;
  --sky:#E8F1F5;
  --paper:#FFFFFF;
  --signal:#F2C230;
  --line:#C9D9E2;
  --muted:#52677A;
}
*{box-sizing:border-box;margin:0}
body{font-family:"BIZ UDPGothic",sans-serif;color:var(--ink);background:var(--paper);font-size:17px;line-height:1.85;-webkit-font-smoothing:antialiased}
img{max-width:100%;display:block}
a{color:inherit}
.wrap{max-width:1080px;margin-left:auto;margin-right:auto;padding-left:20px;padding-right:20px}
h1,h2,h3{font-family:"Zen Kaku Gothic Antique",sans-serif;line-height:1.35;font-weight:900;letter-spacing:.02em}

.top{position:-webkit-sticky;position:sticky;top:0;z-index:20;background:rgba(255,255,255,.96);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;align-items:center;justify-content:space-between;height:64px}
.logo{text-decoration:none;font-family:"Zen Kaku Gothic Antique",sans-serif;font-weight:900;font-size:22px;letter-spacing:.03em;display:flex;align-items:center}
.logo img{height:40px;width:auto;margin-right:10px}
.logo small{font-family:"BIZ UDPGothic";font-weight:400;font-size:12px;color:var(--muted);padding-left:10px;border-left:1px solid var(--line)}
@media (max-width:420px){.logo small{display:none}}
.back{font-size:15px;text-decoration:none;color:var(--sea);font-weight:700;margin-left:16px;white-space:nowrap}

.intro{padding:48px 0 8px}
.intro h1{font-size:30px;font-size:clamp(28px,5vw,40px);margin-bottom:12px}
.intro p.lead{color:var(--muted);max-width:40em;font-size:16px}

/* 業種の切りかえ（JS が動かないときは出さず、全部並ぶ） */
.cats{display:flex;flex-wrap:wrap;margin:20px -4px 0;padding:0}
.no-js .cats{display:none}
.cats button{font:inherit;font-size:15px;font-weight:700;color:var(--ink);background:var(--sky);border:2px solid var(--sky);border-radius:999px;padding:7px 16px;margin:4px;min-height:44px;cursor:pointer;line-height:1.4}
.cats button.on{background:var(--ink);border-color:var(--ink);color:#fff}
.cats button:hover{border-color:var(--sea)}
.cats button:focus-visible{outline:3px solid var(--signal);outline-offset:2px}
.count{font-size:14px;color:var(--muted);margin-top:10px;min-height:1.5em}

/* 小さなカードを並べる：パソコン 3〜4枚、スマホ 2枚 */
.list{display:grid;grid-template-columns:repeat(4,1fr);grid-gap:20px;gap:20px;padding:20px 0 56px}
@media (max-width:1000px){.list{grid-template-columns:repeat(3,1fr)}}
@media (max-width:640px){.list{grid-template-columns:1fr 1fr;grid-gap:12px;gap:12px;padding:16px 0 40px}}
@@SHOW_CSS@@
.card{border:2px solid var(--ink);border-radius:16px;background:#fff;overflow:hidden;display:flex;flex-direction:column}
.card .shot{display:block;border-bottom:1px solid var(--line);background:#f0ede8}
.card .shot img{width:100%;height:auto}
.card-body{padding:12px 14px 14px;display:flex;flex-direction:column;flex:1}
.num{display:inline-block;background:var(--signal);font-weight:700;font-size:12px;padding:1px 10px;border-radius:6px;margin-bottom:6px;align-self:flex-start}
.card h2{font-size:17px;margin-bottom:8px;line-height:1.4}
.card h2 a{text-decoration:none}
.card h2 a:hover{color:var(--sea);text-decoration:underline}
.chips{display:flex;margin:0 -3px 8px}
.chips span{width:22px;height:22px;border-radius:50%;border:1px solid rgba(0,0,0,.12);margin:0 3px}
.more{margin-top:auto;font-size:14px}
.more summary{cursor:pointer;color:var(--sea);font-weight:700;font-size:14px;list-style:none;padding:6px 0;min-height:36px;display:flex;align-items:center}
.more summary::-webkit-details-marker{display:none}
.more summary::before{content:"＋";display:inline-block;width:1.2em;color:var(--sea)}
.more[open] summary::before{content:"－"}
.more dl{margin:4px 0 12px}
.more dt{color:var(--muted);font-size:12px;margin-top:6px}
.more dd{font-size:14px;line-height:1.7}
.btn{display:inline-flex;align-items:center;justify-content:center;font-weight:700;text-decoration:none;border-radius:999px;padding:9px 18px;border:2px solid var(--ink);background:var(--ink);color:#fff;font-size:14px;width:100%;min-height:44px}
.btn:hover{background:var(--sea);border-color:var(--sea)}
@media (max-width:640px){.card-body{padding:10px 10px 12px}.card h2{font-size:15px}.chips span{width:18px;height:18px}.more summary,.more dd,.btn{font-size:13px}}

.extra-head{padding:8px 0 0}
.extra-head h2{font-size:24px;font-size:clamp(22px,3.4vw,30px);margin-bottom:8px}
.extra-head p.lead{color:var(--muted);max-width:40em;font-size:16px}

.howto{background:var(--sky);padding:56px 0}
.howto .wrap{display:grid;grid-template-columns:1fr auto;grid-gap:40px;gap:40px;align-items:center}
.howto h2{font-size:24px;font-size:clamp(22px,3vw,28px);margin-bottom:14px}
.howto ul{padding-left:1.2em;color:var(--ink)}
.howto li{margin-bottom:6px}
.qr{background:#fff;border-radius:16px;padding:16px;text-align:center;font-size:13px;color:var(--muted)}
.qr img{width:180px;height:180px;margin:0 auto 6px}
@media (max-width:820px){.howto .wrap{grid-template-columns:1fr}.qr{justify-self:center}}

.foot{padding:40px 0;text-align:center;font-size:14px;color:var(--muted)}
.foot a{color:var(--sea)}
</style>
<script>document.documentElement.className = 'js';</script>
</head>
<body>

<header class="top">
  <div class="wrap">
    <a class="logo" href="../index.html" aria-label="Lift-Off トップへ"><img src="../img/logo.svg" alt="Lift-Off" width="397" height="140"><small>ホームページ制作</small></a>
    <a class="back" href="../index.html#work">← トップにもどる</a>
  </div>
</header>

<main>
  <section class="intro">
    <div class="wrap">
      <h1>デザイン見本</h1>
      <p class="lead">お店の雰囲気に近いものを選んでください。色・文字・写真は、お店に合わせて変えられます。見本の店名・住所・料金・写真は架空です。</p>
      <nav class="cats" id="cats" aria-label="業種で選ぶ">@@BUTTONS@@</nav>
      <p class="count" id="count" aria-live="polite"></p>
    </div>
  </section>

  <div class="wrap list" id="list" data-show="all">@@CARDS@@
  </div>

  <section class="extra-head">
    <div class="wrap">
      <h2>ホームページと一緒に作れるもの</h2>
      <p class="lead">ロゴや名刺も、ホームページと同じ色・雰囲気でそろえて作れます（別料金。料金はトップの「料金」をご覧ください）。</p>
    </div>
  </section>

  <div class="wrap list">@@EXTRAS@@
  </div>

  <section class="howto">
    <div class="wrap">
      <div>
        <h2>見たあとは</h2>
        <ul>
          <li>気に入った見本の番号を教えてください（「1の色で、2の見出し」なども大丈夫です）</li>
          <li>ロゴやお店の写真があれば、それに合わせて色を決めます</li>
          <li>見本をもとに、お店の情報を入れた試作を作ってお見せします</li>
        </ul>
      </div>
      <div class="qr">
        <img src="thumbs/qr.png" alt="このページを開くQRコード" width="180" height="180">
        スマホでこのページを開く
      </div>
    </div>
  </section>
</main>

<footer class="foot">
  <p><a href="../index.html">Lift-Off ホームページ制作</a>（山口県防府市）</p>
</footer>

<script>
// 業種の切りかえ：押した業種だけ並べる（表示の切りかえは CSS。ここでは .list の data-show を変えるだけ）。選んだ業種は URL の # に残す（…/samples/#salon）
(function(){
  var nav = document.getElementById('cats'), list = document.getElementById('list'), count = document.getElementById('count');
  if (!nav || !list) return;
  var btns = nav.querySelectorAll('button'), names = {};
  for (var i = 0; i < btns.length; i++) names[btns[i].getAttribute('data-cat')] = btns[i].textContent;
  function show(cat, push){
    if (!names[cat]) cat = 'all';
    list.setAttribute('data-show', cat);
    var n = 0, cards = list.querySelectorAll('.card');
    for (var j = 0; j < btns.length; j++) { var on = btns[j].getAttribute('data-cat') === cat; btns[j].className = on ? 'on' : ''; btns[j].setAttribute('aria-pressed', on ? 'true' : 'false'); }
    for (var k = 0; k < cards.length; k++) if (cat === 'all' || (' ' + cards[k].getAttribute('data-cat') + ' ').indexOf(' ' + cat + ' ') >= 0) n++;
    if (count) count.textContent = names[cat] + '：' + n + ' 件';
    if (push) { try { history.replaceState(null, '', location.pathname + location.search + (cat === 'all' ? '' : '#' + cat)); } catch (e) { location.hash = cat === 'all' ? '' : cat; } }
  }
  nav.addEventListener('click', function(ev){
    var b = ev.target; while (b && b !== nav && b.tagName !== 'BUTTON') b = b.parentNode;
    if (!b || b === nav) return;
    show(b.getAttribute('data-cat'), true);
  });
  window.addEventListener('hashchange', function(){ show(location.hash.replace('#', ''), false); });
  show(location.hash.replace('#', ''), false);
})();
// 戻ったときに、見ていた場所に戻す（2026/10/7。押すと一番上に戻ってしまうため）
(function(){
  var key = 'y:' + location.pathname;
  // 「もどる」リンク：同じサイトから来たときは、ブラウザの「戻る」と同じ動きにする（見ていた場所に戻る）
  document.addEventListener('click', function(e){
    var a = e.target.closest ? e.target.closest('a') : null;
    if (!a || a.textContent.indexOf('もどる') < 0) return;
    try {
      if (document.referrer && document.referrer.indexOf(location.protocol + '//' + location.host) === 0 && history.length > 1) {
        e.preventDefault(); history.back();
      }
    } catch (err) {}
  });
  // ブラウザの「戻る」で戻ってきたのに一番上に出たときは、前に見ていた場所へ
  try {
    window.addEventListener('pagehide', function(){ sessionStorage.setItem(key, String(window.pageYOffset || 0)); });
    var nav = performance.getEntriesByType ? performance.getEntriesByType('navigation')[0] : null;
    var back = nav ? nav.type === 'back_forward' : (performance.navigation && performance.navigation.type === 2);
    if (back) {
      window.addEventListener('load', function(){
        var y = parseInt(sessionStorage.getItem(key) || '0', 10);
        if (y > 0 && (window.pageYOffset || 0) < 10) window.scrollTo(0, y);
      });
    }
  } catch (err) {}
})();
</script>
</body>
</html>
'''
page = (PAGE.replace('@@LEN@@', str(len(samples))).replace('@@BUTTONS@@', buttons).replace('@@SHOW_CSS@@', show_css)
            .replace('@@CARDS@@', ''.join(cards)).replace('@@EXTRAS@@', ''.join(extras)))


# 文の折り返し（<wbr>）
try:
    sys.path.insert(0, os.path.join(ROOT, 'tools')); import wbr
    page, n = wbr.add_wbr(page); print(f'文の折り返し：{n}か所')
except SystemExit:
    print('⚠️ budoux がないので文の折り返しを入れていません（pip3 install budoux）')
open(DST, 'w', encoding='utf-8').write(page)
print('作った:', os.path.relpath(DST, ROOT), '見本', len(samples), '／ 一緒に作れるもの', len(extras))
