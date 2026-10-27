#!/usr/bin/env python3
"""Convert source pages to DA documents, upload + preview them, and update the
migration records. Re-runnable: each run overwrites the DA page and the record.

  MIGRATION_HOST=www.example.com python3 tools/migrate/migrate.py --template info-page --limit 1
  MIGRATION_HOST=www.example.com python3 tools/migrate/migrate.py --url https://www.example.com/about
  options: --dry-run (no upload, no record changes), --status pending (rows to pick), --skip-done

Each page goes to the first converter in CONVERTERS whose detect(html) matches:
readme (ReadMe.io knowledge bases), then aem_core (AEM Core Components, the default).
Sources built on other platforms need another module with detect() and convert().
"""
import argparse
import csv
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib as L  # noqa: E402
import aem_core  # noqa: E402
import readme  # noqa: E402

CONVERTERS = [readme, aem_core]

DONE = {'implemented', 'verified', 'published', 'excluded'}


def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def load(name):
    p = os.path.join(L.REC, name)
    rows = list(csv.DictReader(open(p)))
    return p, rows, list(rows[0].keys()) if rows else []


def save(p, rows, fields):
    with open(p, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def migrate_row(r, dry):
    src = r['final_url'] or r['source_url']
    dest = r['destination_path']
    if not dest or '<' in dest:
        return 'blocked', 'no concrete destination_path', []
    note = ''
    if L.eds_path(dest) != dest.rstrip('/') and dest != '/':
        note = 'destination normalized from ' + dest
        dest = r['destination_path'] = L.eds_path(dest)
    html = L.fetch(src)
    conv = next((c for c in CONVERTERS if getattr(c, 'detect', lambda h: True)(html)), aem_core)
    sections, summary, soup = conv.convert(html)
    if not sections:
        return 'failed', 'no convertible content found', summary
    sections[-1] += L.metadata(soup, L.locale_metadata(r.get('locale')))
    doc = L.page(sections)
    if dry:
        print(doc[:3000])
        return r['status'], '', summary
    os.makedirs(os.path.join(L.REC, 'content'), exist_ok=True)
    open(L.content_file(dest), 'w').write(doc)
    put, prev = L.upload(dest if dest != '/' else '/index', doc)
    if put not in ('200', '201') or prev != '200':
        return 'failed', 'DA put ' + put + ' preview ' + prev, summary
    gaps = [n[5:] for _, names in summary for n in names if n.startswith('GAP: ')]
    note = '; '.join(([note] if note else []) + ['unsupported embed: ' + g for g in gaps])
    return 'implemented', note, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--template')
    ap.add_argument('--url', nargs='*')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--status', default='pending')
    ap.add_argument('--locale', help='only rows with this urls.csv locale, e.g. en-US')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    up, urows, ufields = load('urls.csv')
    cp, crows, cfields = load('components.csv')
    if a.url:
        want = {u.rstrip('/') for u in a.url}
        todo = [r for r in urows if r['source_url'].rstrip('/') in want]
    else:
        todo = [r for r in urows if r['template'] == a.template and r['status'] == a.status]
        if a.locale:
            todo = [r for r in todo if r.get('locale') == a.locale]
    todo = [r for r in todo if r['page_classification'] in ('content', 'hybrid') or a.url]
    if a.limit:
        todo = todo[:a.limit]
    print(len(todo), 'page(s)')
    for r in todo:
        try:
            st, reason, summary = migrate_row(r, a.dry_run)
        except Exception as e:  # record and continue the batch
            st, reason, summary = 'failed', str(e)[:200], []
        print(st, r['destination_path'], reason, summary)
        if a.dry_run:
            continue
        r['status'], r['reason'] = st, reason
        cid = (r['destination_path'].strip('/') or 'index').replace('/', '-') + '-page'
        blocks = sorted({b for _, names in summary for b in names if not b.startswith('GAP: ')})
        crow = {'source_url': r['source_url'], 'component_id': cid, 'region': 'main',
                'classification': 'content', 'evidence': 'tools/migrate: ' + str(len(summary)) + ' sections',
                'block': '; '.join(blocks), 'dropin_package': '',
                'implementation_path': 'DA ' + r['destination_path'], 'status': st, 'blocker': reason}
        crows[:] = [c for c in crows if c['component_id'] != cid] + [crow]
        save(up, urows, ufields)
        save(cp, crows, cfields)


if __name__ == '__main__':
    main()
