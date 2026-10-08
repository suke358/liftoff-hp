#!/usr/bin/env python3
"""写真の自動処理（Lift-Off）  2026/10/8 作成

iPhone の写真（HEIC・JPG・PNG）を、ホームページ用・Googleマップ用にまとめて書き出す。
・向きを正しく直す　・位置情報など（Exif）を消す　・大きさをそろえる　・JPG にする

使い方:
  1) 一覧画像を作る（どれを使うか選ぶため。番号とファイル名つき）
     python3 photos.py list <写真のフォルダ> [一覧画像の保存先.jpg]

  2) 書き出す
     python3 photos.py export <写真のフォルダ> <書き出し先> [--size 1600] [--quality 85] [--cover] 元の名前=新しい名前 ...
       例）python3 photos.py export "4 もらった写真" "Googleマップ用の写真" IMG_3107=01_カバー写真 IMG_3101=02_お部屋
       ・名前を指定しないと、フォルダの写真を全部書き出す（元の名前のまま .jpg）
       ・--size  長い辺のピクセル数（ホームページ・Googleマップは 1600 が目安。小さい写真は大きくしない）
       ・--cover 横長 16:9 に真ん中で切る（Googleマップのカバー写真・LINE のカード用）
       ・--square 正方形に真ん中で切る（Instagram・アイコン用）

  3) 位置情報が残っていないか確かめる
     python3 photos.py check <フォルダ>
"""
import sys, os, glob, subprocess, tempfile

from PIL import Image, ImageOps, ImageDraw, ImageFont
try:
    import pillow_heif; pillow_heif.register_heif_opener(); HEIF = True
except Exception:
    HEIF = False

EXTS = ('.heic', '.heif', '.jpg', '.jpeg', '.png', '.webp')

def photos_in(folder):
    fs = [f for f in sorted(os.listdir(folder)) if f.lower().endswith(EXTS) and not f.startswith(('.', '_'))]
    return [os.path.join(folder, f) for f in fs]

def open_img(path):
    """HEIC も開ける。pillow_heif が無ければ ImageMagick の convert で一度 JPG にする"""
    if path.lower().endswith(('.heic', '.heif')) and not HEIF:
        tmp = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
        subprocess.run(['convert', path, '-auto-orient', tmp], check=True)
        im = Image.open(tmp); im.load(); os.unlink(tmp); return im
    im = Image.open(path); im.load()
    return ImageOps.exif_transpose(im)  # 向きを直す

def to_rgb(im):
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA'); bg = Image.new('RGB', im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[-1]); return bg
    return im.convert('RGB')

def crop_ratio(im, rw, rh):
    w, h = im.size; target = rw / rh
    if w / h > target:  # 横が長すぎる → 左右を切る
        nw = int(h * target); x = (w - nw) // 2; return im.crop((x, 0, x + nw, h))
    nh = int(w / target); y = (h - nh) // 2; return im.crop((0, y, w, y + nh))

def font(size):
    for f in ['/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']:
        if os.path.exists(f):
            try: return ImageFont.truetype(f, size)
            except Exception: pass
    return ImageFont.load_default()

def cmd_list(folder, out=None):
    ps = photos_in(folder)
    if not ps: print('写真が見つかりません：', folder); return
    out = out or os.path.join(folder, '_写真の一覧.jpg')
    cell, cols, pad = 300, 5, 10
    rows = (len(ps) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * (cell + pad) + pad, rows * (cell + 44 + pad) + pad), (245, 245, 245))
    d = ImageDraw.Draw(sheet); f = font(18)
    for i, p in enumerate(ps):
        try:
            im = to_rgb(open_img(p)); im.thumbnail((cell, cell))
        except Exception as e:
            im = Image.new('RGB', (cell, cell), (200, 200, 200))
        x = pad + (i % cols) * (cell + pad); y = pad + (i // cols) * (cell + 44 + pad)
        sheet.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
        name = os.path.splitext(os.path.basename(p))[0]
        if len(name) > 12: name = name[:11] + '…'
        tag = '横' if im.width > im.height * 1.05 else ('縦' if im.height > im.width * 1.05 else '正方形')
        d.text((x, y + cell + 6), f'{i+1}. {name}（{tag}）', fill=(23, 40, 58), font=f)
    sheet.save(out, quality=82)
    print(f'一覧画像を作りました：{out}（{len(ps)} 枚）')

def cmd_export(folder, outdir, args):
    size, quality, cover, square, pairs = 1600, 85, False, False, []
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--size': size = int(args[i+1]); i += 2; continue
        if a == '--quality': quality = int(args[i+1]); i += 2; continue
        if a == '--cover': cover = True; i += 1; continue
        if a == '--square': square = True; i += 1; continue
        pairs.append(a); i += 1
    os.makedirs(outdir, exist_ok=True)
    allp = {os.path.splitext(os.path.basename(p))[0]: p for p in photos_in(folder)}
    jobs = []
    if pairs:
        for pr in pairs:
            src, _, dst = pr.partition('=')
            src = os.path.splitext(src)[0]
            if src not in allp: print(f'⚠️ 見つかりません：{src}'); continue
            jobs.append((allp[src], dst or src))
    else:
        jobs = [(p, n) for n, p in allp.items()]
    for p, name in jobs:
        im = to_rgb(open_img(p))
        if cover: im = crop_ratio(im, 16, 9)
        if square: im = crop_ratio(im, 1, 1)
        if max(im.size) > size: im.thumbnail((size, size), Image.LANCZOS)
        out = os.path.join(outdir, os.path.splitext(name)[0] + '.jpg')
        im.save(out, 'JPEG', quality=quality, optimize=True, progressive=True)  # Exif（位置情報）は書き込まない
        print(f'✅ {os.path.basename(p)} → {os.path.basename(out)}（{im.width}×{im.height}・{os.path.getsize(out)//1024}KB）')
    print(f'書き出し：{len(jobs)} 枚 → {outdir}')

def cmd_check(folder):
    bad = 0
    for p in photos_in(folder):
        try:
            ex = Image.open(p).getexif()
            gps = ex.get_ifd(0x8825) if hasattr(ex, 'get_ifd') else {}
            if gps: bad += 1; print(f'⚠️ 位置情報あり：{os.path.basename(p)}')
        except Exception as e:
            print(f'⚠️ 開けません：{os.path.basename(p)}（{e}）')
    print('✅ 位置情報の残っている写真はありません' if not bad else f'⚠️ 位置情報が残っている写真：{bad} 枚')

if __name__ == '__main__':
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    c = sys.argv[1]
    if c == 'list': cmd_list(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif c == 'export' and len(sys.argv) >= 4: cmd_export(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif c == 'check': cmd_check(sys.argv[2])
    else: print(__doc__); sys.exit(1)
