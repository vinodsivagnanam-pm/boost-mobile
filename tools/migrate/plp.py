#!/usr/bin/env python3
"""Create Commerce listing pages (PLPs) from migration/<host>/plp.json.

Each `pages` entry becomes a DA page: an h1, the product-list-page block with
`urlpath` (ACCS category path), and metadata from the source title/description.
Entries with "urlpath": null are recorded as blocked (no matching category).
`records` entries only update urls.csv (redirect-only or query-variant URLs).

  MIGRATION_HOST=www.example.com python3 tools/migrate/plp.py [--dry-run]
"""
import argparse
import json
import os
import sys

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib as L  # noqa: E402
from migrate import load, save  # noqa: E402


def build(p, soup):
    plp = L.block('product-list-page', [['urlpath', L.E(p['urlpath'])]])
    return L.page(['<h1>' + L.E(p['heading']) + '</h1>' + plp + L.metadata(soup)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(L.REC, 'plp.json')))
    up, urows, ufields = load('urls.csv')
    cp, crows, cfields = load('components.csv')
    by_src = {r['source_url']: r for r in urows}

    for p in cfg['pages']:
        r = by_src.get(p['source'])
        if r is None:
            print('missing urls.csv row', p['source'])
            continue
        if p.get('urlpath'):
            soup = BeautifulSoup(L.fetch(p['source']), 'html.parser')
            doc = build(p, soup)
            if a.dry_run:
                print(doc[:1500])
                continue
            put, prev = L.upload(p['destination'], doc)
            open(L.content_file(p['destination']), 'w').write(doc)
            ok = put in ('200', '201') and prev == '200'
            st = 'implemented' if ok else 'failed'
            reason = 'product-list-page urlpath=' + p['urlpath'] if ok else 'upload ' + put + ' preview ' + prev
        else:
            st, reason = 'blocked', 'catalog: no matching ACCS category in the configured catalog'
        print(st, p['destination'], reason)
        if a.dry_run:
            continue
        r.update(destination_path=p['destination'], status=st, reason=reason)
        cid = p['destination'].strip('/').replace('/', '-') + '-plp'
        crow = {'source_url': p['source'], 'component_id': cid, 'region': 'main', 'classification': 'drop-in',
                'evidence': 'source product grid with facets/sort; plp.json', 'block': cfg['block'],
                'dropin_package': cfg['dropin'], 'implementation_path': 'DA ' + p['destination'],
                'status': st, 'blocker': '' if st == 'implemented' else reason}
        crows[:] = [c for c in crows if c['component_id'] != cid
                    and not (c['source_url'] == p['source'] and c['block'] == cfg['block'])] + [crow]

    for rec in cfg.get('records', []):
        r = by_src.get(rec['source'])
        if r is not None and not a.dry_run:
            r.update(destination_path=rec['destination'], status=rec['status'], reason=rec['reason'])

    if not a.dry_run:
        save(up, urows, ufields)
        save(cp, crows, cfields)


if __name__ == '__main__':
    main()
