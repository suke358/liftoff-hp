#!/usr/bin/env python3
"""shian2（切りかえ式）の飛行機を、本当にタブを押して確かめる  2026/10/10 作成

headless Chrome を DevTools（CDP）でつなぎ、下のタブをマウスで本当に押して、requestAnimationFrame を本物で走らせたまま
飛行機の位置（window.jetState()）を読む。jetSim・jetPose のような「JS で置く」確認は使わない。

公開前チェック（マニュアル 17）での使い方：shian2/ を直して push する前に
  1. python3 tools/mihon/make_shian2.py                 … shian/ から shian2/ を作り直す
  2. python3 tools/mihon/tap_test_shian2.py             … このファイル。入り方（4秒待つ）→ 料金→ホーム→相談→できること→相談 と押して、
                                                           2秒後に「その画面に切りかわった・タブの位置で止まった・背中が上（右向き a=0／左向き a=180）・残り 0」を確かめる
  3. python3 tools/mihon/tap_test_shian2.py early       … 入り方の途中（1秒）で料金を押しても、入り方を終えてから料金の位置に着くか
  3''. python3 tools/mihon/tap_test_shian2.py fit       … 幅 320・390・1280 で、開いた直後と ホーム→料金→ホーム のあとに「帯の下と見出しの間が 24px（パソコンは 24px 以上）」か
  3'. python3 tools/mihon/tap_test_shian2.py irai       … 修正依頼：?shop=〇〇 の文字がそのまま店名に入る・ホームの帯を押すと #irai（飛行機はホームの位置）・「メールを作る」で飛行機が飛んでメールの文ができるか
  4. 最後の行が「全部: OK」「結果: OK」なら合格。画像は ~/src/_確認画像/自社_<日付>_shian2_タブを押す/ に残る（git の外）
  引数：python3 tools/mihon/tap_test_shian2.py [normal|early] [ページのURL] [画像を置くフォルダ]
"""
import sys, os, json, time, socket, base64, subprocess, urllib.request, struct

CH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
import datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
args = [a for a in sys.argv[1:]]
mode = args[0] if args and args[0] in ('normal', 'early', 'irai', 'fit') else 'normal'
rest = [a for a in args if a not in ('normal', 'early', 'irai', 'fit')]
URL = rest[0] if rest else 'file://' + os.path.join(ROOT, 'shian2', 'index.html')
OUT = rest[1] if len(rest) > 1 else os.path.expanduser('~/src/_確認画像/自社_%s_shian2_タブを押す' % datetime.date.today().strftime('%Y%m%d'))
os.makedirs(OUT, exist_ok=True)
PORT = 9333
prof = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chrome-prof')
chrome = subprocess.Popen([CH, '--headless=new', '--disable-gpu', '--allow-file-access-from-files', '--hide-scrollbars',
                           '--remote-debugging-port=%d' % PORT, '--user-data-dir=' + prof, '--window-size=390,844', 'about:blank'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try:
            tabs = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json' % PORT)); break
        except Exception: time.sleep(0.2)
    ws_url = [t for t in tabs if t['type'] == 'page'][0]['webSocketDebuggerUrl']

    # ---- 最小限の WebSocket クライアント
    host, rest = ws_url[5:].split('/', 1); h, p = host.split(':')
    sock = socket.create_connection((h, int(p)))
    key = base64.b64encode(os.urandom(16)).decode()
    sock.sendall(('GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n' % (rest, host, key)).encode())
    buf = b''
    while b'\r\n\r\n' not in buf: buf += sock.recv(4096)
    buf = buf.split(b'\r\n\r\n', 1)[1]
    def send(obj):
        data = json.dumps(obj).encode(); mask = os.urandom(4)
        head = bytes([0x81]); n = len(data)
        if n < 126: head += bytes([0x80 | n])
        elif n < 65536: head += bytes([0x80 | 126]) + struct.pack('>H', n)
        else: head += bytes([0x80 | 127]) + struct.pack('>Q', n)
        sock.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
    def recv():
        global buf
        while True:
            while len(buf) < 2: buf += sock.recv(65536)
            n = buf[1] & 0x7f; off = 2
            if n == 126:
                while len(buf) < 4: buf += sock.recv(65536)
                n = struct.unpack('>H', buf[2:4])[0]; off = 4
            elif n == 127:
                while len(buf) < 10: buf += sock.recv(65536)
                n = struct.unpack('>Q', buf[2:10])[0]; off = 10
            while len(buf) < off + n: buf += sock.recv(65536)
            msg = buf[off:off + n]; buf = buf[off + n:]
            return json.loads(msg)
    seq = [0]
    def call(method, **params):
        seq[0] += 1; send({'id': seq[0], 'method': method, 'params': params})
        while True:
            m = recv()
            if m.get('id') == seq[0]: return m.get('result', m)
    def js(expr, wait=False):
        r = call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=wait)
        return r.get('result', {}).get('value')

    call('Page.enable'); call('Runtime.enable')
    call('Emulation.setDeviceMetricsOverride', width=390, height=844, deviceScaleFactor=1, mobile=True)
    call('Page.navigate', url=URL)
    time.sleep(1.0)
    print('hidden=', js('document.hidden'), ' reduced=', js("window.matchMedia('(prefers-reduced-motion: reduce)').matches"))
    def state(label):
        s = js('JSON.stringify(window.jetState())'); d = json.loads(s)
        print('%-28s x=%4d y=%3d a=%4d dir=%2d left=%d entry=%s' % (label, d['x'], d['y'], d['a'], d['dir'], d['left'], d['entry']))
        return d
    def shot(name, top=0, h=130):
        r = call('Page.captureScreenshot', format='png', clip={'x': 0, 'y': top, 'width': 390, 'height': h, 'scale': 1})
        open(os.path.join(OUT, name + '.png'), 'wb').write(base64.b64decode(r['data']))
    def tap(scr):
        # 下のタブを本当に押す（座標を取って、マウスを押して離す）
        rect = json.loads(js("JSON.stringify(document.querySelector('#tabbar a[data-scr=%s]').getBoundingClientRect())" % scr))
        x, y = rect['x'] + rect['width'] / 2, rect['y'] + rect['height'] / 2
        call('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button='left', clickCount=1)
        call('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button='left', clickCount=1)
    def scr():
        return js("document.querySelector('.scr.on').id")

    NAMES = {'home': 'ホーム', 'ryokin': '料金', 'soudan': '相談', 'dekiru': 'できること', 'nagare': '流れ'}
    if mode == 'fit':
        allok = True
        for w in (320, 390, 1280):
            hh = 844 if w < 800 else 900
            call('Emulation.setDeviceMetricsOverride', width=w, height=hh, deviceScaleFactor=1, mobile=w < 800)
            call('Page.navigate', url=URL); time.sleep(0.6)
            def gap(label):
                g = js("(function(){var b=document.getElementById('irai-band').getBoundingClientRect(),h=document.querySelector('#home .hero h1').getBoundingClientRect();return JSON.stringify({band:Math.round(b.bottom),h1:Math.round(h.top),scroll:window.pageYOffset,scr:document.querySelector('.scr.on').id});})()")
                g = json.loads(g); gap = g['h1'] - g['band']
                ok = g['scr'] == 'home' and g['scroll'] == 0 and (24 <= gap <= 32 if w < 800 else gap >= 24)  # スマホは 24px（多すぎてもだめ）、パソコンは 24px 以上
                print('   幅%d %s: 帯の下=%d 見出しの上=%d 間=%d → %s' % (w, label, g['band'], g['h1'], gap, 'OK' if ok else 'NG'))
                return ok
            allok = gap('開いた直後') and allok
            if w < 800: shot('合わせ_幅%d_開いた直後' % w, 0, 300)
            time.sleep(3.6)
            tap('ryokin'); time.sleep(0.5); tap('home'); time.sleep(0.5)
            allok = gap('料金→ホームのあと') and allok
        print('全部:', 'OK' if allok else 'NG')
    elif mode == 'irai':
        # 修正依頼：?shop=colore 付きで開き直す
        call('Page.navigate', url=URL + ('&' if '?' in URL else '?') + 'shop=colore'); time.sleep(4.2)  # ?shop= の文字がそのまま店名の欄に入る
        d = state('開いて4秒（ホーム）'); allok = d['left'] == 0 and not d['entry']
        # ホームの帯を本当に押す
        rect = json.loads(js("JSON.stringify(document.getElementById('irai-band').getBoundingClientRect())"))
        x, y = rect['x'] + rect['width'] / 2, rect['y'] + rect['height'] / 2
        call('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button='left', clickCount=1)
        call('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button='left', clickCount=1)
        time.sleep(2.0)
        sc = scr(); d = state('帯を押して2秒後'); shopv = js("document.getElementById('irai-shop').value")
        ok1 = sc == 'irai' and d['left'] == 0 and abs(d['x'] - 39) < 2 and d['dir'] == -1
        print('   画面=%s 店名=%s → %s' % (sc, shopv, 'OK' if ok1 and shopv == 'colore' else 'NG'))
        shot('修正依頼_1_帯を押した（#irai・飛行機はホームの位置）', 0, 844)
        # 直したい所を1つ押して、ひと言を入れて、「メールを作る」を押す
        js("var c=document.querySelector('#irai-form input[value=\"写真\"]').nextElementSibling; c.scrollIntoView({block:'center'});"); time.sleep(0.3)
        rect = json.loads(js("JSON.stringify(document.querySelector('#irai-form input[value=\"写真\"]').nextElementSibling.getBoundingClientRect())"))
        x, y = rect['x'] + rect['width'] / 2, rect['y'] + rect['height'] / 2
        call('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button='left', clickCount=1)
        call('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button='left', clickCount=1)
        js("document.getElementById('irai-note-in').value='来週の水曜はお休みにします'")
        js("document.getElementById('irai-btn').scrollIntoView({block:'center'})"); time.sleep(0.3)  # 下の固定ボタンに隠れないように
        rect = json.loads(js("JSON.stringify(document.getElementById('irai-btn').getBoundingClientRect())"))
        x, y = rect['x'] + rect['width'] / 2, rect['y'] + rect['height'] / 2
        call('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button='left', clickCount=1)
        call('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button='left', clickCount=1)
        time.sleep(0.5); flying = 'on' in (js("document.getElementById('irai-plane').getAttribute('class')") or '')
        shot('修正依頼_2_メールを作る（飛行機が飛んでいる所）', 0, 844)
        time.sleep(1.2); m = js("document.getElementById('irai-msg').textContent"); href = js('window.iraiLastMailto') or ''
        import urllib.parse; dec = urllib.parse.unquote(href)
        ok2 = flying and 'メールの画面を開きます' in m and dec.startswith('mailto:liftoff.358@gmail.com?subject=ホームページの修正のご依頼&body=お店：colore') and '直したい所：写真' in dec and 'ひと言：来週の水曜はお休みにします' in dec
        print('   飛行機が飛んだ=%s 文=%s' % (flying, m)); print('   メール: %s' % dec.replace('\n', ' / ')[:200])
        shot('修正依頼_3_メールの文ができた', 0, 844)
        # 「メールが開かないときは」：押したときだけ宛先と「コピー」が出て、店名が入る。コピーを押すと「コピーしました」
        call('Browser.grantPermissions', permissions=['clipboardReadWrite', 'clipboardSanitizedWrite'])
        js("document.getElementById('irai-alt').scrollIntoView({block:'center'})"); time.sleep(0.3)
        hidden0 = js("document.getElementById('irai-altbox').hidden")
        rect = json.loads(js("JSON.stringify(document.getElementById('irai-alt').getBoundingClientRect())"))
        x, y = rect['x'] + rect['width'] / 2, rect['y'] + rect['height'] / 2
        call('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button='left', clickCount=1)
        call('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button='left', clickCount=1)
        time.sleep(0.3)
        hidden1 = js("document.getElementById('irai-altbox').hidden"); txt = js("document.getElementById('irai-altbox').textContent")
        rect = json.loads(js("JSON.stringify(document.getElementById('irai-copy').getBoundingClientRect())"))
        x, y = rect['x'] + rect['width'] / 2, rect['y'] + rect['height'] / 2
        call('Input.dispatchMouseEvent', type='mousePressed', x=x, y=y, button='left', clickCount=1)
        call('Input.dispatchMouseEvent', type='mouseReleased', x=x, y=y, button='left', clickCount=1)
        time.sleep(0.5); btn_t = js("document.getElementById('irai-copy').textContent"); clip = js("navigator.clipboard.readText()", True)
        ok3 = hidden0 and (not hidden1) and 'liftoff.358@gmail.com' in txt and 'お店：colore' in txt and btn_t == 'コピーしました'
        print('   メールが開かないときは: 最初は隠れている=%s 押すと出る=%s 店名入り=%s コピーのボタン=%s クリップボード=%s → %s' % (hidden0, not hidden1, 'お店：colore' in txt, btn_t, clip, 'OK' if ok3 else 'NG'))
        shot('修正依頼_4_メールが開かないときは', 0, 844)
        print('全部:', 'OK' if allok and ok1 and shopv == 'colore' and ok2 and ok3 else 'NG')
    elif mode == 'early':
        state('開いて1秒（入り方の途中）'); shot('途中押し_0_開いて1秒', 0, 844)
        tap('ryokin'); print('→ 1秒の時点で 料金 を押した。画面=', scr())
        time.sleep(1.0); state('押して1秒後'); shot('途中押し_1_押して1秒後', 0, 844)
        time.sleep(4.0); d = state('押して5秒後'); shot('途中押し_2_押して5秒後', 0, 130)
        ok = d['left'] == 0 and abs(d['x'] - 195) < 2 and d['dir'] == 1 and not d['entry']
        print('結果:', 'OK' if ok else 'NG', '（入り方3秒＋移動1.5秒のあと、料金の位置 195・右向き・残り 0 か）')
    else:
        # 開いた直後：スクロールなしで帯（ご契約中のお店へ）が全部見えるか・飛行機と重ならないか
        time.sleep(0.3); shot('00_開いた直後（スクロールなし）', 0, 844)
        band = json.loads(js("JSON.stringify(document.getElementById('irai-band').getBoundingClientRect())"))
        vis = band['top'] >= 0 and band['bottom'] <= 844 and js('window.pageYOffset') == 0 and js("getComputedStyle(document.getElementById('irai-band')).display") == 'block'
        print('帯: 上=%d 下=%d 見える=%s' % (band['top'], band['bottom'], 'OK' if vis else 'NG'))
        time.sleep(2.9)
        d = state('開いて4秒（入り方が終わった）'); shot('0_開いて4秒_ホーム', 0, 130)
        # 飛行機（右向き 68px・左向き 78px。機体の高さ ±8px）と帯の文字（padding の内側）が重ならないか
        # 飛行機の一番下（中心＋6px。翼の先）と帯の文字の上（padding の内側）の間が、右向き・左向きとも 12px 以上か
        pt = band['top'] + float(js("parseFloat(getComputedStyle(document.getElementById('irai-band')).paddingTop)"))
        gapL = pt - (d['y'] + 6); gapR = pt - (70 + 6)
        print('帯の文字の上=%d  飛行機の一番下：左向き %d（間 %dpx）・右向き 76（間 %dpx）→ %s' % (pt, d['y'] + 6, gapL, gapR, 'OK（12px 以上）' if gapL >= 12 and gapR >= 12 else 'NG'))
        allok = d['left'] == 0 and not d['entry'] and vis and gapL >= 12 and gapR >= 12
        for i, s in enumerate(['ryokin', 'home', 'soudan', 'dekiru', 'soudan']):
            tap(s); time.sleep(0.1); sc = scr()
            time.sleep(2.0)
            d = state('%s を押して2秒後' % NAMES[s])
            tx = {'home': 39, 'dekiru': 117, 'ryokin': 195, 'nagare': 273, 'soudan': 351}[s]
            want_dir = 1 if d['x'] >= 0 and s in ('ryokin', 'soudan') else -1
            ok = sc == s and d['left'] == 0 and abs(d['x'] - tx) < 2 and d['dir'] == want_dir and (d['a'] == 0 if want_dir == 1 else abs(d['a']) == 180)
            allok = allok and ok
            bd = js("getComputedStyle(document.getElementById('irai-band')).display")
            okb = (bd == 'block') == (s == 'home'); allok = allok and okb
            print('   画面=%s 目標x=%d 帯=%s → %s' % (sc, tx, bd, 'OK' if ok and okb else 'NG'))
            shot('%d_%s' % (i + 1, s), 0, 130)
        print('全部:', 'OK' if allok else 'NG')
finally:
    chrome.terminate()
