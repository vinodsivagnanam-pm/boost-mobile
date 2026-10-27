#!/usr/bin/env python3
"""Generate the EDS `redirects` sheet from the migration records.

Rules come from:
  - urls.csv rows on the source host whose destination differs from the
    source path (normalized EDS paths, PDP SKU URLs, redirect-only rows
    marked excluded with a destination path)
  - link-map.csv overrides (for example legacy product URLs)
  - migration/<host>/redirects-extra.csv (optional source,destination rows
    for rules not tied to a migrated page, such as the cart)
Existing DA sheet rows whose source is not generated here are kept.
Query-string URLs and other hosts cannot be expressed in the sheet and are
reported. The result is versioned at migration/<host>/content/redirects.json,
uploaded to DA /redirects.json, and previewed.

  MIGRATION_HOST=www.example.com python3 tools/migrate/redirects.py [--dry-run]
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib as L  # noqa: E402

LIVE = ('implemented', 'verified', 'published', 'excluded')


def norm(path):
    return '/' + path.strip('/') if path.strip('/') else '/'


def generated():
    rules, skipped = {}, []

    def add(src, dest):
        p = urllib.parse.urlsplit(src)
        if p.netloc != L.HOST:
            skipped.append((src, 'other host'))
        elif p.query:
            skipped.append((src, 'query string'))
        elif dest and dest.startswith('/') and '<' not in dest and '?' not in dest and norm(p.path) != norm(dest):
            rules[norm(p.path)] = dest

    for r in L._read_csv('urls.csv'):
        if r['status'] in LIVE and r['destination_path']:
            add(r['source_url'], r['destination_path'])
    for src, dest in L.link_overrides().items():
        add(src, dest)
    for r in L._read_csv('redirects-extra.csv'):
        add(urllib.parse.urljoin(L.LIVE_ORIGIN, r['source']), r['destination'])
    return rules, skipped


def da(method, path, *extra):
    auth = 'Authorization: Bearer ' + L._token()
    return subprocess.run(['curl', '-s', '-X', method, '-H', auth, *extra,
                           'https://admin.da.live/source/%s/%s/%s' % (L.ORG, L.SITE, path)],
                          capture_output=True, text=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    rules, skipped = generated()
    try:
        current = json.loads(da('GET', 'redirects.json')).get('data', [])
    except ValueError:
        current = []
    data = [r for r in current if norm(r.get('Source', r.get('source', ''))) not in rules]
    data += [{'source': s, 'destination': d} for s, d in sorted(rules.items())]
    sheet = {'total': len(data), 'limit': len(data), 'offset': 0, 'data': data, ':type': 'sheet'}
    for s, why in skipped:
        print('skip', why, s)
    print(len(rules), 'generated rules,', len(data), 'sheet rows')
    if a.dry_run:
        for d in data:
            print(d)
        return
    out = os.path.join(L.REC, 'content', 'redirects.json')
    json.dump(sheet, open(out, 'w'), indent=1)
    put = da('PUT', 'redirects.json', '-o', '/dev/null', '-w', '%{http_code}',
             '-F', 'data=@' + out + ';type=application/json')
    prev = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-X', 'POST',
                           '-H', 'Authorization: Bearer ' + L._token(),
                           'https://admin.hlx.page/preview/%s/%s/main/redirects.json' % (L.ORG, L.SITE)],
                          capture_output=True, text=True).stdout
    print('upload', put, 'preview', prev)


if __name__ == '__main__':
    main()
