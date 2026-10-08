#!/usr/bin/env python3
"""文の折り返しの調整（BudouX）を、HTML にまとめて入れる  2026/10/8 作成

日本語の文に、言葉の切れ目で <wbr>（ここで折り返してよい印）を入れる。
「ホームペー / ジ」のような変な所で行が変わるのを防ぐ。

使い方:
  python3 tools/wbr.py <HTMLファイル> [<HTMLファイル> ...]
  python3 tools/wbr.py samples/*/index.html        … まとめて
  すでに <wbr> が入っているファイルは飛ばす（入れ直すときは --force。先に <wbr> を消してから入れる）

最初の1回だけ:  pip3 install budoux
入れたあと、CSS に次の1行があるか確かめる（なければ <style> のすぐ下に足す）:
  body{word-break:keep-all;overflow-wrap:anywhere;line-break:strict}
"""
import re, sys
try:
    import budoux
except ImportError:
    sys.exit('budoux がありません。ターミナルで  pip3 install budoux  をしてから、もう一度どうぞ')

P = budoux.load_default_japanese_parser()
SKIP = ('script', 'style', 'title', 'textarea', 'option', 'svg', 'head', 'noscript')
# BudouX が間に切れ目を入れてしまう言葉（見つけたら足す）
KEEP = ['よもぎ', 'ホームページ', 'Googleマップ']
JA = re.compile(r'[぀-ヿ㐀-鿿]')


def add_wbr(s):
    out, depth, n = [], {k: 0 for k in SKIP}, 0
    for part in re.split(r'(<!--.*?-->|<[^>]+>)', s, flags=re.S):
        if part.startswith('<'):
            m = re.match(r'<(/?)([a-zA-Z0-9]+)', part)
            if m and m.group(2).lower() in SKIP and not part.endswith('/>'):
                depth[m.group(2).lower()] += -1 if m.group(1) else 1
            out.append(part); continue
        if any(depth.values()) or len(part.strip()) < 7 or not JA.search(part):
            out.append(part); continue
        lead = re.match(r'\s*', part).group(0); tail = re.search(r'\s*$', part).group(0)
        chunks = P.parse(part[len(lead):len(part) - len(tail)]); n += len(chunks) - 1
        out.append(lead + '<wbr>'.join(chunks) + tail)
    s = ''.join(out)
    # かっこの内側・句読点の前では折り返さない
    s = re.sub(r'([（「『【〈《])<wbr>', r'\1', s)
    s = re.sub(r'<wbr>([）」』】〉》、。・])', r'\1', s)
    for w in KEEP:
        for i in range(1, len(w)):
            s = s.replace(w[:i] + '<wbr>' + w[i:], w)
    return s, n


def main():
    files = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not files: sys.exit(__doc__)
    for p in files:
        s = open(p, encoding='utf-8').read()
        if '<wbr>' in s:
            if '--force' not in sys.argv:
                print('飛ばした（もう入っている）:', p); continue
            s = s.replace('<wbr>', '')
        s, n = add_wbr(s)
        open(p, 'w', encoding='utf-8').write(s)
        css = 'ある' if 'keep-all' in s else 'ない → CSS に1行足す（上の説明）'
        print(f'入れた: {p}（{n}か所）  keep-all: {css}')


if __name__ == '__main__':
    main()
