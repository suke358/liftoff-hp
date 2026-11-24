#!/usr/bin/env python3
"""配置の型（"layout":"a1trace"）の「つまみ」をくじ（乱数）で選ぶ（2026/11/24。想永 _8 の くじ.py を道具に移した）
tools/templates/配置の型.md の「変えてよい所（つまみ）」の表と同じ幅から選ぶ。種（seed）を同じにすれば同じ答え＝再現できる。

使い方:
  python3 tools/kuji.py [種]      → つまみ（knobs）の JSON を表示する。種を省くと今の時刻から決めて表示する
  site.json に "knobs_seed": 1124 と書けば、make_site.py が同じくじを引く（"knobs": {...} で 1 つずつ上書きできる）

くじを引く順番は _8 の くじ.py と同じ（種 1124 → _8・_9 と同じ答え）。順番を変えると前の種で同じ答えが出なくなるので変えない。
値の意味（trace_a1.py が読む）：
  p1＝1画面目の写真1の幅％／gap＝すき間％／close＝寄りの写真を置く側（左・右）／word_x＝大きな 1 語の左からの位置％／word_rem＝1 語の大きさ rem／
  word_kind＝1 語は店名か・お店の言葉か（文は site.json の a1_words で決める。くじは種類だけ）／bg・gapc・band・ink＝地・すき間・帯・濃い色／
  vt2・vt3・vt5＝縦書きの 1 語の左右（2画面目・3段目・5段目）／squares＝正方形の枚数（2画面目1枚・4段目2枚／2画面目2枚・4段目1枚）／
  stag_top・stag_drop・stag_ratio＝ずらした 2 枚（上に来る方・下げる幅px・割合）／order＝段の順／tracking＝見出しの字間em／
  swap＝写真の役の入れかえ（そのまま／寄り↔並び を入れかえ／正方形3枚の順を回す）／shift＝切る位置のずらし％"""
import json, random, sys, time

GROUNDS = [('生成り', '#f1efe9', '#e4e1da'), ('薄い灰', '#ececea', '#dedddb'), ('白', '#fafaf8', '#e9e8e4')]
BANDS = [('青灰', '#4b5d6b'), ('緑灰', '#5f6e66'), ('茶灰', '#6b5e55'), ('えんじ灰', '#6b4e55')]
INKS = [('黒', '#26292b'), ('濃い茶', '#2a2623'), ('濃い紺', '#22272e')]
# つまみごとの選べる値（check_site・直す係もこの表で「決まりの中か」を見る）
CHOICES = {
    'p1': [30, 32, 34, 36, 38, 40], 'gap': [6, 7, 8, 9], 'close': ['左', '右'], 'word_x': [32, 35, 38, 41, 44], 'word_rem': [5.6, 6.0, 6.4, 6.8, 7.2],
    'word_kind': ['店名の短い形（2〜4字）', 'お店の言葉1つ（商品や空気を表す 2〜4 字）'],
    'vt2': ['右', '左'], 'vt3': ['左', '右'], 'vt5': ['間', '右端'],
    'squares': ['2画面目1枚・4段目2枚', '2画面目2枚・4段目1枚'],
    'stag_top': ['左', '右'], 'stag_drop': [80, 100, 120, 140, 160], 'stag_ratio': ['43／45', '45／43'],
    'order': ['商品 → はじめて', 'はじめて → 商品'], 'tracking': [0.08, 0.14, 0.2, 0.3],
    'swap': ['そのまま', '寄り↔並び を入れかえ', '正方形3枚の順を回す'], 'shift': [-20, -10, 0, 10, 20],
    'bg': [g[1] for g in GROUNDS], 'gapc': [g[2] for g in GROUNDS], 'band': [b[1] for b in BANDS], 'ink': [d[1] for d in INKS],
}
# 既定（_8 のつまみ。種を書かず knobs も書かないときはこれ）
DEFAULT = {'p1': 34, 'gap': 8, 'close': '左', 'word_x': 38, 'word_rem': 6.4, 'word_kind': '店名の短い形（2〜4字）',
           'bg': '#f1efe9', 'gapc': '#e4e1da', 'band': '#4b5d6b', 'ink': '#26292b',
           'vt2': '右', 'vt3': '左', 'vt5': '間', 'squares': '2画面目1枚・4段目2枚',
           'stag_top': '左', 'stag_drop': 120, 'stag_ratio': '43／45', 'order': '商品 → はじめて', 'tracking': 0.08,
           'swap': 'そのまま', 'shift': 0}

def draw(seed):
    """種からつまみを引く（引く順番は _8 の くじ.py と同じ）"""
    r = random.Random(int(seed))
    g = r.choice(GROUNDS); b = r.choice(BANDS); d = r.choice(INKS)
    p1 = r.choice(CHOICES['p1']); gap = r.choice(CHOICES['gap'])
    k = {'seed': int(seed), 'p1': p1, 'gap': gap, 'close': r.choice(CHOICES['close']), 'word_x': r.choice(CHOICES['word_x']), 'word_rem': r.choice(CHOICES['word_rem']),
         'word_kind': r.choice(CHOICES['word_kind']),
         'bg': g[1], 'gapc': g[2], 'band': b[1], 'ink': d[1], '_色': '%s × %s × %s' % (g[0], b[0], d[0]),
         'vt2': r.choice(CHOICES['vt2']), 'vt3': r.choice(CHOICES['vt3']), 'vt5': r.choice(CHOICES['vt5']),
         'squares': r.choice(CHOICES['squares']),
         'stag_top': r.choice(CHOICES['stag_top']), 'stag_drop': r.choice(CHOICES['stag_drop']), 'stag_ratio': r.choice(CHOICES['stag_ratio']),
         'order': r.choice(CHOICES['order']), 'tracking': r.choice(CHOICES['tracking']),
         'swap': r.choice(CHOICES['swap']), 'shift': r.choice(CHOICES['shift'])}
    return k

def validate(k):
    """つまみが決まりの中か。戻り：外れている物の一覧（空なら OK）。_ で始まる物と seed は見ない"""
    bad = []
    for key, v in (k or {}).items():
        if key.startswith('_') or key == 'seed': continue
        if key not in CHOICES: bad.append('知らないつまみ：%s' % key)
        elif v not in CHOICES[key]: bad.append('%s の値 %r は選べる中にありません（%s）' % (key, v, '・'.join(map(str, CHOICES[key]))))
    return bad

if __name__ == '__main__':
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else int(time.time()) % 100000
    print(json.dumps(draw(seed), ensure_ascii=False, indent=1))
