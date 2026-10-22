#!/usr/bin/env python3
"""Cloudflare Web Analytics から「見た人の数」を読む（Lift-Off）  2026/10/22 作成（claude/商品/毎月の報告.md）

使い方:
  python3 fetch_cf.py list                       … 直近 90 日に見られたサイトの一覧（ホスト名と、その間の数）
  python3 fetch_cf.py <ホスト名> <月>              … その月の 見た人（visits）と 見られた回数（page views）。例）python3 fetch_cf.py colore-yomogi.com 2026-10
  python3 fetch_cf.py <ホスト名> <日>              … その日だけ。例）python3 fetch_cf.py liftoff-hp.liftoff-358.workers.dev 2026-10-22
  --json を付けると {"visits": n, "views": n} だけを出す（make_report.py --auto が使う）

合言葉（API トークン）は ~/.config/liftoff/cf_analytics_token の1行目から読む。中身は画面・ファイルに出さない。liftoff-hp の中には置かない。
アカウントの ID は下の ACCOUNT（秘密ではない）。日付は日本時間で区切る（UTC に直して問い合わせる）。
しくみ：GraphQL の rumPageloadEventsAdaptiveGroups（sum.visits＝見た人・count＝見られた回数）。サイトの一覧も同じ集計を requestHost で分けて出す
（REST の /rum/site_info/list は「Account Analytics: Read」の合言葉では 403 だったので使わない。2026/10/22）。
注意：一覧に出るのは、直近 90 日に1回でも見られたサイトだけ。"""
import sys, os, json, re, urllib.request, urllib.error, datetime

ACCOUNT = '25b99c284af972eae93cdbe79217849d'
TOKEN_FILE = os.path.expanduser('~/.config/liftoff/cf_analytics_token')
GQL = 'https://api.cloudflare.com/client/v4/graphql'

def die(msg): sys.exit('❌ ' + msg)

def token():
    if not os.path.exists(TOKEN_FILE): die(f'合言葉のファイルがありません：{TOKEN_FILE}（1行目に Cloudflare の API トークン。担当者が作る）')
    t = open(TOKEN_FILE, encoding='utf-8').read().strip().split('\n')[0].strip()
    if not t: die('合言葉のファイルが空です')
    return t

def gql(filt, dims):
    q = ('query($acc:String!, $f:AccountRumPageloadEventsAdaptiveGroupsFilter_InputObject!) {'
         ' viewer { accounts(filter:{accountTag:$acc}) {'
         ' rumPageloadEventsAdaptiveGroups(limit:100, filter:$f) { count sum { visits } '
         + ('dimensions { ' + ' '.join(dims) + ' }' if dims else '') + ' } } } }')
    req = urllib.request.Request(GQL, data=json.dumps({'query': q, 'variables': {'acc': ACCOUNT, 'f': filt}}).encode(),
                                 headers={'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: res = json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        die(f'Cloudflare が {ex.code} を返しました（合言葉の権限「Account Analytics: Read」を確かめる）：{ex.read().decode(errors="replace")[:300]}')
    except Exception as ex:
        die('Cloudflare につながりません：' + str(ex))
    if res.get('errors'): die('数が読めません：' + json.dumps(res['errors'], ensure_ascii=False)[:300])
    return res['data']['viewer']['accounts'][0]['rumPageloadEventsAdaptiveGroups']

def sites(days=90):
    """直近 days 日に見られたサイトの一覧（host・その間の visits・views）"""
    now = datetime.datetime.utcnow()
    f = {'datetime_geq': (now - datetime.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ'), 'datetime_lt': now.strftime('%Y-%m-%dT%H:%M:%SZ')}
    out = {}
    for g in gql(f, ['requestHost']):
        h = g['dimensions']['requestHost']; o = out.setdefault(h, {'host': h, 'visits': 0, 'views': 0})
        o['visits'] += int(g['sum']['visits'] or 0); o['views'] += int(g['count'] or 0)
    return sorted(out.values(), key=lambda o: -o['visits'])

def jst_range(period):
    """月（2026-10）か日（2026-10-22）を、日本時間の始まり〜終わりにして UTC の文字にする"""
    if re.fullmatch(r'\d{4}-\d{2}', period):
        y, m = int(period[:4]), int(period[5:7])
        s = datetime.datetime(y, m, 1); e = datetime.datetime(y + (m == 12), 1 if m == 12 else m + 1, 1)
    elif re.fullmatch(r'\d{4}-\d{2}-\d{2}', period):
        s = datetime.datetime.strptime(period, '%Y-%m-%d'); e = s + datetime.timedelta(days=1)
    else: die('月は 2026-10、日は 2026-10-22 のように書く')
    jst = datetime.timedelta(hours=9)
    f = lambda d: (d - jst).strftime('%Y-%m-%dT%H:%M:%SZ')
    return f(s), f(e)

def counts(host, period):
    """ホスト名（requestHost）で、その期間の 見た人（visits）と 見られた回数（views）"""
    geq, lt = jst_range(period)
    g = gql({'requestHost': host, 'datetime_geq': geq, 'datetime_lt': lt}, [])
    if not g: return {'visits': 0, 'views': 0}
    return {'visits': int(g[0]['sum']['visits'] or 0), 'views': int(g[0]['count'] or 0)}

def main():
    a = sys.argv[1:]
    as_json = '--json' in a; a = [x for x in a if x != '--json']
    if not a: sys.exit(__doc__)
    if a[0] == 'list':
        ss = sites()
        if not ss: print('直近 90 日に見られたサイトはありません'); return
        for s in ss: print(f"{s['host']:45} 直近90日 見た人 {s['visits']:,} 人／見られた回数 {s['views']:,} 回")
        return
    if len(a) < 2: sys.exit(__doc__)
    host, period = a[0], a[1]
    c = counts(host, period)
    if as_json: print(json.dumps(c)); return
    print(f'{host}　{period}：見た人 {c["visits"]:,} 人／見られた回数 {c["views"]:,} 回（日本時間で区切り）')

if __name__ == '__main__':
    main()
