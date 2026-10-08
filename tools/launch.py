#!/usr/bin/env python3
"""本公開の準備を一括でする（Lift-Off）  2026/10/8 作成

使い方:
  まず確かめるだけ（ファイルは変えない）：
    python3 launch.py <サイトのフォルダ> <新しいドメインのURL>
      例）python3 launch.py ~/src/colore-website https://colore-hofu.com
  よければ書きかえる：
    python3 launch.py <サイトのフォルダ> <新しいドメインのURL> --apply

やること（マニュアル 10 の手順3）:
  1. トップの「検索に出さない設定」（noindex）を外す
  2. 仮のURL（github.io・workers.dev）を新しいドメインに置きかえる（LINEのカード・お店情報など）
  3. canonical（このページの正式な住所）を足す
  4. robots.txt・sitemap.xml を作る
     ※ 見本帳（samples/）は架空のお店なので、noindex のまま・サイトマップにも入れない
        ほかにも検索に出さないフォルダがあれば --keep-noindex=samples,〇〇 で指定
  5. 消すフォルダ（前の版 v1/・別案 new/ など）を一覧にし、push のときに消すコマンドを出す
     （Claude の作業場所からは消せないので、担当者のターミナルで消す）
"""
import sys, os, re, datetime

REMOVE_DIRS = re.compile(r'^(v\d+|new|kuro|logo-mihon|old|test|draft|tmp)$')
REMOVE_FILES = re.compile(r'\.(bak|orig)$|^_')
SKIP = {'.git', '.wrangler', 'tools', 'node_modules'}

def html_pages(root, removed):
    pages = []
    for d, dirs, files in os.walk(root):
        rel = os.path.relpath(d, root)
        top = rel.split(os.sep)[0]
        if top in SKIP or top in removed or any(p.startswith('.') for p in rel.split(os.sep) if p != '.'):
            dirs[:] = []; continue
        for f in files:
            if f.endswith('.html') and not REMOVE_FILES.search(f):
                pages.append(os.path.normpath(os.path.join(rel, f)))
    return sorted(pages, key=lambda p: (p.count(os.sep), p != 'index.html', p))

def page_url(domain, p):
    p = p.replace(os.sep, '/')
    if p == 'index.html': return domain + '/'
    if p.endswith('/index.html'): return domain + '/' + p[:-len('index.html')]
    return domain + '/' + p

def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if len(a) < 2: print(__doc__); sys.exit(1)
    root, domain = os.path.expanduser(a[0]).rstrip('/'), a[1].rstrip('/')
    apply = '--apply' in sys.argv
    keep = ['samples']
    for x in sys.argv:
        if x.startswith('--keep-noindex='): keep = [k for k in x.split('=', 1)[1].split(',') if k]
    if not domain.startswith('https://'): print('⚠️ ドメインは https:// から書いてください'); sys.exit(1)
    repo = os.path.basename(root)
    olds = [f'https://suke358.github.io/{repo}', f'https://{repo}.liftoff-358.workers.dev']
    today = datetime.date.today().isoformat()
    print(f'{"【書きかえ】" if apply else "【確かめるだけ】"} {root} → {domain}\n')

    # 5. 消すもの
    removed = [n for n in sorted(os.listdir(root)) if os.path.isdir(os.path.join(root, n)) and REMOVE_DIRS.match(n)]
    rmfiles = []
    for d, dirs, files in os.walk(root):
        if os.path.relpath(d, root).split(os.sep)[0] in SKIP | set(removed): dirs[:] = []; continue
        rmfiles += [os.path.relpath(os.path.join(d, f), root) for f in files if f.endswith(('.bak', '.orig'))]

    pages = html_pages(root, set(removed))
    todo, warn = [], []
    hidden = [p for p in pages if p.split(os.sep)[0] in keep]
    for p in pages:
        path = os.path.join(root, p); s = open(path, encoding='utf-8').read(); o = s
        url = page_url(domain, p)
        if p in hidden:
            if 'noindex' not in s: warn.append(f'{p}：検索に出さないフォルダなのに noindex が無い')
            for old in olds:
                if old in s: s = s.replace(old, domain); todo.append(f'{p}：仮のURL → {domain}（noindex はそのまま）')
            if apply and s != o: open(path, 'w', encoding='utf-8').write(s)
            continue
        # 1. noindex（検索に出すページは外す）
        s = re.sub(r'[ \t]*<!--[^\n]*本公開[^\n]*-->\n(?=[ \t]*<meta name="robots")', '', s)
        s, n = re.subn(r'[ \t]*<meta name="robots" content="[^"]*noindex[^"]*">\n?', '', s)
        if n: todo.append(f'{p}：noindex を外す')
        # 2. 仮のURL
        for old in olds:
            c = s.count(old)
            if c: s = s.replace(old, domain); todo.append(f'{p}：仮のURL {old} → {domain}（{c}か所）')
        # 3. canonical
        if 'rel="canonical"' not in s:
            s, n = re.subn(r'(<meta property="og:url"[^>]*>\n)', r'\1' + f'<link rel="canonical" href="{url}">\n', s, count=1)
            if not n: s = s.replace('</title>\n', f'</title>\n<link rel="canonical" href="{url}">\n', 1)
            todo.append(f'{p}：canonical を足す（{url}）')
        # og:url は各ページの住所に
        m = re.search(r'<meta property="og:url" content="([^"]*)">', s)
        if m and m.group(1) != url:
            s = s.replace(m.group(0), f'<meta property="og:url" content="{url}">'); todo.append(f'{p}：og:url を {url} に')
        for left in re.findall(r'https://[^"\'\s<>]*(?:github\.io|workers\.dev)[^"\'\s<>]*', s):
            warn.append(f'{p}：まだ仮のURLが残っている → {left}')
        if apply and s != o: open(path, 'w', encoding='utf-8').write(s)

    # 4. robots.txt・sitemap.xml
    robots = f'User-agent: *\nAllow: /\n\nSitemap: {domain}/sitemap.xml\n'
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    shown = [p for p in pages if p not in hidden]
    for p in shown: sm.append(f'  <url><loc>{page_url(domain, p)}</loc><lastmod>{today}</lastmod></url>')
    sm.append('</urlset>\n')
    for name, body in (('robots.txt', robots), ('sitemap.xml', '\n'.join(sm))):
        cur = open(os.path.join(root, name), encoding='utf-8').read() if os.path.exists(os.path.join(root, name)) else None
        if cur != body:
            todo.append(f'{name} を{"作りなおす" if cur else "作る"}')
            if apply: open(os.path.join(root, name), 'w', encoding='utf-8').write(body)

    print('■ 書きかえ' + ('ました' if apply else 'ること'))
    for t in todo or ['（なし。もう済んでいる）']: print('  ・' + t)
    print('\n■ サイトマップに入れるページ')
    for p in shown: print('  ・' + page_url(domain, p))
    if hidden: print(f'  （検索に出さない：{", ".join(sorted(set(h.split(os.sep)[0] for h in hidden)))}/ の {len(hidden)} ページ）')
    if warn:
        print('\n■ ⚠️ 確かめること'); [print('  ・' + w) for w in warn]
    print('\n■ 消すもの（前の版・別案。本公開では見せない）')
    rm = removed + rmfiles
    for r in rm or ['（なし）']: print('  ・' + r)
    if rm:
        print('  → push のコマンドの前にこれを足す（担当者のターミナル）：')
        print('    git rm -r -q --ignore-unmatch ' + ' '.join(f'"{r}"' for r in rm) + ' &&')
    if not apply: print('\nよければ --apply を付けてもう一度。')
    else: print('\nこのあと：公開前チェック（check_site.py）→ push → 新しいドメインで確認（マニュアル 10）')

if __name__ == '__main__':
    main()
