"""Write site/data/coding.json (WakaTime) and site/data/github.json (contributions).

Env: WAKATIME_API_KEY (falls back to ~/.wakatime.cfg), GITHUB_TOKEN, GH_USER.
A source that fails keeps the snapshot already in site/data.
"""
import base64, configparser, json, os, sys, time, urllib.request
from datetime import datetime, timezone

OUT = os.path.join(os.path.dirname(__file__), '..', 'site', 'data')
USER = os.environ.get('GH_USER', 'sa1ntsinner')


def write(name, data):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, separators=(',', ':'))
    print('wrote', name)


def find(obj, name):
    if isinstance(obj, dict):
        if isinstance(obj.get(name), (int, float)):
            return obj[name]
        for v in obj.values():
            hit = find(v, name)
            if hit is not None:
                return hit
    elif isinstance(obj, list):
        for v in obj:
            hit = find(v, name)
            if hit is not None:
                return hit
    return None


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

    stats = get('/users/current/stats/last_7_days')['data']
    today = get('/users/current/status_bar/today')['data']
    beats = get('/users/current/heartbeats?date=' + datetime.now(timezone.utc).strftime('%Y-%m-%d')).get('data', [])
    last = max((b.get('time', 0) for b in beats), default=0)
    write('coding.json', {'status': {
        'is_live': time.time() - last < 900,
        'total_today': (today.get('grand_total') or {}).get('text') or '0 secs',
        'week_total': stats.get('human_readable_total') or '0 secs',
        'week_languages': pick_languages(stats.get('languages') or []),
        'human_additions': find(stats, 'human_additions') or 0,
        'human_deletions': find(stats, 'human_deletions') or 0,
        'ai_additions': find(stats, 'ai_additions') or 0,
        'ai_deletions': find(stats, 'ai_deletions') or 0,
        'updated': datetime.now(timezone.utc).strftime('%d %b %H:%M utc').lower(),
    }})


def github():
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print('github: no token, keeping snapshot')
        return
    q = {'query': 'query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}',
         'variables': {'u': USER}}
    req = urllib.request.Request('https://api.github.com/graphql', data=json.dumps(q).encode(),
                                 headers={'Authorization': 'bearer ' + token, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        cal = json.load(r)['data']['user']['contributionsCollection']['contributionCalendar']
    days = [d for w in cal['weeks'] for d in w['contributionDays']]
    write('github.json', {'total': cal['totalContributions'], 'start': days[0]['date'], 'days': [d['contributionCount'] for d in days]})


for job in (wakatime, github):
    try:
        job()
    except Exception as e:  # keep the last snapshot rather than break the deploy
        print(f'{job.__name__}: {e}', file=sys.stderr)
