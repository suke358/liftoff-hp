#!/usr/bin/env python3
"""check_site.py のテスト：CSS の背景画像が無いとき ❌ が出るか（2026/11/12 道具7件の7）
使い方: python3 tools/test_check_site_bg.py [確かめる check_site.py]
  仮のサイト：<style> の url(images/hero.jpg)＝無い／読み込んだ css の url(../images/bg.png)＝無い／style="…url(images/ok.jpg)"＝ある／data: ＝調べない
  合格：無い2つに ❌、ある1つには出ない、❌ の中身に hero.jpg と bg.png がある"""
import os, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
tool = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(here, 'check_site.py')
root = tempfile.mkdtemp(prefix='check_site_bg_')
os.makedirs(os.path.join(root, 'css')); os.makedirs(os.path.join(root, 'images'))
open(os.path.join(root, 'images', 'ok.jpg'), 'wb').write(b'\xff\xd8\xff')
open(os.path.join(root, 'css', 'site.css'), 'w', encoding='utf-8').write('body{background:url(../images/bg.png) no-repeat}\n.x{background-image:url("data:image/png;base64,AAAA")}\n')
open(os.path.join(root, 'index.html'), 'w', encoding='utf-8').write('''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>試し</title><link rel="stylesheet" href="css/site.css">
<style>
.hero{background:url('images/hero.jpg') center/cover}
</style></head><body>
<div style="background-image:url(images/ok.jpg)">こんにちは</div>
<a href="tel:0120-000-000">0120-000-000</a>
</body></html>''')
r = subprocess.run([sys.executable, tool, root, '--no-browser'], capture_output=True, text=True)
lines = [l for l in r.stdout.splitlines() if l.startswith('❌') and 'url(' in l]
print('\n'.join(lines) if lines else '（CSS の背景画像の ❌ なし）')
ok = any('hero.jpg' in l for l in lines) and any('bg.png' in l for l in lines) and not any('ok.jpg' in l for l in lines) and len(lines) == 2
print('→', '合格' if ok else '不合格（背景画像が無くても通る）')
import shutil; shutil.rmtree(root)
sys.exit(0 if ok else 1)
