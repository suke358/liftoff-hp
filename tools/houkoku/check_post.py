#!/usr/bin/env python3
"""Googleマップの投稿・口コミ返信の文を、出す前に確かめる（Lift-Off）  2026/10/22 作成（claude/商品/Googleマップの投稿と口コミ返信.md の「書かないこと」）

使い方:
  python3 check_post.py <文のファイル>        … ファイルの文を調べる（1つの文ごとに行番号を出す）
  python3 check_post.py                       … 貼った文を調べる（貼ってから Ctrl+D）
  echo "文" | python3 check_post.py           … 流しこんでもよい

調べること（あれば ❌ と行番号。なければ ✅）:
  1. 電話番号（0 から始まる数字とハイフンの並び）
  2. メールアドレス
  3. URL（http・https・www.）
  4. @ ではじまる ID
  5. 使ってはいけない言葉（check_site.py の NG_WORDS と同じ一覧を読みこむ。ここには書かない）
  6. 「割引」「プレゼント」「お礼」と「口コミ」「レビュー」が同じ文にある（口コミと引きかえのお礼に見える）
"""
import sys, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # tools/ にある check_site.py を読む
try:
    from check_site import NG_WORDS
except Exception as ex:
    sys.exit('❌ check_site.py の NG_WORDS が読めません（tools/check_site.py があるか確かめる）：' + str(ex))

RULES = [
    ('電話番号', re.compile(r'(?<![\d-])0\d{1,4}-\d{1,4}-\d{3,4}(?![\d-])|(?<!\d)0\d{9,10}(?!\d)')),
    ('メールアドレス', re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')),
    ('URL', re.compile(r'https?://\S+|(?<![\w.])www\.\S+')),
    ('@ ではじまる ID', re.compile(r'(?<![\w.+-])@[A-Za-z0-9_.]{2,}')),
]
THANKS = re.compile(r'割引|プレゼント|お礼')
REVIEW = re.compile(r'口コミ|レビュー')
SPLIT = re.compile(r'(?<=[。！!？?\n])')

def check(text):
    out = []   # (行番号, 種類, 見つかった文字)
    lines = text.split('\n')
    for i, line in enumerate(lines, 1):
        for name, rx in RULES:
            for m in rx.finditer(line):
                out.append((i, name, m.group(0)))
        for w, why in NG_WORDS.items():
            if w in line: out.append((i, f'使ってはいけない言葉「{w}」（{why}）', w))
        for sent in SPLIT.split(line):
            if THANKS.search(sent) and REVIEW.search(sent):
                out.append((i, '口コミと引きかえのお礼に見える（割引・プレゼント・お礼 と 口コミ・レビュー が同じ文）', sent.strip()[:40]))
    return out

def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if not os.path.exists(path): sys.exit('❌ ファイルがありません：' + path)
        text = open(path, encoding='utf-8').read()
        label = os.path.basename(path)
    else:
        if sys.stdin.isatty(): print('文を貼って、最後に Ctrl+D を押してください：')
        text = sys.stdin.read(); label = '貼った文'
    if not text.strip(): sys.exit('❌ 文がありません')
    found = check(text)
    if found:
        print(f'❌ {label}：出す前に直す所が {len(found)} か所')
        for i, name, s in found: print(f'  {i}行目：{name} → {s}')
        sys.exit(1)
    print(f'✅ {label}：書いてはいけないもの（電話・メール・URL・@ID・使ってはいけない言葉・口コミと引きかえのお礼）はありません')

if __name__ == '__main__':
    main()
