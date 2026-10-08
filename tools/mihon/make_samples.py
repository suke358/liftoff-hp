import json, os, sys, re, subprocess
sys.path.insert(0, os.path.dirname(__file__)); from art import svg
# 使い方: python3 tools/mihon/make_samples.py [~/src/liftoff-hp] [cafe,school,...]
# 見本帳の「業種の見本」（架空のお店）を make_site.py で作り直す。設定は samples/<名前>/site.json に置かれる
import tempfile
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.expanduser(sys.argv[1]) if len(sys.argv)>1 else os.path.dirname(os.path.dirname(HERE))
S=tempfile.mkdtemp()
COMMON=dict(area='〇〇県〇〇市', tel='0000-00-0000', line_url='#reserve', address='〒000-0000 〇〇県〇〇市〇〇町1-2-3',
            line_msg='ホームページを見ました。{name}について相談したいです。', info_eyebrow='about')
def menu(id,name,text,price=None,note=None,items=None,icon=None):
    m=dict(id=id,name=name,text=text,image=f'images/menu-{id}.svg',w=1000,h=750,alt=name+'の写真',_icon=icon)
    if price: m['price']=price
    if note: m['price_note']=note
    if items: m['items']=items
    return m
SAMPLES={
'cafe':dict(c=dict(slug='komorebi',name='喫茶 こもれび',short_name='こもれび',kind='喫茶・軽食｜〇〇市',
  catch_html='<span class="nw">朝のコーヒーから、</span><br><span class="nw">昼のひと休みまで。</span>',
  lead='〇〇市の小さな喫茶店です。モーニング・日替わりランチ・自家製のケーキをご用意しています。',
  title_place='〇〇市の喫茶店',description='〇〇市の喫茶店「こもれび」のホームページです（デザイン見本・架空のお店）。',
  theme_base='salon',theme=dict(primary='#b5683b',primary_deep='#97522b',accent='#d6a35c',accent_soft='#ead2a8',pale='#f6ebdf',dark='#2e2620',dark2='#3a3029',bg='#f8f3ec',bg2='#efe6da',ink='#3a302a',muted='#7a6b5f',line='#e5d8c8'),
  mark='leaf',font='mincho',menu_title='メニュー',menu_word='メニュー',menu_lead='料金は見本です。',
  menu_note='季節によって内容が変わります。くわしくはお問い合わせください。',
  menus=[menu('morning','モーニング','トースト・ゆで卵・サラダに、お好きな飲みものを。','550円','飲みもの代＋',icon=['toast']),
         menu('lunch','日替わりランチ','週ごとに変わる、ごはんとおかずの定食です。','900円',icon=['cup','toast']),
         menu('coffee','コーヒー','注文を受けてから一杯ずつ淹れています。','450円',icon=['beans']),
         menu('cake','ケーキ','店で焼いたケーキを、日によって2〜3種類。','400円',icon=['cake'])],
  hours='8:00〜17:00（見本）',holiday='水曜日（見本）',parking='3台（見本）',payment='現金・QRコード決済（見本）',
  reserve_title='ご予約・お問い合わせ',info_title='お店のこと',reserve_lead='貸し切りや、ケーキのお取り置きもご相談ください。',
  faq=[dict(q='予約はできますか？',a='ランチのみ、前日までにお電話でお受けしています（見本）。'),
       dict(q='子ども連れでも大丈夫ですか？',a='はい。子ども用のいすをご用意しています（見本）。'),
       dict(q='ケーキの持ち帰りはできますか？',a='はい、できます。数に限りがあるので、お取り置きはお電話でどうぞ（見本）。')],
  schema_type='CafeOrCoffeeShop',area_served='〇〇市'),
  hero=['cup','cake','beans'], c1='#efe2d2', c2='#dcc7ad', stroke='#8a5a38', ink='#8a6a50', bg='#f1e7da'),
'school':dict(c=dict(slug='hidamari',name='こども英語教室 ひだまり',short_name='ひだまり英語',kind='こども英語教室｜〇〇市',
  catch_html='<span class="nw">「話してみたい」を、</span><br><span class="nw">いっしょに育てます。</span>',
  lead='〇〇市の、少人数のこども英語教室です。歌やゲームから始めて、読む・書くまで少しずつ。',
  title_place='〇〇市のこども英語教室',description='〇〇市のこども英語教室「ひだまり」のホームページです（デザイン見本・架空の教室）。',
  theme_base='fresh',theme=dict(primary='#2f7fd1',primary_deep='#2166ae',accent='#f2b84b',accent_soft='#f7d99a',pale='#e8f1fb',dark='#1f3550',dark2='#2a4566',bg='#f7fafd',bg2='#eaf1f9',ink='#22303e',muted='#5d6b7a',line='#d6e2ee'),
  mark='dot',font='gothic',menu_title='クラスと月謝',menu_word='クラス',menu_lead='月謝は見本です。',
  menu_note='入会金・教材費はお問い合わせください。',
  menus=[menu('kids','幼児クラス','3〜6才。歌・絵本・ゲームで英語に親しみます。','月 6,000円','週1回',icon=['music']),
         menu('elementary','小学生クラス','聞く・話すに加えて、読む・書くも少しずつ。','月 7,000円','週1回',icon=['abc']),
         menu('junior','中学生クラス','学校の授業に合わせて、文法と会話をくり返します。','月 8,000円','週1回',icon=['book']),
         menu('trial','体験レッスン','まずは一度、教室の雰囲気を見に来てください。','無料',icon=['star'])],
  flow_title='入会までの流れ',flow=[dict(title='お問い合わせ',text='LINEかお電話で、体験の日を決めます。'),dict(title='体験レッスン',text='実際のレッスンに参加していただきます。'),dict(title='ご入会',text='クラスと曜日を決めて、始めます。')],
  hours='平日 15:00〜20:00（見本）',holiday='土・日・祝日（見本）',parking='2台（見本）',
  reserve_title='体験・お問い合わせ',info_title='教室のこと',reserve_lead='体験レッスンは、保護者の方も一緒に見学できます。',
  faq=[dict(q='英語がはじめてでも大丈夫ですか？',a='はい。はじめての子がほとんどです。'),dict(q='振替はできますか？',a='同じ月の中で、ほかのクラスに振り替えられます（見本）。'),dict(q='送り迎えの駐車場はありますか？',a='教室の前に2台分あります（見本）。')],
  schema_type='EducationalOrganization',area_served='〇〇市'),
  hero=['abc','book','pencil'], c1='#e6f0fb', c2='#cfe0f3', stroke='#2f6fb5', ink='#4a6a8f', bg='#e9f0f8'),
'reform':dict(c=dict(slug='morino',name='森野工務店',short_name='森野工務店',kind='工務店・リフォーム｜〇〇市',
  catch_html='<span class="nw">水まわりから屋根まで、</span><br><span class="nw">家のことを近くで。</span>',
  lead='〇〇市の工務店です。リフォーム・修理・小さな困りごとまで、下見をしてからお見積もりします。',
  title_place='〇〇市の工務店・リフォーム',description='〇〇市の工務店「森野工務店」のホームページです（デザイン見本・架空のお店）。',
  theme_base='fresh',theme=dict(primary='#c0662b',primary_deep='#a25422',accent='#2b5d8a',accent_soft='#c9d6e3',pale='#f4ece4',dark='#1d2a36',dark2='#283846',bg='#f6f4f0',bg2='#ece8e1',ink='#23282e',muted='#646a70',line='#dcd6cc'),
  mark='dot',font='gothic',menu_title='お仕事の内容',menu_word='仕事',menu_lead='小さな修理からお受けしています。',
  menu_note='料金は家の状態で変わります。下見のうえでお見積もりをお出しします。',
  menus=[menu('mizu','水まわり','台所・お風呂・トイレ・洗面所の取りかえや修理。',icon=['faucet']),
         menu('yane','外壁・屋根','ぬりかえ・雨もりの修理・とい の取りかえ。',icon=['roof']),
         menu('naisou','内装','壁紙・床・建具・手すりの取りつけなど。',icon=['house']),
         menu('shuuri','小さな修理','戸のたてつけ・網戸の張りかえなど、1か所からどうぞ。',icon=['tools'])],
  flow_title='ご依頼の流れ',flow=[dict(title='ご相談',text='困っていることをお知らせください。'),dict(title='下見',text='おうちに伺って、様子を見せていただきます。'),dict(title='お見積もり',text='内容と金額をお出しします。決めるのはそのあとで。'),dict(title='工事',text='日程を決めて工事します。終わったら一緒に確かめます。')],
  hours='8:00〜18:00（見本）',holiday='日曜日（見本）',service_area='〇〇市とその周辺（見本）',
  reserve_title='ご相談・お見積もり',info_title='森野工務店について',reserve_lead='下見とお見積もりは無料です（見本）。',
  faq=[dict(q='1か所だけの修理でも頼めますか？',a='はい、お受けしています。'),dict(q='見積もりのあとで断ってもいいですか？',a='はい、大丈夫です（見本）。'),dict(q='どこまで来てもらえますか？',a='〇〇市とその周辺でお受けしています（見本）。')],
  schema_type='HomeAndConstructionBusiness',area_served='〇〇市'),
  hero=['house','faucet','tools'], c1='#efe9e1', c2='#ddd3c6', stroke='#2b5d8a', ink='#5d6670', bg='#ebe6de'),
'hair':dict(c=dict(slug='nagi',name='hair salon nagi',short_name='nagi',kind='美容室｜〇〇市',
  catch_html='<span class="nw">いつもの髪を、</span><br><span class="nw">少しだけ新しく。</span>',
  lead='〇〇市の、席が2つだけの美容室です。ひとりのスタイリストが、最初から最後まで担当します。',
  title_place='〇〇市の美容室',description='〇〇市の美容室「nagi」のホームページです（デザイン見本・架空のお店）。',
  theme_base='salon',theme=dict(primary='#8c7b6b',primary_deep='#6f6052',accent='#c9a27e',accent_soft='#e3d1bd',pale='#f1ece6',dark='#232120',dark2='#302d2b',bg='#f5f3f0',bg2='#ebe7e2',ink='#2a2826',muted='#6e6862',line='#ddd6ce'),
  mark='dot',font='mincho',menu_title='メニュー・料金',menu_word='メニュー',menu_lead='料金は見本です。',
  menu_note='髪の長さや量で変わることがあります。',
  menus=[menu('cut','カット','顔まわりのくせや、ふだんの手入れをうかがってから切ります。','4,400円',icon=['scissors']),
         menu('color','カラー','明るさ・色味を相談しながら決めます。','6,600円〜',icon=['bottle']),
         menu('perm','パーマ','ゆるいくせづけから、しっかりしたカールまで。','8,800円〜',icon=['comb']),
         menu('spa','ヘッドスパ','頭皮をていねいに洗い、ゆっくり過ごしていただく時間です。','3,300円',icon=['dryer'])],
  hours='10:00〜19:00（見本）',holiday='月曜日（見本）',parking='2台（見本）',payment='現金・クレジットカード（見本）',
  reserve_title='ご予約',info_title='お店のこと',reserve_lead='ご予約はLINEかお電話でどうぞ。',
  faq=[dict(q='はじめてでも予約できますか？',a='はい。はじめての方も、LINEかお電話でどうぞ。'),dict(q='子どもも切ってもらえますか？',a='はい。小学生から承っています（見本）。'),dict(q='当日の予約はできますか？',a='空いていればお受けします。お電話でお問い合わせください。')],
  schema_type='HairSalon',area_served='〇〇市'),
  hero=['scissors','comb','bottle'], c1='#efebe6', c2='#ddd5cc', stroke='#6f6052', ink='#7a7067', bg='#ece8e3'),
'relax':dict(c=dict(slug='yururi',name='整体 ゆるり',short_name='ゆるり',kind='整体｜〇〇市',
  catch_html='<span class="nw">からだの話を、</span><br><span class="nw">ゆっくり聞くところから。</span>',
  lead='〇〇市の整体院です。いまのからだの状態をうかがってから、ひとりひとりに合わせて施術します。',
  title_place='〇〇市の整体',description='〇〇市の整体「ゆるり」のホームページです（デザイン見本・架空のお店）。',
  theme_base='fresh',theme=dict(primary='#4f8f86',primary_deep='#3d756d',accent='#d9b26a',accent_soft='#ecd9ad',pale='#e7f1ef',dark='#22393a',dark2='#2d4848',bg='#f5f8f7',bg2='#e8efed',ink='#26302f',muted='#5f6d6b',line='#d4e0dd'),
  mark='leaf',font='mincho',menu_title='メニュー・料金',menu_word='メニュー',menu_lead='料金は見本です。',
  menu_note='どれにすればいいか迷うときは、お気軽にご相談ください。',
  menus=[menu('basic','整体 60分','お話をうかがってから、全身をていねいに施術します。','5,500円',icon=['hands']),
         menu('short','整体 30分','時間のないときに、気になるところを中心に。','3,300円',icon=['leaf']),
         menu('first','はじめての方','最初にお話をうかがう時間を長めにとります。','+1,100円',icon=['chair']),
         menu('ticket','回数券','5回分をまとめてお求めいただけます。','25,000円',icon=['ticket'])],
  hours='9:00〜19:00（見本）',holiday='木曜日（見本）',parking='3台（見本）',payment='現金・QRコード決済（見本）',
  reserve_title='ご予約',info_title='お店のこと',reserve_lead='ご予約はLINEかお電話でどうぞ。持病のある方・妊娠中の方は、事前にご相談ください。',
  faq=[dict(q='はじめてでも大丈夫ですか？',a='はい。最初にお話をうかがう時間をとっています。'),dict(q='着がえは必要ですか？',a='お着がえをご用意しています（見本）。'),dict(q='当日の予約はできますか？',a='空いていればお受けします。お電話でお問い合わせください。')],
  schema_type='HealthAndBeautyBusiness',area_served='〇〇市'),
  hero=['leaf','hands','cal'], c1='#e6efed', c2='#cfdfdb', stroke='#3d756d', ink='#5c7470', bg='#e7eeec'),
}
MIHON_CSS='''
/* 見本帳にもどる（見本だけに出す） */
.mihon{position:fixed;left:50%;-webkit-transform:translateX(-50%);transform:translateX(-50%);bottom:16px;z-index:200;background:rgba(25,25,25,.85);color:#fff !important;font:500 12px/1.4 "Hiragino Sans","Noto Sans CJK JP",sans-serif;letter-spacing:.06em;padding:.7em 1.3em;border-radius:999px;text-decoration:none;white-space:nowrap;box-shadow:0 4px 14px rgba(0,0,0,.2)}
.mihon:hover{background:#000}
@media (max-width:860px){.mihon{bottom:78px}}
'''
only=sys.argv[2].split(',') if len(sys.argv)>2 else list(SAMPLES)
for d in only:
    spec=SAMPLES[d]; c=dict(COMMON); c.update(spec['c'])
    out=f'{ROOT}/samples/{d}'
    for m in c['menus']:
        icons=m.pop('_icon')
        svg(f'{out}/{m["image"]}',1000,750,icons,m['name']+'の写真が入ります',spec['c1'],spec['c2'],spec['stroke'],spec['ink'])
    c['hero']=dict(image='images/hero.svg',w=1200,h=1500,alt='お店の写真')
    t=c['theme']; svg(f'{out}/images/hero.svg',1200,1500,spec['hero'],'お店の写真が入ります',t['dark2'],t['dark'],t['accent_soft'],'rgba(255,255,255,.55)')
    c['_説明']='デザイン見本（架空のお店）。make_site.py で作った'
    cf=f'{S}/{d}.json'; json.dump(c,open(cf,'w'),ensure_ascii=False,indent=1)
    subprocess.run([sys.executable,f'{ROOT}/tools/make_site.py',cf,out],stdout=subprocess.DEVNULL)
    p=f'{out}/index.html'; s=open(p,encoding='utf-8').read()
    s=re.sub(r'href="(#[^"]*)" target="_blank" rel="noopener"', r'href="\1"', s)
    s=s.replace('<title>','<title>【見本】',1)
    s=s.replace('</style>',MIHON_CSS+'</style>',1)
    s=s.replace('</body>','<a class="mihon" href="../index.html">デザイン見本（架空のお店）｜見本帳にもどる</a>\n</body>',1)
    open(p,'w',encoding='utf-8').write(s)
    for f in ('index.old.html',):
        if os.path.exists(f'{out}/{f}'): os.remove(f'{out}/{f}')
    print('ok',d)
