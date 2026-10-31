#!/bin/bash
# 小さい修正（文字の小さな修正・写真の入れ替え）だけを、許可なしで main に出す  2026/10/31 作成（決定 2026/10/31。決定事項 02・マニュアル 20・26）
#
# ふつうの直しは今までどおり：直す → commit → preview_push.sh → 確認用URLで見る → 許可をもらって main へ push
# この道具は preview を通さず main に直接出すので、出してよい直しを厳しくしぼる（下の「止める条件」）。1つでも当てはまれば push せず止まる
#
# 使い方:  cd サイトのフォルダ && bash ~/src/liftoff-hp/tools/push_small.sh [--received "HH:MM"] "何を変えたか"
#   例:    bash ~/src/liftoff-hp/tools/push_small.sh --received "10:12" "トップの営業時間を 10:00〜17:00 に直した"
#   --received は依頼を受けた時刻（LINE が来た時刻）。書かないと「未入力」と記録する
#
# 止める条件（push せず、理由を出して終了コード 1。作業メモにも「push していない・理由」を書く）
#   1. git のフォルダでない  2. 今のブランチが main でない  3. fetch のあと HEAD が origin/main の続き（fast-forward）でない
#   4. commit していない直しがある（.DS_Store と未追跡 ?? は除く）  5. origin/main..HEAD の commit が 4つ以上（0 のときも止める）
#   6. 変えたファイルに、削除・名前の変更／wrangler.jsonc .assetsignore _redirects _headers package.json package-lock.json／
#      tools/ .github/ gas/ src/ yoyaku* の中／拡張子 .css .js .mjs .ts .py .sh .php .yml .yaml .jsonc .toml がある
#   7. HTML の変更行数（追加＋削除）が 30 行を超える  8. check_site.py（この道具と同じ tools/ のもの）で ❌ が 1つでもある・結果が読み取れない
#   9. 「何を変えたか」が空
#  10. check_site.py に「⚠️ [言葉]」（効果をうたう言葉・言い切る言葉）が 1つでもある（2026/10/31 ユーザー決定。他の ⚠️ は止めず、作業メモに書くだけ）
#
# 通ったら：git push origin main（--force は絶対に付けない）→ 公開URL https://<name>.liftoff-358.workers.dev/ の index.html と
#   変えた画像（images/・img/ の中）が HEAD と同じ中身になるまで最大 5 分待つ → 作業メモ（~/src/作業メモ.md）に書く
#   作業メモには「強み記録用」として、依頼を受けた時刻 → 公開を確認した時刻 → その差（分）も書く（更新が早いことの記録）
#   公開URLの確認が時間切れなら「push は済み・確認できず」と書いて終了コード 1
#
# テスト用に上書きできる環境変数はこの2つだけ（本物の動きには影響しない）
#   PUSH_SMALL_MEMO      作業メモの書き込み先（ふだんは ~/src/作業メモ.md）
#   PUSH_SMALL_BASE_URL  公開URLの確認先（ふだんは wrangler.jsonc の name から決まる）
set -u
DOMAIN='liftoff-358.workers.dev'
WAIT_SEC=300
MAX_COMMITS=3
MAX_HTML_LINES=30
MEMO="${PUSH_SMALL_MEMO:-$HOME/src/作業メモ.md}"
TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---- 引数（文字として扱うだけ。eval はしない）----
RECEIVED='未入力'
MSG=''
while [ $# -gt 0 ]; do
  case "$1" in
    --received)
      if [ $# -ge 2 ]; then shift; RECEIVED="$1"; fi ;;
    --received=*)
      RECEIVED="${1#--received=}" ;;
    *)
      if [ -z "$MSG" ]; then MSG="$1"; else MSG="$MSG $1"; fi ;;
  esac
  shift
done
[ -n "$RECEIVED" ] || RECEIVED='未入力'

now_stamp() { date '+%Y/%m/%d %H:%M'; }
SITE='（サイト名 不明）'

# 止める：理由を出し、作業メモに「push していない」を書き、終了コード 1
stop() {
  echo
  echo "❌ push していません：$1"
  {
    echo
    echo "## $(now_stamp)　${SITE}　push_small.sh：push していない"
    echo "- 理由：$1"
    echo "- 何を変えたか：${MSG:-（空）}"
    echo "- 場所：$(pwd)"
  } >> "$MEMO" 2>/dev/null || echo "⚠️ 作業メモに書けませんでした: $MEMO"
  exit 1
}

# ---- 1. git のフォルダか ----
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || stop "ここは git のフォルダではありません: $(pwd)。サイトのフォルダに cd してから動かしてください"
cd "$ROOT" || stop "フォルダに入れません: $ROOT"
SITE="$(basename "$ROOT")"

# ---- 9. 「何を変えたか」が空 ----
[ -n "$(printf '%s' "$MSG" | tr -d '[:space:]')" ] || stop "「何を変えたか」が空です。使い方: bash ~/src/liftoff-hp/tools/push_small.sh [--received \"HH:MM\"] \"何を変えたか\""

# ---- wrangler.jsonc の name → 公開URL ----
[ -f wrangler.jsonc ] || stop "wrangler.jsonc がありません（Cloudflare の設定）。このフォルダは Cloudflare に出すサイトではないようです: $ROOT"
NAME="$(sed 's#//.*$##' wrangler.jsonc | tr -d '\n' | sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
[ -n "$NAME" ] || stop "wrangler.jsonc に \"name\" が見つかりません"
SITE="$NAME"
BASE_URL="${PUSH_SMALL_BASE_URL:-https://${NAME}.${DOMAIN}/}"
case "$BASE_URL" in */) ;; *) BASE_URL="${BASE_URL}/" ;; esac

echo "サイト: ${NAME}（${ROOT}）"
echo "何を変えたか: ${MSG}"
echo "依頼を受けた時刻: ${RECEIVED}"

# ---- 2. ブランチは main か ----
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
[ "$BRANCH" = "main" ] || stop "今のブランチが main ではありません（${BRANCH}）。この道具は main からだけ出します"

# ---- 3. origin/main の続き（fast-forward）か ----
git fetch origin main >/dev/null 2>&1 || stop "origin から取ってこられませんでした（git fetch origin main）。ネットか origin の設定を確かめる"
git rev-parse --verify -q origin/main >/dev/null || stop "origin/main がありません（まだ main を push していないリポジトリ？）"
git merge-base --is-ancestor origin/main HEAD || stop "origin/main が先に進んでいます（HEAD がその続きになっていない）。git pull してから、もう一度"

# ---- 4. commit していない直し ----
DIRTY="$(git -c core.quotepath=false status --short | grep -v 'DS_Store' | grep -v '^??')"
[ -z "$DIRTY" ] || stop "commit していない直しがあります。commit するか元に戻してから：
$DIRTY"

# ---- 5. commit の数 ----
N_COMMITS="$(git rev-list --count origin/main..HEAD)"
[ "$N_COMMITS" -ge 1 ] || stop "出す commit がありません（origin/main と同じ）"
[ "$N_COMMITS" -le "$MAX_COMMITS" ] || stop "origin/main より先の commit が ${N_COMMITS} つあります（${MAX_COMMITS} つまで）。大きな直しは preview から出してください"
COMMITS="$(git log --oneline origin/main..HEAD)"
STAT="$(git -c core.quotepath=false diff --stat origin/main HEAD)"

# ---- 6. 変えたファイルの種類 ----
BAD=''
while IFS="$(printf '\t')" read -r st f1 f2; do
  [ -n "$st" ] || continue
  case "$st" in
    D*) BAD="$BAD
  削除：$f1" ;;
    R*) BAD="$BAD
  名前の変更：$f1 → $f2" ;;
    C*) BAD="$BAD
  コピー：$f1 → $f2" ;;
  esac
done <<EOF
$(git -c core.quotepath=false diff --name-status -M origin/main HEAD)
EOF
FILES="$(git -c core.quotepath=false diff --name-only -M origin/main HEAD)"
while IFS= read -r f; do
  [ -n "$f" ] || continue
  base="${f##*/}"
  case "$base" in
    wrangler.jsonc|.assetsignore|_redirects|_headers|package.json|package-lock.json) BAD="$BAD
  公開の設定ファイル：$f" ;;
  esac
  case "/$f" in
    */tools/*|*/.github/*|*/gas/*|*/src/*|*/yoyaku*/*) BAD="$BAD
  道具・予約システムの中：$f" ;;
  esac
  case "$base" in
    *.css|*.js|*.mjs|*.ts|*.py|*.sh|*.php|*.yml|*.yaml|*.jsonc|*.toml) BAD="$BAD
  見た目・動き・設定のコード：$f" ;;
  esac
done <<EOF
$FILES
EOF
[ -z "$BAD" ] || stop "小さい修正の範囲の外のファイルがあります（preview から出してください）：$BAD"

# ---- 7. HTML の変更行数 ----
HTML_LINES="$(git diff --numstat origin/main HEAD -- '*.html' | awk '$1!="-" && $2!="-" {s+=$1+$2} END {print s+0}')"
[ "$HTML_LINES" -le "$MAX_HTML_LINES" ] || stop "変更が大きいので preview から出してください（HTML の変更が ${HTML_LINES} 行。${MAX_HTML_LINES} 行まで）"
echo "変えたファイル（HTML ${HTML_LINES} 行・commit ${N_COMMITS} つ）:"
echo "$STAT"

# ---- 8. check_site.py ----
CHECK="$TOOLS_DIR/check_site.py"
[ -f "$CHECK" ] || stop "check_site.py が見つかりません: $CHECK"
TMP="$(mktemp -d)"
echo "→ check_site.py を回します（--no-browser）"
python3 "$CHECK" "$ROOT" --no-browser > "$TMP/check.txt" 2>&1
CHECK_RC=$?
CHECK_LINE="$(grep -o '❌ 直す [0-9][0-9]*' "$TMP/check.txt" | tail -n 1)"
if [ -z "$CHECK_LINE" ]; then
  stop "check_site.py の結果が読み取れませんでした（終了コード ${CHECK_RC}）。出力の先頭：
$(head -n 5 "$TMP/check.txt")"
fi
N_NG="${CHECK_LINE##* }"
N_WARN="$(grep -o '⚠️ 確かめる [0-9][0-9]*' "$TMP/check.txt" | tail -n 1)"; N_WARN="${N_WARN##* }"
N_OK="$(grep -o '✅ 問題なし [0-9][0-9]*' "$TMP/check.txt" | tail -n 1)"; N_OK="${N_OK##* }"
WARN_ITEMS="$(grep '^⚠️' "$TMP/check.txt" | sed 's/^/    /')"
NG_ITEMS="$(grep '^❌ \[' "$TMP/check.txt" | sed 's/^/  /')"
CHECK_SUMMARY="❌ ${N_NG}　⚠️ ${N_WARN:-?}　✅ ${N_OK:-?}"
echo "  check_site.py: ${CHECK_SUMMARY}"
if [ "$N_NG" != "0" ] || [ "$CHECK_RC" != "0" ]; then
  stop "check_site.py で ❌ が ${N_NG}（終了コード ${CHECK_RC}）。直してから：
$NG_ITEMS"
fi
# ---- 10. ⚠️ [言葉]（効果をうたう言葉など）は止める。他の ⚠️ は止めない ----
KOTOBA_ITEMS="$(grep '^⚠️ \[言葉\]' "$TMP/check.txt" | sed 's/^/  /')"
if [ -n "$KOTOBA_ITEMS" ]; then
  stop "効果をうたう言葉などの ⚠️ があります。preview から出して、チャットで確かめてください：
$KOTOBA_ITEMS"
fi

# ---- push（--force は絶対に付けない）----
echo "→ origin の main に出します（git push origin main）"
git push origin main || stop "push できませんでした（git push origin main）"
HEAD_SHORT="$(git rev-parse --short HEAD)"

# ---- 公開URLで確かめる：index.html と、変えた画像 ----
TARGETS=''
if git cat-file -e HEAD:index.html 2>/dev/null; then TARGETS='index.html'; fi
while IFS= read -r f; do
  [ -n "$f" ] || continue
  case "$f" in
    images/*|img/*)
      case "${f##*/}" in
        *.jpg|*.jpeg|*.png|*.gif|*.webp|*.svg|*.avif)
          if [ -f .assetsignore ] && grep -qx -- "$f" .assetsignore; then continue; fi
          TARGETS="$TARGETS
$f" ;;
      esac ;;
  esac
done <<EOF
$FILES
EOF

RESULT=''
check_once() {   # 全部が HEAD と同じ中身なら 0
  ok=0; RESULT=''
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    if [ "$p" = "index.html" ]; then url="$BASE_URL"; else url="${BASE_URL}${p}"; fi
    git show "HEAD:$p" > "$TMP/head.bin" 2>/dev/null || { RESULT="$RESULT
  $p：❌ HEAD にありません"; ok=1; continue; }
    code=$(curl -s -o "$TMP/pub.bin" -w '%{http_code}' "$url")
    if [ "$code" = "200" ] && cmp -s "$TMP/pub.bin" "$TMP/head.bin"; then
      RESULT="$RESULT
  $p：✅ ${code}・HEAD と同じ"
    else
      RESULT="$RESULT
  $p：⚠️ ${code}・まだ HEAD と違う"; ok=1
    fi
  done <<EOF
$TARGETS
EOF
  return $ok
}

echo "→ 公開URLに出るのを待ちます（最大 ${WAIT_SEC} 秒）: $BASE_URL"
start=$(date +%s); PUBLISHED=no
while :; do
  if check_once; then PUBLISHED=yes; break; fi
  if [ $(( $(date +%s) - start )) -ge $WAIT_SEC ]; then break; fi
  sleep 15
done
took=$(( $(date +%s) - start ))
CONFIRMED_AT="$(date '+%H:%M')"

# ---- 依頼から公開までの時間（分）----
DIFF_TEXT='—（依頼を受けた時刻が未入力）'
case "$RECEIVED" in
  [0-9]:[0-9][0-9]|[0-9][0-9]:[0-9][0-9])
    rec_min=$(( 10#${RECEIVED%%:*} * 60 + 10#${RECEIVED##*:} ))
    now_min=$(( 10#$(date +%H) * 60 + 10#$(date +%M) ))
    diff=$(( now_min - rec_min )); [ $diff -lt 0 ] && diff=$(( diff + 1440 ))
    DIFF_TEXT="${diff} 分" ;;
  未入力) ;;
  *) DIFF_TEXT="—（時刻の形が HH:MM ではない：${RECEIVED}）" ;;
esac

if [ "$PUBLISHED" = "yes" ]; then
  PUB_TEXT="✅ HEAD と同じ中身が出ています（${took}秒後）"
  TSUYOMI="依頼を受けた時刻 ${RECEIVED} → 公開URLで確認 ${CONFIRMED_AT} → 依頼から公開まで ${DIFF_TEXT}"
else
  PUB_TEXT="⚠️ push は済み・確認できず（${WAIT_SEC}秒待っても HEAD と同じにならない。少し待って curl で確かめる）"
  TSUYOMI="依頼を受けた時刻 ${RECEIVED} → 公開URLで確認できず（${CONFIRMED_AT} 時点）"
fi

echo
echo "公開URL: $BASE_URL"
echo "  $PUB_TEXT"
echo "$RESULT"
echo "  強み記録用: $TSUYOMI"

# ---- 作業メモに書く ----
{
  echo
  echo "## $(now_stamp)　${SITE}　push_small.sh：小さい修正を main に出した（強み記録用）"
  echo "- 何を変えたか：${MSG}"
  echo "- commit：${HEAD_SHORT}（origin/main..HEAD ${N_COMMITS} つ → git push origin main 済み）"
  echo "$COMMITS" | sed 's/^/    /'
  echo "- 変えたファイル（git diff --stat）："
  echo "$STAT" | sed 's/^/    /'
  echo "- check_site.py（--no-browser）：${CHECK_SUMMARY}"
  if [ -n "$WARN_ITEMS" ]; then echo "  ⚠️ の内容："; echo "$WARN_ITEMS"; fi
  echo "- 公開URL：${BASE_URL} ${PUB_TEXT}"
  echo "$RESULT" | sed '/^$/d; s/^/  /'
  echo "- 強み記録用：${TSUYOMI}"
} >> "$MEMO" 2>/dev/null || echo "⚠️ 作業メモに書けませんでした: $MEMO"
echo "作業メモに書きました: $MEMO"

[ "$PUBLISHED" = "yes" ]
