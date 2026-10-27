"""T6: create /modals/* from source modals reused on >=2 source pages."""
import collections, glob, hashlib, json, re, sys
from bs4 import BeautifulSoup
import eds_lib as L

SRC = '/tmp/boost'
NAMES = {
    'Unlimited comes with:': 'unlimited',
    'Unlimited+ comes with:': 'unlimited-plus',
    'Unlimited Premium comes with:': 'unlimited-premium',
    'Global Connection comes with:': 'global-connection',
    'Additional Disclaimers': 'additional-disclaimers',
}
groups = collections.defaultdict(lambda: {'pages': set(), 'ids': set()})
for fn in glob.glob(SRC + '/*.html'):
    if '/es_' in fn:
        continue
    s = BeautifulSoup(open(fn, errors='ignore').read(), 'html.parser')
    for m in s.select('.cmp-modal__info'):
        h = m.select_one('.info-modal__header h3, .info-modal__header')
        title = ' '.join(h.get_text(' ', strip=True).split()) if h else ''
        content = m.select_one('.info-modal__container') or m
        hdr = content.select_one('.info-modal__header')
        if hdr:
            hdr.decompose()
        body = ' '.join(content.get_text(' ', strip=True).split())
        k = hashlib.md5(body.encode()).hexdigest()[:8]
        g = groups[k]
        g['pages'].add(fn.split('/')[-1]); g['ids'].add(m.get('id')); g['title'] = title; g['el'] = content
        g['deals'] = 'Special Deals' in body

out = []
for k, g in groups.items():
    if len(g['pages']) < 2 or g['title'] not in NAMES:
        continue
    slug = NAMES[g['title']]
    folder = 'legal' if slug == 'additional-disclaimers' else 'plans'
    if folder == 'plans':
        slug += '-deals' if g['deals'] else '-details'
    path = f'modals/{folder}/{slug}'
    doc = L.page(['<h2>' + g['title'] + '</h2>\n' + L.clean(g['el'])])
    st = L.upload(path, doc) if '--upload' in sys.argv else ('-', '-')
    open(f'{L.REC}/content/{path.replace("/", "__")}.html', 'w').write(doc)
    out.append({'path': '/' + path, 'source_modal_ids': sorted(g['ids']), 'source_pages': sorted(g['pages']), 'status': st})
    print('/' + path, st, len(doc))
json.dump(out, open(f'{L.REC}/fragments.json', 'w'), indent=2)
