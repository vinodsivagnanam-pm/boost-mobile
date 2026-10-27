#!/usr/bin/env python3
"""Map source product pages (template shop-pdp) to the templated Commerce PDP.

PDPs are not converted from source HTML. The single DA page /products/default
(product-details block) renders every /products/<urlKey>/<sku> URL once the
Config Service folder mapping "/products/" -> "/products/default" is set.

For each urls.csv row with the PDP template, the catalog (Catalog Service
endpoint and headers from config.json) is matched in this order:
  1. link-map.csv override (source_url -> /products/<urlKey>/<sku>)
  2. a catalog SKU contained in the source slug (e.g. pixel-10a-002729)
  3. a source slug equal to a catalog urlKey (e.g. iphone-16e)
Matched rows become implemented with that destination and are added to
link-map.csv so content links and redirects use them; others become blocked.

  MIGRATION_HOST=www.example.com python3 tools/migrate/pdp.py [--template shop-pdp] [--dry-run]
"""
import argparse
import csv
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib as L  # noqa: E402
from migrate import load, save  # noqa: E402


def catalog():
    cfg = json.load(open(os.path.join(L.ROOT, 'config.json')))['public']['default']
    headers = {'Content-Type': 'application/json', 'User-Agent': 'eds-migration'}
    for group in ('all', 'cs'):
        headers.update(cfg.get('headers', {}).get(group, {}))
    items, page = [], 1
    while True:
        q = ('{productSearch(phrase:"",page_size:100,current_page:%d){page_info{total_pages}'
             'items{productView{sku urlKey name}}}}' % page)
        req = urllib.request.Request(cfg['commerce-endpoint'], json.dumps({'query': q}).encode(), headers)
        data = json.load(urllib.request.urlopen(req))['data']['productSearch']
        items += [i['productView'] for i in data['items']]
        if page >= data['page_info']['total_pages']:
            return items
        page += 1


def match(src, products, overrides):
    if src in overrides:
        return overrides[src]
    slug = re.sub(r'\.html$', '', src.rstrip('/').rsplit('/', 1)[-1]).lower()
    for p in products:
        if re.search(r'(^|-)' + re.escape(p['sku'].lower()) + r'$', slug):
            return '/products/%s/%s' % (p['urlKey'], p['sku'])
    for p in products:
        if p['urlKey'] == slug:
            return '/products/%s/%s' % (p['urlKey'], p['sku'])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--template', default='shop-pdp')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    products = catalog()
    overrides = L.link_overrides()
    up, urows, ufields = load('urls.csv')
    new_links = {}
    for r in urows:
        if r['template'] != a.template or r['status'] == 'excluded':
            continue
        dest = match(r['source_url'], products, overrides)
        if dest:
            r.update(destination_path=dest, page_classification='commerce',
                     reason='Templated PDP /products/default (product-details); catalog match')
            if r['status'] not in ('verified', 'published'):
                r['status'] = 'implemented'
            if r['source_url'] not in overrides:
                new_links[r['source_url']] = dest
        else:
            r.update(status='blocked', reason='catalog: no matching SKU in the configured catalog')
        print(r['status'], r['source_url'], dest or '')
    if a.dry_run:
        return
    save(up, urows, ufields)
    if new_links:
        path = os.path.join(L.REC, 'link-map.csv')
        exists = os.path.exists(path)
        with open(path, 'a', newline='') as f:
            w = csv.writer(f)
            if not exists:
                w.writerow(['source_url', 'destination_path'])
            w.writerows(new_links.items())


if __name__ == '__main__':
    main()
