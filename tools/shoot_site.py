#!/usr/bin/env python3
"""shoot_site.py — お店のページを、採点役（AIの物差し）が見る形で撮る道具（2026/11/21 ⑥-2。物差しのチャットの capture.py・link_fallback.py を1つにして tools/ に置いた）

  python3 tools/shoot_site.py <サイトのフォルダ か URL> <画像を置く親フォルダ> --num 23 --name 試しのHP_⑥-2_1_松葉造園 [--port 8765]

  - フォルダを渡すと、手元のサーバー（127.0.0.1:port）を立てて開き、撮り終えたら閉じる。URL を渡すとそのまま開く
  - 幅 390（iPhone 13 の形）と 1280 で撮る。ゆっくり下まで流して（遅れて出る写真を出し切って）から上に戻って撮る
  - 置く物：<親>/<num>_<name>/ に 390_01.png〜（画面ごと）・390_bottom.png・390_full.png（全体）・390_sheet.png（一覧）・390_yoyaku.png（予約ボタンを1回押した先）、1280 も同じ、facts.json、事実の記録.md
  - 予約ボタン：予約らしい文字のボタン（予約 → 相談・問い合わせ → LINE の順）を自動で1つ選んで押す。入力はしない。押せなかったときはリンク先を直接開いて撮り、事実の記録.md に「押せなかった分の補い」を足す
  - 要る物：pip3 install playwright pillow と python3 -m playwright install chromium
"""
import sys, os, json, re, math, time, datetime, traceback, argparse, subprocess, socket

CTA_RE = r"予約|相談|問い合わせ|問合せ|問い合せ|LINE|ライン|電話|TEL|Tel|tel|お申し込み|申込|Instagram|インスタ|アクセス|道順|地図|MAP|Map|Reserve|Reservation|Contact|Booking"
YOYAKU_RE = r"予約|Reserv|Booking|ホットペッパー|hotpepper|LINE|ライン|お問い合わせ|問い合わせ|問合せ|Contact|相談"

FACTS_JS = r"""
() => {
  const vw = window.innerWidth, vh = window.innerHeight;
  const H = document.documentElement.scrollHeight;
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width>0 && r.height>0 && s.visibility!=='hidden' && s.display!=='none' && s.opacity!=='0'; };
  const sizes=[]; let small=0, total=0, longest=0, lines=[];
  document.querySelectorAll('p,li,span,div,td,dd,a').forEach(el=>{
    if([...el.children].some(c=>/^(P|DIV|UL|OL|LI|SECTION|TABLE|H[1-6]|ARTICLE|NAV|HEADER|FOOTER)$/.test(c.tagName))) return;
    const t=(el.innerText||'').trim(); if(t.length<20) return;
    if(!vis(el)) return;
    const fs=parseFloat(getComputedStyle(el).fontSize); sizes.push(fs); total++; if(fs<14) small++;
    lines.push(t.length);
  });
  sizes.sort((a,b)=>a-b); const med = sizes.length? sizes[Math.floor(sizes.length/2)] : null;
  lines.sort((a,b)=>a-b); const medLen = lines.length? lines[Math.floor(lines.length/2)] : null;
  const longBlocks = lines.filter(x=>x>=120).length;
  const heads=[...document.querySelectorAll('h1,h2,h3')].filter(vis).map(h=>h.innerText.trim().replace(/\s+/g,' ').slice(0,40)).filter(x=>x);
  const imgs=[...document.querySelectorAll('img')].filter(i=>{const r=i.getBoundingClientRect(); return r.width>=150 && r.height>=100 && vis(i);});
  const bgImgs=[...document.querySelectorAll('*')].filter(e=>{const bi=getComputedStyle(e).backgroundImage; if(!bi||bi==='none'||!bi.includes('url(')) return false; const r=e.getBoundingClientRect(); return r.width>=150&&r.height>=100;}).length;
  const srcs = imgs.map(i=>i.currentSrc||i.src); const uniq=new Set(srcs);
  const text=document.body.innerText||'';
  const foot = text.slice(-1200);
  const has = (re, s) => re.test(s);
  const addr = has(/〒|[都道府県][^\n]{1,12}[市区町村郡]|[市区町村][^\n]{0,20}\d/, text);
  const phone = has(/0\d{1,4}[-‐ー−]\d{1,4}[-‐ー−]\d{3,4}|0\d{9,10}/, text);
  const hours = has(/営業時間|受付時間|\d{1,2}:\d{2}\s*[〜~～-]\s*\d{1,2}:\d{2}|定休/, text);
  const links=[...document.querySelectorAll('a')].map(a=>a.href||'');
  const sns={instagram:links.some(l=>/instagram\.com/.test(l)), line:links.some(l=>/line\.me|lin\.ee/.test(l)), facebook:links.some(l=>/facebook\.com/.test(l)), x:links.some(l=>/twitter\.com|x\.com\//.test(l)), tiktok:links.some(l=>/tiktok\.com/.test(l)), youtube:links.some(l=>/youtube\.com|youtu\.be/.test(l)), hotpepper:links.some(l=>/hotpepper|beauty\.hotpepper/.test(l)), tel:links.some(l=>/^tel:/.test(l)), map:links.some(l=>/google\.[a-z.]+\/maps|goo\.gl\/maps|maps\.app/.test(l))};
  const ctaRe = new RegExp(%CTA%);
  const ctas=[];
  document.querySelectorAll('a,button,[role=button]').forEach(el=>{
    const t=((el.innerText||el.getAttribute('aria-label')||el.title||'')+'').trim().replace(/\s+/g,' ');
    const href=el.href||'';
    if(!(ctaRe.test(t) || /^tel:|line\.me|lin\.ee|hotpepper/.test(href))) return;
    if(!vis(el)) return;
    const r=el.getBoundingClientRect();
    let fixed=false; let e=el; while(e && e!==document.body){ const p=getComputedStyle(e).position; if(p==='fixed'||p==='sticky'){fixed=true;break;} e=e.parentElement; }
    ctas.push({text:t.slice(0,30), href:href.slice(0,120), fixed, firstScreen: (r.top+window.scrollY) < vh, top: Math.round(r.top+window.scrollY), w:Math.round(r.width), h:Math.round(r.height)});
  });
  const overlays=[...document.querySelectorAll('*')].filter(e=>{const s=getComputedStyle(e); if(s.position!=='fixed') return false; const r=e.getBoundingClientRect(); return r.width*r.height > vw*vh*0.25 && vis(e) && parseInt(s.zIndex||'0')>0;}).map(e=>({tag:e.tagName, cls:(e.className||'').toString().slice(0,40), area:Math.round(e.getBoundingClientRect().width*e.getBoundingClientRect().height/(vw*vh)*100)}));
  const iframes=[...document.querySelectorAll('iframe')].filter(vis).map(f=>(f.src||'').slice(0,80));
  const overflowX = document.documentElement.scrollWidth > vw+2;
  return {vw,vh,H, screens: Math.ceil(H/vh), fontMedian:med, fontCount:total, fontSmallCount:small, lineMedianChars:medLen, longBlocks, headings:heads.length, headingList:heads.slice(0,60), imgCount:imgs.length, imgUniq:uniq.size, bgImgs, addr, phone, hours, sns, ctas: ctas.slice(0,40), overlays, iframes, overflowX, title: document.title, textLen: text.length, footer: foot};
}
""".replace("%CTA%", json.dumps(CTA_RE))


def sheet(paths, cols, scale, out):
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths]
    if not ims: return
    w = int(ims[0].width * scale); h = int(ims[0].height * scale)
    rows = math.ceil(len(ims) / cols)
    S = Image.new("RGB", (w * cols + (cols - 1) * 8, h * rows + (rows - 1) * 8), (120, 120, 120))
    for i, im in enumerate(ims):
        im = im.resize((w, h))
        S.paste(im, ((i % cols) * (w + 8), (i // cols) * (h + 8)))
    S.save(out, optimize=True)


def score(c):
    """予約ボタンらしさ（小さいほど先に押す）"""
    t = c["text"]; h = c["href"]
    if re.search(r"/news/|/blog/|/post/|/category/", h): return 5
    if re.match(r"^(ご|WEB|Web|ウェブ|ネット|オンライン|24時間)?(予約|Reserv|Booking)", t) or re.search(r"予約(は|を)?(する|こちら|フォーム|ページ)", t): return 0
    if re.search(r"予約|Reserv|Booking|hotpepper", t + h): return 1
    if re.search(r"問い合わせ|問合せ|相談|Contact", t): return 2
    if re.search(r"LINE|ライン|line\.me|lin\.ee", t + h): return 3
    return 4


def new_context(pw, browser, width):
    if width == 390:
        dev = pw.devices["iPhone 13"]
        return browser.new_context(**{**dev, "viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "locale": "ja-JP"})
    return browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1, locale="ja-JP")


def capture(pw, browser, d, url, width):
    pre = f"{width}"; maxshots = 12 if width == 390 else 8
    ctx = new_context(pw, browser, width)
    rec = {"url": url, "width": width, "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "ok": False}
    page = ctx.new_page()
    try:
        try: page.goto(url, wait_until="load", timeout=45000)
        except Exception as ex: rec["goto_note"] = f"load待ちで時間切れ→そのまま続けた({type(ex).__name__})"
        page.wait_for_timeout(3000)
        rec["final_url"] = page.url
        try:
            Hw = page.evaluate("document.documentElement.scrollHeight"); yy = 0
            while yy < Hw and yy < 40000:
                yy += 400; page.evaluate(f"window.scrollTo(0,{yy})"); page.wait_for_timeout(250)
                Hw = page.evaluate("document.documentElement.scrollHeight")
            page.wait_for_timeout(1500); page.evaluate("window.scrollTo(0,0)"); page.wait_for_timeout(2000)
            rec["warmup"] = "ゆっくり下まで流してから上に戻って撮った"
        except Exception as ex:
            rec["warmup"] = f"ならし失敗 {str(ex)[:60]}"
        shots = []
        p = os.path.join(d, f"{pre}_01.png"); page.screenshot(path=p); shots.append(p)
        facts = page.evaluate(FACTS_JS)
        vh = facts["vh"]; H = facts["H"]
        step = int(vh * 0.9); y = step; n = 2
        while y < H - 20 and n <= maxshots:
            page.evaluate(f"window.scrollTo(0,{y})"); page.wait_for_timeout(1300)
            p = os.path.join(d, f"{pre}_{n:02d}.png"); page.screenshot(path=p); shots.append(p); y += step; n += 1
        page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)"); page.wait_for_timeout(800)
        p = os.path.join(d, f"{pre}_bottom.png"); page.screenshot(path=p)
        rec["shots"] = len(shots); rec["reached_bottom"] = (y >= H - 20)
        H2 = page.evaluate("document.documentElement.scrollHeight")
        if H2 <= 25000:
            try: page.screenshot(path=os.path.join(d, f"{pre}_full.png"), full_page=True)
            except Exception as ex: rec["full_note"] = str(ex)[:80]
        sheet(shots + [p], 4 if width == 390 else 2, 0.5, os.path.join(d, f"{pre}_sheet.png"))
        # 予約ボタンを1回押す（入力はしない）
        page.evaluate("window.scrollTo(0,0)"); page.wait_for_timeout(500)
        click = {"tried": False}
        cands = [c for c in facts["ctas"] if re.search(YOYAKU_RE, c["text"] + " " + c["href"]) and not c["href"].startswith("tel:")]
        cands.sort(key=lambda c: (score(c), 0 if (c["fixed"] or c["firstScreen"]) else 1, c["top"]))
        tried = []
        for c in cands[:4]:
            click = {"tried": True, "target": c["text"], "href": c["href"], "fixed": c["fixed"], "firstScreen": c["firstScreen"], "tried_before": tried[:]}
            try:
                loc = None
                if c["href"] and '"' not in c["href"]:
                    l = page.locator(f'a[href="{c["href"]}"]')
                    if l.count() > 0: loc = l.first
                if loc is None: loc = page.get_by_text(c["text"], exact=False).first
                newpage = [None]
                ctx.on("page", lambda pg: newpage.__setitem__(0, pg))
                loc.scroll_into_view_if_needed(timeout=5000); page.wait_for_timeout(300)
                loc.click(timeout=8000, no_wait_after=True)
                page.wait_for_timeout(3500)
                tgt = newpage[0] if newpage[0] else page
                try: tgt.wait_for_load_state("load", timeout=10000)
                except Exception: pass
                tgt.wait_for_timeout(1000)
                click["result_url"] = tgt.url; click["new_tab"] = bool(newpage[0])
                try:
                    click["result_title"] = tgt.title()
                    tgt.screenshot(path=os.path.join(d, f"{pre}_yoyaku.png"))
                    click["form_inputs_on_result"] = tgt.evaluate("document.querySelectorAll('input:not([type=hidden]),textarea,select').length")
                except Exception as ex:
                    click["result_note"] = str(ex)[:120]
                break
            except Exception as ex:
                click["error"] = str(ex)[:160]; tried.append(c["text"])
                try: page.goto(url, wait_until="load", timeout=30000); page.wait_for_timeout(1500)
                except Exception: pass
        rec["yoyaku_click"] = click
        rec["facts"] = facts
        rec["ok"] = True
    except Exception:
        rec["error"] = traceback.format_exc()[-400:]
    finally:
        try: ctx.close()
        except Exception: pass
    return rec


def link_fallback(pw, browser, d, rec):
    """押せなかったとき：入口の一覧から予約らしいリンク先を直接開いて撮る。足す文を返す（無ければ None）"""
    yc = rec.get("yoyaku_click", {})
    if not rec.get("ok") or not yc.get("tried") or yc.get("result_url"): return None
    w = rec["width"]
    cands = sorted([c for c in rec["facts"]["ctas"] if c["href"].startswith("http")], key=lambda c: (score(c), 0 if (c["fixed"] or c["firstScreen"]) else 1, c["top"]))
    cands = [c for c in cands if score(c) <= 3]
    if not cands: return f"- 幅{w}: 押せる入口も、開けるリンク先も見つからなかった(操作なし)"
    c = cands[0]; ctx = new_context(pw, browser, w); pg = ctx.new_page()
    try:
        try: pg.goto(c["href"], wait_until="load", timeout=30000)
        except Exception: pass
        pg.wait_for_timeout(2500)
        pg.screenshot(path=os.path.join(d, f"{w}_yoyaku.png"))
        n = pg.evaluate("document.querySelectorAll('input:not([type=hidden]),textarea,select').length")
        return f"- 幅{w}: ボタン「{yc.get('target')}」は道具では押せなかった(操作なし)。代わりに入口の一覧の「{c['text'] or '(文字なしのボタン)'}」のリンク先 {c['href']} を直接開いて {w}_yoyaku.png に撮った(題名: {pg.title()}; 入力欄の数: {n}; {datetime.datetime.now().strftime('%H:%M')})"
    except Exception as ex:
        return f"- 幅{w}: リンク先 {c['href']} を開けなかった: {str(ex)[:100]}"
    finally:
        ctx.close()


def facts_md(num, name, url, recs, note):
    L = [f"# {num} {name}  事実の記録", f"- 開く先: {url}" + (f"（{note}）" if note else ""), ""]
    for r in recs:
        w = r["width"]; L.append(f"## 幅{w}(撮った時刻 {r['time']})")
        if not r.get("ok"):
            L.append(f"- 開けなかった: {r.get('error','')[:200]}"); L.append(""); continue
        f = r["facts"]
        L.append(f"- 題名: {f['title']}")
        if r.get("goto_note"): L.append(f"- 注: {r['goto_note']}")
        if r.get("warmup"): L.append(f"- 撮り方: {r['warmup']}")
        L.append(f"- ページの長さ: 画面{f['screens']}枚分(高さ{f['H']}px)。横はみ出し: {'あり' if f['overflowX'] else 'なし'}。撮った枚数 {r['shots']}(下まで届いた: {'はい' if r.get('reached_bottom') else 'いいえ(長いので途中まで)'})")
        L.append(f"- 本文の文字の大きさ(中央値): {f['fontMedian']}px。14px未満の文の塊: {f['fontSmallCount']}/{f['fontCount']}。1塊の文字数(中央値): {f['lineMedianChars']}字。120字以上の長い塊: {f['longBlocks']}")
        L.append(f"- 見出し(h1-h3)の数: {f['headings']}。大きい画像: {f['imgCount']}枚(違う画像 {f['imgUniq']})。背景画像の箱: {f['bgImgs']}")
        L.append(f"- 文の中に 住所らしき: {'あり' if f['addr'] else 'なし'} / 電話番号: {'あり' if f['phone'] else 'なし'} / 営業時間: {'あり' if f['hours'] else 'なし'}")
        s = f['sns']; L.append("- リンク先: " + (", ".join([k for k, v in s.items() if v]) or "なし"))
        if f['overlays']: L.append(f"- 開いたときの大きい固定の覆い(ポップアップ/広告の可能性): {f['overlays']}")
        if f['iframes']: L.append(f"- 埋め込み(iframe): {f['iframes'][:5]}")
        L.append("- 見出しの並び(上から): " + " / ".join(f['headingList'][:40]))
        L.append("- 予約・相談・電話などの入口(見えているもの):")
        for c in f['ctas'][:25]:
            L.append(f"  - 「{c['text']}」 {'[固定]' if c['fixed'] else ''}{'[最初の画面]' if c['firstScreen'] else ''} → {c['href'] or '(リンクなし/ボタン)'}  大きさ{c['w']}x{c['h']}")
        if not f['ctas']: L.append("  - 見つからなかった")
        yc = r.get("yoyaku_click", {})
        if yc.get("tried"):
            L.append(f"- 予約ボタンを1回押した: 「{yc.get('target')}」 → " + (f"{yc.get('result_url','')} (題名: {yc.get('result_title','')}; 新しいタブ: {yc.get('new_tab')}; 入力欄の数: {yc.get('form_inputs_on_result')})") + (f" エラー: {yc['error']}" if yc.get('error') else ""))
            L.append(f"  - 押した先の画面: {w}_yoyaku.png(あれば)。※押す相手は道具が自動で選んだ(予約らしい文字のボタンを優先)。本当の入口は上の一覧で確かめる" + (f"。先に押せなかったもの: {yc.get('tried_before')}" if yc.get('tried_before') else ""))
        else:
            L.append("- 予約ボタン: 押せるものが見つからなかった(操作なし)")
        L.append(f"- 下の段(フッター付近の文):\n```\n{f['footer'].strip()[-700:]}\n```")
        L.append("")
    return "\n".join(L)


def free_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def main():
    ap = argparse.ArgumentParser(description="お店のページを採点役が見る形で撮る")
    ap.add_argument("target", help="サイトのフォルダ（index.html のある所）か URL")
    ap.add_argument("out", help="画像を置く親フォルダ（この中に <num>_<name>/ ができる）")
    ap.add_argument("--num", required=True, help="番号（例 23）")
    ap.add_argument("--name", required=True, help="名前（例 試しのHP_⑥-2_1_松葉造園）")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    server = None; note = ""
    if re.match(r"https?://", a.target):
        url = a.target
    else:
        folder = os.path.abspath(a.target)
        if not os.path.exists(os.path.join(folder, "index.html")): sys.exit(f"⚠️ index.html がありません: {folder}")
        port = a.port
        while not free_port(port): port += 1
        server = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", folder], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0)
        url = f"http://127.0.0.1:{port}/"; note = f"手元のサーバー 127.0.0.1:{port}・{folder} を開いた"
    d = os.path.join(a.out, f"{a.num}_{a.name}"); os.makedirs(d, exist_ok=True)
    recs = []; adds = []
    try:
        with sync_playwright() as pw:
            try: browser = pw.chromium.launch(headless=True)
            except Exception: browser = pw.chromium.launch(channel="chrome", headless=True)
            for w in (390, 1280):
                t0 = time.time()
                r = capture(pw, browser, d, url, w)
                print(f"{a.num} {a.name} 幅{w}: ok={r['ok']} 枚数={r.get('shots')} {time.time()-t0:.0f}秒", flush=True)
                recs.append(r)
                x = link_fallback(pw, browser, d, r)
                if x: adds.append(x)
            browser.close()
    finally:
        if server: server.terminate()
    with open(os.path.join(d, "facts.json"), "w") as f: json.dump(recs, f, ensure_ascii=False, indent=1)
    md = facts_md(a.num, a.name, url, recs, note)
    if adds: md += "\n## 押せなかった分の補い(リンク先を直接開いた)\n" + "\n".join(adds) + "\n"
    with open(os.path.join(d, "事実の記録.md"), "w") as f: f.write(md)
    with open(os.path.join(a.out, "撮影の記録.json"), "a") as f:
        for r in recs: f.write(json.dumps({k: v for k, v in r.items() if k != 'facts'}, ensure_ascii=False) + "\n")
    # 撮影の記録（11月21日）.md に貼る行
    for r in recs:
        yc = r.get("yoyaku_click", {}); f_ = r.get("facts", {})
        yo = f"「{yc.get('target')}」→ {yc.get('result_url','')}" if yc.get("tried") else "押せる入口なし(操作なし)"
        print(f"| {a.num}_{a.name} | {r['width']} | {r['time']} | {r.get('shots')}枚＋下＋全体 | 画面{f_.get('screens')}枚分 | ならし有 | {yo}{'（' + note + '）' if note else ''} |")
    print("置いた:", d)


if __name__ == "__main__":
    main()
