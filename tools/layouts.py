# レイアウトの型（2026/11/11）。make_site.py が設定の "layout" を見て、この CSS を最後に足す（色・書体の決まりはそのまま）。
# 1つの役目：トップとメニューの「並び方」を変えるだけ。HTML は変えない（どの型でも中身・リンク・部品は同じ）。
# 型：full（写真を画面いっぱい）／magazine（雑誌風・ジグザグ）／split（左右に分ける・料金は一覧）／
#     cards（文が上・写真が下・大きいカード）／frame（額縁の写真に文の箱を重ねる）／pop（傾けた写真・太い枠）
# 明るい上の部分が合う型（magazine・split・cards・frame・pop）は、設定で "hero_style":"light" にする。full は dark。
# 古いスマホ対策：aspect-ratio・inset・flex の gap・min() は使わない。transform には -webkit- を付ける。

COMMON = r'''/* レイアウトの型：共通 */
.hero .poster img{position:absolute;top:0;left:0;width:100%;height:100%;-o-object-fit:cover;object-fit:cover}
.card > .card-body:first-child{border-top:4px solid var(--accent-soft)}
.price small:empty{display:none}
'''
# 写真のないカードの見出しを、写真の場所と同じ大きさの色のタイルにする（グリッドの型だけ）。m＝card-body の余白
def tile(m, m_sp=16, extra=''):
    return (f'''
.menu .card > .card-body:first-child{{border-top:0}}
.menu .card > .card-body:first-child h3{{margin:-{m}px -{m}px 18px;padding:15% 16px;padding:calc(37.5% - .9em) 16px;background:var(--pale);color:var(--primary-deep);text-align:center;font-size:1.5rem;letter-spacing:.16em{extra}}}
@media (max-width:640px){{.menu .card > .card-body:first-child h3{{margin:-{m_sp}px -{m_sp}px 14px}}}}''')

L = {}

L['full'] = r'''/* 型：full（写真を画面いっぱい） */
.hero .wrap{display:block;position:relative;width:100%;min-height:100vh;min-height:min(100vh,940px)}
.hero .poster{position:absolute;top:0;left:0;right:0;bottom:0}
.hero .poster::after{left:0;width:auto;background:linear-gradient(90deg,rgba(0,0,0,.78) 0%,rgba(0,0,0,.45) 55%,rgba(0,0,0,.15) 100%)}
.hero-info{position:relative;z-index:2;max-width:680px;padding:200px 40px 110px;margin-left:6%}
.hero h1{font-size:2.6rem;font-size:clamp(1.8rem,4vw,3.1rem);text-shadow:0 2px 18px rgba(0,0,0,.35)}
.sec-head h2{font-size:2rem;font-size:clamp(1.6rem,3.2vw,2.4rem)}
.sec-head.center i,.sec-head.center{text-align:left;-webkit-box-pack:start;-ms-flex-pack:start;justify-content:flex-start}
.sec-head h2::after{content:"";display:block;width:56px;height:4px;background:var(--primary);margin-top:14px}
.menu-tabs{-webkit-box-pack:start;-ms-flex-pack:start;justify-content:flex-start;margin-left:-4px;max-width:none}
.card{border-radius:0;box-shadow:none;border:1px solid var(--line);border-top:5px solid var(--primary)}
.card > .card-body:first-child{border-top:0}
.card h3{font-family:var(--gothic);font-weight:700;letter-spacing:.08em}
@media (max-width:860px){
  .hero{padding-bottom:0}
  .hero .wrap{min-height:92vh;display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-orient:vertical;-ms-flex-direction:column;flex-direction:column;-webkit-box-pack:end;-ms-flex-pack:end;justify-content:flex-end}
  .hero .poster img{position:absolute;height:100%}
  .hero .poster::after{display:block;background:linear-gradient(180deg,rgba(0,0,0,.25) 0%,rgba(0,0,0,.5) 40%,rgba(0,0,0,.85) 100%)}
  .hero-info{margin:0;padding:120px 20px 40px}
}'''+tile(24)

L['magazine'] = r'''/* 型：magazine（雑誌風。文が左・写真が右。メニューはジグザグ） */
.hero .wrap{width:auto;max-width:1180px;margin:0 auto;padding:140px 20px 90px;min-height:0;grid-template-columns:minmax(0,1fr) minmax(0,1.05fr);align-items:center}
.hero .poster{-webkit-box-ordinal-group:3;-ms-flex-order:2;order:2;height:620px;box-shadow:-22px 22px 0 var(--accent-soft)}
.hero .poster::after{display:none}
.hero-info{-webkit-box-ordinal-group:2;-ms-flex-order:1;order:1;padding:0 56px 0 0;max-width:none}
.hero h1{font-size:2.6rem;font-size:clamp(1.9rem,3.8vw,3rem);line-height:1.6;border-left:3px solid var(--primary);padding-left:22px}
.menu-cards,.menu-cards.n4{display:block}
.menu-cards{counter-reset:mz}
.menu .card{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:center;background:transparent;box-shadow:none;border-radius:0;margin-bottom:56px;counter-increment:mz}
.menu .card:nth-child(even) .photo{-webkit-box-ordinal-group:3;-ms-flex-order:2;order:2}
.menu .card .photo{border-radius:0}
.menu .card-body{padding:10px 48px}
.menu .card > .card-body:first-child .ask-line{-ms-flex-item-align:start;align-self:flex-start;padding:.55em 2.4em}
.menu .card > .card-body:first-child{grid-column:1 / -1;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:28px 8px;margin-top:-24px}
.menu .card h3{font-size:1.6rem}
.menu .card h3::before{content:counter(mz,decimal-leading-zero);display:block;font-family:var(--latin);font-style:italic;font-size:1rem;color:var(--primary-deep);letter-spacing:.1em}
@media (max-width:860px){
  .hero .wrap{grid-template-columns:1fr;padding:96px 20px 20px}
  .hero .poster{-webkit-box-ordinal-group:1;-ms-flex-order:0;order:0;height:300px;margin:0 0 0 12px;box-shadow:-12px 12px 0 var(--accent-soft)}
  .hero .poster img{position:absolute;height:100%}
  .hero-info{padding:0;margin:40px 0 0}
  .menu .card{grid-template-columns:1fr;margin-bottom:40px}
  .menu .card:nth-child(even) .photo{-webkit-box-ordinal-group:1;-ms-flex-order:0;order:0}
  .menu .card-body{padding:18px 4px 0}
  .menu .card > .card-body:first-child{margin-top:0;padding:22px 4px}
}'''

L['split'] = r'''/* 型：split（左右に分ける。写真は右いっぱい・角を大きく丸める。料金は一覧） */
.hero .wrap{grid-template-columns:minmax(0,1fr) minmax(0,1.1fr)}
.hero .poster{-webkit-box-ordinal-group:3;-ms-flex-order:2;order:2;border-bottom-left-radius:180px}
.hero .poster::after{display:none}
.hero-info{-webkit-box-ordinal-group:2;-ms-flex-order:1;order:1;max-width:620px;padding:140px 56px 100px 9%}
.menu-cards,.menu-cards.n4{display:block;max-width:880px;margin:0 auto}
.menu .card{display:grid;grid-template-columns:220px minmax(0,1fr);grid-gap:0 32px;align-items:center;background:transparent;box-shadow:none;border-radius:0;border-bottom:1px solid var(--line);padding:28px 0}
.menu .card:first-child{border-top:1px solid var(--line)}
.menu .card .photo{border-radius:999px 999px 18px 18px}
.menu .card > .card-body:first-child{grid-column:1 / -1;border-top:0;padding:0 8px}
.menu .card-body{padding:0}
.menu .card .price{border-top:0;padding-top:0;-webkit-box-pack:start;-ms-flex-pack:start;justify-content:flex-start}
.menu .card .price small{margin-right:1em}
.menu .ask-line{-ms-flex-item-align:start;align-self:flex-start;padding:.5em 1.4em}
@media (max-width:860px){
  .hero .wrap{grid-template-columns:1fr}
  .hero .poster{-webkit-box-ordinal-group:1;-ms-flex-order:0;order:0;height:56vh;min-height:320px;border-bottom-left-radius:90px}
  .hero .poster img{position:absolute;height:100%}
  .hero-info{justify-self:stretch;padding:0;margin:32px 20px 0}
  .menu .card{grid-template-columns:1fr;padding:22px 0}
  .menu .card .photo{max-width:260px;margin-bottom:14px}
}'''

L['cards'] = r'''/* 型：cards（文を真ん中に・写真は下に大きく。メニューは大きいカード2列） */
.hero .wrap{display:-webkit-box;display:-ms-flexbox;display:flex;-webkit-box-orient:vertical;-ms-flex-direction:column;flex-direction:column;-webkit-box-align:center;-ms-flex-align:center;align-items:center;width:auto;max-width:1140px;margin:0 auto;padding:150px 20px 80px;min-height:0}
.hero-info{-webkit-box-ordinal-group:2;-ms-flex-order:1;order:1;text-align:center;max-width:780px;padding:0}
.hero .eyebrow,.hero .addr,.hero-btns,.toc{-webkit-box-pack:center;-ms-flex-pack:center;justify-content:center}
.hero .eyebrow::after{content:"";width:36px;height:1px;background:currentColor;margin-left:14px;-ms-flex:none;flex:none}
.hero h1{font-size:2.6rem;font-size:clamp(1.8rem,4vw,3rem)}
.hero .poster{-webkit-box-ordinal-group:3;-ms-flex-order:2;order:2;width:100%;height:460px;margin-top:56px;border-radius:28px;box-shadow:0 24px 60px rgba(0,0,0,.14)}
.hero .poster::after{display:none}
.menu-cards.n4,.menu-cards{grid-template-columns:1fr 1fr;grid-gap:32px}
.menu .card{border-radius:24px;border:2px solid var(--line);box-shadow:none;-webkit-transition:-webkit-transform .2s;transition:transform .2s}
.menu .card:hover{-webkit-transform:translateY(-4px);transform:translateY(-4px)}
.menu .card .photo{margin:10px 10px 0;border-radius:16px}
.menu .card h3{font-family:var(--gothic);font-weight:700}
.menu .card .price b{color:var(--primary-deep)}
@media (prefers-reduced-motion:reduce){.menu .card,.menu .card:hover{-webkit-transition:none;transition:none;-webkit-transform:none;transform:none}}
@media (max-width:860px){
  .hero .wrap{padding:104px 20px 10px}
  .hero .poster{height:240px;margin-top:36px;border-radius:20px}
  .hero .poster img{position:absolute;height:100%}
}
@media (max-width:600px){.menu-cards.n4,.menu-cards{grid-template-columns:1fr}}'''+tile(14, 6, ';border-radius:16px')

L['frame'] = r'''/* 型：frame（額縁のような大きい写真に、文の箱を重ねる。メニューは細い枠） */
.hero{background:var(--bg)}
.hero .wrap{display:block;width:auto;min-height:0;padding:96px 28px 40px}
.hero .poster{height:78vh;max-height:760px;min-height:420px}
.hero .poster::after{display:none}
.hero-info{position:relative;z-index:2;background:#fff;max-width:600px;margin:-200px 0 0 6%;padding:52px 56px 46px;box-shadow:0 20px 50px rgba(0,0,0,.12)}
.sec-head.center h2{display:inline-block;position:relative;padding:0 28px}
.sec-head.center h2::before,.sec-head.center h2::after{content:"";position:absolute;top:50%;width:40px;border-top:1px solid var(--primary)}
.sec-head.center h2::before{right:100%}
.sec-head.center h2::after{left:100%}
.menu .card{border-radius:0;box-shadow:none;border:1px solid var(--line);padding:12px;background:#fff}
.menu .card .photo{border-radius:0}
.menu .card-body{padding:22px 6px 10px;text-align:center}
.menu .card .price{-webkit-box-pack:center;-ms-flex-pack:center;justify-content:center}
.menu .ask-line{padding:.6em .5em;font-size:.8rem}
.menu .card .price small{margin-right:1em}
@media (max-width:860px){
  .hero{padding-bottom:30px}
  .hero .wrap{padding:76px 12px 0}
  .hero .poster{height:58vh;min-height:300px}
  .hero .poster img{position:absolute;height:100%}
  .hero-info{margin:-70px 10px 0;padding:30px 22px 26px}
  .sec-head.center h2::before,.sec-head.center h2::after{width:20px}
}'''+tile(22, 22)+'''
.menu .card > .card-body:first-child h3{margin:-22px -6px 18px}'''

L['pop'] = r'''/* 型：pop（傾けた写真・太い枠・丸い飾り） */
.hero::before{content:"";position:absolute;width:560px;height:560px;border-radius:50%;background:var(--accent-soft);opacity:.55;right:-140px;top:-160px}
.hero::after{content:"";position:absolute;width:220px;height:220px;border-radius:50%;background:var(--primary);opacity:.12;left:-60px;bottom:-60px}
.hero .wrap{position:relative;z-index:1;width:auto;max-width:1180px;margin:0 auto;padding:140px 20px 100px;min-height:0;grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:center}
.hero .poster{-webkit-box-ordinal-group:3;-ms-flex-order:2;order:2;height:520px;border:10px solid #fff;border-radius:32px;-webkit-transform:rotate(-3deg);transform:rotate(-3deg);box-shadow:16px 16px 0 var(--primary)}
.hero .poster::after{display:none}
.hero-info{-webkit-box-ordinal-group:2;-ms-flex-order:1;order:1;padding:0 50px 0 0;max-width:none}
.hero h1{font-family:var(--gothic);font-weight:700;font-size:2.6rem;font-size:clamp(1.9rem,4vw,3.1rem);letter-spacing:.08em}
.sec-head i{display:inline-block;background:var(--primary);color:#fff !important;font-style:normal;font-family:var(--gothic);font-weight:700;font-size:.8rem;letter-spacing:.14em;padding:.2em 1.1em;border-radius:999px;text-transform:uppercase}
.sec-head i .mk{fill:#fff}
.sec-head h2{font-family:var(--gothic);font-weight:700}
.menu .card{border:2px solid var(--ink);border-radius:22px;box-shadow:6px 6px 0 var(--primary)}
.menu .card .photo{border-bottom:2px solid var(--ink)}

.menu .card h3{font-family:var(--gothic);font-weight:700}
.menu .card .price b{color:var(--primary-deep);font-family:var(--gothic);font-weight:700}
@media (max-width:860px){
  .hero::before{width:320px;height:320px;right:-120px;top:-80px}
  .hero .wrap{grid-template-columns:1fr;padding:100px 20px 10px}
  .hero .poster{-webkit-box-ordinal-group:1;-ms-flex-order:0;order:0;height:270px;margin:0 10px;border-width:7px;border-radius:24px;box-shadow:10px 10px 0 var(--primary)}
  .hero .poster img{position:absolute;height:100%}
  .hero-info{padding:0;margin:40px 0 0}
}'''+tile(24, 16, ';border-bottom:2px solid var(--ink);background:var(--accent-soft);color:var(--ink)')

NAMES = list(L)

def css(name):
    """設定の layout の名前から、足す CSS を返す。空・知らない名前なら ''（今までと同じ見た目）"""
    if not name: return ''
    if name not in L:
        print(f'⚠️ layout：「{name}」という型はありません（使えるのは {"・".join(NAMES)}）。型なしで作ります')
        return ''
    return COMMON + '\n' + L[name]
