#!/usr/bin/env python3
"""フォームの答え → site.json の下書き（Lift-Off）  2026/10/31 作成（設計書 04「入力フォームと設定の対応表」のとおり）

Google フォーム「Lift-Off ホームページ作りのための入力フォーム」の答え（スプレッドシートを CSV で書き出したもの）から、
make_site.py の設定（site.json）の下書きと、打ち合わせで聞く「確かめたい所.md」を作り、最後に make_site.py を動かして試作まで作る。
文は作らない（「文を作る」項目は答えをそのまま入れて、頭に「(案)」を付ける。文を作るのはチャットの Claude、確かめるのは担当者）。
外部のライブラリは使わない（Python 3 だけ）。

使い方:
  python3 tools/form_to_site.py <答え.csv> <作るフォルダ> [--row 行番号]
    ・答え.csv … 1行目が質問（質問の頭に 01〜30 の番号。14b もある）。Google スプレッドシートの「ダウンロード → CSV」
    ・行番号   … スプレッドシートで見える行の番号（1 行目は質問なので、最初の答えは 2）。省くと最後の行
  できるもの: <作るフォルダ>/site.json（下書き）・確かめたい所.md・index.html・404.html ほか（make_site.py が作る）

決まり:
  ・空の答え・「わからない・あとで」は、その項目を出さない（確かめたい所.md の一覧に出す）
  ・11（Lift-Off との連絡先）は site.json にも確かめたい所.md にも入れない
  ・パスワードらしい文字（「パスワード」「pass」など）がある答えは使わず、確かめたい所.md に「パスワードが書かれていたので使っていません」とだけ書く
  ・雰囲気 → theme_base：やわらか=salon・和=wa・さわやか=fresh・シンプル=simple・上品=jouhin・元気=genki
  ・好きな色は、primary・primary_deep・pale の3色をひと組で上書きする（1色だけ変えるとボタンや印が背景に溶けるため）。
    雰囲気の dark・白い文字と見分けにくい色なら上書きせず、確かめたい所.md に書く
"""
import sys, os, re, csv, json, time, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = 'わからない・あとで'
THEME_OF = {'やわらか': 'salon', '和': 'wa', 'さわやか': 'fresh', 'シンプル': 'simple', '上品': 'jouhin', '元気': 'genki'}
FONT_OF = {'salon': 'mincho', 'wa': 'mincho', 'jouhin': 'mincho', 'fresh': 'gothic', 'simple': 'gothic', 'genki': 'gothic'}
MARK_OF = {'salon': 'heart', 'wa': 'leaf', 'fresh': 'leaf', 'simple': 'dot', 'jouhin': 'heart', 'genki': 'dot'}
SCHEMA_OF = {'美容室・理容室': 'HairSalon', 'エステ・サロン': 'BeautySalon', '整体・整骨院': 'HealthAndBeautyBusiness', '飲食店・カフェ': 'Restaurant',
             '教室・習いごと': 'LocalBusiness', '工務店・リフォーム': 'HomeAndConstructionBusiness', '造園・植木': 'HomeAndConstructionBusiness', '小売店': 'Store'}
COLORS = {  # 好きな色 → (primary, primary_deep, pale)。3色ひと組
    'ピンク': ('#e2738f', '#c85473', '#fbeaef'), '赤': ('#b8322f', '#962623', '#f8e6e5'), 'オレンジ': ('#c9571c', '#a3430f', '#fff0e4'),
    '黄色': ('#b8860b', '#946b06', '#fbf3dc'), '緑': ('#2f7f4f', '#245f3c', '#e6f2ea'), '水色': ('#2c7fa6', '#1f6485', '#e4f1f7'),
    '青・紺': ('#2f4f8f', '#223c70', '#e6ebf5'), '紫': ('#6f4a8e', '#563871', '#efe8f4'), '茶色': ('#7a5230', '#5e3e22', '#f3ebe3'),
}
DAY_JP = {'月': 'Mo', '火': 'Tu', '水': 'We', '木': 'Th', '金': 'Fr', '土': 'Sa', '日': 'Su'}
DAY_KEY = {'月': 'mon', '火': 'tue', '水': 'wed', '木': 'thu', '金': 'fri', '土': 'sat', '日': 'sun'}
DAYS = '月火水木金土日'
PASSWORD_RX = re.compile(r'パスワード|ﾊﾟｽﾜｰﾄﾞ|\bpass(word|wd)?\b|パスワ|暗証', re.I)
FEATURES = {'お問い合わせフォーム': 'form', 'ネットで売る': 'shop', 'お知らせ': 'news', 'お客様の声': 'voices', '営業時間の表示': 'hours',
            '対応エリア': 'areas', '動画': 'video', '写真の拡大': 'lightbox'}


def lum(h):
    h = h.lstrip('#'); r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = lum(a), lum(b); return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


# ---------- CSV を読む ----------
def read_answers(path, row=None):
    """CSV を読み、{番号: 答え} と {番号: 質問} を返す。番号は質問の頭の 01〜30（14b も）。row はスプレッドシートの行番号（2 が最初の答え）"""
    with open(path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    if len(rows) < 2: sys.exit('❌ 答えの行がありません（1行目は質問、2行目から答え）')
    head = rows[0]
    data = [r for r in rows[1:] if any(c.strip() for c in r)]
    if row is None: rec = data[-1]; row_no = len(rows)
    else:
        if row < 2 or row > len(rows): sys.exit(f'❌ 行番号 {row} はありません（2〜{len(rows)}）')
        rec = rows[row - 1]; row_no = row
    rec = list(rec) + [''] * (len(head) - len(rec))
    qs, ans = {}, {}
    for h, a in zip(head, rec):
        m = re.match(r'^\s*(\d{2}[a-z]?)\s', h)
        if not m: continue
        qs[m.group(1)] = h.strip(); ans[m.group(1)] = a.strip()
    if not qs: sys.exit('❌ 質問の頭に番号（01〜30）が見つかりません。フォームの質問の番号は消さないでください')
    return qs, ans, row_no


# ---------- 小さな変換 ----------
def split_city(address):
    """住所 → (都道府県＋市区町村, 市区町村)。見つからなければ ('', '')"""
    s = re.sub(r'^〒?\s*\d{3}-?\d{4}\s*', '', address)
    m = re.match(r'((?:東京都|北海道|京都府|大阪府|.{2,3}県)?)(.+?[市区町村])', s)
    if not m: return '', ''
    return m.group(1) + m.group(2), m.group(2)


def norm_time(t):
    """'10時' '10:00' '9:30' → '10:00' '09:30'（検索用・営業時間の部品用）。合わなければ ''"""
    m = re.match(r'^(\d{1,2})(?:[:：時](\d{0,2}))?分?$', t.strip())
    if not m: return ''
    h, mi = int(m.group(1)), int(m.group(2) or 0)
    if h > 24 or mi > 59: return ''
    return '%02d:%02d' % (h, mi)


def parse_hours(text):
    """営業時間の段落 → (opening_hours のリスト, 曜日ごとの schedule, 読めなかった行)。
    読める形：「月〜金 10:00〜18:00」「土 10:00-15:00」「月・水・金 9時〜17時」「毎日 10:00〜20:00」「日 休み」。1行に時間帯2つは「,」でつなぐ"""
    opening, sched, bad = [], {}, []
    for raw in re.split(r'[\n/／]', text):
        line = raw.strip()
        if not line: continue
        s = line.replace('～', '〜').replace('−', '-').replace('ー', '-').replace('　', ' ')
        days = []
        head = re.match(r'^(毎日|年中無休|([月火水木金土日祝][〜\-・、,～]?)+)', s)
        if not head: bad.append(line); continue
        d = head.group(0)
        rest = s[len(d):].strip(' :：')
        if d in ('毎日', '年中無休'): days = list(DAYS)
        else:
            d = d.replace('祝', '')
            for part in re.split(r'[・、,]', d):
                part = part.strip('〜-')
                if not part: continue
                m = re.match(r'^([月火水木金土日])[〜\-]([月火水木金土日])$', part)
                if m:
                    a, b = DAYS.index(m.group(1)), DAYS.index(m.group(2))
                    days += list(DAYS[a:b + 1]) if a <= b else list(DAYS[a:] + DAYS[:b + 1])
                elif len(part) == 1 and part in DAYS: days.append(part)
            days = [x for i, x in enumerate(days) if x not in days[:i]]
        if not days: bad.append(line); continue
        if re.search(r'休|定休|閉', rest) or not rest:
            for x in days: sched[DAY_KEY[x]] = ''
            continue
        spans = []
        for seg in re.split(r'[,，]', rest):
            m = re.match(r'^\s*(\S+?)\s*[〜\-]\s*(\S+?)\s*$', seg)
            a, b = (norm_time(m.group(1)), norm_time(m.group(2))) if m else ('', '')
            if not (a and b): spans = []; break
            spans.append(a + '-' + b)
        if not spans: bad.append(line); continue
        for x in days: sched[DAY_KEY[x]] = ','.join(spans)
        # 検索用（schema.org の openingHours）：連続した曜日は Mo-Fr にまとめる
        idx = sorted(DAYS.index(x) for x in days)
        runs, start = [], idx[0]
        for i, v in enumerate(idx):
            if i == len(idx) - 1 or idx[i + 1] != v + 1:
                runs.append((start, v)); start = idx[i + 1] if i + 1 < len(idx) else None
        for a, b in runs:
            dd = DAY_JP[DAYS[a]] if a == b else DAY_JP[DAYS[a]] + '-' + DAY_JP[DAYS[b]]
            for sp in spans: opening.append(dd + ' ' + sp)
    return opening, sched, bad


def parse_holiday_days(text):
    """定休日の文に出てくる曜日（「日曜・祝日」→ ['日']）"""
    return [x for x in DAYS if re.search(x + r'(曜|・|、|$|\s|と)', text)]


def parse_menu_line(line):
    """1行 → (名前, 料金, 時間, ひとこと, 分けられたか)。区切りは / ／ ｜ |"""
    parts = [p.strip() for p in re.split(r'[/／｜|]', line)]
    if len(parts) < 2 or not parts[0]: return line.strip(), '', '', '', False
    parts += [''] * (4 - len(parts))
    return parts[0], parts[1], parts[2], parts[3], True


def parse_faq_line(line):
    m = re.split(r'\s*(?:→|->|⇒|＝|=>)\s*', line, maxsplit=1)
    if len(m) == 2 and m[0].strip() and m[1].strip(): return m[0].strip(), m[1].strip()
    m = re.match(r'^(.+?[？?])\s*(.+)$', line)
    if m: return m.group(1).strip(), m.group(2).strip()
    return line.strip(), ''


def sns_name(url):
    for k, n in (('instagram', 'Instagram'), ('facebook', 'Facebook'), ('twitter', 'X'), ('x.com', 'X'), ('tiktok', 'TikTok'),
                 ('youtube', 'YouTube'), ('youtu.be', 'YouTube'), ('line.me', 'LINE'), ('lin.ee', 'LINE'), ('threads', 'Threads')):
        if k in url.lower(): return n
    return 'SNS'


# ---------- 本体 ----------
def convert(qs, ans):
    """答え → (site.json の辞書, 確かめたい所の辞書)"""
    note = {'blank': [], 'conflict': [], 'menu': [], 'skip': [], 'photo': [], 'text': [], 'other': [], 'password': []}

    def A(k):
        """答え（空・SKIP は ''。パスワードらしければ使わない）"""
        v = (ans.get(k) or '').strip()
        if not v: return ''
        if v == SKIP or v.startswith(SKIP): note['skip'].append(k); return ''
        if PASSWORD_RX.search(v):
            note['password'].append(k); return ''
        return v

    def label(k): return qs.get(k, k)
    def q_blank(k):
        if not A(k) and k not in note['password']: note['blank'].append(k)

    c = {}
    # 1. お店の基本
    for k in ('01', '02', '03', '06', '17', '23', '30'): q_blank(k)
    name = A('01') or '（お店の名前）'
    c['slug'] = 'site'; c['name'] = name; c['short_name'] = name
    if len(name) > 10: note['other'].append(f'お店の名前が長い（{len(name)}文字）→ 短い呼び名（short_name）を聞く')
    addr = A('03'); area, city = split_city(addr) if addr else ('', '')
    if addr:
        c['address'] = addr
        if area: c['area'] = area
        else: note['other'].append('住所から市町が読み取れなかった → area（市町）を確かめる')
        c['map_query'] = name + ' ' + addr
    kind = A('02')
    if kind:
        c['kind'] = kind + ('｜' + city if city else '')
        c['schema_type'] = SCHEMA_OF.get(kind, 'LocalBusiness')
        if kind not in SCHEMA_OF: note['other'].append(f'業種が「その他」（{kind}）→ 見本の業種に近いものを選ぶ')
    tel = A('04')
    if tel:
        if re.match(r'^[\d\-‐－() 　]{9,15}$', tel): c['tel'] = tel.replace('－', '-').replace('‐', '-').replace(' ', '').replace('　', '')
        else: note['other'].append(f'電話番号の形が読めない（{tel}）→ 確かめる')
    ln = A('05')
    if ln:
        if ln.startswith('@'): c['line_id'] = ln; c['line_url'] = 'https://line.me/R/ti/p/' + ln
        elif ln.startswith('http'): c['line_url'] = ln
        else: note['other'].append(f'公式LINE の書き方が ID（@〜）でも URL でもない（{ln}）→ 確かめる')
    hours = A('06'); opening, sched, bad_hours = [], {}, []
    if hours:
        c['hours'] = ' / '.join(l.strip() for l in hours.splitlines() if l.strip())
        opening, sched, bad_hours = parse_hours(hours)
        if opening: c['opening_hours'] = opening
        if bad_hours: note['other'].append('営業時間で読めなかった行（検索用の形にできない）：' + '／'.join(bad_hours))
    hol = A('07')
    if hol:
        c['holiday'] = hol
        for d in parse_holiday_days(hol): sched.setdefault(DAY_KEY[d], '')
    if A('08'): c['parking'] = A('08')
    pay = [p.strip() for p in A('09').split(',') if p.strip() and p.strip() != SKIP]
    if pay: c['payment'] = '・'.join(pay)
    sns = []
    for l in A('10').splitlines():
        l = l.strip()
        if not l: continue
        if l.startswith('http'): sns.append({'name': sns_name(l), 'url': l})
        else: note['other'].append(f'SNS の行が URL ではない（{l}）→ URL を聞く')
    if sns: c['sns'] = sns
    # 11 は使わない（Lift-Off との連絡先。site.json にも確かめたい所にも書かない）

    # 2. メニューと料金
    q_blank('12')
    menus, rows = [], []
    for i, l in enumerate([l for l in A('12').splitlines() if l.strip()], 1):
        nm, price, tm, text, ok = parse_menu_line(l)
        if not ok: note['menu'].append(l.strip())
        mid = 'm%d' % i
        m = {'id': mid, 'name': nm, 'image': f'images/menu-{mid}.svg', 'w': 1000, 'h': 750, 'alt': nm + 'の写真'}
        if text: m['text'] = text
        if price: m['price'] = price
        if tm: m['price_note'] = tm
        menus.append(m); rows.append({'label': nm, 'text': (tm + ('　' if tm and text else '') + text).strip(), 'price': price or 'お問い合わせください'})
    if menus:
        c['menus'] = menus[:6]
        if len(menus) > 6: c['price_table'] = {'title': '料金表', 'rows': rows}; note['other'].append(f'メニューが {len(menus)} 行 → 写真つきは先頭の 6 つ、全部は料金表に入れた。並びを確かめる')
    if A('13'): c['menu_note'] = A('13')

    # 3. 写真・ロゴ
    ph = A('14'); link = A('14b')
    if ph.startswith('LINE'): note['photo'].append('写真：LINE で受け取る → photos.py で縮小・位置情報を消してから images/ に入れる（menus の image を差しかえる）')
    elif ph.startswith('Google') or 'リンク' in ph:
        note['photo'].append('写真：リンクから受け取る → photos.py で縮小・位置情報を消してから images/ に入れる' + (f'　リンク：{link}' if link else '　※リンク欄（14b）が空'))
    elif ph.startswith('まだない'): note['photo'].append('写真：まだない → 撮り方を伝える（横向きで多めに）。それまでは仮画像')
    elif '14' in note['skip']: note['photo'].append('写真：「わからない・あとで」→ 打ち合わせで送り方を決める')
    else: note['photo'].append('写真：答えなし → 打ち合わせで送り方を決める')
    lg = A('15'); tb = THEME_OF.get(A('17'), 'salon')
    if lg.startswith('ある'):
        note['photo'].append('ロゴ：ある（' + lg + '）→ 受け取ったら images/logo.png に入れ、site.json の logo に書く')
    else:
        c['mark'] = MARK_OF[tb]
        if '15' in note['skip']: note['photo'].append('ロゴ：「わからない・あとで」→ 仮に印（mark）を雰囲気から選んだ（' + MARK_OF[tb] + '）。あるかどうかを打ち合わせで聞く')
        elif lg == 'ない': note['photo'].append('ロゴ：ない → 印（mark）を雰囲気から選んだ（' + MARK_OF[tb] + '）。ロゴを作るなら別料金（料金表）')
        else: note['photo'].append('ロゴ：答えなし → 仮に印（mark）を雰囲気から選んだ（' + MARK_OF[tb] + '）。あるかどうかを打ち合わせで聞く')
    if A('16') and A('16') != 'はい': note['photo'].append('写真の掲載：「相談したい」→ 了承をもらうまで写真は使わない')
    elif not A('16'): note['photo'].append('写真の掲載：答えなし → 了承を確かめてから使う')

    # 4. 好み・伝えたいこと
    sys.path.insert(0, HERE)
    try:
        from make_site import THEMES
        T = THEMES[tb]
    except Exception:
        T = {'dark': '#23221f', 'pale': '#ffffff', 'hero_style': 'dark'}
    c['theme_base'] = tb; c['font'] = FONT_OF[tb]
    c['hero_style'] = T.get('hero_style', 'dark')  # 上の部分の明るさは雰囲気から（やわらか・さわやか・シンプル・元気＝light、和・上品＝dark）
    col = A('18')
    if col and col != '白・黒':
        if col in COLORS:
            pr, pd, pl = COLORS[col]
            hero_bg = T['pale'] if c['hero_style'] == 'light' else T['dark']
            if contrast('#ffffff', pr) >= 3.0 and contrast(pr, hero_bg) >= 1.5 and contrast(pr, T['dark']) >= 1.5:
                c['theme'] = {'primary': pr, 'primary_deep': pd, 'pale': pl}
            else:
                note['other'].append(f'好きな色「{col}」は雰囲気「{A("17")}」の色と見分けにくい（上書きしていない）→ 打ち合わせで決める')
        else:
            note['other'].append(f'好きな色「{col}」（その他）→ 色（theme の primary）を打ち合わせで決める')
    catch = A('19')
    if catch: c['catch'] = catch
    else: c['catch'] = '(案)' + name; note['text'].append('19 決め文句：答えなし → 文を作る（今は店名を仮に入れた）')
    who = A('20')
    if who:
        c['lead'] = '(案)' + who; c['description'] = '(案)' + who
        note['text'].append('20 来てほしいお客さん → lead・description の文を作る（答えをそのまま (案) で入れた）')
    else: note['text'].append('20 来てほしいお客さん：答えなし → lead・description の文を作る')
    if city and kind: c['title_place'] = '(案)' + city + 'の' + kind; note['text'].append('title_place（検索の題名）→ 文を整える')
    diff = [l.strip() for l in re.split(r'[\n／/]', A('21')) if l.strip()]  # 1行に1つ。／や/で区切ってあっても分ける
    parts = {}
    if diff:
        parts['strengths'] = {'title': '選ばれる理由', 'items': [{'title': '(案)' + l} for l in diff[:4]]}
        note['text'].append('21 ほかのお店との違い → 選ばれる理由（strengths）の文を作る（言い切らない）')
    refs = [l.strip() for l in A('22').splitlines() if l.strip()]
    if refs: note['other'].append('参考にしたいホームページ：' + '／'.join(refs) + '（雰囲気・並びの参考に。中身はまねない）')

    # 5. 欲しい機能
    main = A('23'); rsv = A('24')
    if main == '予約がメイン': c['reserve_title'] = 'ご予約'
    elif main == '問い合わせがメイン': c['reserve_title'] = 'お問い合わせ'
    elif main == '両方': c['reserve_title'] = 'ご予約・お問い合わせ'
    elif main: note['other'].append('23 予約と問い合わせ：「まだわからない」→ 打ち合わせで決める')
    if main == '予約がメイン' and rsv == '使わない': note['conflict'].append('予約がメインなのに、予約の受け方が「使わない」')
    if main == '予約がメイン' and not (c.get('tel') or c.get('line_url')) and not rsv.startswith('今使'): note['conflict'].append('予約がメインなのに、電話も LINE もない（予約の入口がない）')
    if main == '問い合わせがメイン' and 'お問い合わせフォーム' not in A('26') and not (c.get('tel') or c.get('line_url')): note['conflict'].append('問い合わせがメインなのに、電話・LINE・フォームのどれもない')
    if rsv.startswith('ネットで受けたい(決まった') or rsv.startswith('ネットで受けたい（決まった'): note['other'].append('24 ネット予約（決まった時間を選ぶだけ）→ 予約カレンダー（ご契約のお店 初期 22,000円〜＋月 1,100円）の候補。見積もりに入れるか決める')
    elif rsv.startswith('ネットで受けたい'): note['conflict'].append('ネット予約で「複雑」（メニューの組み合わせ・担当者を選ぶ）を選んでいる → 作る前に金額を伝える（料金表の決まり）')
    elif rsv.startswith('今使っている'): note['other'].append('24 今使っている予約サービスがある → その URL を聞いて reserve_url に入れる')
    inc = A('25')
    if inc == 'はい' and 'strengths' not in parts: note['other'].append('25 お客さんを増やすことを一番に → 選ばれる理由（21）が空なので、打ち合わせで 2〜4 個聞く')
    feats = [f.strip() for f in A('26').split(',') if f.strip()]
    for f in feats:
        key = next((v for k, v in FEATURES.items() if f.startswith(k)), None)
        if key == 'form': parts['form'] = {'endpoint': ''}; note['other'].append('26 お問い合わせフォーム → Formspree の送り先（endpoint）を作って入れる。「フォームの管理」月 550円 を見積もりに')
        elif key == 'shop': note['other'].append('26 ネットで売る → 商品ページ（ご契約のお店 22,000円〜・5点まで）。商品の名前・金額・写真・特定商取引法の表示を聞いてから parts.shop に書く')
        elif key == 'news': note['other'].append('26 お知らせ → 最初のお知らせの文（日付つき）を 1〜3 件聞いてから parts.news に書く')
        elif key == 'voices': note['other'].append('26 お客様の声 → 実在のお客様の声と掲載の了承（consent）がないと入れられない。了承の取り方を話す')
        elif key == 'hours':
            if sched and all(k in sched for k in DAY_KEY.values()): parts['hours'] = {'title': '営業時間', 'schedule': {k: sched[k] for k in DAY_KEY.values()}}
            else: note['other'].append('26 営業時間の表示 → 曜日ごとの時間が全部そろっていない（06 と 07 から読めた分：' + ('・'.join(k for k in DAY_KEY.values() if k in sched) or 'なし') + '）→ 打ち合わせでそろえる')
        elif key == 'areas':
            if city: parts['areas'] = {'main': [city]}; note['other'].append('26 対応エリア → 近くの市町（also）を聞いて足す')
            else: note['other'].append('26 対応エリア → 市町が読めなかったので、打ち合わせで聞く')
        elif key == 'video': note['other'].append('26 動画 → お店の動画（YouTube の ID か mp4）を受け取ってから parts.video に書く')
        elif key == 'lightbox': parts['lightbox'] = True
        else: note['other'].append(f'26 欲しい機能に知らないものがある（{f}）')
    if parts: c['parts'] = parts

    # 6. ほか
    faq = []
    for l in [l for l in A('27').splitlines() if l.strip()]:
        q, a = parse_faq_line(l)
        if a: faq.append({'q': q, 'a': a})
        else: note['menu'].append('（よくある質問）答えの部分が読めない：' + l.strip())
    if faq: c['faq'] = faq
    else: note['text'].append('27 よくある質問：答えなし → 業種の見本から案を作る')
    flow = []
    for l in [l for l in A('28').splitlines() if l.strip()]:
        t, _, x = l.partition('/')
        flow.append({'title': t.strip(), 'text': x.strip()} if x.strip() else {'title': t.strip()})
    if flow: c['flow'] = flow
    if A('29'): note['other'].append('29 ほかに伝えたいこと：' + A('29').replace('\n', '／'))
    if A('30') != '同意する': note['other'].append('30 同意：「同意する」になっていない → 作る前に同意をもらう')
    return c, note


def write_notes(path, qs, note, row_no, src):
    L = ['# 確かめたい所（打ち合わせで聞く）', '', f'- 元：{os.path.basename(src)} の {row_no} 行目（{time.strftime("%Y/%m/%d %H:%M")} に作成）', '- site.json の「(案)」が付いた所は、チャットの Claude が文を作り、担当者が確かめる', '']
    def sec(title, items, empty):
        L.append('## ' + title)
        L.extend(['- ' + x for x in items] if items else ['- ' + empty]); L.append('')
    sec('① ★の質問の空欄', [qs.get(k, k) for k in note['blank']], 'なし')
    sec('② 食い違い（作る前に決める・金額を伝える）', note['conflict'], 'なし')
    sec('③ 分けられなかった行（メニューは「名前/料金/時間/ひとこと」）', note['menu'], 'なし')
    sec('④ 「わからない・あとで」の質問', [qs.get(k, k) for k in note['skip']], 'なし')
    sec('⑤ 写真・ロゴの送り方', note['photo'], 'なし')
    sec('⑥ 文を作る項目（(案) を付けて入れた）', note['text'], 'なし')
    sec('⑦ そのほか確かめること', note['other'], 'なし')
    if note['password']: L += ['## ⑧ 注意', '- パスワードが書かれていたので使っていません（質問 ' + '・'.join(note['password']) + '）', '']
    open(path, 'w', encoding='utf-8').write('\n'.join(L))


def main():
    args = [a for a in sys.argv[1:]]
    row = None
    if '--row' in args:
        i = args.index('--row'); row = int(args[i + 1]); del args[i:i + 2]
    if len(args) < 2: sys.exit(__doc__)
    src, outdir = args[0], os.path.expanduser(args[1])
    t0 = time.time()
    qs, ans, row_no = read_answers(src, row)
    c, note = convert(qs, ans)
    os.makedirs(outdir, exist_ok=True)
    sj = os.path.join(outdir, 'site.json')
    json.dump(c, open(sj, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    md = os.path.join(outdir, '確かめたい所.md')
    write_notes(md, qs, note, row_no, src)
    print(f'読んだ答え：{os.path.basename(src)} の {row_no} 行目（{c["name"]}）')
    print('作りました：', sj)
    print('作りました：', md, f'（空欄 {len(note["blank"])}・食い違い {len(note["conflict"])}・分けられない行 {len(note["menu"])}・あとで {len(note["skip"])}）')
    print('→ make_site.py で試作を作ります'); sys.stdout.flush()
    rc = subprocess.call([sys.executable, os.path.join(HERE, 'make_site.py'), sj, outdir])
    took = time.time() - t0
    print(f'\nかかった時間：{took:.1f} 秒（CSV を読んでから、試作と確かめたい所.md ができるまで）')
    sys.exit(rc)


if __name__ == '__main__':
    main()
