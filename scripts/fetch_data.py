"""Write site/data/coding.json (WakaTime) and site/data/github.json (contributions).

Env: WAKATIME_API_KEY (falls back to ~/.wakatime.cfg), GITHUB_TOKEN.
A source that fails keeps the snapshot already in site/data.
"""
import base64, configparser, json, os, sys, time, urllib.request
from datetime import datetime, timezone

OUT = os.path.join(os.path.dirname(__file__), '..', 'site', 'data')
ACCOUNTS = [('personal', 'sa1ntsinner'), ('work', 'emirzayev-ant')]


def write(name, data):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, separators=(',', ':'))
    print('wrote', name)


# the site always shows the same three rows: python, c++, and everything else
SHOWN = [('Python', 'python'), ('C++', 'c++')]


def pick_languages(langs):
    pct = {l.get('name'): float(l.get('percent') or 0) for l in langs}
    rows = [{'name': label, 'percent': round(pct.get(name, 0))} for name, label in SHOWN]
    total = sum(pct.values())
    rows.append({'name': 'others', 'percent': max(0, round(total) - sum(r['percent'] for r in rows)) if total else 0})
    return rows


def wakatime():
    key = os.environ.get('WAKATIME_API_KEY')
    if not key:
        cfg = configparser.ConfigParser()
        cfg.read(os.path.expanduser('~/.wakatime.cfg'))
        key = cfg.get('settings', 'api_key', fallback='')
    if not key:
        print('wakatime: no key, keeping snapshot')
        return
    auth = 'Basic ' + base64.b64encode(key.encode()).decode()

    def get(path):
        req = urllib.request.Request('https://wakatime.com/api/v1' + path, headers={'Authorization': auth})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)

    # summaries are computed on request; /stats/last_7_days is a cache that can sit stale for days
    week = get('/users/current/summaries?range=last_7_days')
    days = week.get('data') or []
    secs = {}
    for d in days:
        for l in d.get('languages') or []:
            secs[l['name']] = secs.get(l['name'], 0) + (l.get('total_seconds') or 0)
    total = sum(secs.values())
    langs = [{'name': n, 'percent': 100 * v / total} for n, v in secs.items()] if total else []

    def lines(name):
        return sum((d.get('grand_total') or {}).get(name) or 0 for d in days)

    today = get('/users/current/status_bar/today')['data']
    beats = get('/users/current/heartbeats?date=' + datetime.now(timezone.utc).strftime('%Y-%m-%d')).get('data', [])
    last = max((b.get('time', 0) for b in beats), default=0)
    write('coding.json', {'status': {
        'is_live': time.time() - last < 900,
        'total_today': (today.get('grand_total') or {}).get('text') or '0 secs',
        'week_total': (week.get('cumulative_total') or {}).get('text') or '0 secs',
        'week_languages': pick_languages(langs),
        'human_additions': lines('human_additions'),
        'human_deletions': lines('human_deletions'),
        'ai_additions': lines('ai_additions'),
        'ai_deletions': lines('ai_deletions'),
        'updated': datetime.now(timezone.utc).strftime('%d %b %H:%M utc').lower(),
    }})


def github():
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print('github: no token, keeping snapshot')
        return
    q = 'query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'
    per_day, parts = {}, {}
    # personal account plus the work one; private work repos only show up as counts
    for label, user in ACCOUNTS:
        req = urllib.request.Request('https://api.github.com/graphql',
                                     data=json.dumps({'query': q, 'variables': {'u': user}}).encode(),
                                     headers={'Authorization': 'bearer ' + token, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as r:
            cal = json.load(r)['data']['user']['contributionsCollection']['contributionCalendar']
        parts[label] = cal['totalContributions']
        for w in cal['weeks']:
            for d in w['contributionDays']:
                per_day[d['date']] = per_day.get(d['date'], 0) + d['contributionCount']
    dates = sorted(per_day)
    write('github.json', {'total': sum(parts.values()), 'parts': parts, 'start': dates[0], 'days': [per_day[d] for d in dates]})


for job in (wakatime, github):
    try:
        job()
    except Exception as e:  # keep the last snapshot rather than break the deploy
        print(f'{job.__name__}: {e}', file=sys.stderr)
