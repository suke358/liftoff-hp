#!/usr/bin/env python3
"""make_site.py の「道具の版」と安全弁の検査（2026/11/21 順0「既存の店を守る」）
使い方: python3 tools/test_make_site_version.py
  仮のお店のフォルダ（git の外＝wrangler.jsonc が作られる＝公開先のあるサイトの扱い）で、見本の設定 templates/site_sample.json を使って確かめる：
  1. 作ると、index.html の目印に「道具の版 〇〇」が入る（今の道具の版と同じ）
  2. 同じ道具でもう一度作る → 通る（止まらない）
  3. 目印の版を「ふるい」に書きかえて作る → ⚠️ で止まり、index.html は1文字も変わらない（これが「検査が効いている証拠」）
  4. --uwagaki を付ける → 通る（作り直せる）
  5. wrangler.jsonc の無いフォルダ（見本帳 samples/ と同じ扱い）は、版が違っても止まらない
  合格：5つ全部 OK"""
import hashlib, os, re, shutil, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
tool = os.path.join(here, 'make_site.py')
conf = os.path.join(here, 'templates', 'site_sample.json')
sys.path.insert(0, here)
import make_site
now = make_site.TOOL_VERSION

def run(outdir, *flags):
    return subprocess.run([sys.executable, tool, conf, outdir, *flags], capture_output=True, text=True)
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def stamp(p): return make_site.stamped_version(p)

ok = True
def check(cond, msg):
    global ok
    print(('OK ' if cond else 'NG ') + msg)
    ok = ok and cond

root = tempfile.mkdtemp(prefix='make_site_version_')
site = os.path.join(root, 'mise'); os.makedirs(site)
idx = os.path.join(site, 'index.html')
r = run(site)
check(r.returncode == 0 and os.path.exists(idx) and os.path.exists(os.path.join(site, 'wrangler.jsonc')), '1. 作れた（wrangler.jsonc も入った）')
check(stamp(idx) == now, f'1. 目印の版 = 今の道具の版（{now}）')
r = run(site)
check(r.returncode == 0 and '止めました' not in r.stdout + r.stderr, '2. 同じ版なら止まらない')
s = open(idx, encoding='utf-8').read()
s2 = re.sub(r'・道具の版 [^）\s]+）', '・道具の版 ふるい）', s, count=1)
open(idx, 'w', encoding='utf-8').write(s2)
before = sha(idx)
r = run(site)
check(r.returncode != 0 and '止めました' in r.stdout + r.stderr and sha(idx) == before, '3. 版が違えば ⚠️ で止まり、index.html は変わらない')
r = run(site, '--uwagaki')
check(r.returncode == 0 and stamp(idx) == now, '4. --uwagaki なら作り直せる（版も今の道具に）')
site2 = os.path.join(root, 'mihon'); os.makedirs(site2)
run(site2)
os.remove(os.path.join(site2, 'wrangler.jsonc'))
s = open(os.path.join(site2, 'index.html'), encoding='utf-8').read()
open(os.path.join(site2, 'index.html'), 'w', encoding='utf-8').write(re.sub(r'・道具の版 [^）\s]+）', '・道具の版 ふるい）', s, count=1))
r = run(site2)
check(r.returncode == 0 and '止めました' not in r.stdout + r.stderr, '5. wrangler.jsonc の無いフォルダ（見本帳）は止めない')
shutil.rmtree(root, ignore_errors=True)
print('合格：道具の版と安全弁は効いています' if ok else '不合格：上の NG を直す')
sys.exit(0 if ok else 1)
