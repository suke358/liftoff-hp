#!/bin/bash
# 今のコミット（HEAD）を、確認用の preview ブランチに出す  2026/10/10 作成（決定 2026/10/10）
#
# 流れ：直す → commit → bash tools/preview_push.sh → 確認用URL（下）で見る → OK なら main へ push（main は許可をもらってから）
# 確認用URL：https://preview-liftoff-hp.liftoff-358.workers.dev/ （Cloudflare の Workers Builds が preview ブランチから作る）
#
# 使い方:  bash tools/preview_push.sh [出ているか確かめる文字]
#   例:    bash tools/preview_push.sh                 → 出して、トップが 200 で HEAD の index.html と同じ中身になるのを待つ
#          bash tools/preview_push.sh 'id="irai-band"' → さらに、その文字がトップに何か所あるかも表示
#
# 決まり：--force は、この道具の中で preview ブランチに出すときだけ使う（main には絶対に出さない。下の PREVIEW_BRANCH は変えない）
set -u
PREVIEW_BRANCH='preview'
PREVIEW_URL='https://preview-liftoff-hp.liftoff-358.workers.dev/'
WAIT_SEC=300

cd "$(dirname "$0")/.." || exit 1
if [ "$PREVIEW_BRANCH" = "main" ] || [ "$PREVIEW_BRANCH" = "master" ]; then
  echo "❌ 出す先が $PREVIEW_BRANCH になっています。この道具は preview 以外に出しません"; exit 1
fi
if [ ! -d .git ]; then echo "❌ git のフォルダではありません: $(pwd)"; exit 1; fi

echo "出すコミット: $(git log --oneline -1)"
if [ -n "$(git status --short | grep -v 'DS_Store' | grep -v '^??')" ]; then
  echo "⚠️ commit していない直しがあります（下）。出るのは commit した分だけです"
  git status --short | grep -v 'DS_Store' | grep -v '^??'
fi

# --force は preview にだけ（前回の preview を上書きして、いまの HEAD に置きかえる）
echo "→ origin の $PREVIEW_BRANCH ブランチに出します（--force は preview にだけ）"
git push --force origin "HEAD:refs/heads/$PREVIEW_BRANCH" || { echo "❌ push できませんでした"; exit 1; }

# Workers Builds が終わって、確認用URLのトップが HEAD の index.html と同じ中身になるのを待つ
TMP="$(mktemp -d)"
git show HEAD:index.html > "$TMP/head_index.html"
echo "→ 確認用URLに出るのを待ちます（最大 ${WAIT_SEC} 秒）: $PREVIEW_URL"
start=$(date +%s); code=000; same=no
while :; do
  code=$(curl -s -o "$TMP/pub_index.html" -w '%{http_code}' "$PREVIEW_URL")
  if [ "$code" = "200" ] && cmp -s "$TMP/pub_index.html" "$TMP/head_index.html"; then same=yes; break; fi
  if [ $(( $(date +%s) - start )) -ge $WAIT_SEC ]; then break; fi
  sleep 15
done
took=$(( $(date +%s) - start ))

echo
echo "確認用URL: $PREVIEW_URL"
echo "  状態コード: $code（${took}秒後）"
if [ "$same" = "yes" ]; then
  echo "  トップの中身: ✅ HEAD の index.html と同じ"
elif [ "$code" = "200" ]; then
  echo "  トップの中身: ⚠️ 200 だが HEAD の index.html とまだ違う（Workers Builds が終わっていないかも。少し待ってもう一度）"
else
  echo "  トップの中身: ❌ まだ開けない（初回は Workers Builds が preview ブランチを作るのに数分かかる。少し待ってもう一度）"
fi
if [ $# -ge 1 ] && [ "$code" = "200" ]; then
  n=$(grep -c -- "$1" "$TMP/pub_index.html")
  echo "  「$1」: ${n} か所"
fi
echo
echo "次：確認用URLをチャットか iPhone で見て OK なら、main への push は許可をもらってから（git push origin main）。作業メモに確認用URLを書く"
[ "$same" = "yes" ]
