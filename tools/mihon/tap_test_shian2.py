#!/usr/bin/env python3
"""headless Chrome を DevTools（CDP）でつないで、本当にタブを押して飛行機の位置を読む
（jetSim・jetPose は使わない。requestAnimationFrame は本物が走る）
使い方: cdp_test.py <ページのURL> <画像を置くフォルダ>
"""
import sys, os, json, time, socket, base64, subprocess, urllib.request, struct

CH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
URL, OUT = sys.argv[1], sys.argv[2]
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
    def js(expr):
        r = call('Runtime.evaluate', expression=expr, returnByValue=True)
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
    mode = sys.argv[3] if len(sys.argv) > 3 else 'normal'
    if mode == 'early':
        state('開いて1秒（入り方の途中）'); shot('途中押し_0_開いて1秒', 0, 844)
        tap('ryokin'); print('→ 1秒の時点で 料金 を押した。画面=', scr())
        time.sleep(1.0); state('押して1秒後'); shot('途中押し_1_押して1秒後', 0, 844)
        time.sleep(6.0); d = state('押して7秒後'); shot('途中押し_2_押して7秒後', 0, 130)
        ok = d['left'] == 0 and abs(d['x'] - 195) < 2 and d['dir'] == 1 and not d['entry']
        print('結果:', 'OK' if ok else 'NG', '（料金の位置 195・右向き・残り 0 か）')
    else:
        time.sleep(3.2)
        d = state('開いて4秒（入り方が終わった）'); shot('0_開いて4秒_ホーム', 0, 130)
        allok = d['left'] == 0 and not d['entry']
        for i, s in enumerate(['ryokin', 'home', 'soudan', 'dekiru', 'soudan']):
            tap(s); time.sleep(0.1); sc = scr()
            time.sleep(6.0)
            d = state('%s を押して6秒後' % NAMES[s])
            tx = {'home': 39, 'dekiru': 117, 'ryokin': 195, 'nagare': 273, 'soudan': 351}[s]
            want_dir = 1 if d['x'] >= 0 and s in ('ryokin', 'soudan') else -1
            ok = sc == s and d['left'] == 0 and abs(d['x'] - tx) < 2 and d['dir'] == want_dir and (d['a'] == 0 if want_dir == 1 else abs(d['a']) == 180)
            allok = allok and ok
            print('   画面=%s 目標x=%d → %s' % (sc, tx, 'OK' if ok else 'NG'))
            shot('%d_%s' % (i + 1, s), 0, 130)
        print('全部:', 'OK' if allok else 'NG')
finally:
    chrome.terminate()
