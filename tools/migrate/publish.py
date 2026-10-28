#!/usr/bin/env python3
"""Preview and publish DA.live content to aem.page / aem.live in bulk.

  MIGRATION_HOST=www.example.com python3 tools/migrate/publish.py [--dry-run] [--preview-only]
      [--prefix /es] [--exclude /drafts/ ...]

Walks the DA source tree of site.json destination.repository, collects every
document (.html -> /path, index -> /) and sheet (.json -> /path.json), skips the
excluded prefixes (default: /drafts/), then runs the Admin API bulk preview and
bulk publish jobs (POST admin.hlx.page/{preview|live}/<org>/<site>/main/* with
{"paths": [...]}) and waits for them. Pages must be previewed before they can be
published, so preview always runs first. Results are written to
migration/<host>/publish-log.json, and urls.csv published_url and status are
updated for rows whose destination was published (or, for routes without their
own DA document such as folder-mapped PDPs, whose aem.live URL returns 200).

Publishing makes content public on aem.live: run it only with the site owner's
authorization. Auth: DA token in $DA_TOKEN or ~/.da-token (needs publish rights).
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib as L  # noqa: E402

DA = 'https://admin.da.live'
ADMIN = 'https://admin.hlx.page'
BATCH = 500


def req(url, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, method=method or ('POST' if body else 'GET'),
                               headers={'Authorization': 'Bearer ' + L._token(),  # pylint: disable=protected-access
                                        'Content-Type': 'application/json', 'User-Agent': 'migration-publish'})
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            txt = resp.read().decode() or '{}'
            return resp.status, json.loads(txt) if txt.strip().startswith('{') else {}
    except urllib.error.HTTPError as e:
        return e.code, {'error': e.headers.get('x-error', '')}


def walk(path=''):
    """Yield EDS paths for every DA document and sheet under path."""
    url = DA + '/list/' + L.ORG + '/' + L.SITE + path
    r = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + L._token(),  # pylint: disable=protected-access
                                            'User-Agent': 'migration-publish'})
    with urllib.request.urlopen(r, timeout=60) as resp:
        st, items = resp.status, json.loads(resp.read().decode())
    if st != 200:
        return
    for it in items:
        name, ext = it['name'], it.get('ext')
        if not ext:
            yield from walk(path + '/' + name)
        elif ext == 'html':
            p = path + '/' + name
            yield '/' if p == '/index' else (p[:-len('/index')] + '/' if p.endswith('/index') else p)
        elif ext == 'json':
            yield path + '/' + name + '.json'


def run_job(kind, paths):
    st, res = req(ADMIN + '/' + kind + '/' + L.ORG + '/' + L.SITE + '/main/*',
                  {'paths': paths, 'forceUpdate': True})
    if st != 202:
        return {'status': st, 'error': res.get('error'), 'failed': paths}
    self_url = res['links']['self']
    while True:
        time.sleep(5)
        _, job = req(self_url)
        state = job.get('state')
        prog = job.get('progress', {})
        print(' ', kind, state, prog.get('processed', 0), '/', prog.get('total', len(paths)), end='\r')
        if state in ('stopped', 'completed'):
            break
    _, details = req(self_url + '/details')
    rs = details.get('data', {}).get('resources', [])
    if not rs:
        print('\n  warning: no per-path details returned; verify with a live status sweep')
    failed = [x['path'] for x in rs if x.get('status') not in (200, 204)]
    print()
    return {'status': 202, 'job': job.get('name'), 'total': len(paths), 'failed': failed,
            'failures': {x['path']: (x.get('status'), x.get('error')) for x in rs
                         if x.get('status') not in (200, 204)}}


def live_ok(url):
    try:
        r = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'migration-publish'})
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--preview-only', action='store_true')
    ap.add_argument('--prefix', default='', help='only paths under this DA folder, e.g. /es')
    ap.add_argument('--exclude', nargs='*', default=['/drafts/'])
    a = ap.parse_args()
    paths = sorted(p for p in walk(a.prefix.rstrip('/'))
                   if not any(p.startswith(x) for x in a.exclude))
    print(len(paths), 'paths to', 'preview' if a.preview_only else 'preview and publish')
    if a.dry_run:
        print('\n'.join(paths))
        return
    log = {'site': L.ORG + '/' + L.SITE, 'started': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
           'paths': len(paths), 'preview': [], 'live': []}
    kinds = ['preview'] if a.preview_only else ['preview', 'live']
    ok = {k: set() for k in kinds}
    for k in kinds:
        src = paths if k == 'preview' else sorted(ok['preview'])
        for i in range(0, len(src), BATCH):
            chunk = src[i:i + BATCH]
            res = run_job(k, chunk)
            log[k].append({x: res[x] for x in res if x != 'failed'})
            ok[k] |= set(chunk) - set(res['failed'])
        print(k, len(ok[k]), 'ok,', len(src) - len(ok[k]), 'failed')
    open(os.path.join(L.REC, 'publish-log.json'), 'w').write(json.dumps(log, indent=2) + '\n')
    if 'live' in ok:
        live = 'https://main--' + L.SITE + '--' + L.ORG + '.aem.live'
        p = os.path.join(L.REC, 'urls.csv')
        rows = list(csv.DictReader(open(p)))
        n = 0
        for r in rows:
            d = r['destination_path']
            d = '/' if d in ('', '/') else d.rstrip('/')
            if r['status'] not in ('implemented', 'verified', 'published'):
                continue
            # Routes without their own DA document (folder-mapped PDPs) count only if they serve live.
            if d in ok['live'] or (not a.prefix and live_ok(live + d)):
                r['published_url'] = live + d
                r['status'] = 'published'
                n += 1
        with open(p, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print('urls.csv rows marked published:', n)


if __name__ == '__main__':
    main()
