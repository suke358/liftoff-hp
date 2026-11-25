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
KEEP = ['よもぎ', 'ホームページ', 'Googleマップ', '目立ちにくく', 'ぽたぽた', 'はがれ', 'しにくい', 'ほぐして',  # 11/17 見本の悩みの文で切れた言葉を足した
        '日替わり', 'ひとつずつ', '1本ずつ', '少しずつ', '贈りもの', 'ながめる', 'たのしんで', 'うかがい', 'うかがえ',
        'へこみ', '軽自動車', 'あおぞら', '送り迎え', '取り置き', '1〜2回',  # 11/17 夜 残り13見本で切れた言葉を足した（別の目の指摘）
        '今日']  # 11/18 残り18見本で切れた言葉を足した（別の目の指摘：wa の「今/日」）
PAREN_MAX = 12  # かっこを 1 かたまりにする長さ（かっこを含む字数。2026/11/25 B6。長いものは狭い画面で入りきらず、かえって変な所で切られるので中で折り返す）
JA = re.compile(r'[぀-ヿ㐀-鿿]')


def paren_glue(t):
    """かっこの折り返し（2026/11/25 B6：定休日「不定休(LINE・…)」の「)」1字だけが次の行に落ちた）。
    ①かっこの中が短い（PAREN_MAX 字まで）なら 1 かたまり（中の <wbr> を消し、かっこの前で折り返せるようにする）
    ②閉じかっこは前の 1 字と折り返さない枠（nw）でくっつける（狭い所で言葉が入りきらず、最後の 1 字で切られても「)」だけにならない）"""
    def one(m):
        g = m.group(0).replace('<wbr>', '')
        if len(g) > PAREN_MAX: return m.group(0)
        return ('<wbr>' if m.start() and JA.match(m.string[m.start() - 1]) else '') + g
    t = re.sub(r'[（(][^（）()<>]*(?:<wbr>[^（）()<>]*)+[）)]', one, t)
    return re.sub(r'(?:<wbr>)?([^\s<>（）()])(?:<wbr>)?([）)])', r'<span class="nw">\1\2</span>', t)


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
        out.append(lead + paren_glue('<wbr>'.join(chunks)) + tail)
    s = ''.join(out)
    # かっこの内側・句読点の前では折り返さない
    s = re.sub(r'([（「『【〈《(])<wbr>', r'\1', s)
    s = re.sub(r'<wbr>([）」』】〉》、。・)])', r'\1', s)  # 半角の「)」も（2026/11/25 B6）
    for w in KEEP:
        for i in range(1, len(w)):
            s = s.replace(w[:i] + '<wbr>' + w[i:], w)
    # 折り返さない枠（class="nw"）の中には入れない。<wbr> は nowrap の中でも折り返してしまうため（10/8 つまずき）
    s = re.sub(r'(<span class="nw">)(.*?)(</span>)', lambda m: m.group(1) + m.group(2).replace('<wbr>', '') + m.group(3), s, flags=re.S)
    return s, n


def main():
    files = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not files: sys.exit(__doc__)
    for p in files:
        s = open(p, encoding='utf-8').read()
        if '<wbr>' in s:
            if '--force' not in sys.argv:
                # 2026/10/30：ひな形（make_site.py）で作ったページは最初から <wbr> が10個ほど入っているので、ここで必ず飛ばされる。次の手を出す
                n0 = s.count('<wbr>')
                if 'tools/make_site.py で作った' in s:
                    print(f'飛ばした（もう入っている・{n0}個）: {p}\n  → このページはひな形（make_site.py）で作ったものです。budoux を入れたあとは、同じ設定で make_site.py を実行して作り直すと、文の折り返しが全部入ります（例：cd サイトのフォルダ && python3 ~/src/liftoff-hp/tools/make_site.py site.json .）')
                else:
                    print(f'飛ばした（もう入っている・{n0}個）: {p}\n  → 入れ直すときは --force を付けます（先に <wbr> を消してから入れ直す）')
                continue
            s = s.replace('<wbr>', '')
        s, n = add_wbr(s)
        open(p, 'w', encoding='utf-8').write(s)
        css = 'ある' if 'keep-all' in s else 'ない → CSS に1行足す（上の説明）'
        print(f'入れた: {p}（{n}か所）  keep-all: {css}')


if __name__ == '__main__':
    main()
