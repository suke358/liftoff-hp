#!/usr/bin/env python3
"""新しいお客さんの準備セットを一括で作る（Lift-Off）  2026/10/8 作成

使い方:
  初回の打ち合わせの前：
    python3 new_client.py <英字の短い名前> <お店の名前> [<置く場所>]
      例）python3 new_client.py hiyori "よもぎ蒸しサロン hiyori"
      置く場所を省くと ~/Desktop/03_Lift-off事業/1_HP制作/2_お客さん に作る（2026/10/9 変更。前は ~/Desktop を指定していた）

  2回目の打ち合わせの前（初回の資料を「5 済んだ打ち合わせ」に移し、2回目の道具を入れる）：
    python3 new_client.py <英字の短い名前> <お店の名前> [<置く場所>] --second

  料金表は ~/Desktop/03_Lift-off事業/1_HP制作/1_お客さまに渡す資料/1_料金表（10月9日版）.pdf からコピーする（見つからないときは ⚠️ を出して先へ進む）

できるもの:
  <お店の名前>_今日の打ち合わせ/
    1 次の打ち合わせで使うもの/ … 入力シート（Mac で入力・自動保存・「Claudeに渡す用にコピー」）、見本帳のリンク、料金表
    2 名刺の見本/  3 ロゴ案/  4 もらった写真/  5 済んだ打ち合わせ/  6 LINEの下書き/  7 古いもの（使わない）/
    はじめに読む（フォルダの中身）.txt
  ＋ 画面に「お客さんのファイル（claude/お客さん/〇〇.md）のひな形」と「顧客管理シートに足す1行」を出す
"""
import sys, os, shutil, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, 'templates')
SAMPLES = 'https://liftoff-hp.liftoff-358.workers.dev/samples/'
BASE_DEFAULT = '~/Desktop/03_Lift-off事業/1_HP制作/2_お客さん'  # 打ち合わせフォルダを作る場所（置く場所を省いたとき）
PRICE_PDF = '~/Desktop/03_Lift-off事業/1_HP制作/1_お客さまに渡す資料/1_料金表（10月9日版）.pdf'  # 料金表のコピー元（版が変わったらここを直す）
DIRS = ['1 次の打ち合わせで使うもの', '2 名刺の見本', '3 ロゴ案', '4 もらった写真', '5 済んだ打ち合わせ', '6 LINEの下書き', '7 古いもの（使わない）']

def fill(name, slug, shop):
    s = open(os.path.join(TPL, name), encoding='utf-8').read()
    return s.replace('{{SHOP}}', shop).replace('{{SLUG}}', slug)

def webloc(path, url):
    open(path, 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        f'<plist version="1.0"><dict><key>URL</key><string>{url}</string></dict></plist>\n')

def readme(root, shop, second):
    today = datetime.date.today().strftime('%Y/%m/%d')
    first = ('   1 2回目の打ち合わせ_チェック表（Macで書き込める・印刷も可）.html … チェックと答えを書き込める →「Claudeに渡す用にコピー」\n'
             '   2 取り決めメモ（2部印刷する）… Claude が作って入れる\n'
             '   3 予約メニュー入力シート（Macで開く）.html … その場で入力 →「Claudeに渡す用にコピー」→ チャットに貼る\n'
             '   4 Googleマップに入れる文.txt ／ 5 Googleマップ用の写真 … Claude が作って入れる\n') if second else (
             '   1 初回の打ち合わせ_入力シート（Macで開く）.html … 話しながら入力 →「Claudeに渡す用にコピー」→ チャットに貼る\n'
             '   2 デザイン見本帳を開く.webloc … テイストを番号で選んでもらう\n'
             '   3 料金表_A4.pdf … 印刷して持っていく（「1_お客さまに渡す資料」の料金表を自動でコピー）\n'
             '   4 お見積もり（Macで開く・印刷やPDFにできる）.html … その場で選ぶと金額が出る →「印刷 / PDFにする」（マニュアル 22）\n')
    txt = f'''【{shop}_今日の打ち合わせ フォルダの中身】{today} 作成（new_client.py）

1 次の打ち合わせで使うもの … {"2回目" if second else "初回"}の打ち合わせで使うもの。使う順に番号
{first}2 名刺の見本 … 名刺の見本10枚（ご契約のお店へのサービス。決定事項）
3 ロゴ案 … ロゴを作るとき
4 もらった写真 … AirDrop でもらった写真をここへ（Claude が一覧画像・書き出しをする。マニュアル 18）
5 済んだ打ち合わせ … 終わった打ち合わせの資料・結果
6 LINEの下書き … 送る前の文
7 古いもの（使わない）… 前の版など。いらなければ消してよい

入力シートの保存：入力は開いたブラウザに自動で残る（いつも同じアプリで開く）。終わったら「Claudeに渡す用にコピー」→ チャットに貼る
'''
    open(os.path.join(root, 'はじめに読む（フォルダの中身）.txt'), 'w', encoding='utf-8').write(txt)

def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if len(a) < 2: print(__doc__); sys.exit(1)
    slug, shop, base = a[0], a[1], os.path.expanduser(a[2] if len(a) >= 3 else BASE_DEFAULT)
    second = '--second' in sys.argv
    root = os.path.join(base, f'{shop}_今日の打ち合わせ')
    for d in DIRS: os.makedirs(os.path.join(root, d), exist_ok=True)
    nxt = os.path.join(root, DIRS[0])
    made = []
    if second:
        done = os.path.join(root, DIRS[4], '初回の打ち合わせ')
        os.makedirs(done, exist_ok=True)
        for f in os.listdir(nxt):
            if f.startswith('.'): continue
            shutil.move(os.path.join(nxt, f), os.path.join(done, f)); made.append(f'移動：{f} → 5 済んだ打ち合わせ/初回の打ち合わせ')
        out = [('second.html', '1 2回目の打ち合わせ_チェック表（Macで書き込める・印刷も可）.html'),
               ('menu.html', f'3 {shop}_予約メニュー入力シート（Macで開く）.html')]
        os.makedirs(os.path.join(nxt, '5 Googleマップ用の写真'), exist_ok=True)
    else:
        out = [('first.html', '1 初回の打ち合わせ_入力シート（Macで開く）.html')]
        webloc(os.path.join(nxt, '2 デザイン見本帳を開く.webloc'), SAMPLES); made.append('2 デザイン見本帳を開く.webloc')
        est = os.path.join(HERE, 'お見積もりを作る.html')
        if os.path.exists(est):
            shutil.copy(est, os.path.join(nxt, '4 お見積もり（Macで開く・印刷やPDFにできる）.html')); made.append('4 お見積もり（Macで開く・印刷やPDFにできる）.html')
        price = os.path.expanduser(PRICE_PDF)
        if os.path.exists(price):
            shutil.copy(price, os.path.join(nxt, '3 料金表_A4.pdf')); made.append('3 料金表_A4.pdf')
        else:
            print(f'⚠️ 料金表が見つかりません（コピーしていません）：{price}')
    for tpl, name in out:
        p = os.path.join(nxt, name)
        if os.path.exists(p): made.append(f'（そのまま）{name} … もうあるので上書きしない'); continue
        open(p, 'w', encoding='utf-8').write(fill(tpl, slug, shop)); made.append(name)
    readme(root, shop, second)
    print(f'✅ 作りました：{root}')
    for m in made: print('   ・' + m)
    if not second:
        print(f'''
---- お客さんのファイルのひな形（claude/お客さん/{slug}.md。Claude がプロジェクトに作る）----
# お客さん：{shop}

## 今の状態（{datetime.date.today():%Y/%m/%d}）
- 段階：声かけ／初回の打ち合わせ待ち
- いま待っていること：
- 次にやること：初回の打ち合わせ（入力シート）

## 基本
- 店名（正式）・読み方：
- 住所：／電話：／営業時間：／定休日：／駐車場：
- 連絡手段：
- サイトのファイル：Mac ~/src/{slug}-website ／ 試作（お客さんに見せる先）：https://{slug}-website.liftoff-358.workers.dev/
- 打ち合わせフォルダ：デスクトップ「{shop}_今日の打ち合わせ」

## 条件（決定事項との違いだけ書く）
-

## 確認事項

## 進み具合
- {datetime.date.today():%Y/%m/%d}：準備セットを作成（new_client.py）

---- 顧客管理シート「お店」タブに足す1行（Claude が足す）----
お店：{shop}｜段階：声かけ｜いま待っていること：初回の打ち合わせの日程｜お店のファイル：claude/お客さん/{slug}.md
''')

if __name__ == '__main__':
    main()
