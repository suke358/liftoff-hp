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
  ・画像は設定に書いた場所（images/〜）に自分で入れる。トップとメニューのカードに写真が無いときは、設定の "業種" のフォルダ（~/src/_素材写真/<業種>/）から
    自動で入れる（下の「写真の自動入れ」）。仮の絵（「写真が入ります」の .svg）は作らない（2026/11/21 ⑥-1）
  ・最後に check_site.py（公開前チェック）を自動で走らせる
設定の書き方は templates/site_sample.json（山口造庭舎のデモ）を見る。分からない情報は書かない（空にすると、その行は出ない）
  "url_base" … 公開URL（例 "https://〇〇.liftoff-358.workers.dev/"）。書くと og:url・canonical・LINE のカード画像（og_image）の URL が入る
  "card_v"   … LINE のカードの番号（1から。url_base があるときだけ）。og:url・canonical・開いたときアドレスバーに足す ?v= の3か所に入る（2026/10/10 追加。マニュアル 17）。
               カードの画像を変えたら、画像の名前を変え、card_v を次の数字にして作り直す（LINE はページの URL ごとにカードを覚えるため）
  公開先の住所（2026/11/11）：作り終わったあとの案内（公開URL・確認用URL。wrangler.jsonc を初めて置くときに出る）の後ろは、作るフォルダの .okiba
               （1行：例 omise-site.workers.dev）があればそれ、なければ今までどおり liftoff-358.workers.dev（preview_push.sh・push_small.sh と同じ読み方）。
               ココナラのお客さんのサイトは別アカウント omise-site に置くため（2026/11/7 決定）。.okiba の中身が読めないときは ❌ を出し、住所は出さない

404 ページ（2026/10/21 決定事項 08）：index.html と一緒に 404.html も作る（店名・色・印・LINE・電話は設定から）。
  wrangler.jsonc に not_found_handling を入れるので、Cloudflare が無い住所のときに 404 の印のまま返す。メニューのボタンは /menu（転送で /#menu へ）
部品（入れる／入れないを選べる。2026/10/9 追加）：設定に "parts": {...} を書く。全部入れた見本は templates/site_sample_parts.json
  "belt"    … 写真の帯（横にゆっくり流れる。さわると止まる。動きを減らす設定の人には流さない）
  "compare" … 作業の前と後を、つまみで見比べる（JS がないときは2枚を並べて出す）
  "calc"    … 本数・回数を選ぶと合計の目安が出る料金（JS がないときは料金表として出る）
  "cases"   … 施工例（作業前・作業後の写真を並べる）
  "form"    … 選んで送れるフォーム（Formspree。JS がないときもふつうのフォームとして送れる）
  "shop"    … 商品（物販。2026/10/11 追加。決定事項：商品ページ＝ご契約のお店 22,000円〜・1ページ・商品5点まで・決済は Square）
              商品5点まで（6点以上は ⚠️ を出して5点だけ出す）。「購入する」ボタンは buy_url（Square の購入ページ）へ新しいタブで。buy_url が空なら「準備中」（押せない）
              商品の下に「特定商取引法に基づく表示」（開閉式）。販売者・住所・電話はお店の設定から取る
              本物のお店（sample_note がない）では shipping・payment・pay_timing・delivery・returns が空だと ❌ で止まる（「お問い合わせください」のまま公開しない。2026/10/22 マニュアル K）。見本は ⚠️
              書き方：{"title":"商品","lead":"…","items":[{"name":"…","amount":"30g×5包","price":"2,200円","text":"…","image":"images/item-1.svg","alt":"…","buy_url":"https://square.link/u/…","note":"送料別"}],
                      "note":"お支払いは Square の画面で…",
                      "tokushoho":{"seller":"…","manager":"（法人の責任者。空なら出さない）","address":"…","tel":"…","email":"…","disclose":false,
                                   "price":"…","shipping":"…","payment":"…","pay_timing":"（支払いの時期）","delivery":"…","period":"（申込みの期限。空なら出さない）","returns":"…"}}
              disclose を true にすると、名前・住所・電話の代わりに「ご請求があれば遅滞なく開示します」と連絡先のメールを出す（個人事業の人向け）
              見本：templates/site_sample_shop.json（架空のよもぎ蒸しサロン hiyori）→ samples/shop/
  それぞれ true と書くと決まった中身（メニューの写真など）で入る。{...} で中身を書ける。色・書体はお店の theme に合わせて出る
  "sample_note" … 見本のとき、ページのいちばん上に出す注（例 "※画面は架空のお店の見本です"）。本物のお店では書かない
  "dm_url"  … インスタグラムの DM の入口（2026/11/7）。お店のインスタのページの URL（例 "https://www.instagram.com/〇〇/"）。書くと「インスタのDM」のボタンが
              トップの入口・ご予約の欄・スマホの下の固定ボタンに出る（新しいタブ）。LINE がないお店は、メニューのカードにも「インスタのDMで相談」（電話より先）。
              電話より先に並べる（施術中は電話に出られないお店のため）。スマホの下は「ネット予約」がないときだけ右の枠に DM が入る。書かなければ今までと同じ
              "dm_text" … ご予約の欄の DM の説明（空なら「インスタグラムのメッセージで、お気軽にどうぞ。」）
  "map_query" … 地図と「Googleマップで道順を見る」の行き先（店名＋住所など）。空ならどちらも出ない
  "show_map" / "show_route" … 地図（埋め込み）と「道順を見る」ボタンを別々に消す（2026/11/7）。false と書くと出ない。書かなければ両方出る（住所を出したくないお店は show_map:false など）
  "layout" … レイアウトの型（2026/11/11）。full・magazine・split・cards・frame・pop のどれか。書かなければ今までと同じ。説明は tools/layouts.py
  "menu_cols" … メニューのカードを2列にする（2026/11/7）。2 と書くと、パソコン幅でも2列（スマホは1列）。4つのとき4列になって写真が小さくなるお店用。書かなければ今までと同じ（数で決まる）
  "analytics_token" … Cloudflare Web Analytics のトークン（2026/10/22）。書くと数える一文が入る。独自ドメインを Cloudflare につないだお店は自動で数えるので空でよい
確認用の帯（2026/11/14・部品 V）：どのサイトにも </body> の前に templates/preview_band.html を入れる。住所が preview- で始まるとき（preview_push.sh の確認用URL）だけ、
  いちばん上に「確認用（まだ公開前です）」の帯が出て、題名の頭に【確認用】・noindex が付く。本番の住所では何も出ない（設定は要らない）。納品後は preview_push.sh --close で確認用を閉じる
道具の版（2026/11/21・順0「既存の店を守る」）：作った index.html の目印の注釈に「道具の版 〇〇〇〇〇〇〇」を書く（見た目を決めるファイル make_site.py・parts_extra.py・layouts.py・
  wbr.py・templates/ を最後に直した commit の7けた。未 commit の直しがあれば + が付く）。公開先のあるサイト（フォルダに wrangler.jsonc がある＝お店のサイト。見本帳 samples/ には無い）を
  作り直すとき、前の index.html の版が今の道具と違えば ⚠️ で止まり、何も書きかえない（道具を直したあとの「電話番号1か所直し」で見た目が黙って変わるのを防ぐ。
  版の記録がない＝11/21 より前の道具で作ったページも止まる）。見比べて作り直すと決めたら --uwagaki を付ける（index.old.html と diff で見比べる）。
  直す前の道具（2026/11/20 まで）は git のタグ tools-v1（commit 7071235）で取り出せる（例 git checkout tools-v1 -- tools/）。検査は tools/test_make_site_version.py
写真の自動入れ（2026/11/21・⑥-1「写真」。本人の採点「写真がない＝2点」を二度と出さない）：
  トップ（hero）とメニューのカード（menus）に写真が無い（image が空・ファイルが無い・前の道具の仮の絵 .svg）とき、設定の "業種"（例 "造園"。~/src/_素材写真/ のフォルダ名）の
  写真を images/ に写して入れる。使うのは _素材写真/素材一覧.md に載っていて「商用可・表記不要」のものだけ（一覧に無い写真はフォルダにあっても使わない）。
  トップは名前に hero が付く写真、カードは残り。どちらも明るい順（平均の明るさ。2026/11/21 ⑥-2 3周目。前は一覧の順）。名前に owner が付く人物の写真は、お店の人と間違われるので使わない。
  カードは、メニューの "stock"（素材の名前の一部）＞ id（gel・off…）＞ 名前の言葉（PHOTO_WORDS。剪定→prun など）と素材のファイル名を照らして、合う組から当てる（2026/11/22 ネイル2周目）。手がかりが無ければ順に
  暗い写真（平均の明るさ 105 未満）は写すときに最大 1.3 倍まで明るくする。トップの写真の上の影は薄め（黒 .3）
  写した先は、設定の image が .jpg ならその名前（例 images/menu-sentei.jpg。あとでお店の写真に同じ名前で差しかえられる）、それ以外は元の名前。カードの写真は設定の w:h（無ければ 4:3）に真ん中を切る（Pillow があるとき）
  写真が足りない・フォルダが無い・"業種" が無いときは ⚠️ で止まり、何も書かない（黙って仮の絵にしない）。
  ごあいさつ・部品（belt・cases・shop・compare）の写真はまだ自動では入れない（⑥-3）。設定に書いた場所にファイルが無ければ ⚠️ で止まる（写真を置くか、設定から外す）。
  スマホではトップの写真が画面の高さの 6 割になる（最初の画面の半分以上が写真。layout の型を使うときは型の決まりのまま）。仮の絵が残っていないかは check_site.py が ❌ で止める
連絡の入口（2026/11/21・⑥-2 1周目）：ご予約・ご相談の欄には、設定にある入口（tel・line_url・parts の form・form_url・dm_url・reserve_url）だけを出す。
  1つも無いときは「準備中」の欄を出さずに ⚠️ で止まる（pending_text はもう使わない）。check_site.py は「準備中」の欄が残っていれば ❌
下の段（2026/11/21・⑥-2 2周目）：フッターに 店名・住所（address）・電話（tel）・営業時間（hours）・定休日（holiday）・「Googleマップで道順を見る」（map_query）・Googleマップの埋め込み（map_query。show_map:false で消える）を出す。
  設定に無いものは出ない。地図は店舗情報の欄の「道順を見る」のすぐ下に出す（2026/11/22・⑥-2 ネイル9周目。本人「道順の下は地図に」）。**地図は 1 か所だけ**（2026/11/22 本人「Googleマップ 2回でてくる ×」）："access_map": false のときだけ下の段に出る。check_site.py は地図が 2 つあれば ❌
後半の区画の写真（2026/11/22・⑥-2 4周目。本人「もう少し写真の枚数が欲しい」）：店舗情報の横（about。地図が無いとき）・ご依頼の流れの横（flow）・ご相談の背景（reserve）に、
  業種の素材の残りから写真を入れる（"sec_photos": {"about": {"image": "images/sec-about.jpg"}, …} と設定に書いてもよい。"sec_photos": false で入れない）。
  名前に hands・back・work・tool の付く「人の気配」の写真（顔の出ない手元・後ろ姿）を先に使う。足りなければ入れない（止めない）。
  注意：お店の写真がそろっていてメニューの自動入れが無いときは、素材がメニューと重なることがある（そのときは設定の sec_photos に書く）
部品の写真の自動入れ（2026/11/22・⑥-3 1周目）：belt・cases・compare・shop に写真が無ければ、業種の素材から入れる。施工例・見比べは 〇〇_before.jpg ↔ 〇〇_after.jpg の組（カードより後回しにはしない。足りなければその項目を外す）、
  商品は名前の手がかり＞物撮り（足りなければ写真なし）、帯は名前の手がかり＞残り（足りなければ使った写真をもう一度。印を出す）。仮の絵は残さない。見本は templates/site_sample_buhin.json
部品の見た目を本体にそろえる（2026/11/22・⑥-3 2周目）：帯・施工例・見比べの写真にも色味の統一（TONE_CSS）と同じ影、帯の余白を .sec と同じに、小見出しの字間をカードと同じに
区画ごとの背景（2026/11/22・⑥-3 3周目）：部品の区画（写真の帯・施工例・見比べ・料金の目安・お客様の声・お知らせ・受付時間・対応エリア・選ばれる理由 など）と流れに、直前と違う見え方の背景（無地・薄い色・点・罫線・斜めの帯）を上から順に振る（vary_backgrounds）。同じ見え方が続かない。"design": false で無地
写真を 1 ページ 8 枚以上に（2026/11/22・⑥-2 ネイル8周目。本人「写真が7枚以下で Googleマップに載る写真と変わらない」）：後半の区画の写真に よくある質問の横（faq。PC は左に縦長・スマホは上に横長の帯）と
  店舗情報の小さい写真（about2。大きい写真の角に重ねる正方形）を足した。素材の残りから入れる（足りなければ入れない・止めない）。大きさを変えて同じ構図のくり返しにしない。"sec_photos" の書き方は同じ
背景のデザイン（2026/11/22・⑥-2 5周目。本人「デザイン性が欲しい」）：型（layout）を使わないページに、見出しの後ろの薄い英字（重ね）・メニューの面のずらし・店舗情報の罫線・よくある質問の点の模様・
  暗い区画と下の段の上の端の斜めの切りかえ・後半の写真の重ね枠を入れる。色はテーマの変数だけ。"design": false で前の無地に戻る
  PC 幅では区画の見せ方に変化（2026/11/22 ネイル4周目）：カードの段違い・流れ（写真が無いとき）は横一列・質問は2列・店舗情報の写真を表に少し重ねる
手書き風フォント（2026/11/22・⑥-2 6周目）：区画の見出し（h2）とトップの一言（h1）に Google Fonts の手書き風（Klee One・Yomogi・Zen Kurenaido・Yusei Magic・Kaisei Decol。無料・表記不要）。
  設定の "hand_font": "Klee One" ＞ 業種（HAND_BY_GYOUSHU）＞ 雰囲気（HAND_BY_THEME）。"hand_font": false で切る。本文は今までのまま
重ねる型（2026/11/22・⑥-2 ネイル1周目。AI が毎回「最初の画面に写真と文字の重ねが無い」）：型（layout）を使わないページは、最初の画面で写真の上に小見出し・一言・ボタンを重ね、
  文（lead）・場所・目次は写真の下の帯に出す。暗い／明るい上の部分（hero_style）に合わせて影の色が変わる。"hero_overlay": false で前の形（写真と文の面が分かれる）
写真の色味（2026/11/22・⑥-2 ネイル6周目）：型を使わないページの写真（トップ・カード・後半の区画）に、雰囲気ごとの薄いフィルター（PHOTO_TONE。彩度を少し落とし、ほんのり同じ色に寄せる）。"photo_tone": false で切る・文字列で指定
料金の目安（2026/11/22・⑥-2 7周目）：メニューのカードは menus[].price があるときだけ「料金の目安」の札つきで出す（price_note で札の文を変えられる）。無ければ「料金はお問い合わせください」のまま（分からない料金は作らない）
"""
import sys, os, re, json, html, shutil, subprocess, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_DOMAIN = 'liftoff-358.workers.dev'  # 公開先の住所の後ろ（Lift-Off 自社）。.okiba があればそちら

VERSION_FILES = ['tools/make_site.py', 'tools/parts_extra.py', 'tools/layouts.py', 'tools/wbr.py', 'tools/templates']  # 出来上がりの見た目を決めるファイル（道具の版はこれで決まる）

def tool_version():
    """道具の版（2026/11/21 順0）：VERSION_FILES を最後に直した commit の7けた。未 commit の直しがあれば + を付ける。git が使えなければ「不明」"""
    root = os.path.dirname(HERE)
    try:
        v = subprocess.run(['git', '-C', root, 'log', '-1', '--format=%h', '--'] + VERSION_FILES, capture_output=True, text=True).stdout.strip()
        if not v: return '不明'
        dirty = subprocess.run(['git', '-C', root, 'status', '--porcelain', '--'] + VERSION_FILES, capture_output=True, text=True).stdout.strip()
        return v + ('+' if dirty else '')
    except Exception:
        return '不明'

TOOL_VERSION = tool_version()

def stamped_version(path):
    """前に作った index.html の目印の注釈から「道具の版」を読む。書いてなければ None（2026/11/21 より前の道具で作ったページ）"""
    try:
        s = open(path, encoding='utf-8').read()
    except Exception:
        return None
    m = re.search(r'tools/make_site\.py で作った（設定：[^）]*?・道具の版 ([^）\s]+)）', s)
    return m.group(1) if m else None

def read_okiba(folder):
    """サイトのフォルダの .okiba から、公開先の住所の後ろを読む（2026/11/11。preview_push.sh・push_small.sh の read_okiba と同じ読み方）。
    .okiba がなければ (DEFAULT_DOMAIN, '')。あれば # で始まる行と空行を飛ばした最初の1行（https:// と最後の / は消す）を返す。
    中身が空・英数字と . - 以外の文字がある・. がない → (None, 理由)。呼んだ側は住所を出さない（だまって liftoff-358 にはしない）"""
    p = os.path.join(folder, '.okiba')
    if not os.path.exists(p): return DEFAULT_DOMAIN, ''
    lines = [l.strip() for l in open(p, encoding='utf-8', errors='ignore').read().splitlines()]
    lines = [l for l in lines if l and not l.startswith('#')]
    d = re.sub(r'^https?://', '', lines[0]).rstrip('/') if lines else ''
    if not d: return None, f'{p} の中身が空です（公開先の住所を1行書く。例 omise-site.workers.dev）'
    if not re.fullmatch(r'[A-Za-z0-9.-]+', d) or '.' not in d:
        return None, f'{p} の「{d[:40]}」が住所の形ではありません（英数字と . - だけ・. が要る。例 omise-site.workers.dev）'
    return d, ''

def e(t): return html.escape(str(t or ''), quote=True)

THEMES = {  # 色の組み合わせ。設定の "theme" で上書きできる
    # hero_style（2026/10/31）：上の部分（トップ）を 'light'（明るい。背景は pale・文字は ink）か 'dark'（濃い。今までどおり）にする。
    #   書いていなければ dark（今あるサイトの見た目は変えない）。お店の設定の "hero_style" が THEMES より優先
    # salon の primary は 2026/10/31 に #fe97b2 → #e8557d（白い文字との差 2.04 → 3.48。check_site の基準 3.0）。前の色を使う見本は site.json の theme に前の色を書いてある
    'salon': dict(primary='#e8557d', primary_deep='#cf3d66', accent='#c4a466', accent_soft='#e2cf9f', pale='#fdeef2', dark='#24342b', dark2='#2d4136', bg='#faf5ee', bg2='#f3ebe0', ink='#3a3330', muted='#75695f', line='#e6dccd', hero_style='light'),
    'wa':    dict(primary='#a8432a', primary_deep='#8f3822', accent='#3e5640', accent_soft='#c9b98f', pale='#efe6d6', dark='#23221f', dark2='#33312c', bg='#f3eee3', bg2='#e9e2d3', ink='#23221f', muted='#6d675c', line='#cfc6b4', hero_style='dark'),
    'fresh': dict(primary='#2f8f6f', primary_deep='#22735a', accent='#f2b84b', accent_soft='#f7d99a', pale='#e6f3ee', dark='#1f3b33', dark2='#2a4a41', bg='#f7faf8', bg2='#eaf2ee', ink='#22302b', muted='#5d6e67', line='#d5e2dc', hero_style='light'),
    # 2026/10/31 追加（設計書 04：雰囲気 シンプル・上品・元気）。どの組も、ボタンの白い文字／ボタンとトップの背景／地図の印（primary）と背景／
    # 小見出しと背景／札（primary_deep と pale）の差を、check_site.py の「色」の検査と同じ基準で確かめてある
    'simple': dict(primary='#4f7488', primary_deep='#3c5b6c', accent='#b89b5a', accent_soft='#dccda4', pale='#eaf0f3', dark='#2b2e31', dark2='#3b3f43', bg='#f7f7f5', bg2='#ecece8', ink='#2a2a2a', muted='#6a6a6a', line='#dcdcd8', hero_style='light'),  # シンプル：灰色＋青灰
    'jouhin': dict(primary='#8e3f55', primary_deep='#722f42', accent='#b3975e', accent_soft='#dfcf9f', pale='#f4e9ed', dark='#2a2226', dark2='#3c3137', bg='#faf7f3', bg2='#f1ebe4', ink='#332b2e', muted='#776b70', line='#e3d9d4', hero_style='dark'),  # 上品：えんじ＋金＋生成り
    'genki':  dict(primary='#c9571c', primary_deep='#a3430f', accent='#f5c33b', accent_soft='#fde28a', pale='#fff0e4', dark='#2d2a26', dark2='#403b35', bg='#fffaf3', bg2='#fdefdc', ink='#2f2a25', muted='#7a6d62', line='#ecdccb', hero_style='light'),  # 元気：だいだい＋黄
}
THEME_LABELS = {'salon': 'やわらか', 'wa': '和', 'fresh': 'さわやか', 'simple': 'シンプル', 'jouhin': '上品', 'genki': '元気'}  # フォームの「雰囲気」の答え → theme_base
LINE_ICON = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 3C6.5 3 2 6.6 2 11c0 3.9 3.5 7.2 8.3 7.9.3.1.8.2.9.5.1.3.1.7 0 1l-.1.9c0 .3-.2 1 .9.5s5.9-3.5 8-6C21.4 14.3 22 12.7 22 11c0-4.4-4.5-8-10-8z"/></svg>'
PIN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>'
MARKS = {
    'heart': '<path d="M12 21s-7.6-4.6-9.6-9.4C1 8.2 3 4.5 6.6 4.5c2.2 0 3.7 1.3 5.4 3.3 1.7-2 3.2-3.3 5.4-3.3 3.6 0 5.6 3.7 4.2 7.1C19.6 16.4 12 21 12 21z"/>',
    'leaf':  '<path d="M20 4C10 4 4 9 4 16c0 1.6.4 3 1 4 1-4 4-8 9-10-4 3-6 6-7 10 1 .3 2 .5 3 .5 7 0 10-7 10-16z"/>',
    'dot':   '<circle cx="12" cy="12" r="6"/>',
}

IG_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2">'
           '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.3" cy="6.7" r="1" fill="currentColor" stroke="none"/></svg>')

def line_url(c, msg=None):
    oid = c.get('line_id')  # 例 "@224ybmlu"。あれば下書き入りで開く
    if msg and oid:
        return 'https://line.me/R/oaMessage/' + urllib.parse.quote(oid) + '/?' + urllib.parse.quote(msg)
    return c.get('line_url') or ''

def ext(url): return f'href="{e(url)}" target="_blank" rel="noopener"'

def build(c):
    t = dict(THEMES[c.get('theme_base', 'salon')]); t.update(c.get('theme', {}))
    # Cloudflare Web Analytics（2026/10/22）：設定に analytics_token があれば </body> の直前に入れる。空なら入れない（独自ドメインを Cloudflare につないだお店は自動で数えるので不要）
    tok = str(c.get('analytics_token') or '').strip()
    # 確認用の帯（部品 V・2026/11/14）：住所が preview- で始まるときだけ「確認用（まだ公開前です）」を出す。元は templates/preview_band.html の1か所
    pv_band = open(os.path.join(HERE, 'templates', 'preview_band.html'), encoding='utf-8').read().strip()
    analytics = ('<!-- Cloudflare Web Analytics --><script defer src=\'https://static.cloudflareinsights.com/beacon.min.js\' data-cf-beacon=\'{"token": "' + e(tok) + '"}\'></script><!-- End Cloudflare Web Analytics -->') if tok else ''
    name, short = c['name'], c.get('short_name', c['name'])
    mark = MARKS.get(c.get('mark', 'heart'), MARKS['heart'])
    head_font = 'var(--mincho)' if c.get('font', 'mincho') == 'mincho' else 'var(--gothic)'
    base = c.get('url_base', '')
    has_line = bool(c.get('line_url'))
    has_rsv = bool(c.get('reserve_url'))
    dm = c.get('dm_url') or ''  # インスタの DM の入口（2026/11/7）。空なら今までと同じ
    tel = c.get('tel', ''); tel_d = ''.join(ch for ch in tel if ch.isdigit())
    I = lambda: '<svg class="mk"><use href="#mk"/></svg>'
    P = parts_conf(c)  # 入れる部品（"parts"）。{} なら部品なし
    a1 = c.get('photo_style') == 'a1'  # 写真の見せ方を A1（手本）に寄せる（2026/11/24 おしゃれの基準③。付けなければ今までと同じ出力）
    W = reserve_words(c)  # 予約・相談の言葉（介護系は「見学・体験・ご相談」。2026/11/22）

    # ---------- 予約・相談の入口（いま使えるものを先に） ----------
    first_btns = []
    if has_rsv: first_btns.append(f'<a class="btn btn-main" {ext(c["reserve_url"])}>{W["rsv_btn"]}</a>')
    if has_line: first_btns.append(f'<a class="btn btn-line" {ext(c["line_url"])}>{LINE_ICON}{W["line_btn"]}</a>')
    if dm: first_btns.append(f'<a class="btn btn-main btn-dm" {ext(dm)}>{IG_ICON}{W["dm_btn"]}</a>')
    if tel: first_btns.append(f'<a class="btn btn-ghost" href="tel:{tel_d}">電話する <span class="nw">{e(tel)}</span></a>')
    if not first_btns: first_btns.append(f'<a class="btn btn-main" href="#reserve">{W["ask_btn"]}</a>')

    secs = [('menu', c.get('menu_title', 'メニュー・料金'))]
    if 'shop' in P: secs.append(('shop', P['shop'].get('title', '商品')))  # 商品はメニューのすぐ後ろ
    if 'calc' in P: secs.append(('calc', P['calc'].get('title', '料金の目安')))
    if 'cases' in P: secs.append(('cases', P['cases'].get('title', '施工例')))
    if c.get('flow'): secs.append(('flow', c.get('flow_title', 'ご依頼の流れ')))
    secs += [('reserve', c.get('reserve_title', W['title'])), ('access', c.get('info_title', '店舗情報')), ('faq', 'よくある質問')]
    if c.get('greeting'): secs.insert(0, ('greeting', 'ごあいさつ'))
    def _ins(before, item):  # 追加の部品をメニューの順番のよい所に入れる
        for n, (k, _v) in enumerate(secs):
            if k == before: secs.insert(n, item); return
        secs.append(item)
    if 'worries' in P: secs.insert(0, ('worries', P['worries'].get('nav', 'お悩みから探す')))
    if 'voices' in P: _ins('flow' if c.get('flow') else 'reserve', ('voices', P['voices'].get('title', 'お客様の声')))
    if 'news' in P: _ins('reserve', ('news', P['news'].get('title', 'お知らせ')))
    nav = ''.join(f'<a href="#{k}">{e(v)}</a>' for k, v in secs if k not in ('reserve', 'voices', 'news'))  # 上の案内が長くなりすぎないよう、お客様の声・お知らせは目次（toc）だけに出す
    toc = ''.join(f'<li><a href="#{k}">{e(v)}</a></li>' for k, v in secs)

    # ---------- トップ ----------
    hero = c.get('hero') or {}
    if hero.get('image'):
        hero_vis = f'<figure class="poster"><img src="{e(hero["image"])}" alt="{e(hero.get("alt","イメージ"))}" width="{hero.get("w",1600)}" height="{hero.get("h",1000)}" fetchpriority="high"></figure>'
    else:
        hero_vis = f'<div class="poster plain"><p class="plain-name">{e(short)}</p></div>'
    # 横長のヘッダー画像（hero.banner：全幅で最上部に出す。店のFacebookのカバーなど）。あるときは hero.image の大きな写真は出さない（2026/10/30）
    hb_cls = ''
    hb_html = ''
    if hero.get('banner'):
        hero_vis = ''
        hb_cls = ' has-banner'
        hb_html = f'<div class="hero-banner"><img src="{e(hero["banner"])}" alt="{e(hero.get("alt", short))}" width="{hero.get("w", 1170)}" height="{hero.get("h", 424)}" fetchpriority="high"></div>\n    '
    # 重ねる型（2026/11/22 ⑥-2 ネイル1周目）：写真があり・横長のヘッダー画像でなく・型（layout）を使わないとき。"hero_overlay": false で前の形
    ov = bool(hero.get('image')) and not hero.get('banner') and not c.get('layout') and c.get('hero_overlay', True)
    addr_html = f'<p class="addr">{PIN}<span>{e(c.get("area") or c.get("address",""))}</span></p>' if (c.get("area") or c.get("address")) else ''
    if a1 and hero.get('image') and not hero.get('banner'):
        # A1 の見せ方 6（2026/11/24 おしゃれの基準③・壊し役 3）：1画面目＝お店の写真（hero.image）が主役で大きく前、素材（hero.bg。source:stock で札）は後ろの雰囲気。文字は一言と小見出しとボタンだけ。重ねは囲み（stage）の中で切る
        bg = hero.get('bg') or {}
        bg_html = f'<figure class="hero-a1-bg"><img src="{e(bg["image"])}" alt="{e(bg.get("alt",""))}" width="{bg.get("w",1600)}" height="{bg.get("h",1000)}"></figure>' if bg.get('image') else ''
        hero_html = f'''
  <section class="hero a1">
    <div class="hero-a1-stage{' has-bg' if bg_html else ''}">
      {bg_html}
      <div class="hero-a1-text">
        <p class="eyebrow">{e(c.get("kind",""))}</p>
        <h1>{c.get("catch_html") or e(c.get("catch",""))}</h1>
        <div class="hero-btns">{''.join(first_btns)}</div>
      </div>
      <figure class="hero-a1-main"><img src="{e(hero["image"])}" alt="{e(hero.get("alt","イメージ"))}" width="{hero.get("w",1600)}" height="{hero.get("h",1000)}" fetchpriority="high"></figure>
    </div>
    <div class="hero-under"><div class="hu">
      <p class="lead">{e(c.get("lead",""))}</p>
      {addr_html}
      <ul class="toc" aria-label="このページの案内">{toc}</ul>
    </div></div>
  </section>'''
    elif ov:
        hero_html = f'''
  <section class="hero ov{hb_cls}">
    {hb_html}<div class="wrap">
      {hero_vis}
      <div class="hero-info hero-over">
        <p class="eyebrow">{e(c.get("kind",""))}</p>
        <h1>{c.get("catch_html") or e(c.get("catch",""))}</h1>
        <div class="hero-btns">{''.join(first_btns)}</div>
      </div>
    </div>
    <div class="hero-under"><div class="hu">
      <p class="lead">{e(c.get("lead",""))}</p>
      {addr_html}
      <ul class="toc" aria-label="このページの案内">{toc}</ul>
    </div></div>
  </section>'''
    else:
        hero_html = f'''
  <section class="hero{hb_cls}">
    {hb_html}<div class="wrap">
      {hero_vis}
      <div class="hero-info">
        <p class="eyebrow">{e(c.get("kind",""))}</p>
        <h1>{c.get("catch_html") or e(c.get("catch",""))}</h1>
        <p class="lead">{e(c.get("lead",""))}</p>
        {addr_html}
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
    m2 = str(c.get('menu_cols', '')) == '2'  # メニューを2列にする（2026/11/7）。書かなければ今までと同じ
    tabs = ''.join(f'<a href="#m-{e(m["id"])}">{e(m["name"])}</a>' for m in menus)
    if c.get('price_table'): tabs += f'<a href="#m-table">{e(c["price_table"].get("title","料金表"))}</a>'
    cards = []
    for m in menus:
        img = f'<div class="photo"><img src="{e(m["image"])}" alt="{e(m.get("alt", m["name"]))}" width="{m.get("w",1000)}" height="{m.get("h",750)}" loading="lazy"></div>' if m.get('image') else ''
        # 料金の目安（2026/11/22 ⑥-2 7周目）：price があるときだけ。price_note が無ければ「料金の目安」。無ければ今までどおり「お問い合わせください」
        # 値段の欄ごと出さない（2026/11/24 おしゃれの基準 7「空欄の扱い」：値段が無いときは「お問い合わせください」で埋めず、欄を出さない）："menu_price": false
        price = f'<div class="price"><small>{e(m.get("price_note") or "料金の目安")}</small><b>{e(m["price"])}</b></div>' if m.get('price') else ('' if c.get('menu_price', True) is False else '<div class="price"><span class="ask">料金は<wbr>お問い合わせください</span></div>')
        sub = ''.join(f'<li>{e(x)}</li>' for x in m.get('items', []))
        ask = ''
        if has_line:
            msg = c.get('line_msg', W['line_msg']).replace('{name}', m['name'])
            ask = f'<a class="ask-line" {ext(line_url(c, msg))}>{LINE_ICON}<span class="nw">{W["ask_line"].replace("{word}", e(c.get("menu_word","メニュー")))}</span></a>'
        elif tel:
            ask = f'<a class="ask-line tel" href="tel:{tel_d}"><span class="nw">{W["ask_tel"]}</span></a>'
        if dm and not has_line:
            ask = f'<a class="ask-line dm" {ext(dm)}>{IG_ICON}<span class="nw">インスタのDMで相談</span></a>' + ask
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
      <div class="menu-cards n{len(cards)}{' c2' if m2 else ''}">{''.join(cards)}
      </div>{table}
      <p class="price-note muted center">{e(c.get("menu_note","どれにすればいいか迷うときも、お気軽にご相談ください。"))}</p>
    </div>
  </section>'''

    # ---------- 流れ ----------
    # 後半の区画の写真（2026/11/22 ⑥-2 4周目。fill_photos が sec_photos に入れる。設定に書いてもよい）
    SP = c.get('sec_photos') if isinstance(c.get('sec_photos'), dict) else {}
    def sec_photo(k, cls='sec-photo'):
        o = SP.get(k) or {}
        if not o.get('image'): return ''
        return f'<figure class="{cls}"><img src="{e(o["image"])}" alt="{e(o.get("alt",""))}" width="{o.get("w",1200)}" height="{o.get("h",900)}" loading="lazy"></figure>'
    flow_html = ''
    if c.get('flow'):
        steps = ''.join(f'<li><h3>{e(s["title"])}</h3><p>{e(s.get("text",""))}</p></li>' for s in c['flow'])
        fp = sec_photo('flow')
        flow_html = f'''
  <section id="flow" class="sec flow">
    <div class="wrap{' has-photo' if fp else ''}">
      <div class="sec-head center"><i>{I()}flow</i><h2>{e(c.get("flow_title","ご依頼の流れ"))}</h2></div>
      {fp}<ol class="steps">{steps}</ol>
    </div>
  </section>'''

    # ---------- 予約・相談 ----------
    ways = []
    # ネット予約は欄の先頭（最初の画面・下の帯と同じ「いま使える窓口を先に」。2026/11/22 ⑥-2 ネイル10周目。前は LINE・電話のあと）
    if has_rsv:
        ways.append(f'<div class="way"><h3>{W["rsv_h"]}</h3><p>{e(W["rsv_p"])}</p><a class="btn btn-main" {ext(c["reserve_url"])}>{W["rsv_btn"]}</a></div>')
    if has_line:
        ways.append(f'<div class="way"><h3>LINE</h3><p>{e(c.get("line_text",W["line_p"]))}</p><a class="btn btn-line" {ext(c["line_url"])}>{LINE_ICON}友だち追加</a></div>')
    if dm:
        ways.append(f'<div class="way way-dm"><h3>インスタグラムのDM</h3><p>{e(c.get("dm_text","インスタグラムのメッセージで、お気軽にどうぞ。"))}</p><a class="btn btn-main" {ext(dm)}>{IG_ICON}DMを送る</a></div>')
    if tel:
        ways.append(f'<div class="way"><h3>お電話</h3><p>{e(c.get("tel_note",W["tel_p"]))}</p><a class="tel" href="tel:{tel_d}">{e(tel)}</a></div>')
    if 'form' in P:
        ways.append(f'<div class="way"><h3>フォーム</h3><p>{e(P["form"].get("way_text","選んで送るだけ。24時間いつでも送れます。"))}</p><a class="btn btn-main" href="#form">{W["form_btn"]}</a></div>')
    elif c.get('form_url'):
        ways.append(f'<div class="way"><h3>フォーム</h3><p>24時間いつでも送れます。</p><a class="btn btn-main" {ext(c["form_url"])}>フォームを開く</a></div>')
    if not ways: sys.exit('⚠️ 止めました：連絡の入口（tel・line_url・form・dm_url・reserve_url）が設定に1つもありません（「準備中」の欄は作りません。2026/11/21 ⑥-2）')
    rules = ''.join(f'<li>{e(x)}</li>' for x in c.get('rules', []))
    ctx = dict(c=c, P=P, I=I, has_line=has_line, tel=tel, tel_d=tel_d, name=name, short=short)
    rp = sec_photo('reserve', 'sec-bg')
    reserve_html = f'''
  <section id="reserve" class="sec reserve dark{' has-bg' if rp else ''}">{rp}
    <div class="wrap">
      <div class="sec-head center"><i>{I()}contact</i><h2>{e(c.get("reserve_title", W["title"]))}</h2></div>
      {f'<p class="muted center" style="margin-bottom:40px">{e(c.get("reserve_lead") or W["lead"])}</p>' if (c.get("reserve_lead") or W["lead"]) else ''}
      <div class="ways n{len(ways)}">{''.join(ways)}</div>
      {f'<div class="rules"><h4>{e(c.get("rules_title","ご予約について"))}</h4><ul>{rules}</ul></div>' if rules else ''}{part_form(ctx)}
    </div>
  </section>'''

    # ---------- 店舗情報 ----------
    info_rows = [('店名', name), ('住所', c.get('address')), ('アクセス', c.get('access_note')), ('営業時間', c.get('hours')), ('定休日', c.get('holiday')),
                 ('対応エリア', c.get('service_area')), ('駐車場', c.get('parking')), ('お支払い', c.get('payment'))] + [(k, v) for k, v in c.get('info_extra', [])]
    info = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in info_rows if v)
    if tel: info += f'<div><dt>電話</dt><dd><a href="tel:{tel_d}">{e(tel)}</a></dd></div>'
    mq = c.get('map_query')
    route = f'<a class="route" {ext("https://www.google.com/maps/dir/?api=1&destination=" + urllib.parse.quote(mq))}>{PIN}Googleマップで<wbr>道順を見る</a>' if mq and c.get('show_route', True) else ''
    # 地図と道順のボタンは別々に出し入れできる（2026/11/7）：show_map:false で地図（埋め込み）だけ、show_route:false で「道順を見る」だけ消す。どちらも書かなければ両方出る
    map_iframe = f'<iframe src="https://maps.google.com/maps?q={urllib.parse.quote(mq)}&amp;z=15&amp;output=embed" title="{e(short)}の地図" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>' if mq and c.get('show_map', True) else ''
    # 地図は「道順を見る」のすぐ下にも出す（2026/11/22 ⑥-2 ネイル9周目。本人「道順の下は地図に」。前は下の段だけで、店舗情報の欄は "access_map": true のときだけだった）。"access_map": false で店舗情報の欄の地図だけ消える
    mapf = f'<div class="map">{map_iframe}</div>' if map_iframe and c.get('access_map', True) else ''
    ap = sec_photo('about')  # 店舗情報の横の仕事の様子の写真（⑥-2 4周目）
    ap2 = sec_photo('about2', 'sec-photo sec-photo2') if ap else ''  # 大きい写真の角に重ねる小さい写真（⑥-2 ネイル8周目。大きさに変化）
    if ap: ap = f'<div class="sec-photos">{ap}{ap2}</div>'
    access_html = f'''
  <section id="access" class="sec access">
    <div class="wrap{' nomap' if not ap else ''}">
      <div>
        <div class="sec-head"><i>{I()}{e(c.get("info_eyebrow","access"))}</i><h2>{e(c.get("info_title","店舗情報"))}</h2></div>
        <dl class="info">{info}</dl>
        {route}{mapf}
      </div>
      {ap}
    </div>
  </section>'''

    # ---------- 下の段（フッター）：地図・住所・電話・営業時間・定休日・道順（2026/11/21 ⑥-2 2周目。本人「Googleマップなし ×」。設定に無いものは出ない） ----------
    foot_rows = []
    if c.get('address'): foot_rows.append(f'<p><span class="flabel">住所</span><span>{e(c["address"])}</span></p>')
    if tel: foot_rows.append(f'<p><span class="flabel">TEL</span><span><a href="tel:{tel_d}">{e(tel)}</a></span></p>')
    if c.get('hours'): foot_rows.append(f'<p><span class="flabel">営業時間</span><span>{e(c["hours"])}</span></p>')
    if c.get('holiday'): foot_rows.append(f'<p><span class="flabel">定休日</span><span>{e(c["holiday"])}</span></p>')
    # 地図は 1 か所だけ（2026/11/22 本人「Googleマップ 2回でてくる ×」＝壊れ）：店舗情報の「道順を見る」の下に出したときは下の段には出さない。"access_map": false のときだけ下の段に出る
    foot_map = f'<div class="foot-map">{map_iframe}</div>' if map_iframe and not mapf else ''
    foot_info = f'<div class="foot-grid{" nomap" if not foot_map else ""}"><div class="foot-info"><p class="fname">{e(name)}</p>{"".join(foot_rows)}{route}</div>{foot_map}</div>'

    # ---------- よくある質問 ----------
    faq = ''.join(f'<details><summary><span class="q">Q</span><span>{e(f["q"])}</span></summary><p><span class="a">A</span><span>{e(f["a"])}</span></p></details>' for f in c.get('faq', []))
    qp = sec_photo('faq')  # よくある質問の横の写真（⑥-2 ネイル8周目。PC は左に縦長・スマホは上に横長の帯）
    faq_html = f'''
  <section id="faq" class="sec faq">
    <div class="wrap{' has-photo' if qp else ''}">
      <div class="sec-head center"><i>{I()}q &amp; a</i><h2>よくある<wbr>ご質問</h2></div>
      {qp}<div class="faq-list">{faq}</div>
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
    if has_line: bar.append(f'<a class="l" {ext(c["line_url"])}>{W["line_bar"]}</a>')
    if has_rsv: bar.append(f'<a class="r" {ext(c["reserve_url"])}>{W["rsv_bar"]}</a>')
    elif dm: bar.insert(0, f'<a class="r" {ext(dm)}>{IG_ICON}インスタのDM</a>')  # DM は電話より先（左）
    elif 'form' in P: bar.append(f'<a class="r" href="#form">{W["form_bar"]}</a>')
    else: bar.append('<a class="r" href="#menu">メニュー</a>')

    # ---------- 頭 ----------
    desc = c.get('description', c.get('lead', ''))
    og = ''
    card_js = ''
    if base:
        # LINE のカードの番号（2026/10/10 自社で再発防止）：LINE はページの URL ごとにカードを覚える。iPhone の Safari の共有ボタンは canonical の URL を送るので、
        # 設定の card_v（1か所）から、og:url・canonical・開いたときアドレスバーに足す JS の3つを作る。カードの画像を変えたら、画像の名前を変え、card_v を次の数字にして作り直す
        card_v = int(c.get('card_v', 1))
        og = f'''<meta property="og:url" content="{e(base)}?v={card_v}">
<link rel="canonical" href="{e(base)}?v={card_v}">
<meta property="og:image" content="{e(base + c.get('og_image','images/og.jpg'))}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">'''
        card_js = f'''
<!-- LINE のカードの番号 ?v={card_v}（設定の card_v。og:url・canonical・この JS の3か所でそろえる。カードの画像を変えたら、画像の名前を変えて card_v を次の数字に） -->
<script>
(function(){{ try {{
  var q = location.search || '';
  if (/[?&]v=/.test(q)) return;
  history.replaceState(history.state, '', location.pathname + (q ? q + '&' : '?') + 'v={card_v}' + (location.hash || ''));
}} catch (e) {{}} }})();
</script>'''
    ld = {"@context": "https://schema.org", "@type": c.get('schema_type', 'LocalBusiness'), "name": name}
    if base: ld["url"] = base
    if tel: ld["telephone"] = '+81-' + tel.lstrip('0')
    if c.get('address'): ld["address"] = {"@type": "PostalAddress", "addressCountry": "JP", "streetAddress": c['address']}
    if c.get('area_served'): ld["areaServed"] = c['area_served']
    if c.get('opening_hours'): ld["openingHours"] = c['opening_hours']
    if sns: ld["sameAs"] = [s['url'] for s in sns]

    css = CSS
    # 上の部分の明るさ（2026/10/31）：設定の hero_style ＞ THEMES の hero_style ＞ dark。light のときだけ、明るい色の上書きを足す（dark は今までどおり）
    if (c.get('hero_style') or t.get('hero_style') or 'dark') == 'light': css += '\n' + LIGHT_HERO_CSS
    if dm: css += '\n' + DM_CSS
    if m2: css += '\n' + MENU2_CSS
    if c.get('layout'): css += '\n' + layouts.css(c['layout'])  # レイアウトの型（2026/11/11。tools/layouts.py）
    else:  # 型を使わないときだけ：写真の上の端に影・スマホでトップの写真を画面の 6 割の高さに（2026/11/21 ⑥-1。型は layouts.py の決まりのまま）
        light = (c.get('hero_style') or t.get('hero_style') or 'dark') == 'light'
        # 影は薄く（⑥-2 3周目。本人「もう少し明るい方がいい」：黒 .5 → .3、白 .7 → .6）
        css += '\n' + HERO_SP_CSS.replace('HERO_SHADE_A', 'rgba(255,255,255,.6)' if light else 'rgba(0,0,0,.3)').replace('HERO_SHADE_B', 'rgba(255,255,255,0)' if light else 'rgba(0,0,0,0)')
        if c.get('design', True): css += '\n' + DESIGN_CSS + '\n' + BGV_CSS  # 背景のデザイン（⑥-2 5周目）＋区画ごとの背景（⑥-3 3周目）。"design": false で前の無地に
        tone = c.get('photo_tone', True)
        if tone:  # 写真の色味をそろえる（⑥-2 ネイル6周目）
            css += '\n' + TONE_CSS.replace('PHOTO_TONE', tone if isinstance(tone, str) else PHOTO_TONE.get(c.get('theme_base', ''), 'saturate(.9)'))
        if c.get('hero_overlay', True):  # 重ねる型（⑥-2 ネイル1周目）
            css += '\n' + (OVERLAY_CSS.replace('OV_MID', 'rgba(255,255,255,.22)').replace('OV_END', 'var(--pale)').replace('OV_TEXT', 'var(--ink)').replace('OV_SHADOW', '0 1px 14px rgba(255,255,255,.95), 0 0 2px rgba(255,255,255,.8)') if light else
                            OVERLAY_CSS.replace('OV_MID', 'rgba(0,0,0,.25)').replace('OV_END', 'var(--dark)').replace('OV_TEXT', '#fff').replace('OV_SHADOW', '0 2px 16px rgba(0,0,0,.45)'))
    if a1: css += '\n' + A1_CSS  # 写真の見せ方を A1 に寄せる（2026/11/24 おしゃれの基準③。"photo_style":"a1" のときだけ）
    if P:
        pk = [k for k in PART_ORDER if k in P]
        if 'events' in P and 'notice' not in pk: pk.insert(0, 'notice')  # events が最上部に出す「次のライブ」の帯は notice の見た目を使う（最後のテスト・バー 2026/11/22）
        css += '\n' + PARTS_CSS['common'] + ''.join('\n' + PARTS_CSS[k] for k in pk)
    js = JS
    if P: js += ''.join('\n' + PARTS_JS[k] for k in PART_ORDER if k in P and k in PARTS_JS)
    for k, v in t.items(): css = css.replace('{{' + k + '}}', v)
    css = css.replace('{{head_font}}', head_font)
    hf = hand_font(c, t)  # 手書き風フォント（⑥-2 6周目）
    css = css.replace('{{hand_font}}', (f'"{hf}",' if hf else '') + 'var(--head)')
    if hf: css += '\n' + HAND_CSS
    belt_html, calc_html, cases_html, compare_html, shop_html = part_belt(ctx), part_calc(ctx), part_cases(ctx), part_compare(ctx), part_shop(ctx)
    bands = a1_bands(c) if a1 else ['', '', '']  # A1 の見せ方 6：写真の帯（大小の重ね・ずらし）を文の段の間に。写真の帯と白・灰の段が交互になる
    xp = parts_extra.render(ctx)  # 追加の部品の HTML（notice・credentials・strengths・news・voices・hours・areas・video）
    sample_note = f'<p class="sample-note" role="note">{e(c["sample_note"])}</p>' if c.get('sample_note') else ''

    out = f'''<!DOCTYPE html>
<html lang="ja" class="no-js">
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
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,500&family=Shippori+Mincho+B1:wght@500;600;700&family=Zen+Kaku+Gothic+New:wght@400;500;700{('&family=' + HAND_FONTS[hf]) if hf else ''}&display=swap" rel="stylesheet">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False)}
</script>
<style>
{css}
</style>
<script>document.documentElement.className = 'js';</script>{card_js}
</head>
<body>
<!-- このページは tools/make_site.py で作った（設定：{e(c.get('slug',''))}.json・道具の版 {e(TOOL_VERSION)}）。直すときは設定を直して作り直すか、このファイルを直接直す -->{sample_note}{xp["notice"]}
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="mk" viewBox="0 0 24 24">{mark}</symbol></svg>
<header class="head">
  <div class="wrap">
    <a href="#top" class="brand" aria-label="{e(short)} トップへ">{f'<img src="{e(c["logo"])}" alt="{e(short)}" width="46" height="46">' if c.get('logo') else ''}<span class="bn">{e(short)}</span>{f'<span class="bk">{e(c["kind"])}</span>' if c.get('kind') else ''}</a>
    <nav class="nav" id="gnav" aria-label="ページ内">{nav}<a href="#reserve" class="rsv">{e(c.get("nav_cta","ご相談"))}</a></nav>
    <button type="button" class="menubtn" aria-expanded="false" aria-controls="gnav"><i aria-hidden="true"></i>メニュー</button>
  </div>
</header>
<main id="top">{hero_html}{xp["events"]}{xp["credentials"]}{xp["worries"]}{greet}{xp["strengths"]}{belt_html}{menu_html}{bands[0]}{shop_html}{calc_html}{cases_html}{compare_html}{xp["video"]}{xp["voices"]}{flow_html}{bands[1]}{xp["news"]}{reserve_html}{xp["hours"]}{xp["areas"]}{access_html}{faq_html}{bands[2]}{sns_html}
</main>
<footer class="foot">
  <div class="wrap">
    {foot_info}
    <nav aria-label="フッター">{nav}</nav>
    <p class="copy">© {e(short)}</p>
  </div>
</footer>
{f'<nav class="spbar n{len(bar)}" aria-label="ご予約・ご相談">' + ''.join(bar) + '</nav>' if (tel or has_line or has_rsv or dm) else ''}
<a class="totop" href="#top" aria-label="ページの上へ">↑</a>
<script>
{js}
</script>
{analytics}
{pv_band}
</body>
</html>
'''
    if c.get('eyebrow_en', True) is False or a1: out = strip_eyebrow_en(out)  # 英字の飾りを出さない（2026/11/24 おしゃれの基準 6：英字と日本語で同じ意味を 2 回言わない。A1 の見せ方では必ず）
    else: out = add_sec_en(out)  # 見出しの後ろの薄い英字（⑥-2 5周目）
    if a1: out = a1_backgrounds(out)  # A1 の見せ方：区画の背景は白と薄い灰の交互（模様・斜めなし。2026/11/24 おしゃれの基準③）
    elif c.get('design', True) and not c.get('layout'): out = vary_backgrounds(out)  # 区画ごとの背景（⑥-3 3周目。同じ見え方が続かないように）
    out = mark_sources(out, c)  # 写真の出どころ（source：own＝お店の写真／stock＝素材）を img に書き、素材には「写真はイメージです」の札（2026/11/24 おしゃれの基準③ 壊し役 4）
    return out

# ======================================================================
# 写真の出どころ（2026/11/24 おしゃれの基準③ 壊し役 4）：site.json の写真ごとの "source"（"own"＝お店が撮って了承した写真／"stock"＝素材・見本）を
# <img data-source="…"> に写し、stock には「写真はイメージです」の札を付ける。source の無い写真は今までどおり（何も付けない）。check_site.py が「素材に札・お店の写真に札なし」を確かめる
# ======================================================================
IMG_NOTE = '<span class="img-note" aria-hidden="true">写真はイメージです</span>'

def photo_sources(c):
    """設定の中の {写真の道: source}（image と source を持つ dict を全部）"""
    out = {}
    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get('image'), str) and o.get('source') in ('own', 'stock'): out[o['image']] = o['source']
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(c); return out

def mark_sources(html, c):
    srcs = photo_sources(c)
    if not srcs: return html
    def f(m):
        tag = m.group(0)
        if 'data-source=' in tag: return tag
        sm = re.search(r'\bsrc="([^"]+)"', tag)
        if not sm or sm.group(1) not in srcs: return tag
        s = srcs[sm.group(1)]
        tag = tag[:-1].rstrip('/') + f' data-source="{s}">'
        return tag + (IMG_NOTE if s == 'stock' else '')
    return re.sub(r'<img\b[^>]*>', f, html)

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
  --hand:{{hand_font}};
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--gothic);font-size:16px;line-height:2;letter-spacing:.06em}
img{max-width:100%;height:auto;display:block}
/* 素材写真の札「写真はイメージです」（2026/11/24 おしゃれの基準③ 壊し役 4。source:"stock" の写真だけに付く） */
.photo,.b-shot,.sec-photo,.sec-bg,.card .photo,.case figure,.pb-big,.pb-small,.hero-a1-bg,.hero-a1-main{position:relative}
.img-note{position:absolute;right:8px;bottom:8px;z-index:3;font-family:var(--gothic);font-size:.62rem;line-height:1;letter-spacing:.08em;color:#fff;background:rgba(0,0,0,.42);padding:.45em .7em;border-radius:999px;pointer-events:none;white-space:nowrap}
a{color:inherit}
:focus-visible{outline:2px solid var(--primary);outline-offset:4px}
.wrap{width:min(1100px,100% - 40px);margin-left:auto;margin-right:auto}
h1,h2,h3{font-family:var(--head);font-weight:500;margin:0;line-height:1.7}
p{margin:0 0 1.2em}
.muted{color:var(--muted)}
.center{text-align:center}
.sample-note{margin:0;padding:0 16px;height:34px;line-height:34px;background:#333;color:#fff;font-size:.78rem;text-align:center;letter-spacing:.06em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis} /* 見本のときだけ出る注（sample_note）。1行に固定 */
.sample-note ~ .head{top:34px} /* 注がある分、ヘッダー（absolute）を下げる */
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
.head .wrap{text-shadow:0 1px 10px rgba(0,0,0,.6),0 0 2px rgba(0,0,0,.45)}  /* 店名・小見出しが明るい写真の上でも読めるように（⑥-2。影を薄くした分の補い） */
.brand{display:flex;align-items:center;text-decoration:none}
.brand img{width:46px;height:46px;border-radius:10px;margin-right:12px}
.bn{font-family:var(--head);font-size:1.15rem;letter-spacing:.14em}
.bk{font-size:.74rem;letter-spacing:.18em;color:var(--accent-soft);margin-left:12px}
.nav{display:flex;align-items:center;font-size:.86rem}
.nav a{text-decoration:none;opacity:.9;margin-left:24px;white-space:nowrap}
@media (min-width:861px) and (max-width:1180px){.bk{display:none}.nav a{margin-left:16px}}
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
.hero.has-banner{padding-top:74px;background:#000}
.hero-banner{background:#000}
.hero-banner img{display:block;width:100%;height:auto;max-width:1000px;margin:0 auto}
.hero.has-banner .wrap{display:block;min-height:0}
.hero.has-banner .hero-info{max-width:720px;margin:0 auto;padding:34px clamp(20px,6vw,90px) 70px}
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
.ask-line.tel{color:var(--primary-deep);border-color:var(--primary);font-family:inherit;font-size:.85rem;margin-top:14px}
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
/* 店舗情報の地図は「道順を見る」のすぐ下に小さめ（⑥-2 ネイル9周目。本人「道順の下は地図に」。下の段の地図と2つになるので、下の段の方を小さくした） */
.map{border-radius:var(--r);overflow:hidden;height:240px;margin-top:18px;background:var(--bg2);position:relative}
.map::before{content:"Googleマップ";position:absolute;left:0;right:0;top:50%;margin-top:-.7em;text-align:center;color:var(--muted);font-size:.85rem;letter-spacing:.2em}  /* 読み込みの間の文字（⑥-3 2周目。空の箱に見えないように） */
.map iframe{position:relative}
.map iframe{width:100%;height:100%;border:0;display:block}
@media (max-width:860px){.access .wrap{grid-template-columns:1fr;grid-gap:36px;gap:36px}.info{padding:4px 18px}.info div{grid-template-columns:5.5em 1fr}.map{height:200px}}
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
/* 後半の区画の写真（⑥-2 4周目）：流れの横・店舗情報の横・ご相談の背景 */
.sec-photo{margin:0;border-radius:var(--r);overflow:hidden;background:var(--bg2)}
.sec-photo img{display:block;width:100%;height:100%;-o-object-fit:cover;object-fit:cover}
.flow .wrap.has-photo{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,3fr);grid-gap:56px;gap:56px;align-items:center;max-width:1100px}
.flow .wrap.has-photo .sec-head{grid-column:1/-1}
.flow .wrap.has-photo .steps{margin:0;max-width:none}
.access .sec-photo{min-height:0;height:460px}
.access .sec-photos{-ms-flex-item-align:start;align-self:start}  /* 列の高さに伸ばさない（重ねる小さい写真が大きい写真から離れないように。ネイル9周目で直した） */
.reserve.has-bg{position:relative;overflow:hidden}
.reserve .sec-bg{position:absolute;top:0;left:0;right:0;bottom:0;margin:0}
.reserve .sec-bg img{width:100%;height:100%;-o-object-fit:cover;object-fit:cover;opacity:.35}
.reserve .sec-bg::after{content:"";position:absolute;top:0;left:0;right:0;bottom:0;background:-webkit-linear-gradient(top,rgba(0,0,0,.35),rgba(0,0,0,.62));background:linear-gradient(180deg,rgba(0,0,0,.35),rgba(0,0,0,.62))}
.reserve.has-bg .wrap{position:relative;z-index:1}
@media (max-width:860px){.flow .wrap.has-photo{grid-template-columns:1fr;grid-gap:28px;gap:28px}.flow .sec-photo{height:240px}.access .sec-photo{min-height:0;height:240px}}
/* 写真を 1 ページ 8 枚以上に（⑥-2 ネイル8周目。本人「写真が7枚以下」）：店舗情報の大きい写真の角に小さい正方形を重ねる・よくある質問の横に写真。大きさを変えて同じ構図のくり返しにしない */
.sec-photos{position:relative;margin-bottom:30px}
.sec-photos .sec-photo2{position:absolute;left:-10px;bottom:-30px;width:40%;max-width:210px;min-height:0;height:auto;border:4px solid #fff;border-radius:var(--r);box-shadow:0 10px 28px rgba(0,0,0,.18);background:#fff}
.sec-photos .sec-photo2 img{height:auto;border-radius:calc(var(--r) - 4px)}
.faq .wrap.has-photo{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,3fr);grid-gap:48px;gap:48px;align-items:start;max-width:1100px}
.faq .wrap.has-photo .sec-head{grid-column:1/-1}
.faq .wrap.has-photo .faq-list{max-width:none;margin:0;display:block}
.faq .sec-photo{height:380px}
@media (max-width:860px){.faq .wrap.has-photo{grid-template-columns:1fr;grid-gap:24px;gap:24px}.faq .sec-photo{min-height:0;height:190px}.access .sec-photos .sec-photo2{height:auto;left:-6px;bottom:-24px;width:38%}.sec-photos{margin-bottom:26px}}
/* SNS・下 */
.sns{background:var(--pale)}
.sns-list{display:flex;flex-wrap:wrap;justify-content:center}
.sns-list a{margin:6px;background:#fff;border-radius:14px;padding:16px 26px;text-decoration:none}
.foot{background:var(--dark);color:#e9e4d8;padding:56px 0 110px;font-size:.88rem}
.foot .fname{font-family:var(--head);font-size:1.1rem;letter-spacing:.14em;color:#fff}
.foot nav{display:flex;flex-wrap:wrap;margin:20px -10px}
.foot nav a{margin:4px 10px;text-decoration:none;opacity:.85}
.foot .copy{font-family:var(--latin);font-style:italic;opacity:.7;margin:0}
/* 下の段の地図・住所・電話・時間（⑥-2） */
.foot-grid{display:grid;grid-template-columns:1fr 1fr;grid-gap:40px;gap:40px;align-items:start;margin-bottom:28px}
.foot-grid.nomap{grid-template-columns:1fr}
.foot-info p{margin:0 0 10px;line-height:1.75;display:flex;align-items:baseline}
.foot-info .fname{display:block;margin-bottom:18px}
.foot-info .flabel{display:inline-block;width:5.4em;min-width:5.4em;margin-right:.6em;color:rgba(255,255,255,.55);font-size:.78rem;letter-spacing:.12em}
.foot-info a{color:#fff;text-decoration:none;border-bottom:1px solid rgba(255,255,255,.4)}
.foot-info .route{display:inline-flex;width:auto;margin-top:12px;background:var(--primary);color:#fff;padding:.8em 1.3em;font-size:.86rem}
.foot-info .route svg{fill:#fff}
.foot-map{border-radius:var(--r);overflow:hidden;min-height:200px;background:rgba(255,255,255,.08)}
.foot-map iframe{width:100%;height:100%;min-height:200px;border:0;display:block}
@media (max-width:860px){.foot-grid{grid-template-columns:1fr;grid-gap:22px;gap:22px}.foot-map,.foot-map iframe{min-height:170px}.foot-info .flabel{width:5em;min-width:5em}}
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

MENU2_CSS = r'''/* メニューを2列にする（menu_cols:2。2026/11/7） */
.menu-cards.c2{grid-template-columns:1fr 1fr}
@media (max-width:600px){.menu-cards.c2{grid-template-columns:1fr}}
'''

# 上の部分（トップ）を明るくする上書き（hero_style: light。2026/10/31）。背景は pale・文字は ink・小見出しと印は primary_deep。
# :root の --hero-style は check_site.py が「明るい上の部分」と見分けるための印。スマホのメニュー（開いたとき）は濃い色のまま
DM_CSS = r'''/* インスタグラムの DM の入口（dm_url。2026/11/7） */
.btn-dm svg,.way-dm .btn svg{width:1.2em;height:1.2em;margin-right:.5em;flex:none}
.ask-line.dm{color:#fff;background:var(--primary);border-color:var(--primary)}
.ask-line.dm:hover{background:var(--primary-deep);border-color:var(--primary-deep);color:#fff}
.ask-line.dm svg{width:1.1em;height:1.1em;margin-right:.45em;flex:none}
.ask-line.dm + .ask-line.tel{margin-top:8px}
@media (max-width:860px){.spbar a.r svg{width:1.1em;height:1.1em;margin-right:.35em;vertical-align:-.2em}}
'''

# スマホのトップの写真（2026/11/21 ⑥-1）：型（layout）を使わないときだけ足す。写真を画面の高さの 6 割にして、最初の画面の半分以上が写真になる形
# （前は写真の高さが成り行きで、横長の写真だと画面の 3 割ほどだった）。px の予備を先に書く（古いスマホ対策）
# 写真の上の端に薄い影（HERO_SHADE）：ヘッダーの店名・メニューの文字が、明るい空などの上でも読めるように。濃い上の部分は黒の影、明るい上の部分（hero_style light）は白の影
# 手書き風フォント（2026/11/22 ⑥-2 6周目。本人「手書き風フォントを使いたい」）。Google Fonts の無料・SIL Open Font License（表記不要）のものだけ
HAND_FONTS = {'Klee One': 'Klee+One:wght@400;600', 'Yomogi': 'Yomogi', 'Zen Kurenaido': 'Zen+Kurenaido', 'Yusei Magic': 'Yusei+Magic', 'Kaisei Decol': 'Kaisei+Decol:wght@400;500'}
def is_kaigo(c):
    """介護系か（デイサービス・訪問介護・訪問看護・福祉用具 など）。設定の "reserve_words": "kengaku" でも介護の言葉にできる（2026/11/22）"""
    if c.get('reserve_words') == 'kengaku': return True
    if c.get('reserve_words') == 'yoyaku': return False
    s = ' '.join(str(c.get(k) or '') for k in ('kind', '業種', 'title_place'))
    return any(w in s for w in ('介護', 'デイサービス', '訪問看護', '福祉用具', '通所', '居宅'))

def reserve_words(c):
    """予約・相談の入口の言葉。ふつうは「予約・相談」。介護系は「見学・体験・ご相談」（介護は予約でなく見学から。しさくんと同じ言葉。
    効果・医療・一番・割引の言葉は入れない＝成果物/2026-11-22/HP制作/介護系_言葉の決まり ⑤。2026/11/22）"""
    if not is_kaigo(c):
        return dict(rsv_btn='ネットで<wbr>予約する', rsv_bar='ネット予約', rsv_h='ネット予約', rsv_p='空いている日時を見て、24時間いつでもご予約いただけます。',
                    line_btn='LINEで<wbr>相談する', line_bar='LINEで相談', line_p='友だち追加して、メッセージでご相談ください。',
                    line_msg='ホームページを見ました。{name}について相談したいです。', ask_line='この{word}を<wbr>LINEで相談', ask_tel='電話で相談する',
                    tel_p='作業中は出られないことがあります。折り返しご連絡いたします。', dm_btn='インスタの<wbr>DMで予約・相談',
                    form_btn='フォームで<wbr>送る', form_bar='フォーム', ask_btn='お問い合わせ', title='ご予約・ご相談', lead='')
    return dict(rsv_btn='見学・体験を<wbr>申し込む', rsv_bar='見学を申し込む', rsv_h='見学・体験の申し込み', rsv_p='空いている日にちを選んで、見学・体験を申し込めます。',
                line_btn='LINEで<wbr>見学・ご相談', line_bar='見学・ご相談', line_p='友だち追加して、見学・体験・ご相談のメッセージをどうぞ。ケアマネジャーさんからのご相談も受けています。',
                line_msg='ホームページを見ました。{name}の見学・体験について相談したいです。', ask_line='この{word}を<wbr>LINEで相談', ask_tel='電話で見学・ご相談',
                tel_p='お電話で見学・体験・ご相談を承ります。ケアマネジャーさんからのご相談も受けています。', dm_btn='インスタの<wbr>DMで見学・ご相談',
                form_btn='フォームで<wbr>見学・ご相談', form_bar='ご相談', ask_btn='見学・ご相談', title='ご見学・体験・ご相談',
                lead='ご利用には要介護・要支援の認定が必要です。認定前の方もご相談ください。')

HAND_BY_GYOUSHU = {'造園': 'Klee One', 'カフェ': 'Yomogi', 'パン屋': 'Yomogi', 'まつげ': 'Zen Kurenaido', 'ネイル': 'Zen Kurenaido', 'よもぎ蒸し': 'Klee One', '美容室': 'Zen Kurenaido', '整体': 'Klee One',
                   '学習塾': 'Klee One', '英語教室': 'Yomogi', '居酒屋': 'Yusei Magic', 'スポーツ店': 'Yusei Magic', '農家の直売': 'Yomogi', '工務店': 'Klee One', '古民家・リトリート': 'Klee One', 'トリミング': 'Yomogi'}
HAND_BY_THEME = {'salon': 'Klee One', 'wa': 'Klee One', 'fresh': 'Yomogi', 'simple': 'Klee One', 'jouhin': 'Zen Kurenaido', 'genki': 'Yusei Magic'}
HAND_CSS = r'''/* 見出しと一言に手書き風フォント（⑥-2 6周目） */
.sec-head h2,.hero h1{font-family:var(--hand);font-weight:400;letter-spacing:.1em}
.hero h1{font-size:2.3rem;font-size:clamp(1.75rem,3.5vw,2.75rem);line-height:1.7}
.sec-head h2{font-size:1.9rem;font-size:clamp(1.6rem,3vw,2.2rem)}
'''

def hand_font(c, t):
    """手書き風フォントの名前（HAND_FONTS の鍵）か None。設定の hand_font ＞ 業種 ＞ 雰囲気（theme_base）＞ Klee One。false なら None"""
    v = c.get('hand_font', True)
    if v is False or v == '': return None
    if isinstance(v, str):
        if v in HAND_FONTS: return v
        print(f'⚠️ hand_font「{v}」は使えません（使えるもの：' + '・'.join(HAND_FONTS) + '）。業種・雰囲気から選びます')
    return HAND_BY_GYOUSHU.get(str(c.get('業種') or '').strip()) or HAND_BY_THEME.get(c.get('theme_base', ''), 'Klee One')

# 重ねる型（2026/11/22 ⑥-2 ネイル1周目。AI が「最初の画面に写真と文字の重ねが無い」と毎回書いた分）。OV_〜 は build で 暗い／明るい上の部分に合わせて置きかえる
OVERLAY_CSS = r'''/* 重ねる型：最初の画面で写真の上に小見出し・一言・ボタンを重ねる（"hero_overlay": false で前の形） */
.hero.ov .wrap{display:block;position:relative;min-height:600px;min-height:min(100vh,900px)}
.hero.ov .poster{position:absolute;top:0;left:0;right:0;bottom:0;height:auto;min-height:0}
.hero.ov .poster img{position:absolute;top:0;left:0;width:100%;height:100%;-o-object-fit:cover;object-fit:cover}
.hero.ov .poster::after{display:block;left:0;width:auto;background:-webkit-linear-gradient(top,rgba(0,0,0,0) 50%,OV_MID 80%,OV_END 100%);background:linear-gradient(180deg,rgba(0,0,0,0) 50%,OV_MID 80%,OV_END 100%)}  /* 膜はさらに薄く・下寄りに（ネイル3→7周目。写真の力を残し、文字は影で読ませる） */
.hero.ov .hero-over{position:absolute;left:0;right:0;bottom:0;z-index:2;max-width:none;padding:0 6% 60px;margin:0}
.hero.ov .hero-over .eyebrow{margin-bottom:14px;font-weight:700;text-shadow:OV_SHADOW}  /* 小見出し（地名）が写真に埋もれないように（ネイル7周目） */
.hero.ov .hero-over h1{color:OV_TEXT;font-size:2.8rem;font-size:clamp(2rem,4.2vw,3.4rem);line-height:1.6;margin-bottom:26px;text-shadow:OV_SHADOW}
.hero.ov .hero-btns{max-width:600px}
.hero-under{padding:30px 0 44px}
.hero-under .hu{max-width:1180px;margin:0 auto;padding:0 6%}
.hero-under .lead{max-width:760px;margin:0}
.hero-under .addr{margin-top:22px;padding-top:18px}
@media (max-width:860px){
  .hero.ov .wrap{min-height:560px;min-height:88vh}
  .hero.ov .poster{height:auto}
  .hero.ov .poster::after{display:block}
  .hero.ov .hero-over{padding:0 20px 26px}
  .hero.ov .hero-over h1{font-size:2rem;margin-bottom:18px}
  .hero.ov .hero-btns .btn{flex:1 1 100%}
  .hero-under{padding:22px 0 10px}
  .hero-under .hu{padding:0 20px}
}
'''

# 写真の色味をそろえる（2026/11/22 ⑥-2 ネイル6周目。AI が毎回「写真の色味がばらばら」）。雰囲気（theme_base）ごとの薄いフィルター。"photo_tone": false で切る・文字列で指定
PHOTO_TONE = {'salon': 'saturate(.85) sepia(.1) contrast(1.02)', 'wa': 'saturate(.88) sepia(.08)', 'fresh': 'saturate(.95) contrast(1.02)', 'simple': 'saturate(.9)', 'jouhin': 'saturate(.85) sepia(.1)', 'genki': 'saturate(1.02)'}
TONE_CSS = '.photo img,.poster img,.sec-photo img,.reserve .sec-bg img,.b-shot img,.case figure img,.cmp-frame img{-webkit-filter:PHOTO_TONE;filter:PHOTO_TONE}'  # 部品（帯・施工例・見比べ）の写真にも（⑥-3 2周目）

# 背景のデザイン（2026/11/22 ⑥-2 5周目。本人「デザイン性が欲しい」・⑭の「重ね・切りかえ・模様」）。色はテーマの変数だけを使う（どの組でも破綻しない）
DESIGN_CSS = r'''/* 背景のデザイン（⑥-2 5周目）：見出しの後ろに薄い英字（重ね）・区画の模様・斜めの切りかえ・写真の重ね枠 */
.sec-head{position:relative;z-index:0}
.sec-head::before{content:attr(data-en);position:absolute;left:0;top:-.42em;font-family:var(--latin);font-style:italic;font-weight:500;font-size:5.2rem;font-size:clamp(3.6rem,8vw,6.5rem);line-height:1;letter-spacing:.02em;color:var(--ink);opacity:.07;pointer-events:none;white-space:nowrap;z-index:-1;text-transform:capitalize}
.sec-head.center::before{left:50%;-webkit-transform:translateX(-50%);transform:translateX(-50%)}
.dark .sec-head::before{color:#fff;opacity:.09}
.sec-head i,.sec-head h2{position:relative}
.menu{background-color:var(--bg);background-image:-webkit-linear-gradient(top,var(--bg2) 0,var(--bg2) 46%,rgba(0,0,0,0) 46%);background-image:linear-gradient(180deg,var(--bg2) 0,var(--bg2) 46%,rgba(0,0,0,0) 46%)}
.access{background-color:var(--bg);background-image:-webkit-repeating-linear-gradient(top,rgba(0,0,0,0) 0,rgba(0,0,0,0) 31px,rgba(0,0,0,.05) 31px,rgba(0,0,0,.05) 32px);background-image:repeating-linear-gradient(180deg,rgba(0,0,0,0) 0,rgba(0,0,0,0) 31px,rgba(0,0,0,.05) 31px,rgba(0,0,0,.05) 32px)}
.faq{background-color:var(--bg2);background-image:-webkit-radial-gradient(rgba(0,0,0,.1) 1px,rgba(0,0,0,0) 1.6px);background-image:radial-gradient(rgba(0,0,0,.1) 1px,rgba(0,0,0,0) 1.6px);background-size:22px 22px}
.sec.dark,.foot{position:relative;z-index:0}
.sec.dark::before,.foot::before{content:"";position:absolute;left:0;right:0;top:-26px;height:60px;background:var(--dark);-webkit-transform:skewY(-1.5deg);transform:skewY(-1.5deg);z-index:-1}
.reserve.has-bg{overflow:visible}
.sec-photo{overflow:visible;position:relative;z-index:0}
.sec-photo img{border-radius:var(--r)}
.sec-photo::after{content:"";position:absolute;top:14px;left:14px;right:-14px;bottom:-14px;border:1px solid var(--accent-soft);border-radius:var(--r);z-index:-1}
.sec-photos .sec-photo2{z-index:2}.sec-photos .sec-photo2::after{display:none}  /* 重ねる小さい写真には枠線を付けない（ネイル8周目） */
@media (max-width:860px){.sec-head::before{top:-.3em}.sec-photo::after{top:10px;left:10px;right:-10px;bottom:-10px}}
/* 区画の見せ方に変化（⑥-2 ネイル4周目）：カードの段違い・流れは横一列・質問は2列・店舗情報の写真を表に重ねる（PC 幅だけ） */
@media (min-width:861px){
  .menu-cards.n4 .card:nth-child(even),.menu-cards.n3 .card:nth-child(2){margin-top:36px}
  .menu-cards.n4,.menu-cards.n3{align-items:start}
  .flow .wrap:not(.has-photo) .steps{max-width:none;display:grid;grid-template-columns:repeat(4,1fr);grid-gap:28px;gap:28px}
  .flow .wrap:not(.has-photo) .steps li{padding:64px 0 0;text-align:center}
  .flow .wrap:not(.has-photo) .steps li::before{left:50%;margin-left:-22px}
  .flow .wrap:not(.has-photo) .steps li::after{left:calc(50% + 30px);right:calc(-50% + 30px);top:21px;bottom:auto;border-left:0;border-top:2px dotted var(--line)}
  .faq-list{max-width:1000px;display:grid;grid-template-columns:1fr 1fr;grid-gap:0 20px;gap:0 20px;align-items:start}
  .access .wrap:not(.nomap) .sec-photos{margin-left:-48px;margin-top:40px;z-index:1}
}
'''

# 写真の見せ方を A1（手本）に寄せる（2026/11/24 おしゃれの基準③）。"photo_style":"a1" のときだけ足す CSS。実在のお店の形・文・写真は写していない（取り出したのは決まりだけ）
A1_CSS = r'''/* A1 の見せ方 4：緑の LINE ボタンは最初の画面と下の固定の帯だけ。カードの「LINE で相談」は文字のリンク、ご相談の友だち追加は細い枠 */
.card .ask-line{border:0;border-radius:0;padding:0;margin-top:12px;justify-content:flex-start;font-size:.78rem;letter-spacing:.1em;color:var(--muted);text-decoration:underline;text-underline-offset:.35em}
.card .ask-line svg{width:.95em;height:.95em;opacity:.55}
.reserve .btn-line{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.7)}
.reserve .btn-line:hover{background:rgba(255,255,255,.1)}
/* A1 の見せ方 5：斜めの切りかえをやめる（本人「外す＝まっすぐに」）。まっすぐの区切り＋余白で分ける。模様の背景も使わない（白と薄い灰の交互は a1_backgrounds が振る） */
.sec.dark::before,.foot::before{display:none}
.sec.bgv-band,.menu,.access,.faq{background-image:none}
.sec.a1-white{background-color:var(--bg);background-image:none}
.sec.a1-gray{background-color:var(--bg2);background-image:none}
.sec+.sec.a1-white,.sec+.sec.a1-gray{border-top:1px solid var(--line)}
/* A1 の見せ方 6-④：本文は小さく細く、見出しは大きく細い字で字間を広く、余白を広く（本人 ◎ の余白：白を広く・文は 1 行ずつ短く） */
body{font-size:14.5px;line-height:2.1;letter-spacing:.08em}
.sec{padding:130px 0}
.sec-head{margin-bottom:46px}
.sec-head h2{font-weight:500;font-size:1.9rem;font-size:clamp(1.6rem,3vw,2.3rem);letter-spacing:.24em;line-height:1.7}
.sec-lead,.price-note,.reserve .muted.center,.belt-note{max-width:30em;margin-left:auto;margin-right:auto}
.card p{font-size:.86rem;line-height:1.95}
.card h3{font-weight:500;letter-spacing:.16em}
.owner h3,.steps h3{font-weight:500;letter-spacing:.16em}
.card{border-radius:6px}.card .photo img,.sec-photo img,.b-shot img{border-radius:6px}
/* A1 の見せ方 6-①：1画面目＝画面いっぱい。お店の写真（主役）を大きく前に、素材（後ろ）は薄く。重ねは囲み（stage）の中で切る（横はみ出し 0） */
.hero.a1{background:var(--dark);color:#fff}
.hero.a1 .hero-a1-stage{position:relative;overflow:hidden;min-height:620px;min-height:min(92vh,900px);background:var(--dark)}
.hero.a1 .hero-a1-bg{position:absolute;top:0;left:0;right:0;bottom:0;margin:0;z-index:0}
.hero.a1 .hero-a1-bg img{position:absolute;top:0;left:0;width:100%;height:100%;-o-object-fit:cover;object-fit:cover;opacity:.5;-webkit-filter:saturate(.6);filter:saturate(.6)}
.hero.a1 .hero-a1-bg .img-note{right:auto;left:16px;bottom:14px;z-index:4}
.hero.a1 .hero-a1-text{position:absolute;left:6%;top:50%;-webkit-transform:translateY(-50%);transform:translateY(-50%);width:44%;z-index:2;text-shadow:0 2px 16px rgba(0,0,0,.45)}
.hero.a1 .hero-a1-text .eyebrow{color:rgba(255,255,255,.85);font-weight:500;margin-bottom:18px}
.hero.a1 .hero-a1-text h1{color:#fff;font-weight:500;font-size:2.4rem;font-size:clamp(1.7rem,3.6vw,3rem);letter-spacing:.2em;line-height:1.75;margin:0 0 30px}
.hero.a1 .hero-a1-main{position:absolute;right:5%;bottom:-7%;width:42%;max-width:520px;margin:0;z-index:1;border:6px solid #fff;box-shadow:0 18px 50px rgba(0,0,0,.35);background:#fff}
.hero.a1 .hero-a1-main img{width:100%;height:auto}
.hero.a1 .hero-under{background:var(--bg);color:var(--ink);padding:70px 0 44px}
.hero.a1 .hero-under .lead{max-width:30em;margin:0 auto;text-align:center}
.hero.a1 .hero-under .addr{justify-content:center;border-top:0}
/* A1 の見せ方 6-②③：写真の帯＝大きい写真と小さい写真を重ねてずらす（囲みの中で切る）。横に流れる帯も大小をずらす */
.pband{padding:40px 0 60px;overflow:hidden;background:var(--bg)}
.pband .pb-wrap{position:relative;width:min(1100px,100% - 40px);margin:0 auto;height:0;padding-bottom:54%}
.pband figure{margin:0;position:absolute}
.pband .pb-big{left:-4%;top:0;width:70%}
.pband .pb-small{right:0;bottom:0;width:38%;border:6px solid #fff;box-shadow:0 14px 40px rgba(0,0,0,.22);background:#fff}
.pband.alt .pb-big{left:auto;right:-4%}.pband.alt .pb-small{right:auto;left:0}
.pband img{width:100%;height:auto;display:block}
.pband .pb-big img{border-radius:4px}
.pband.one .pb-big{left:0;width:100%}.pband.one .pb-wrap{padding-bottom:46%}
.belt-track li:nth-child(even){margin-top:48px}
.belt-track li:nth-child(3n){width:280px}
@media (max-width:860px){
  body{font-size:14px}
  .sec{padding:84px 0}
  .hero.a1 .hero-a1-stage{min-height:0;padding:96px 0 0}
  .hero.a1 .hero-a1-text{position:static;-webkit-transform:none;transform:none;width:auto;padding:0 22px 18px}
  .hero.a1 .hero-a1-main{position:relative;right:auto;bottom:auto;width:80%;margin:0 0 -24px auto;border-width:5px}
  .hero.a1 .hero-under{padding:50px 0 24px}
  .pband .pb-wrap{padding-bottom:72%}
  .pband .pb-big{width:78%}.pband .pb-small{width:46%;border-width:4px}
  .belt-track li:nth-child(even){margin-top:30px}
}
'''

def a1_bands(c):
    """A1 の見せ方 6：写真の帯（文の段の間に入れる「大きい写真＋小さい写真の重ね」）。c["bands"]＝写真の配列（image・w・h・alt・source）。2 枚ずつ 1 つの帯に、最大 3 つ。
    写真は fill_a1（素材）か設定で入れる。無ければ帯は出ない。同じ写真は 2 回使わない（fill_a1 が見る）"""
    ph = [p for p in (c.get('bands') or []) if isinstance(p, dict) and p.get('image')]
    out = []
    for i in range(3):
        pair = ph[i * 2:i * 2 + 2]
        if not pair: out.append(''); continue
        big = pair[0]; small = pair[1] if len(pair) > 1 else None
        figs = f'<figure class="pb-big"><img src="{e(big["image"])}" alt="{e(big.get("alt",""))}" width="{big.get("w",1200)}" height="{big.get("h",800)}" loading="lazy"></figure>'
        if small: figs += f'<figure class="pb-small"><img src="{e(small["image"])}" alt="{e(small.get("alt",""))}" width="{small.get("w",800)}" height="{small.get("h",800)}" loading="lazy"></figure>'
        out.append(f'\n  <section class="pband{" alt" if i % 2 else ""}{" one" if not small else ""}" aria-label="写真"><div class="pb-wrap">{figs}</div></section>')
    return out

def a1_backgrounds(html):
    """A1 の見せ方：背景が決まっていない区画（暗い区画・最初の画面・写真の帯の区画を除く）に、白（a1-white）と薄い灰（a1-gray）を交互に振る。模様・斜めは使わない（2026/11/24 おしゃれの基準③ 5・6）"""
    n = [0]
    def f(m):
        cls = m.group(1).split()
        if 'sec' not in cls or 'dark' in cls or 'hero' in cls or 'pband' in cls: return m.group(0)
        look = 'a1-white' if n[0] % 2 == 0 else 'a1-gray'; n[0] += 1
        return m.group(0).replace('class="' + m.group(1) + '"', 'class="' + m.group(1) + ' ' + look + '"', 1)
    return re.sub(r'<section(?: id="[^"]*")? class="([^"]*)"', f, html)

def strip_eyebrow_en(html):
    """区画の見出しの小さな英字（sec-head の <i> の文字。menu・flow など）を消し、印（svg）だけ残す（"eyebrow_en": false。2026/11/24 おしゃれの基準 6「英字の飾り＋日本語の見出しで同じ意味を 2 回言わない」。
    薄い英字（data-en）も付けない。最初の画面の小見出し（地名）は別の class なので残る）"""
    def f(m):
        inner = m.group(2)
        svg = re.match(r'\s*(<svg\b.*?</svg>)', inner, re.S)
        return m.group(1) + (svg.group(1) if svg else '') + '</i>'
    return re.sub(r'(<div class="sec-head[^"]*">\s*<i>)(.*?)</i>', f, html, flags=re.S)

def add_sec_en(html):
    """見出しの後ろの薄い英字（⑥-2 5周目）：各区画の小見出し（sec-head の i の文字。menu・flow など）を data-en に写す（CSS の content:attr(data-en) が使う。JS なし・部品の見出しにも効く）"""
    def f(m):
        txt = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if not txt or len(txt) > 16 or 'data-en' in m.group(1): return m.group(0)
        return f'<div class="sec-head{m.group(1)}" data-en="{txt}"><i>{m.group(2)}</i>'
    return re.sub(r'<div class="sec-head([^"]*)"><i>(.*?)</i>', f, html, flags=re.S)

BG_LOOK_FIXED = {'hero': 'hero', 'dark': 'dark', 'menu': 'grad', 'access': 'lines', 'faq': 'dots', 'sns': 'pale', 'cred': 'soft'}  # 背景が決まっている区画（変えない）
BG_LOOKS = ['plain', 'soft', 'dots', 'lines', 'band']  # 部品の区画に順に振る背景（CSS の .sec.bgv-〇〇）

def vary_backgrounds(html):
    """区画ごとの背景（2026/11/22 ⑥-3 3周目。指示書「部品の区画にも模様。同じ背景が3つ続かない」）：
    <main> の区画を上から見て、背景が決まっていない区画（部品・流れ など）に、直前と違う見え方（無地・薄い色・点・罫線・斜めの帯）を順に振る。
    決まっている区画（最初の画面・メニューの面のずらし・暗いご相談・店舗情報の罫線・質問の点・下の段）はそのまま。"design": false・型（layout）のときは呼ばない"""
    prev = ['hero']; n = [0]
    def f(m):
        cls = m.group(1).split()
        fixed = next((BG_LOOK_FIXED[k] for k in cls if k in BG_LOOK_FIXED), None)
        if fixed or 'sec' not in cls: prev.append(fixed or 'other'); return m.group(0)
        for _ in BG_LOOKS:
            look = BG_LOOKS[n[0] % len(BG_LOOKS)]; n[0] += 1
            if look != prev[-1] and not (look == 'soft' and prev[-1] == 'grad'): break  # 直前と同じ見え方にしない（メニューの面のずらしの次に薄い色も避ける）
        prev.append(look)
        return m.group(0).replace('class="' + m.group(1) + '"', 'class="' + m.group(1) + ' bgv-' + look + '"', 1)
    return re.sub(r'<section(?: id="[^"]*")? class="([^"]*)"', f, html)

BGV_CSS = r'''/* 区画ごとの背景（⑥-3 3周目）：vary_backgrounds が部品の区画に順に振る。同じ見え方が続かないように */
.sec.bgv-plain{background-color:var(--bg);background-image:none}
.sec.bgv-soft{background-color:var(--bg2);background-image:none}
.sec.bgv-dots{background-color:var(--bg);background-image:-webkit-radial-gradient(rgba(0,0,0,.09) 1px,rgba(0,0,0,0) 1.6px);background-image:radial-gradient(rgba(0,0,0,.09) 1px,rgba(0,0,0,0) 1.6px);background-size:22px 22px}
.sec.bgv-lines{background-color:var(--pale);background-image:-webkit-repeating-linear-gradient(top,rgba(0,0,0,0) 0,rgba(0,0,0,0) 31px,rgba(0,0,0,.05) 31px,rgba(0,0,0,.05) 32px);background-image:repeating-linear-gradient(180deg,rgba(0,0,0,0) 0,rgba(0,0,0,0) 31px,rgba(0,0,0,.05) 31px,rgba(0,0,0,.05) 32px)}
.sec.bgv-band{background-color:var(--bg);background-image:-webkit-linear-gradient(top,var(--bg2) 0,var(--bg2) 56%,rgba(0,0,0,0) 56%);background-image:linear-gradient(172deg,var(--bg2) 0,var(--bg2) 56%,rgba(0,0,0,0) 56%)}
'''

HERO_SP_CSS = r'''/* トップの写真（⑥-1）：上の端に薄い影・スマホで大きく */
.poster::before{content:"";position:absolute;top:0;left:0;right:0;height:150px;background:-webkit-linear-gradient(top,HERO_SHADE_A,HERO_SHADE_B);background:linear-gradient(180deg,HERO_SHADE_A,HERO_SHADE_B);pointer-events:none;z-index:1}
@media (max-width:860px){
  .poster{height:420px;height:62vh;min-height:380px}
  .poster img{position:absolute;top:0;left:0;width:100%;height:100%;-o-object-fit:cover;object-fit:cover}
  .poster.plain{height:auto;min-height:220px}
}'''

LIGHT_HERO_CSS = r'''/* 明るい上の部分（hero_style: light） */
:root{--hero-style:light}
.head .wrap{color:var(--ink);text-shadow:none}
.bk{color:var(--primary-deep)}
.nav a:hover{color:var(--primary-deep)}
@media (max-width:860px){
  .menubtn{background:rgba(255,255,255,.75);color:var(--ink);border-color:var(--line)}
  .head.open .nav{color:#f3efe6}
}
.hero{background:var(--pale);color:var(--ink)}
.poster::after{background:linear-gradient(90deg,rgba(255,255,255,0),var(--pale))}
.poster.plain{background:radial-gradient(70% 60% at 50% 45%,#fff,var(--bg2))}
.plain-name{color:var(--primary-deep)}
.eyebrow{color:var(--primary-deep)}
.eyebrow::before{background:var(--primary-deep)}
.hero .lead{color:var(--muted)}
.addr{color:var(--ink);border-top-color:var(--line)}
.toc a{color:var(--ink);background:#fff;border-color:var(--line)}
.toc a:hover{border-color:var(--primary);color:var(--primary-deep)}
.hero .btn-ghost{border-color:var(--primary-deep);color:var(--primary-deep);background:#fff}
.hero .btn-ghost:hover{border-color:var(--primary)}'''

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

# ======================= 部品（入れる／入れないを選べる。2026/10/9） =======================
# 設定の "parts": {"belt": true, "compare": {...}, "calc": {...}, "cases": {...}, "form": {...}}
# それぞれの部品は、①動きを減らす設定の人には動かさない ②古いスマホ対策（マニュアル16の書き方）③JS がないときの代わりの表示 を入れている
# 色・書体は :root の変数（--primary・--head など）だけを使う → お店の theme に自然に合う
import layouts  # レイアウトの型（2026/11/11）
import parts_extra  # 追加の部品（お知らせの帯・実績・選ばれる理由・お知らせ・お客様の声・営業時間・対応エリア・動画・写真の拡大。2026/10/30）
PART_ORDER = ['belt', 'compare', 'calc', 'cases', 'form', 'shop'] + parts_extra.NAMES
SHOP_MAX = 5  # 商品は5点まで（決定事項 2026/10/10：商品ページ＝商品5点まで。6点以上は作る前に金額を伝える）

def parts_conf(c):
    """設定の "parts" を {部品名: 中身の辞書} にそろえる。true → {}（決まった中身）、false / null → 入れない。中身が足りない部品は外す"""
    if '_P' in c: return c['_P']
    P = {}
    for k, v in (c.get('parts') or {}).items():
        if k not in PART_ORDER: print('⚠️ 知らない部品です（入れません）：', k); continue
        if v is True: v = {}
        if isinstance(v, dict): P[k] = v
    if 'cases' in P and not P['cases'].get('items'): print('⚠️ cases：施工例（items）がないので入れません'); del P['cases']
    if 'compare' in P and not (P['compare'].get('before') and P['compare'].get('after')):
        cs = (P.get('cases') or {}).get('items') or []
        if cs: P['compare'].setdefault('before', cs[0].setdefault('before', {})); P['compare'].setdefault('after', cs[0].setdefault('after', {}))  # 施工例の1つ目を借りる（同じ辞書。写真の自動入れで施工例が埋まれば見比べも埋まる。⑥-3 1周目）
        else: print('⚠️ compare：前と後の写真（before・after）がないので入れません'); del P['compare']
    if 'calc' in P and not P['calc'].get('items'): print('⚠️ calc：項目（items）がないので入れません'); del P['calc']
    if 'shop' in P:
        items = [it for it in (P['shop'].get('items') or []) if it.get('name')]
        if not items: print('⚠️ shop：商品（items）がないので入れません'); del P['shop']
        elif len(items) > SHOP_MAX:
            print(f'⚠️ shop：商品が {len(items)} 点あります。商品ページは {SHOP_MAX} 点までなので、はじめの {SHOP_MAX} 点だけ出します（6点以上は作る前に金額を伝える）')
            P['shop']['items'] = items[:SHOP_MAX]
        else: P['shop']['items'] = items
        # 特商法の表示：本物のお店は必須の項目が空だと止める（見本は ⚠️）。2026/10/22 マニュアル K
        tk = P['shop'].get('tokushoho') or {}
        need = [('shipping', '送料'), ('payment', 'お支払い方法'), ('pay_timing', 'お支払いの時期'), ('delivery', 'お届けの時期'), ('returns', '返品について')]
        miss = [jp for k, jp in need if not str(tk.get(k) or '').strip()]
        if miss:
            if c.get('sample_note'): print('⚠️ shop：特定商取引法の表示が空の項目があります（見本なので「お問い合わせください」で出します）：' + '・'.join(miss))
            else: sys.exit('❌ shop：特定商取引法の表示に空の項目があります → ' + '・'.join(miss) + '。本物のお店では「お問い合わせください」のまま公開できません。設定の parts.shop.tokushoho に書いてから作り直してください')
        if tk.get('disclose') and not str(tk.get('email') or '').strip():
            sys.exit('❌ shop：tokushoho.disclose が true のときは、連絡先のメール（tokushoho.email）が要ります')
    parts_extra.validate(P, c)  # 追加の部品の中身を調べる（足りないものは外す）
    c['_P'] = P
    return P

def img_tag(o, alt='', w=1000, h=750):
    return f'<img src="{e(o["image"])}" alt="{e(o.get("alt") or alt)}" width="{o.get("w", w)}" height="{o.get("h", h)}" loading="lazy">'

def sec_head(I, eyebrow, title):
    return f'<div class="sec-head center"><i>{I()}{e(eyebrow)}</i><h2>{e(title)}</h2></div>'

def sec_lead(p):
    return f'<p class="sec-lead center muted">{e(p["lead"])}</p>' if p.get('lead') else ''

def yen(n): return f'{int(n):,}円'

def part_belt(x):
    """写真の帯：横にゆっくり流れる。中身は items か、なければメニューの写真"""
    p = x['P'].get('belt')
    if p is None: return ''
    c, I = x['c'], x['I']
    items = p.get('items') or [dict(image=m['image'], alt=m.get('alt', m['name']), title=m['name'], w=m.get('w', 1000), h=m.get('h', 750)) for m in c.get('menus', []) if m.get('image')]
    if not items: print('⚠️ belt：写真がないので入れません'); return ''
    lis = []
    for it in items:
        ttl, sub = it.get('title', ''), it.get('sub', '')
        sub_html = f'<small>{e(sub)}</small>' if sub else ''
        cap = f'<figcaption><b>{e(ttl)}</b>{sub_html}</figcaption>' if (ttl or sub) else ''
        lis.append(f'<li><figure><span class="b-shot">{img_tag(it, alt=ttl)}</span>{cap}</figure></li>')
    title = p.get('title', '写真')
    return f'''
  <section id="gallery" class="sec belt-sec">
    <div class="wrap">
      {sec_head(I, p.get('eyebrow', 'photo'), title)}
      {sec_lead(p)}
    </div>
    <div class="belt" id="belt"><ul class="belt-track" aria-label="{e(title)}の一覧">{''.join(lis)}</ul></div>
    <p class="belt-note center muted">{e(p.get('note', '横に動かして見られます。'))}</p>
  </section>'''

def part_compare(x):
    """前と後の見比べ：下に「後」の写真、その上に「前」の写真を左から重ね、つまみで「前」の見える幅を変える（左が前・右が後）。clip-path は使わず「幅＋overflow:hidden」（古いスマホでも動く）"""
    p = x['P'].get('compare')
    if p is None: return ''
    I = x['I']
    lb, la = p.get('label_before', '作業前'), p.get('label_after', '作業後')
    cap = f'<p class="cmp-cap muted center">{e(p["caption"])}</p>' if p.get('caption') else ''
    return f'''
  <section id="compare" class="sec compare-sec">
    <div class="wrap narrow">
      {sec_head(I, p.get('eyebrow', 'before / after'), p.get('title', '作業の前と後'))}
      {sec_lead(p)}
      <div class="cmp">
        <div class="cmp-frame" id="cmp-frame">
          <div class="cmp-over" id="cmp-over">{img_tag(p["before"], alt=lb)}</div>
          {img_tag(p["after"], alt=la)}
          <span class="cmp-line" id="cmp-line" aria-hidden="true"><i></i></span>
          <span class="cmp-tag l">{e(lb)}</span><span class="cmp-tag r">{e(la)}</span>
        </div>
        <label class="cmp-range"><span>つまみを<wbr>動かして<wbr>見比べる</span><input type="range" id="cmp-range" min="0" max="100" value="50" aria-label="{e(lb)}と{e(la)}を見比べる（左が{e(lb)}、右が{e(la)}）"></label>
        {cap}
      </div>
    </div>
  </section>'''

def part_calc(x):
    """合計の目安が出る料金：items の本数・回数（select）やチェックを足す。金額は HTML の data-price に持つ（JS に金額を書かない）"""
    p = x['P'].get('calc')
    if p is None: return ''
    c, I, has_line = x['c'], x['I'], x['has_line']
    rows = []
    for it in p['items']:
        note = f'<small>{e(it["note"])}</small>' if it.get('note') else ''
        unit = it.get('unit', '')
        unit_html = f'<small>／{e(unit)}</small>' if unit else ''
        price = f'<div class="calc-price">{yen(it["price"])}{unit_html}</div>'
        if it.get('type') == 'check':
            rows.append(f'<li class="chk"><label class="calc-chk"><input type="checkbox" data-price="{int(it["price"])}" data-name="{e(it["name"])}"><span><b>{e(it["name"])}</b>{note}</span></label>{price}</li>')
        else:
            opts = ''.join(f'<option value="{k}">{k}{e(unit)}</option>' for k in range(0, int(it.get('max', 10)) + 1))
            rows.append(f'<li><div class="calc-name"><b>{e(it["name"])}</b>{note}</div>{price}<div class="calc-q"><label><span class="vh">{e(it["name"])}の{e(unit or "数")}</span><select data-price="{int(it["price"])}" data-name="{e(it["name"])}" data-unit="{e(unit)}">{opts}</select></label></div></li>')
    line_btn = ''
    if has_line:
        msg = p.get('line_msg', 'ホームページの「料金の目安」を見ました。{items}（合計の目安 {total}）について相談したいです。')
        line_btn = f'<a class="btn btn-line calc-line" id="calc-line" {ext(c["line_url"])} data-oa="{e(c.get("line_id", ""))}" data-msg="{e(msg)}">{LINE_ICON}この内容で<wbr>LINEで相談</a>'
    note = p.get('note', '目安の金額です。実際の金額は、内容を確かめてからお見積もりでお出しします。')
    return f'''
  <section id="calc" class="sec calc-sec">
    <div class="wrap narrow">
      {sec_head(I, p.get('eyebrow', 'estimate'), p.get('title', '料金の目安'))}
      {sec_lead(p)}
      <div class="calc" id="calc-box">
        <ul class="calc-rows">{''.join(rows)}</ul>
        <div class="calc-total"><span>合計の<wbr>目安<small>（税込）</small></span><output id="calc-out" aria-live="polite">0円</output></div>
        <p class="calc-note muted">{e(note)}</p>
        <div class="calc-act">{line_btn}<button type="button" class="calc-reset" id="calc-reset">選び直す</button></div>
      </div>
    </div>
  </section>'''

def part_cases(x):
    """施工例：作業前・作業後の写真を並べる（samples/wa の作りを元に）"""
    p = x['P'].get('cases')
    if p is None: return ''
    I = x['I']
    lb, la = p.get('label_before', '作業前'), p.get('label_after', '作業後')
    arts = []
    for it in p['items']:
        meta = f'<span class="meta">{e(it["meta"])}</span>' if it.get('meta') else ''
        txt = f'<p>{e(it["text"])}</p>' if it.get('text') else ''
        arts.append(f'''
        <article class="case">
          <figure>{img_tag(it["before"], alt=lb)}<figcaption>{e(lb)}</figcaption></figure>
          <figure class="after">{img_tag(it["after"], alt=la)}<figcaption>{e(la)}</figcaption></figure>
          <div class="txt"><h3>{e(it.get("title", ""))}{meta}</h3>{txt}</div>
        </article>''')
    return f'''
  <section id="cases" class="sec cases-sec">
    <div class="wrap">
      {sec_head(I, p.get('eyebrow', 'works'), p.get('title', '施工例'))}
      {sec_lead(p)}
      <div class="cases">{''.join(arts)}
      </div>
    </div>
  </section>'''

def part_form(x):
    """選んで送れるフォーム：Formspree（endpoint）に送る。欄の名前は日本語（届くメールがそのまま読める）。JS がなくてもふつうに送れる"""
    p = x['P'].get('form')
    if p is None: return ''
    c, has_line, tel, name = x['c'], x['has_line'], x['tel'], x['name']
    topics = p.get('topics') or [m['name'] for m in c.get('menus', [])] + ['そのほか']
    reply = p.get('reply')
    if reply is None: reply = (['電話'] if tel else []) + (['LINE'] if has_line else []) + ['メール']
    times = p.get('times') or ['午前（〜12時）', '午後（12〜17時）', '夕方以降（17時〜）', 'いつでも']
    def chips(nm, vals, kind):
        out = []
        for v in vals:  # 最初は何も選ばれていない状態（radio も。2026/10/9 決定）
            out.append(f'<label class="chip"><input type="{kind}" name="{e(nm)}" value="{e(v)}"><span>{e(v)}</span></label>')
        return '<div class="chips">' + ''.join(out) + '</div>'
    endpoint = p.get('endpoint') or ''
    if not endpoint: print('⚠️ form：送り先（endpoint。Formspree の URL）がまだありません。送るボタンを押すと「準備中」と出ます')
    return f'''
      <div class="formbox" id="form">
        <div class="form-top"><span>{e(p.get("title", "ご相談フォーム"))}</span><span class="form-sub">{e(p.get("sub", "選んで送るだけ"))}</span></div>
        <form id="cform" action="{e(endpoint)}" method="POST" data-endpoint="{e(endpoint)}">
          <p class="form-lead">{e(p.get("lead", "選んで送るだけで大丈夫です。文を考えなくても、こちらからうかがいます。"))}</p>
          <label class="f-row"><span>お名前<span class="req">必須</span></span><input name="お名前" required autocomplete="name"></label>
          <label class="f-row"><span>ご連絡先（電話番号かメール）<span class="req">必須</span></span><input name="ご連絡先" required autocomplete="tel" placeholder="例：090-0000-0000"></label>
          <fieldset><legend>ご相談の内容<span class="opt-label">いくつでも</span></legend>{chips('ご相談の内容', topics, 'checkbox')}</fieldset>
          <fieldset><legend>ご希望の連絡方法</legend>{chips('ご希望の連絡方法', reply, 'radio')}</fieldset>
          <fieldset><legend>連絡がつきやすい時間<span class="opt-label">いくつでも</span></legend>{chips('連絡がつきやすい時間', times, 'checkbox')}</fieldset>
          <label class="f-row"><span>ほかに伝えたいこと<span class="opt-label">なくても可</span></span><textarea name="ほかに伝えたいこと" placeholder="なければ空のままで大丈夫です"></textarea></label>
          <input type="hidden" name="_subject" value="【{e(name)}】ホームページからのお問い合わせ">
          <input type="text" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true" class="gotcha">
          <button class="btn btn-main" type="submit">この<wbr>内容で<wbr>送る</button>
          <p class="formnote" id="formnote" role="status">{e(p.get("note", "送信後、こちらから折り返しご連絡します。"))}</p>
          <p class="formnote">いただいた内容は、ご相談への返事のためだけに使います。</p>
        </form>
      </div>'''

def part_shop(x):
    """商品（物販）：商品5点までをメニューと同じカードで並べ、「購入する」で Square の購入ページ（buy_url）へ（新しいタブ）。buy_url が空なら「準備中」（押せない）。
    下に「特定商取引法に基づく表示」を開閉式（details）で。書いていない項目は「お問い合わせください」（販売者・住所・電話はお店の設定から取る）。JS は使わない"""
    p = x['P'].get('shop')
    if p is None: return ''
    c, I = x['c'], x['I']
    arts = []
    for it in p['items']:
        img = f'<div class="photo">{img_tag(it, alt=it["name"])}</div>' if it.get('image') else ''
        price = f'<div class="price"><small>{e(it.get("price_note", "税込"))}</small><b>{e(it["price"])}</b></div>' if it.get('price') else '<div class="price"><span class="ask">価格は<wbr>お問い合わせください</span></div>'
        note = f'<p class="item-note muted">{e(it["note"])}</p>' if it.get('note') else ''
        if it.get('buy_url'): buy = f'<a class="btn btn-main buy" {ext(it["buy_url"])}>購入する</a>'
        else: buy = '<span class="btn buy soon" aria-disabled="true">準備中</span>'
        arts.append(f'''
        <article class="card item">
          {img}
          <div class="card-body">
            <h3>{e(it["name"])}</h3>
            {f'<p class="item-amount muted">{e(it["amount"])}</p>' if it.get('amount') else ''}
            <p>{e(it.get("text", ""))}</p>
            {price}
            {note}
            {buy}
          </div>
        </article>''')
    t = p.get('tokushoho') or {}
    ask = 'お問い合わせください'
    if t.get('disclose'):
        # 個人事業：名前・住所・電話は「請求があれば開示」でよい（連絡先のメールは出す）
        rows = [('販売者の氏名・住所・電話番号', 'ご請求があれば遅滞なく開示します。お問い合わせは下のメールアドレスへ'), ('メールアドレス', t.get('email'))]
    else:
        rows = [('販売者', t.get('seller') or c['name'])]
        if t.get('manager'): rows.append(('運営責任者', t['manager']))
        rows += [('住所', t.get('address') or c.get('address')), ('電話番号', t.get('tel') or c.get('tel')), ('メールアドレス', t.get('email'))]
    rows += [('販売価格', t.get('price')), ('送料', t.get('shipping')), ('お支払い方法', t.get('payment')), ('お支払いの時期', t.get('pay_timing')),
             ('お届けの時期', t.get('delivery'))]
    if t.get('period'): rows.append(('申込みの期限', t['period']))
    rows += [('返品について', t.get('returns'))] + [(k, v) for k, v in t.get('extra', [])]
    dl = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v or ask)}</dd></div>' for k, v in rows)
    note = p.get('note', 'お支払いは Square（スクエア）の画面で行います。カードの情報はお店には届きません。')
    return f'''
  <section id="shop" class="sec shop-sec">
    <div class="wrap">
      {sec_head(I, p.get('eyebrow', 'shop'), p.get('title', '商品'))}
      {sec_lead(p)}
      <div class="shop-items n{len(arts)}">{''.join(arts)}
      </div>
      <p class="shop-note muted center">{e(note)}</p>
      <details class="tokushoho" id="tokushoho">
        <summary>{e(p.get('tokushoho_title', '特定商取引法に基づく表示'))}</summary>
        <dl>{dl}</dl>
      </details>
    </div>
  </section>'''

PARTS_CSS = {
'common': r'''/* ---------- 部品（parts）共通 ---------- */
@media (prefers-reduced-motion:reduce){*,*::before,*::after{-webkit-transition:none!important;transition:none!important;-webkit-animation:none!important;animation:none!important}}
.wrap.narrow{max-width:760px}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}''',
'belt': r'''/* 部品：写真の帯（横にゆっくり流れる） */
.belt-sec{background:var(--bg2)}  /* 余白は .sec と同じ（⑥-3 2周目。前は 72/56px で詰まって見えた） */
.belt-sec .sec-head{margin-bottom:28px}
.belt-sec .sec-lead{margin:-12px auto 24px}
.belt{overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding:6px 0 10px}
.belt::-webkit-scrollbar{display:none}
.belt-track{list-style:none;margin:0;display:flex;width:-webkit-max-content;width:max-content;padding:0 20px}
.belt-track li{width:340px;flex:none;margin-right:22px}
.belt-track figure{margin:0}
.b-shot{display:block;border-radius:var(--r);overflow:hidden;background:var(--bg);box-shadow:0 10px 26px rgba(0,0,0,.08)}
.b-shot img{width:100%;height:auto}
.belt-track figcaption{display:flex;align-items:baseline;margin-top:10px;font-size:.92rem}
.belt-track figcaption b{font-family:var(--head);font-weight:500;letter-spacing:.12em;font-size:1.02rem}  /* カードの小見出しと同じ字間（⑥-3 2周目） */
.belt-track figcaption small{font-size:.8rem;color:var(--muted);margin-left:10px}
.belt-note{font-size:.82rem;margin:8px 20px 0}
@media (max-width:760px){.belt-track li{width:260px;margin-right:16px}}''',
'compare': r'''/* 部品：前と後の見比べ（つまみ） */
.compare-sec{background:var(--pale)}
.cmp-frame{position:relative;overflow:hidden;border-radius:var(--r);background:var(--bg2);box-shadow:0 10px 30px rgba(0,0,0,.06);-webkit-user-select:none;-moz-user-select:none;user-select:none;-webkit-touch-callout:none;cursor:ew-resize}
.cmp-frame > img{width:100%;height:auto;display:block}
.cmp-over{position:absolute;top:0;left:0;bottom:0;width:50%;overflow:hidden}
.cmp-over img{width:200%;max-width:none;height:auto;display:block}
.cmp-line{position:absolute;top:0;bottom:0;left:50%;width:3px;margin-left:-1px;background:#fff;box-shadow:0 0 0 1px rgba(0,0,0,.15);pointer-events:none}
.cmp-line i{position:absolute;top:50%;left:50%;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:var(--primary);box-shadow:0 4px 12px rgba(0,0,0,.25)}
.cmp-line i::before,.cmp-line i::after{content:"";position:absolute;top:50%;margin-top:-6px;border:6px solid transparent}
.cmp-line i::before{left:7px;border-right-color:#fff}
.cmp-line i::after{right:7px;border-left-color:#fff}
.cmp-tag{position:absolute;top:12px;z-index:2;font-family:var(--head);font-size:.82rem;letter-spacing:.14em;background:rgba(0,0,0,.6);color:#fff;padding:.25em 1em;border-radius:999px;line-height:1.7}
.cmp-tag.l{left:12px}
.cmp-tag.r{right:12px;background:var(--primary)}
.cmp-range{display:block;max-width:420px;margin:22px auto 0;font-size:.88rem;color:var(--muted);text-align:center}
.cmp-range span{display:block;margin-bottom:6px}
.cmp-range input{width:100%;accent-color:var(--primary);min-height:32px;margin:0}
.cmp-cap{font-size:.88rem;margin:14px 0 0}
/* JS がないとき：2枚を並べて出す */
.no-js .cmp-frame{display:grid;grid-template-columns:1fr 1fr;grid-gap:12px;gap:12px;background:none;overflow:visible;cursor:auto}
.no-js .cmp-frame > img,.no-js .cmp-over img{width:100%;border-radius:12px}
.no-js .cmp-over{position:static;width:auto}
.no-js .cmp-line,.no-js .cmp-range{display:none}
.no-js .cmp-tag{top:0}.no-js .cmp-tag.l{left:0}.no-js .cmp-tag.r{right:0}''',
'calc': r'''/* 部品：合計の目安が出る料金 */
.calc{background:#fff;border-radius:var(--r);padding:30px 24px;padding:30px clamp(18px,4vw,40px);box-shadow:0 10px 30px rgba(0,0,0,.06)}
.calc-rows{list-style:none;margin:0;padding:0}
.calc-rows li{display:grid;grid-template-columns:1fr auto 7.5em;grid-gap:14px;gap:14px;align-items:center;padding:16px 0;border-bottom:1px solid var(--line)}
.calc-rows li.chk{grid-template-columns:1fr auto}
.calc-name b,.calc-chk b{display:block;font-family:var(--head);font-weight:500;letter-spacing:.08em;font-size:1.05rem;line-height:1.6}
.calc-name small,.calc-chk small{display:block;font-size:.8rem;color:var(--muted);line-height:1.6}
.calc-price{font-family:var(--head);color:var(--dark);font-size:1.1rem;white-space:nowrap}
.calc-price small{font-family:var(--gothic);font-size:.78rem;color:var(--muted)}
.calc-q select{font:inherit;font-size:1rem;width:100%;min-height:44px;padding:6px 10px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink)}
.calc-chk{display:flex;align-items:flex-start;cursor:pointer}
.calc-chk input{width:22px;height:22px;margin:.45em 12px 0 0;flex:none;accent-color:var(--primary)}
.calc-total{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;margin-top:18px;padding-top:18px;border-top:2px solid var(--dark)}
.calc-total span{font-family:var(--head);letter-spacing:.1em}
.calc-total small{font-family:var(--gothic);font-size:.8rem;color:var(--muted)}
.calc-total output{font-family:var(--head);font-size:2rem;color:var(--primary-deep);letter-spacing:.04em;line-height:1.3}
.calc-note{font-size:.85rem;margin:14px 0 0}
.calc-act{display:flex;flex-wrap:wrap;align-items:center;margin:18px -6px 0}
.calc-act .btn{margin:6px}
.calc-reset{margin:6px;font:inherit;font-size:.88rem;background:none;border:1px solid var(--line);border-radius:999px;padding:.6em 1.3em;color:var(--muted);cursor:pointer;min-height:44px}
.calc-reset:hover{border-color:var(--primary);color:var(--primary-deep)}
@media (max-width:640px){
  .calc-rows li{grid-template-columns:1fr auto}
  .calc-rows li .calc-q{grid-column:1 / -1}
  .calc-total output{font-size:1.7rem}
  .calc-act .btn{flex:1 1 100%}
}
/* JS がないとき：料金表として出す */
.no-js .calc-q,.no-js .calc-total,.no-js .calc-act,.no-js .calc-chk input{display:none}
.no-js .calc-rows li{grid-template-columns:1fr auto}''',
'cases': r'''/* 部品：施工例（作業前・作業後） */
.cases-sec{background:var(--bg2)}
.cases{display:grid;grid-gap:56px;gap:56px;max-width:1000px;margin:0 auto}
.case{display:grid;grid-template-columns:1fr 1fr;grid-gap:18px;gap:18px}
.case figure{margin:0;position:relative;border-radius:var(--r);overflow:hidden;background:var(--bg);box-shadow:0 10px 30px rgba(0,0,0,.06)}  /* カードと同じ影（⑥-3 2周目） */
.case figure img{width:100%;height:auto;display:block}
.case figcaption{position:absolute;left:0;top:0;background:rgba(0,0,0,.6);color:#fff;font-family:var(--head);font-size:.85rem;letter-spacing:.2em;padding:.35em 1.1em;border-radius:0 0 12px 0;line-height:1.7}
.case figure.after figcaption{background:var(--primary)}
.case .txt{grid-column:1 / -1;display:grid;grid-template-columns:16em 1fr;grid-gap:28px;gap:28px;border-top:1px solid var(--line);padding-top:18px}
.case h3{font-size:1.2rem;letter-spacing:.12em}  /* カードの小見出しと同じ（⑥-3 2周目） */
.case .txt p{margin:0;font-size:.93rem;color:var(--muted)}
.case .meta{display:block;font-size:.8rem;color:var(--muted);font-family:var(--gothic);letter-spacing:.1em;margin-top:4px}
@media (max-width:760px){.case{grid-template-columns:1fr}.case .txt{grid-template-columns:1fr;grid-gap:6px;gap:6px}.cases{grid-gap:44px;gap:44px}}''',
'form': r'''/* 部品：選んで送れるフォーム */
.formbox{max-width:760px;margin:44px auto 0;background:var(--dark2);border:1px solid rgba(255,255,255,.14);border-radius:var(--r);overflow:hidden;scroll-margin-top:16px}
.form-top{display:flex;justify-content:space-between;align-items:baseline;padding:12px 28px;background:var(--primary);color:#fff;font-family:var(--head);letter-spacing:.14em}
.form-sub{font-family:var(--gothic);font-size:.78rem;letter-spacing:.1em;opacity:.9}
.formbox form{display:grid;grid-gap:18px;gap:18px;padding:24px 28px 28px}
.formbox .form-lead{margin:0;font-size:.92rem;color:#d9d4c8}
.f-row{display:block;font-size:.9rem}
.f-row > span{display:block;margin-bottom:6px;font-family:var(--head);letter-spacing:.08em}
.formbox input,.formbox textarea{font:inherit;font-size:16px;padding:12px 14px;border-radius:10px;border:2px solid transparent;background:#fff;color:var(--ink);width:100%;min-height:50px;display:block}
.formbox input:focus,.formbox textarea:focus{border-color:var(--primary);outline:none}
.formbox textarea{min-height:130px;resize:vertical}
.formbox fieldset{border:none;margin:0;padding:0;min-width:0}
.formbox legend{padding:0;margin-bottom:8px;font-family:var(--head);letter-spacing:.08em;font-size:.9rem}
.req,.opt-label{display:inline-block;margin-left:8px;font-family:var(--gothic);font-size:.7rem;letter-spacing:.05em;border-radius:4px;padding:0 6px;vertical-align:.15em;line-height:1.7}
.req{background:var(--primary);color:#fff}
.opt-label{border:1px solid rgba(255,255,255,.4);color:#d9d4c8}
.chips{display:flex;flex-wrap:wrap;margin:-4px}
.chip{position:relative;margin:4px;font-size:.92rem;cursor:pointer}
.formbox .chip input{position:absolute;left:0;top:0;width:1px;height:1px;min-height:0;padding:0;opacity:0}
.formbox .chip span{display:block;margin:0;padding:9px 16px;border-radius:999px;border:1.5px solid rgba(255,255,255,.4);color:#fff;line-height:1.5;min-height:44px;-webkit-transition:background .15s;transition:background .15s}
.formbox .chip input:checked + span{background:var(--primary);border-color:var(--primary)}
.formbox .chip input:checked + span::before{content:"✓ "}
.formbox .chip input:focus-visible + span{outline:2px solid #fff;outline-offset:2px}
.formbox .btn{width:100%;font-size:1.05rem}
.formnote{font-size:.82rem;color:#cfcabd;margin:0;line-height:1.7}
.formbox .gotcha{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}
.form-sent{text-align:center;padding:20px 0}
.form-sent h3{font-size:1.3rem;letter-spacing:.14em;margin-bottom:10px}
@media (max-width:640px){.form-top{padding:11px 18px}.formbox form{padding:18px 18px 22px}.form-sub{display:none}}''',
'shop': r'''/* 部品：商品（物販）。カードはメニューと同じ作り。「購入する」は Square の購入ページへ。特定商取引法の表示は details で開閉（JS なし） */
.shop-sec{background:var(--bg2)}
.shop-items{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));grid-gap:24px;gap:24px;max-width:1040px;margin:0 auto}
.shop-items.n1{max-width:380px}
.shop-items.n2{max-width:720px}
.shop-items .item h3{font-size:1.1rem}
.shop-items .item .item-amount{font-size:.82rem;margin:-6px 0 8px;letter-spacing:.04em}
.shop-items .price{margin-top:auto}
.item-note{font-size:.8rem;margin:8px 0 0;line-height:1.6}
.shop-items .buy{margin-top:16px;width:100%;min-height:48px}
.shop-items .buy.soon{background:var(--line);color:var(--muted);cursor:default;pointer-events:none}
.shop-note{font-size:.85rem;margin:28px auto 0;max-width:760px}
.tokushoho{max-width:760px;margin:40px auto 0;background:#fff;border-radius:var(--r);box-shadow:0 10px 30px rgba(0,0,0,.06)}
.tokushoho summary{cursor:pointer;position:relative;padding:18px 56px 18px 24px;min-height:44px;font-family:var(--head);font-weight:500;letter-spacing:.1em;list-style:none;line-height:1.6}
.tokushoho summary::-webkit-details-marker{display:none}
.tokushoho summary::after{content:"＋";position:absolute;right:22px;top:50%;margin-top:-.75em;font-size:1.2rem;line-height:1.5;color:var(--primary-deep)}
.tokushoho[open] summary::after{content:"－"}
.tokushoho dl{margin:0;padding:4px 24px 22px;border-top:1px solid var(--line)}
.tokushoho dl div{display:grid;grid-template-columns:9em 1fr;grid-gap:12px;gap:12px;padding:12px 0;border-bottom:1px solid var(--line);font-size:.92rem;line-height:1.8}
.tokushoho dl div:last-child{border-bottom:none}
.tokushoho dt{font-family:var(--head);color:var(--dark);letter-spacing:.06em}
.tokushoho dd{margin:0;color:var(--ink)}
@media (max-width:640px){
  .tokushoho dl div{grid-template-columns:1fr;grid-gap:2px;gap:2px}
  .tokushoho summary{padding:16px 48px 16px 18px}
  .tokushoho dl{padding:2px 18px 16px}
}''',
}

PARTS_JS = {
'belt': r'''// 部品：写真の帯。横にゆっくり流れる。さわっている間・マウスを乗せている間は止まる。指で横に動かせる
// 動きを減らす設定の人には流さない（横に動かして見られる）。古いスマホでも動くよう scrollLeft を requestAnimationFrame で動かす
(function(){
  var belt = document.getElementById('belt'); if (!belt || !window.requestAnimationFrame) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var track = belt.querySelector('.belt-track'), orig = track.innerHTML, n = 1;
  // 2つ以上並べて、1つ分まで来たら最初に戻す（つなぎ目が見えない）。短いときは画面の2倍になるまで増やす
  while (n < 2 || (track.scrollWidth < belt.clientWidth * 2 && n < 6)) { track.innerHTML += orig; n++; }
  var items = track.querySelectorAll('li'), per = items.length / n;
  for (var i = per; i < items.length; i++) items[i].setAttribute('aria-hidden', 'true');
  var x = 0, hold = false, until = 0, last = null, speed = 0.03, seen = true; // speed：1ミリ秒あたりの点数（約30点/秒）
  function one(){ return track.scrollWidth / n; }
  function stop(){ hold = true; }
  function later(){ hold = false; until = Date.now() + 2500; }
  belt.addEventListener('mouseenter', stop); belt.addEventListener('mouseleave', later);
  belt.addEventListener('touchstart', stop, {passive:true}); belt.addEventListener('touchend', later);
  belt.addEventListener('focusin', stop); belt.addEventListener('focusout', later);
  if ('IntersectionObserver' in window) new IntersectionObserver(function(es){ seen = es[0].isIntersecting; }).observe(belt);
  function step(ts){
    var dt = last === null ? 16 : Math.min(64, ts - last); last = ts;
    var w = one();
    if (!hold && seen && !document.hidden && Date.now() > until) {
      if (Math.abs(belt.scrollLeft - Math.round(x)) > 2) x = belt.scrollLeft; // 指で動かしたら、そこから続ける
      x += speed * dt; if (x >= w) x -= w;
      belt.scrollLeft = Math.round(x);
    } else { x = belt.scrollLeft; if (x >= w) { x -= w; belt.scrollLeft = x; } }
    requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
})();''',
'compare': r'''// 部品：前と後の見比べ。つまみ（range）か、写真の上を指・マウスで動かすと、左に重ねた「前」の写真の見える幅が変わる（左が前・右が後）
// clip-path は使わず「幅＋overflow:hidden」で切る（古いスマホでも動く）。中の写真の幅は枠と同じにそろえる
(function(){
  var frame = document.getElementById('cmp-frame'), r = document.getElementById('cmp-range'), a = document.getElementById('cmp-over'), line = document.getElementById('cmp-line');
  if (!frame || !r || !a) return;
  var img = a.querySelector('img');
  function fit(){ if (img) img.style.width = frame.clientWidth + 'px'; }
  function set(){ var v = r.value; a.style.width = v + '%'; if (line) line.style.left = v + '%'; }
  r.addEventListener('input', set); r.addEventListener('change', set);
  window.addEventListener('resize', fit); window.addEventListener('load', fit);
  fit(); set();
  var down = false;
  function at(ev){ var p = ev.touches ? ev.touches[0] : ev, b = frame.getBoundingClientRect(); var v = (p.clientX - b.left) / b.width * 100; r.value = Math.round(Math.max(0, Math.min(100, v))); set(); }
  frame.addEventListener('mousedown', function(ev){ down = true; at(ev); ev.preventDefault(); });
  window.addEventListener('mousemove', function(ev){ if (down) at(ev); });
  window.addEventListener('mouseup', function(){ down = false; });
  frame.addEventListener('touchstart', at, {passive:true});
  frame.addEventListener('touchmove', at, {passive:true});
})();''',
'calc': r'''// 部品：合計の目安。本数・回数（select）とチェックを足して出す。金額は HTML の data-price から読む（この JS に金額は書かない）
// LINE のボタンがあれば、選んだ内容と合計を下書きに入れる（line_id があるとき）
(function(){
  var box = document.getElementById('calc-box'); if (!box) return;
  var out = document.getElementById('calc-out'), line = document.getElementById('calc-line'), reset = document.getElementById('calc-reset');
  var ctrls = box.querySelectorAll('select[data-price], input[data-price]');
  function yen(n){ return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '円'; }
  function draw(){
    var total = 0, picked = [];
    for (var i = 0; i < ctrls.length; i++) {
      var el = ctrls[i], price = parseInt(el.getAttribute('data-price'), 10) || 0, q;
      if (el.tagName === 'SELECT') q = parseInt(el.value, 10) || 0; else q = el.checked ? 1 : 0;
      if (q > 0) { total += price * q; picked.push(el.getAttribute('data-name') + (el.tagName === 'SELECT' ? ' ' + q + (el.getAttribute('data-unit') || '') : '')); }
    }
    out.textContent = yen(total);
    if (line) {
      var oa = line.getAttribute('data-oa'), tpl = line.getAttribute('data-msg') || '';
      if (oa) line.href = 'https://line.me/R/oaMessage/' + encodeURIComponent(oa) + '/?' + encodeURIComponent(tpl.replace('{items}', picked.length ? picked.join('、') : '（まだ選んでいません）').replace('{total}', yen(total)));
    }
  }
  for (var j = 0; j < ctrls.length; j++) { ctrls[j].addEventListener('change', draw); ctrls[j].addEventListener('input', draw); }
  if (reset) reset.addEventListener('click', function(){ for (var k = 0; k < ctrls.length; k++) { if (ctrls[k].tagName === 'SELECT') ctrls[k].selectedIndex = 0; else ctrls[k].checked = false; } draw(); });
  draw();
})();''',
'form': r'''// 部品：フォーム。送り先は Formspree（form の action）。JS があれば、ページを離れずに送って「送りました」と出す
// 送れなかったとき（XMLHttpRequest が使えない・エラー）は、ふつうの送信（Formspree の画面）に切りかえる。送り先が未設定なら送らず案内を出す
(function(){
  var form = document.getElementById('cform'); if (!form) return;
  var note = document.getElementById('formnote'), btn = form.querySelector('button[type=submit]'), ep = form.getAttribute('data-endpoint');
  var done = note ? note.textContent : 'こちらから折り返しご連絡します。', plain = false;
  form.addEventListener('submit', function(ev){
    if (plain) return; // 切りかえたあとは、ふつうに送る
    if (!ep) { ev.preventDefault(); if (note) note.textContent = 'フォームの送り先はただいま準備中です。お電話など、ほかの方法でご相談ください。'; return; }
    if (!window.XMLHttpRequest || !window.FormData) return;
    ev.preventDefault();
    var g = form.querySelector('.gotcha'); if (g && g.value) return;
    if (btn) btn.disabled = true; if (note) note.textContent = '送っています…';
    var xhr = new XMLHttpRequest();
    xhr.open('POST', ep, true); xhr.setRequestHeader('Accept', 'application/json');
    xhr.onreadystatechange = function(){
      if (xhr.readyState !== 4) return;
      if (xhr.status >= 200 && xhr.status < 300) {
        form.innerHTML = '<div class="form-sent" role="status"><h3>送りました</h3><p class="formnote">' + done + '</p></div>';
      } else { plain = true; if (btn) btn.disabled = false; if (note) note.textContent = done; form.submit(); }
    };
    try { xhr.send(new FormData(form)); } catch (err) { plain = true; if (btn) btn.disabled = false; form.submit(); }
  });
})();''',
}

PARTS_CSS.update(parts_extra.CSS); PARTS_JS.update(parts_extra.JS)  # 追加の部品の見た目と動き（parts_extra.py）

STOCK_ROOT = os.path.join(os.path.dirname(os.path.dirname(HERE)), '_素材写真')  # 素材写真の置き場所（~/src/_素材写真。業種ごとのフォルダ。2026/11/6 決定）
FAKE_TEXT = '写真が入ります'  # 前の道具（2026/11/20 まで）が作っていた仮の絵の文。残っていれば置きかえる・check_site.py は ❌

def stock_folders():
    """_素材写真/ の業種のフォルダ名（_ で始まるものは除く）"""
    try: return sorted(d for d in os.listdir(STOCK_ROOT) if os.path.isdir(os.path.join(STOCK_ROOT, d)) and not d.startswith('_'))
    except Exception: return []

# メニューの名前の言葉 → 素材のファイル名に入っていそうな英字（2026/11/22 ⑥-2 ネイル2周目「カードの写真を仕事の名前に合う素材から」）。増やすのはここだけ
PHOTO_WORDS = {
    'ジェル': ['gel'], 'ケア': ['care'], 'オフ': ['off'], '長さ出し': ['ext', 'long'], 'フット': ['foot', 'pedi'], 'アート': ['art'], 'ハンド': ['hand'],
    '剪定': ['prun', 'shears', 'sentei'], '伐採': ['fell', 'saw', 'log', 'bassai'], '外構': ['exterior', 'wall', 'fence', 'stone', 'path', 'gaikou'], '庭': ['garden', 'niwa', 'yard'], '植栽': ['plant'],
    'まつげ': ['lash'], 'パーマ': ['perm'], 'カット': ['cut'], 'カラー': ['color'], 'トリートメント': ['treat'], 'ヘッドスパ': ['spa', 'head'],
    'よもぎ': ['yomogi', 'steam'], '脱毛': ['datsumou', 'removal', 'smooth'], 'フェイシャル': ['facial', 'face'], 'ボディ': ['body'], '整体': ['seitai', 'massage'], '骨盤': ['pelvis', 'kotsuban'],
    'パン': ['bread', 'pan'], 'コーヒー': ['coffee'], 'ケーキ': ['cake', 'sweet'], 'ランチ': ['lunch', 'plate'], 'モーニング': ['morning', 'toast'],
    'ジントニック': ['gin', 'tonic', 'cocktail'], 'カクテル': ['cocktail'], 'ウイスキー': ['whisk'], 'ビール': ['beer'], 'ワイン': ['wine'], 'おつまみ': ['food', 'snack', 'plate'], 'ライブ': ['live', 'stage', 'drums', 'music'],
    'リフォーム': ['reform', 'renov'], 'キッチン': ['kitchen'], '外壁': ['wall', 'exterior'], '屋根': ['roof'], '水回り': ['bath', 'sink'],
    '英会話': ['english', 'eikaiwa'], '学習': ['study', 'desk'], '車検': ['shaken', 'inspection'], '整備': ['repair', 'engine'], 'トリミング': ['trim', 'dog'], 'シャンプー': ['shampoo'],
}

OBJECT_WORDS = ['bottle', 'tool', 'shelf', 'product', 'item', 'goods']  # 物撮りらしい素材の名前。カードの写真としては最後に使う

def menu_tokens(m):
    """メニュー1つの手がかり：(種類, 英字) の集まり。stock（設定で指定）＞ id ＞ 名前の言葉"""
    toks = set()
    if m.get('stock'): toks.add(('stock', str(m['stock']).lower()))
    mid = str(m.get('id') or '').lower()
    if len(mid) >= 3: toks.add(('id', mid))
    name = str(m.get('name') or '')
    for jp, ens in PHOTO_WORDS.items():
        if jp in name: toks.update(('word', w) for w in ens)
    return toks

def match_menus(menus, photos):
    """メニューと素材を、名前の手がかりが合う組から当てる（stock 5点・id 3点・言葉 2点）。手がかりの無いメニューは残りを順に（景色→人の気配）。
    返り：[(menu, (name, path)), …]（メニューの順）。写真が足りなければ足りない分は入らない"""
    pairs = []
    for i, m in enumerate(menus):
        for j, (n, _) in enumerate(photos):
            nl = n.lower(); s = 0
            for kind, t in menu_tokens(m):
                if t in nl: s += {'stock': 5, 'id': 3, 'word': 2}[kind]
            if s: pairs.append((s, i, j))
    pairs.sort(key=lambda x: (-x[0], x[1], x[2]))
    got, used = {}, set()
    for s, i, j in pairs:
        if i in got or j in used: continue
        got[i] = j; used.add(j)
    is_object = lambda n: any(k in n.lower() for k in OBJECT_WORDS)  # 物撮り（瓶・道具・棚）は、手がかりの無いカードには最後に回す（ネイル5周目）
    rest = [j for j in range(len(photos)) if j not in used and not is_object(photos[j][0])] + [j for j in range(len(photos)) if j not in used and is_object(photos[j][0])]
    out = []
    for i, m in enumerate(menus):
        if i in got: out.append((m, photos[got[i]], '名前の手がかり'))
        elif rest: out.append((m, photos[rest.pop(0)], '順'))
    return out

def stock_photos(gyoushu):
    """業種のフォルダの写真を、_素材写真/素材一覧.md に載っている順に返す（利用条件が「商用可・表記不要」で、ファイルが実際にあるものだけ）。
    返り：[(ファイル名, フルパス), …]。一覧が無ければ []（一覧に無い写真は、フォルダにあっても使わない）"""
    lst = os.path.join(STOCK_ROOT, '素材一覧.md')
    if not os.path.exists(lst): return []
    out = []
    for line in open(lst, encoding='utf-8'):
        cells = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(cells) < 4 or not cells[0].startswith(gyoushu + '/'): continue
        if '商用可' not in cells[3] or '表記不要' not in cells[3]: continue
        rel = cells[0].split('（')[0].split('(')[0].strip()  # 「ネイル/nail4.jpg（薄紫の背景に…）」のような注釈つきも読む（2026/11/22）
        p = os.path.join(STOCK_ROOT, rel)
        if os.path.exists(p): out.append((os.path.basename(rel), p))
    return out

def jpeg_size(path):
    """JPEG の幅と高さ（Pillow なしで読む。読めなければ None）"""
    try:
        with open(path, 'rb') as f:
            if f.read(2) != b'\xff\xd8': return None
            while True:
                b = f.read(1)
                while b and b != b'\xff': b = f.read(1)
                while b == b'\xff': b = f.read(1)
                if not b: return None
                mk = b[0]
                if mk in (0x01, 0xd8) or 0xd0 <= mk <= 0xd7: continue
                ln = int.from_bytes(f.read(2), 'big')
                if 0xc0 <= mk <= 0xcf and mk not in (0xc4, 0xc8, 0xcc):
                    f.read(1); h = int.from_bytes(f.read(2), 'big'); w = int.from_bytes(f.read(2), 'big'); return w, h
                f.seek(ln - 2, 1)
    except Exception:
        return None

BRIGHT_MIN = 105   # 写真の平均の明るさ（0〜255）がこれ未満なら、写すときに少し明るくする（⑥-2 3周目）
BRIGHT_MAX_GAIN = 1.3

def photo_brightness(path):
    """写真の平均の明るさ（0〜255。Pillow が無ければ 128）。明るい素材を先に選ぶのに使う（2026/11/21 ⑥-2 3周目）"""
    try:
        from PIL import Image, ImageStat
        im = Image.open(path).convert('L'); im.thumbnail((200, 200))
        return ImageStat.Stat(im).mean[0]
    except Exception:
        return 128

def copy_photo(src, dst, ratio=None):
    """素材写真を images/ に写す。ratio（w/h）があれば真ん中をその比に切る（Pillow があるとき。無ければそのまま写す）。向きを直し、位置情報などは消える。
    暗い写真（平均の明るさ BRIGHT_MIN 未満）は BRIGHT_MAX_GAIN 倍まで少し明るくする（2026/11/21 ⑥-2 3周目）"""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        from PIL import Image, ImageOps, ImageEnhance, ImageStat
        im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
        b = ImageStat.Stat(im.convert('L')).mean[0]
        if b < BRIGHT_MIN: im = ImageEnhance.Brightness(im).enhance(min(BRIGHT_MAX_GAIN, BRIGHT_MIN / max(b, 1)))
        if ratio:
            W, H = im.size
            if W / H > ratio: nw = int(H * ratio); im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
            else: nh = int(W / ratio); im = im.crop((0, (H - nh) // 2, W, (H - nh) // 2 + nh))
        if im.size[0] > 1600: im = im.resize((1600, int(im.size[1] * 1600 / im.size[0])), Image.LANCZOS)
        im.save(dst, 'JPEG', quality=82, optimize=True, progressive=True)
    except ImportError:
        shutil.copy(src, dst)

def fill_photos(c, outdir):
    """トップ（hero）とメニューのカード（menus）に写真が無いところへ、業種の素材写真を入れる（2026/11/21 ⑥-1「写真」）。
    ・無い＝image が空／ファイルが outdir に無い／前の道具の仮の絵（FAKE_TEXT の入った .svg）
    ・設定の image・w・h を写した写真に書きかえる（alt は設定のまま。無ければ付ける）。設定ファイル（site.json）は書きかえない（次に作り直しても同じ写真が入る）
    ・足りない・フォルダが無い・"業種" が無い → ⚠️ で止まり、何も書かない（黙って仮の絵にしない）"""
    def missing(o):
        if not (o and o.get('image')): return True
        p = os.path.join(outdir, o['image'])
        if not os.path.exists(p): return True
        if p.endswith('.svg') and FAKE_TEXT in open(p, encoding='utf-8', errors='ignore').read(): return True
        return False
    hero = c.get('hero') or {}
    need_hero = not hero.get('banner') and missing(hero)
    need_menus = [m for m in c.get('menus', []) if missing(m)]
    # 後半の区画の写真（2026/11/22 ⑥-2 4周目）：about（店舗情報の横）・flow（流れの横）・reserve（ご相談の背景）。"sec_photos": false で入れない
    spc = c.get('sec_photos')
    # faq（よくある質問の横）・about2（店舗情報の小さい写真）は ⑥-2 ネイル8周目（本人「写真が7枚以下」→ 1ページ 8枚以上に。大きさを変えて同じ構図のくり返しにしない）
    sec_slots = [] if spc is False else [k for k in ('about', 'flow', 'reserve', 'faq', 'about2') if missing((spc if isinstance(spc, dict) else {}).get(k))]
    # 部品の写真（2026/11/22 ⑥-3 1周目）：belt・cases・compare・shop に写真が無ければ、業種の素材から入れる（下の「部品の写真」）
    P = c.get('_P') if isinstance(c.get('_P'), dict) else {}
    cs, cp, sp, bp = P.get('cases') or {}, P.get('compare'), P.get('shop') or {}, P.get('belt')
    need_pairs = sum(1 for it in cs.get('items', []) if missing(it.get('before')) or missing(it.get('after')))
    borrowed = bool(cs.get('items')) and cp is not None and cp.get('before') is cs['items'][0].get('before')  # 施工例の1つ目を借りている（parts_conf）→ 施工例が埋まれば埋まる
    cp_need = cp is not None and not borrowed and bool(cp.get('before') or cp.get('after')) and (missing(cp.get('before')) or missing(cp.get('after')))
    if cp_need: need_pairs += 1
    need_shop = [it for it in sp.get('items', []) if missing(it)]
    need_belt = [it for it in (bp.get('items') or [])] if bp is not None else []
    need_belt = [it for it in need_belt if missing(it)]
    part_need = need_pairs or need_shop or need_belt or (bp is not None and not bp.get('items'))
    if not need_hero and not need_menus and not sec_slots and not part_need: return
    where = (['トップ（hero）'] if need_hero else []) + ['メニュー「' + m['name'] + '」' for m in need_menus]
    gy = str(c.get('業種') or '').strip()
    if not gy:
        if not (need_hero or need_menus): return  # 後半の区画だけなら、業種が無ければ黙って入れない
        sys.exit('⚠️ 止めました（何も書きかえていません）：' + '・'.join(where) + ' に写真がありません。\n'
                 f'   設定に "業種": "〇〇" を1行足すと、{STOCK_ROOT}/〇〇/ の写真を自動で入れます（今あるフォルダ：' + '・'.join(stock_folders()) + '）。\n'
                 '   または、設定に書いた場所（images/〜）に写真を置いてください（仮の絵は作りません。2026/11/21）')
    folder = os.path.join(STOCK_ROOT, gy)
    if not os.path.isdir(folder):
        if not (need_hero or need_menus): return
        sys.exit(f'⚠️ 止めました（何も書きかえていません）：業種「{gy}」の写真のフォルダ {folder} がありません（今あるフォルダ：' + '・'.join(stock_folders()) +
                 '。写真の取り方は _素材写真/素材の探し方と置き方.md）')
    photos = stock_photos(gy)
    photos = sorted(photos, key=lambda p: -photo_brightness(p[1]))  # 明るい素材を先に（⑥-2 3周目。前は素材一覧.md の順）
    heroes = [p for p in photos if 'hero' in p[0].lower()]
    rest = [p for p in photos if 'hero' not in p[0].lower() and 'owner' not in p[0].lower()]  # 人物（owner）はお店の人と間違われるので使わない
    is_people = lambda n: any(k in n.lower() for k in ('hands', 'back', 'work', 'tool'))  # 人の気配（顔の出ない手元・後ろ姿）
    rest = [p for p in rest if not is_people(p[0])] + [p for p in rest if is_people(p[0])]  # カードには景色を先に。人の気配は後半の区画へ（⑥-2 4周目）
    if need_hero and not heroes and rest: heroes, rest = rest[:1], rest[1:]
    if (need_hero and not heroes) or len(rest) < len(need_menus):
        sys.exit(f'⚠️ 止めました（何も書きかえていません）：業種「{gy}」の写真が足りません → 要る：' + '・'.join(where) + f'（{len(where)}枚）／使える：{len(photos)}枚'
                 f'（{folder}。素材一覧.md に載っていて商用可・表記不要のものだけ。人物（owner）は数えません）。\n'
                 '   写真を足して素材一覧.md に1行足すか（_素材写真/素材の探し方と置き方.md）、設定に書いた場所に写真を置いてください')
    def put(o, src, label, alt, ratio):
        name, path = src
        rel = o['image'] if (o.get('image') and o['image'].lower().endswith(('.jpg', '.jpeg'))) else 'images/' + name
        dst = os.path.join(outdir, rel)
        if not os.path.exists(dst): copy_photo(path, dst, ratio)
        o['image'] = rel
        wh = jpeg_size(dst)
        if wh: o['w'], o['h'] = wh
        if not o.get('alt'): o['alt'] = alt
        o['source'] = 'stock'  # 素材写真＝札「写真はイメージです」が付く（2026/11/24 壊し役 4）
        print(f'写真を入れました：{label} ← _素材写真/{gy}/{name} → {rel}')
    if need_hero:
        c['hero'] = hero; put(hero, heroes[0], 'トップ', (c.get('short_name') or c['name']) + 'のイメージ', None)
    # before/after の組（施工例・見比べ用。〇〇_before.jpg ↔ 〇〇_after.jpg）を先に取り分ける。カードの分が足りなくなるなら組をほどく（カードが先）
    pairs = []
    if need_pairs:
        byname = {n: (n, pth) for n, pth in rest}
        for n in list(byname):
            a = n.replace('before', 'after')
            if 'before' in n.lower() and a != n and a in byname and len(pairs) < need_pairs: pairs.append((byname[n], byname[a]))
    reserved = set(n for pr in pairs for n, _ in pr)
    avail = [p for p in rest if p[0] not in reserved]
    while len(avail) < len(need_menus) and pairs:
        pr = pairs.pop(); reserved -= set(n for n, _ in pr); avail = [p for p in rest if p[0] not in reserved]
    assign = match_menus(need_menus, avail)  # 仕事・メニューの名前に合う素材から（2026/11/22 ⑥-2 ネイル2周目）
    for m, src, how in assign:
        r = (m.get('w') / m.get('h')) if (m.get('w') and m.get('h')) else 4 / 3
        put(m, src, 'メニュー「' + m['name'] + '」' + ('' if how == '順' else '（' + how + '）'), m['name'], r)
    used = set(n for n, _ in heroes[:1]) if need_hero else set()
    used |= set(src[0] for (_m, src, _h) in assign)
    # ---------- 部品の写真（2026/11/22 ⑥-3 1周目。仮の絵は残さない） ----------
    # 施工例（cases）・見比べ（compare）は before/after の組から。商品（shop）は名前の手がかり＞物撮り（瓶・道具・棚）。写真の帯（belt）は残り。
    # 素材が足りないとき：施工例は入らない項目を外す（組が無いのに作らない）、商品は写真なしで出す、帯は使った写真をもう一度使う（印を出す）。止めない
    def put2(o, src, label, alt, ratio):
        put(o, src, label, alt, ratio); used.add(src[0])
    lb, la = cs.get('label_before', '作業前'), cs.get('label_after', '作業後')
    for it in cs.get('items', []):
        if missing(it.get('before')) or missing(it.get('after')):
            if not pairs:
                print(f'⚠️ 施工例「{it.get("title", "")}」：before/after の組の素材が足りないので外します（_素材写真/{gy}/ に 〇〇_before.jpg と 〇〇_after.jpg の組を足す）'); it['_drop'] = True; continue
            b, a = pairs.pop(0)
            it.setdefault('before', {}); it.setdefault('after', {})
            put2(it['before'], b, '施工例「' + it.get('title', '') + '」の' + lb, lb, 4 / 3)
            put2(it['after'], a, '施工例「' + it.get('title', '') + '」の' + la, la, 4 / 3)
    if cs.get('items'):
        cs['items'] = [it for it in cs['items'] if not it.get('_drop')]
        if not cs['items']: print('⚠️ 施工例：写真が入らないので部品ごと外します'); P.pop('cases', None)
    if cp_need:
        if pairs:
            b, a = pairs.pop(0); cp.setdefault('before', {}); cp.setdefault('after', {})
            put2(cp['before'], b, '見比べの' + cp.get('label_before', '作業前'), cp.get('label_before', '作業前'), 4 / 3)
            put2(cp['after'], a, '見比べの' + cp.get('label_after', '作業後'), cp.get('label_after', '作業後'), 4 / 3)
        elif P.get('cases'):
            cp.pop('before', None); cp.pop('after', None); print('見比べ：before/after の組が足りないので、施工例の1つ目の写真を使います')
        else:
            print('⚠️ 見比べ：before/after の組の素材が無いので外します'); P.pop('compare', None)
    if need_shop:
        avail2 = [p for p in rest if p[0] not in used]
        is_object = lambda n: any(k in n.lower() for k in OBJECT_WORDS)
        got = match_menus(need_shop, [p for p in avail2 if is_object(p[0])])  # 物撮りを先に
        done = set(id(m) for m, _, _ in got)
        got += match_menus([m for m in need_shop if id(m) not in done], [p for p in avail2 if not is_object(p[0]) and p[0] not in set(s[0] for _, s, _ in got)])
        for m, src, how in got:
            put2(m, src, '商品「' + m['name'] + '」' + ('' if how == '順' else '（' + how + '）'), m['name'], (m.get('w') / m.get('h')) if (m.get('w') and m.get('h')) else 4 / 3)
        for m in need_shop:
            if missing(m): print(f'⚠️ 商品「{m["name"]}」：素材が足りないので写真なしで出します'); m.pop('image', None)
    if bp is not None:
        avail2 = [p for p in rest if p[0] not in used]
        if need_belt:
            # 帯は景色（全景）を先に。物撮り・手元は明るさ・寄りがそろわないので後ろへ（⑥-3 2周目。AI「1枚目だけ暗くて寄りすぎ」）
            is_object = lambda n: any(k in n.lower() for k in OBJECT_WORDS)
            avail2 = [p for p in avail2 if not is_object(p[0]) and not is_people(p[0])] + [p for p in avail2 if is_people(p[0]) and not is_object(p[0])] + [p for p in avail2 if is_object(p[0])]
            scenery = [p for p in avail2 if not is_object(p[0]) and not is_people(p[0])]
            pseudo = [dict(name=it.get('title', ''), _ref=it) for it in need_belt]
            for m, src, how in match_menus(pseudo, scenery or avail2):  # まず景色だけで名前合わせ→順
                put2(m['_ref'], src, '写真の帯「' + m['name'] + '」' + ('' if how == '順' else '（' + how + '）'), m['name'], 4 / 3)
            left_b = [p for p in avail2 if p[0] not in used]
            for it in need_belt:  # 景色が足りなければ残り（手元→物撮り）
                if missing(it) and left_b:
                    src = left_b.pop(0); put2(it, src, '写真の帯「' + it.get('title', '') + '」（景色が足りないので手元の写真）', it.get('title', ''), 4 / 3)
            again = [p for p in rest if p[0] not in set(n for n, _ in heroes[:1])]  # 足りなければ、使った写真をもう一度（トップ以外）
            for it in need_belt:
                if missing(it) and again:
                    src = again.pop(0); put2(it, src, '写真の帯「' + it.get('title', '') + '」（素材が足りないので、ほかの区画と同じ写真）', it.get('title', ''), 4 / 3)
            bp['items'] = [it for it in bp['items'] if not missing(it)]
        elif not bp.get('items') and len(avail2) >= 3:  # items が無ければ、まだ使っていない素材で帯を作る（3枚未満なら今までどおりメニューの写真）
            bp['items'] = []
            for src in avail2[:6]:
                it = {}; put2(it, src, '写真の帯', (c.get('short_name') or c['name']) + 'の写真', 4 / 3); bp['items'].append(it)
    ev = P.get('events') or {}
    import datetime as _dt
    _today = (_dt.datetime.utcnow() + _dt.timedelta(hours=9)).date().isoformat()
    _up = sorted([it for it in ev.get('items', []) if str(it.get('date') or '') >= _today], key=lambda it: str(it.get('date')))
    need_ev = [it for it in _up[:1] if missing(it)]  # 写真が出るのは「次のイベント」だけなので、いちばん近い 1 件だけ入れる
    if need_ev:  # イベントの写真（ライブの素材 live・stage を先に。最後のテスト「バー」2026/11/22）
        avail2 = [p for p in rest if p[0] not in used]
        pseudo = [dict(name=(it.get('title') or '') + ' ライブ', _ref=it) for it in need_ev]
        for mm, src, how in match_menus(pseudo, avail2):
            put2(mm['_ref'], src, 'イベント「' + mm['_ref'].get('title', '') + '」' + ('' if how == '順' else '（' + how + '）'), mm['_ref'].get('title', ''), 3 / 2)
    # 後半の区画（about・flow・reserve）：残った素材から。名前に hands・back・work・tool の付く「人の気配」の写真を先に（顔の出ない手元・後ろ姿。2026/11/22 本人の決め）。足りなければ入れない（止めない）
    if sec_slots:
        left = [p for p in rest if p[0] not in used]
        ratios = {'about': 4 / 3, 'flow': 4 / 5, 'reserve': 16 / 9, 'faq': 3 / 2, 'about2': 1}  # faq は横長・about2 は正方形（大きさに変化。ネイル8周目）
        import math
        def pick(k):  # 人の気配の写真を先に、その中で枠の縦横（ratios）に近いものを選ぶ
            pool = [p for p in left if is_people(p[0])] or left
            if not pool: return None
            def dist(p):
                wh = jpeg_size(p[1]) or (4, 3)
                return abs(math.log((wh[0] / wh[1]) / ratios[k]))
            best = min(pool, key=dist); left.remove(best); return best
        order = [pick(k) for k in sec_slots]
        order = [p for p in order if p]
        labels = {'about': c.get('info_title', '店舗情報') + 'の横', 'flow': c.get('flow_title', 'ご依頼の流れ') + 'の横', 'reserve': c.get('reserve_title', 'ご予約・ご相談') + 'の背景',
                  'faq': 'よくある質問の横', 'about2': c.get('info_title', '店舗情報') + 'の小さい写真'}
        if not isinstance(c.get('sec_photos'), dict): c['sec_photos'] = {}
        for k, src in zip(sec_slots, order):
            o = c['sec_photos'].setdefault(k, {})
            if not (o.get('image') and o['image'].lower().endswith(('.jpg', '.jpeg'))): o['image'] = f'images/sec-{k}.jpg'
            put(o, src, labels[k], (c.get('short_name') or c['name']) + 'の仕事の様子', ratios[k])
        for k in sec_slots[len(order):]: print(f'（{labels[k]} の写真は、業種の素材が足りないので入れません）')

def fill_a1(c, outdir):
    """A1 の見せ方（"photo_style":"a1"）の素材：①1画面目の後ろ（hero.bg）②写真の帯（bands。2 枚×最大 3）を、業種の素材の「まだ使っていない物」から入れる（2026/11/24 おしゃれの基準③ 1・壊し役 3）。
    お店の写真は差しかえない（hero.image はそのまま主役）。素材は source:stock（札が付く）。同じ写真は 2 回使わない。業種のフォルダが無い・足りないときは入れない（止めない）"""
    if c.get('photo_style') != 'a1': return
    gy = str(c.get('業種') or '').strip()
    if not gy or not os.path.isdir(os.path.join(STOCK_ROOT, gy)): print('（A1 の見せ方：業種の素材が無いので、1画面目の後ろと写真の帯は入れません）'); return
    hero = c.get('hero') or {}
    used = set()  # もう使っている写真のファイル名（素材の名前の末尾と、images/ の中の名前）
    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get('image'), str): used.add(os.path.basename(o['image']))
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(c)
    photos = [p for p in stock_photos(gy) if 'owner' not in p[0].lower() and os.path.basename(p[0]) not in used and not os.path.exists(os.path.join(outdir, 'images', os.path.basename(p[0])))]
    photos = sorted(photos, key=lambda p: -photo_brightness(p[1]))
    def take(prefer=None):
        if not photos: return None
        i = next((k for k, p in enumerate(photos) if prefer and prefer in p[0].lower()), 0)
        return photos.pop(i)
    def put(o, src, label, ratio):
        name, path = src
        rel = o['image'] if (o.get('image') and o['image'].lower().endswith(('.jpg', '.jpeg'))) else 'images/' + os.path.basename(name)
        dst = os.path.join(outdir, rel)
        if not os.path.exists(dst): copy_photo(path, dst, ratio)
        o['image'] = rel; wh = jpeg_size(dst)
        if wh: o['w'], o['h'] = wh
        if not o.get('alt'): o['alt'] = ''
        o['source'] = 'stock'; used.add(os.path.basename(rel))
        print(f'写真を入れました（A1）：{label} ← _素材写真/{gy}/{name} → {rel}')
    if hero.get('image') and not (hero.get('bg') or {}).get('image'):
        src = take('hero')
        if src: hero['bg'] = {}; put(hero['bg'], src, '1画面目の後ろ（雰囲気）', 16 / 10)
    bands = c.get('bands')
    if not isinstance(bands, list): bands = []; c['bands'] = bands
    have = len([b for b in bands if isinstance(b, dict) and b.get('image')])
    k = have
    while k < 6 and photos:
        src = take()
        o = {'image': 'images/band-%d.jpg' % (k + 1)}; put(o, src, '写真の帯 %d' % (k + 1), 3 / 2 if k % 2 == 0 else 1)
        bands.append(o); k += 1
    if k < 2: print('（A1 の見せ方：写真の帯に入れる素材が足りません（%d 枚）。帯は少なめになります）' % k)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2: sys.exit(__doc__)
    conf, outdir = args[0], os.path.expanduser(args[1])
    c = json.load(open(conf, encoding='utf-8'))
    if c.get('pages'): import make_houjin; return make_houjin.main(conf, outdir)  # 法人の型（複数ページ。2026/11/13 段2a）。"pages" がなければ今までどおり
    # 安全弁（2026/11/21 順0「既存の店を守る」）：公開先のあるサイト（wrangler.jsonc あり）を、前と違う版の道具で作り直すときは止まる（見本帳 samples/ は wrangler.jsonc が無いので止めない）
    p_old = os.path.join(outdir, 'index.html')
    if os.path.exists(p_old) and os.path.exists(os.path.join(outdir, 'wrangler.jsonc')) and '--uwagaki' not in sys.argv:
        old = stamped_version(p_old)
        if old != TOOL_VERSION:
            sys.exit(f'⚠️ 止めました（何も書きかえていません）：{p_old} は道具の版「{old or "記録なし（2026/11/21 より前の道具）"}」で作ったページで、今の道具は「{TOOL_VERSION}」です。\n'
                     '   道具が変わっているので、作り直すと見た目が変わるかもしれません。作り直すなら --uwagaki を付けて動かし、できた index.html を前の index.old.html と見比べてください（diff index.old.html index.html）')
    os.makedirs(outdir, exist_ok=True)
    # 写真（2026/11/21 ⑥-1）：仮の絵（「写真が入ります」の .svg）はもう作らない
    P = parts_conf(c)
    # 連絡の入口（2026/11/21 ⑥-2）：電話・LINE・フォーム・インスタのDM・ネット予約のどれも無ければ ⚠️ で止まる（前は「準備中」の欄を出していた。お客さんがそこで止まる・作りかけに見えるのでやめた）
    if not (c.get('tel') or c.get('line_url') or c.get('reserve_url') or c.get('dm_url') or c.get('form_url') or 'form' in P):
        sys.exit('⚠️ 止めました（何も書きかえていません）：連絡の入口が設定に1つもありません → "tel"（電話）・"line_url"（LINE）・"parts" の "form"（フォーム）・"dm_url"・"reserve_url" のどれか1つを書いてください（「準備中」の欄は作りません。2026/11/21 ⑥-2）')
    # ①トップ・メニューのカード・後半の区画・部品（belt・cases・shop・compare）に写真が無ければ、設定の "業種" の素材写真を入れる（トップとカードが足りなければ ⚠️ で止まる。部品は 2026/11/22 ⑥-3 1周目から）
    fill_photos(c, outdir)
    fill_a1(c, outdir)  # A1 の見せ方の素材（1画面目の後ろ・写真の帯。2026/11/24）。"photo_style":"a1" でなければ何もしない
    # ②それでも、ごあいさつ・部品に設定に書いた写真が無ければ ⚠️ で止まる（写真を置くか、設定から外す。仮の絵は作らない）
    lack = []
    def need(obj, label):
        if obj and obj.get('image') and not os.path.exists(os.path.join(outdir, obj['image'])): lack.append(label + '：' + obj['image'])
    need(c.get('greeting'), 'ごあいさつ')
    for it in (P.get('belt') or {}).get('items', []): need(it, '写真の帯「' + (it.get('title') or '') + '」')
    cs = P.get('cases') or {}
    for it in cs.get('items', []):
        need(it.get('before'), '施工例の' + cs.get('label_before', '作業前')); need(it.get('after'), '施工例の' + cs.get('label_after', '作業後'))
    for it in (P.get('shop') or {}).get('items', []): need(it, '商品「' + it['name'] + '」')
    cp = P.get('compare') or {}
    need(cp.get('before'), '見比べの' + cp.get('label_before', '作業前')); need(cp.get('after'), '見比べの' + cp.get('label_after', '作業後'))
    if lack: sys.exit('⚠️ 止めました（何も書きかえていません）：写真がありません → ' + '／'.join(lack) +
                      '\n   設定に書いた場所に写真を置くか、設定からその写真（部品）を外してください（仮の絵は作りません。2026/11/21 ⑥-1）')
    s = build(c)
    try:
        sys.path.insert(0, HERE); import wbr
        s, n = wbr.add_wbr(s); print(f'文の折り返し：{n}か所')
    except SystemExit:
        print('⚠️ budoux がないので文の折り返しを入れていません（pip3 install budoux）')
    p = os.path.join(outdir, 'index.html')
    if os.path.exists(p): shutil.copy(p, os.path.join(outdir, 'index.old.html'))
    open(p, 'w', encoding='utf-8').write(s)
    print('作りました：', p, f'（道具の版 {TOOL_VERSION}）')
    # 「ページが見つかりません」ページ（404.html）。2026/10/21 決定事項 08
    p404 = os.path.join(outdir, '404.html')
    open(p404, 'w', encoding='utf-8').write(build_404(c))
    print('作りました：', p404, '（Cloudflare が無い住所のときに返す。wrangler.jsonc の not_found_handling）')
    # 設定はサイトのフォルダに一緒に置く（次に作り直すときはこれを直す）
    keep = os.path.join(outdir, 'site.json')
    if os.path.abspath(conf) != os.path.abspath(keep): shutil.copy(conf, keep); print('設定を置きました：', keep)
    write_cloudflare_files(outdir)
    chk = os.path.join(HERE, 'check_site.py')
    if os.path.exists(chk): subprocess.call([sys.executable, chk, outdir, '--no-browser'])

def build_404(c):
    """「ページが見つかりません」ページ（404.html）。2026/10/21 決定事項 08「404 ページを置く」。
    店名・色・印（ロゴ）・LINE・電話は設定から。道は全部サイトの根から（/ や /images/…）にする（無い住所がどの深さでも同じ所を指すため）。
    外に貼るリンクは # を使わない決まりなので、メニューは /menu（Cloudflare の転送で /#menu へ）。動きは付けない"""
    t = dict(THEMES[c.get('theme_base', 'salon')]); t.update(c.get('theme', {}))
    name, short = c['name'], c.get('short_name', c['name'])
    mark = MARKS.get(c.get('mark', 'heart'), MARKS['heart'])
    head_font = 'var(--mincho)' if c.get('font', 'mincho') == 'mincho' else 'var(--gothic)'
    tel = c.get('tel', ''); tel_d = ''.join(ch for ch in tel if ch.isdigit())
    logo = c.get('logo', '')
    if logo and not re.match(r'(https?:|/)', logo): logo = '/' + logo
    brand_img = f'<img src="{e(logo)}" alt="{e(short)}" width="46" height="46">' if logo else '<svg class="mk" viewBox="0 0 24 24" aria-hidden="true">' + mark + '</svg>'
    btns = ['<a class="btn btn-main" href="/">トップへ<wbr>戻る</a>', '<a class="btn btn-ghost" href="/menu">メニューを<wbr>見る</a>']
    if c.get('line_url'): btns.append(f'<a class="btn btn-line" {ext(c["line_url"])}>{LINE_ICON}LINE で<wbr>相談</a>')
    tel_html = f'<div class="tel-box">お電話での<wbr>ご相談<a class="tel" href="tel:{tel_d}">{e(tel)}</a></div>' if tel else ''
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>ページが見つかりません｜{e(name)}</title>
<!-- 「ページが見つかりません」ページ（404）。make_site.py が作る（決定事項 08）。Cloudflare が無い住所のときに 404 の印のまま返す（wrangler.jsonc の assets.not_found_handling） -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,500&family=Shippori+Mincho+B1:wght@500;600&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{{
  --primary:{t['primary']};--primary-deep:{t['primary_deep']};--accent-soft:{t['accent_soft']};--dark:{t['dark']};--bg:{t['bg']};--ink:{t['ink']};--muted:{t['muted']};--line:{t['line']};
  --mincho:"Shippori Mincho B1","Hiragino Mincho ProN","Yu Mincho","Noto Serif CJK JP",serif;
  --gothic:"Zen Kaku Gothic New","Hiragino Sans","Yu Gothic","Noto Sans CJK JP",sans-serif;
  --latin:"Cormorant Garamond","Shippori Mincho B1",serif;
  --head:{head_font};
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--gothic);font-size:16px;line-height:2;letter-spacing:.06em;word-break:keep-all;overflow-wrap:anywhere;line-break:strict}}
img{{max-width:100%;display:block}}
a{{color:inherit}}
:focus-visible{{outline:2px solid var(--primary);outline-offset:4px}}
.top{{background:var(--dark);padding:14px 20px}}
.brand{{display:-webkit-box;display:-webkit-flex;display:flex;-webkit-box-align:center;-webkit-align-items:center;align-items:center;text-decoration:none;width:-webkit-fit-content;width:fit-content;margin:0 auto;color:#f3efe6}}
.brand img,.brand .mk{{width:46px;height:46px;border-radius:10px;margin-right:12px}}
.brand .mk{{fill:var(--primary)}}
.bn{{font-family:var(--head);font-size:1.15rem;letter-spacing:.14em}}
.wrap{{max-width:560px;margin:0 auto;padding:48px 20px 64px;text-align:center}}
.mark{{font-family:var(--latin);font-style:italic;font-size:2.4rem;color:var(--primary-deep);line-height:1;letter-spacing:.1em}}
h1{{font-family:var(--head);font-weight:500;font-size:1.35rem;line-height:1.8;margin:10px 0 16px}}
p{{margin:0 0 1.2em;color:var(--muted);font-size:.95rem}}
.btns{{margin-top:22px}}
.btn{{display:-webkit-inline-box;display:-webkit-inline-flex;display:inline-flex;-webkit-box-align:center;-webkit-align-items:center;align-items:center;-webkit-box-pack:center;-webkit-justify-content:center;justify-content:center;text-decoration:none;font-weight:500;letter-spacing:.12em;padding:.95em 1.8em;border-radius:999px;line-height:1.4;text-align:center;width:100%;max-width:320px;margin:0 auto 12px}}
.btn svg{{width:1.25em;height:1.25em;margin-right:.5em}}
.btn-main{{background:var(--primary);color:#fff}}
.btn-ghost{{border:1px solid var(--ink);color:var(--ink);background:transparent}}
.btn-line{{background:#06c755;color:#fff}}
.tel-box{{margin-top:26px;padding-top:22px;border-top:1px solid var(--line);font-size:.9rem;color:var(--muted)}}
.tel{{display:block;font-family:var(--latin);font-size:1.9rem;letter-spacing:.06em;text-decoration:none;color:var(--ink);line-height:1.3;margin-top:4px}}
footer{{text-align:center;font-size:.75rem;color:var(--muted);padding:0 20px 32px;letter-spacing:.1em}}
</style>
</head>
<body>
<div class="top"><a href="/" class="brand" aria-label="{e(short)} トップへ">{brand_img}<span class="bn">{e(short)}</span></a></div>
<main class="wrap">
  <div class="mark" aria-hidden="true">404</div>
  <h1>お探しのページが<wbr>見つかりませんでした</h1>
  <p>住所が<wbr>変わったか、<wbr>入力が<wbr>まちがっている<wbr>かもしれません。</p>
  <div class="btns">{''.join(btns)}</div>
  {tel_html}
</main>
<footer>{e(name)}</footer>
</body>
</html>
'''

def write_cloudflare_files(outdir):
    """お店のサイトのフォルダに、Cloudflare の設定（wrangler.jsonc）と公開しないファイルの一覧（.assetsignore）を入れる（2026/10/10 決定）。
    wrangler.jsonc には "previews": {} を入れる（確認用の preview ブランチのページを作るため。tools/preview_push.sh が使う）。
    もうあるときは上書きしない。liftoff-hp の中（samples/ など、別のリポジトリの中）に作るときは入れない"""
    outdir = os.path.abspath(outdir)
    parent = os.path.dirname(outdir)
    while parent and parent != os.path.dirname(parent):
        if os.path.isdir(os.path.join(parent, '.git')): return  # 別のリポジトリの中（見本帳など）
        parent = os.path.dirname(parent)
    name = os.path.basename(outdir.rstrip('/'))
    wr = os.path.join(outdir, 'wrangler.jsonc')
    if not os.path.exists(wr):
        open(wr, 'w', encoding='utf-8').write(f'''// Cloudflare（クラウドフレア）でこのサイトを公開するための設定ファイル
// サイトのファイル（index.html・images など）をそのまま置くだけの設定
{{
  "name": "{name}",
  "compatibility_date": "2026-10-01",
  "assets": {{
    "directory": "./",
    // 無い住所のときは 404.html を「404」の印のまま返す（決定事項 08）
    "not_found_handling": "404-page"
  }},
  // ブランチごとの確認用ページ（プレビュー）を作るための設定。本番には関係しない
  "previews": {{}}
}}
''')
        # 公開後の案内。住所の後ろは .okiba で決まる（ココナラのお店は omise-site 側。なければ liftoff-358。2026/11/11）
        dom, err = read_okiba(outdir)
        if dom: print('Cloudflare の設定を置きました：', wr, f'（公開URL https://{name}.{dom}/ ・確認用 https://preview-{name}.{dom}/）')
        else:
            print('Cloudflare の設定を置きました：', wr)
            print(f'❌ 公開URLの案内を出せません：{err}。.okiba を直してから preview_push.sh・push_small.sh を使う（代わりに liftoff-358 の住所は出しません）')
    ai = os.path.join(outdir, '.assetsignore')
    if not os.path.exists(ai):
        open(ai, 'w', encoding='utf-8').write('# 公開しないファイル（設定ファイルや説明書き）\n.git\n.gitignore\n.assetsignore\nwrangler.jsonc\nREADME.md\n.wrangler\n.DS_Store\nsite.json\nindex.old.html\n')
        print('公開しないファイルの一覧を置きました：', ai)

if __name__ == '__main__':
    main()
