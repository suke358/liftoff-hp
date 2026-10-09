#!/usr/bin/env python3
"""shian2 を WebKit（iPhone の Safari と同じ描画エンジン。Playwright の webkit）で開いて、何も触らずに画像を撮る  2026/10/10 作成

iPhone 14 の設定（幅 390・高さ 844・dpr 3・タッチあり・Safari の UA）。開いた直後 0秒・0.5秒・1.5秒で画面を撮り、
帯（ご契約中のお店へ）の下と見出し「お店のホームページ、」の文字の間が空いているかを見る。
数字（getBoundingClientRect）と絵がずれる iPhone の不具合を、Mac で再現して確かめるための道具。

使い方:
  python3 tools/mihon/webkit_test_shian2.py [保存するフォルダ名] [URL]
  例: python3 tools/mihon/webkit_test_shian2.py 直す前
      python3 tools/mihon/webkit_test_shian2.py 直した後 file:///Users/taisuke/src/liftoff-hp/shian2/index.html?shop=colore
最初の1回だけ: pip3 install playwright && python3 -m playwright install webkit
画像は tools/mihon/webkit_shots/<フォルダ名>/ に入る
"""
import sys, os, time
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
name = sys.argv[1] if len(sys.argv) > 1 else time.strftime('%Y%m%d_%H%M')
URL = sys.argv[2] if len(sys.argv) > 2 else 'https://liftoff-hp.liftoff-358.workers.dev/shian2/?shop=colore'
OUT = os.path.join(HERE, 'webkit_shots', name)
os.makedirs(OUT, exist_ok=True)

MEASURE = """() => { var b = document.getElementById('irai-band'), h = document.querySelector('#home .hero h1');
  var br = b ? b.getBoundingClientRect() : null, hr = h ? h.getBoundingClientRect() : null;
  return { band_bottom: br ? Math.round(br.bottom) : null, h1_top: hr ? Math.round(hr.top) : null, scrollY: Math.round(window.pageYOffset || 0),
           band_display: b ? getComputedStyle(b).display : null, scr: (document.querySelector('.scr.on') || {}).id }; }"""

with sync_playwright() as pw:
    iphone = pw.devices['iPhone 14']
    browser = pw.webkit.launch()
    ctx = browser.new_context(**iphone)
    page = ctx.new_page()
    t0 = time.time()
    page.goto(URL, wait_until='commit')
    results = []
    for at in (0, 0.5, 1.5, 3.0):
        wait = at - (time.time() - t0)
        if wait > 0: time.sleep(wait)
        label = '%.1f秒' % at
        try:
            m = page.evaluate(MEASURE)
        except Exception as e:
            m = {'error': str(e)[:80]}
        page.screenshot(path=os.path.join(OUT, '%s.png' % label.replace('.', '_')), full_page=False)
        results.append((label, m))
        print(label, m)
    # 見出しの文字が実際にどこに描かれているか：画面の絵から調べる（帯の下から下へ、文字の色（紺）の点が最初に出る行）
    from PIL import Image
    im = Image.open(os.path.join(OUT, '1_5秒.png')).convert('RGB')
    W, H = im.size; dpr = W / 390.0
    m = results[2][1]
    if m.get('band_bottom') is not None:
        y0 = int(m['band_bottom'] * dpr) + 2
        first = None
        for y in range(y0, int(H * 0.6)):
            dark = 0
            for x in range(int(20 * dpr), int(330 * dpr), 3):
                r, g, b = im.getpixel((x, y))
                if r < 90 and g < 110 and b < 130: dark += 1
            if dark > 8: first = y; break
        if first is not None:
            print('絵の上で、帯の下（%dpx）から最初に紺の文字が出る高さ: %dpx（CSS px）→ 帯の下との間 %dpx。数字（rect）の見出しの上は %dpx' % (m['band_bottom'], first / dpr, first / dpr - m['band_bottom'], m['h1_top']))
            print('判定:', 'くっついている（ずれあり）' if first / dpr - m['band_bottom'] < 20 else 'OK（間が空いている）')
    browser.close()
print('画像:', OUT)
