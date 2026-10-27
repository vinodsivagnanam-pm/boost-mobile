"""Generic converter for AEM Sites pages built from core components (cmp-*).

Each top-level page section becomes an EDS section. Inside a section, known
component patterns are replaced in place by block tables; everything else is
kept as default content (headings, text, images, links/buttons).

  cmp-accordion            -> accordion (title | panel)
  cmp-card-shelf (plans)   -> plan-cards (cards with icon feature lists)
  cmp-card-shelf (other)   -> cards (image | body)
  aem-Grid with 2+ partial-width content columns -> columns
  cmp-breadcrumb           -> dropped (EDS breadcrumbs come from metadata)
  cmp-modal / overlays     -> dropped (modals migrate to /modals/, see MIGRATION.md)

Site-specific hints live in migration/<host>/converter.json (optional):
  {"plan_details": {"<plan name lower>": "/modals/plans/<page>"},
   "drop_text": ["Anchor", ...],
   "drop_labels": ["<regex for bare authoring-label text nodes inside divs>"],
   "shelf_variant": "<cards variant for card shelves, e.g. offers>"}
"""
import json
import os
import re
import uuid

from bs4 import BeautifulSoup

import lib as L

_cfg_path = os.path.join(L.REC, 'converter.json')
CFG = json.load(open(_cfg_path)) if os.path.exists(_cfg_path) else {}
PLAN_DETAILS = CFG.get('plan_details', {})
DROP_TEXT = {t.lower() for t in CFG.get('drop_text', [])}
DROP_LABELS = [re.compile(r, re.I) for r in CFG.get('drop_labels', [])]


def top_sections(soup):
    for x in soup.select('header, footer, .cmp-mega, .experiencefragment.header, .experiencefragment.footer'):
        x.decompose()
    L.strip_noise(soup)
    if DROP_LABELS:
        for t in soup.find_all(string=True):
            if t.parent and t.parent.name == 'div' and any(r.search(t.strip()) for r in DROP_LABELS):
                t.extract()
    for x in soup.select('.cmp-breadcrumb, .breadcrumb, .cmp-container__background-content'):
        x.decompose()
    cur = soup.select_one('.root.container') or soup.select_one('main') or soup.body
    while True:
        kids = [k for k in cur.find_all(recursive=False) if L.text(k) or k.find('img')]
        if len(kids) == 1:
            cur = kids[0]
            continue
        if len(kids) == 2 and 'experiencefragment' in ' '.join(kids[1].get('class', [])):
            cur = kids[0]
            continue
        return kids


def _width(el):
    for c in el.get('class', []):
        m = re.fullmatch(r'aem-GridColumn--default--(\d+)', c)
        if m:
            return int(m.group(1))
    return 12


def _dedupe(html):
    """Drop paragraphs/headings repeated verbatim (responsive copies) keeping the first."""
    frag = BeautifulSoup(html, 'html.parser')
    seen = set()
    for t in frag.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        if t.find_parent(['li', 'td']):
            continue
        key = (t.name, L.text(t), str(t.find('img')))
        if key in seen or L.text(t).lower() in DROP_TEXT:
            t.decompose()
        else:
            seen.add(key)
    return str(frag)


class Section:
    def __init__(self, el):
        self.el = el
        self.blocks = {}
        self.found = []

    def _mark(self, el, html_, name):
        k = 'BLK' + uuid.uuid4().hex[:10]
        self.blocks[k] = html_
        self.found.append(name)
        p = BeautifulSoup('<p>' + k + '</p>', 'html.parser').p
        el.replace_with(p)

    def accordions(self):
        for acc in self.el.select('.cmp-accordion'):
            rows = []
            for it in acc.select(':scope > .cmp-accordion__item'):
                t = it.select_one('.cmp-accordion__title')
                p = it.select_one('.cmp-accordion__panel')
                if t and p:
                    rows.append([L.E(L.text(t)), L.clean(p, h1=False)])
            if rows:
                self._mark(acc, L.block('accordion', rows), 'accordion')

    def _is_plan_shelf(self, shelf):
        return bool(shelf.select('.card-container .text-icon-item'))

    def _plan_rows(self, shelf):
        out = []
        for c in shelf.select(':scope > .card-container'):
            ps = [t.find('p') for t in c.select('.cmp-text')[:3] if t.find('p')]
            if not ps:
                continue
            name = L.text(ps[0])
            header = '<h3>' + L.E(name) + '</h3>' + ''.join(L.clean(p) for p in ps[1:])
            items = []
            for it in c.select('.text-icon-item'):
                im = it.find('img')
                icon = ('<img src="' + L.E(L.img_url(im.get('src'))) + '" alt="">') if im and im.get('src') else ''
                items.append('<li>' + icon + L.E(L.text(it)) + '</li>')
            acts = []
            if name.lower() in PLAN_DETAILS:
                acts.append('<p><a href="' + PLAN_DETAILS[name.lower()] + '">Full Plan Details</a></p>')
            for a in c.select('a.cmp-button'):
                if a.get('href'):
                    acts.append('<p><a href="' + L.E(L.map_link(a['href'])) + '">'
                                + L.E(L.text(a).replace('→', '').strip()) + '</a></p>')
            out.append([header, '<ul>' + ''.join(items) + '</ul>' if items else '', ''.join(acts)])
        return out

    def _card_rows(self, cards):
        out = []
        for c in cards:
            im = c.find('img')
            pic = L.img(im.get('src') or im.get('data-src'), im.get('alt', ''), 750) if im else ''
            if im:
                im.decompose()
            body = _dedupe(L.clean(c, h1=False))
            link = c if c.name == 'a' else None
            if link is not None and link.get('href') and '<a ' not in body:
                body += '<p><a href="' + L.E(L.map_link(link['href'])) + '">' + L.E(L.text(link)[:60] or 'Learn more') + '</a></p>'
            if body.strip() or pic:
                out.append([pic, body] if pic else [body])
        return out

    def shelves(self):
        for shelf in self.el.select('.cmp-card-shelf'):
            if not shelf.parent:
                continue
            if self._is_plan_shelf(shelf):
                rows = self._plan_rows(shelf)
                if rows:
                    self._mark(shelf, L.block('plan-cards', rows), 'plan-cards')
                continue
            rows = self._card_rows(shelf.select(':scope > .card-container') or shelf.find_all(recursive=False))
            if rows:
                v = CFG.get('shelf_variant', '')
                texts = [re.sub(r'<[^>]+>', '', r[-1]).strip() for r in rows]
                if texts and all(t[:1] in '"“' for t in texts):
                    v = 'testimonials'
                self._mark(shelf, L.block(('cards ' + v).strip(), rows), 'cards (%s)' % v if v else 'cards')

    def link_tiles(self):
        tiles = self.el.select('a.cmp-container-link, .cmp-container-link')
        groups = {}
        for t in tiles:
            groups.setdefault(id(t.find_parent(class_='aem-Grid')), []).append(t)
        for g in groups.values():
            if len(g) >= 2:
                rows = self._card_rows(g)
                for t in g[1:]:
                    t.decompose()
                self._mark(g[0], L.block('cards', rows), 'cards (tiles)')

    def grids(self):
        for grid in reversed(self.el.select('.aem-Grid')):
            if not grid.parent:
                continue
            kids = [k for k in grid.find_all(recursive=False) if L.text(k) or k.find('img')]
            cols = [k for k in kids if 3 <= _width(k) <= 9]
            if len(cols) < 2 or len(cols) != len(kids) or not grid.find('img'):
                continue
            rows, row, w = [], [], 0
            for k in cols:
                if row and w + _width(k) > 12:
                    rows.append(row)
                    row, w = [], 0
                row.append(_dedupe(L.clean(k)))
                w += _width(k)
            if row:
                rows.append(row)
            n = max(len(r) for r in rows)
            rows = [r + [''] * (n - len(r)) for r in rows]
            self._mark(grid, L.block('columns', rows), 'columns')

    def convert(self):
        self.accordions()
        self.shelves()
        self.link_tiles()
        self.grids()
        html_ = _dedupe(L.clean(self.el))
        # blocks may nest markers (e.g. cards inside a column); resolve until stable
        for _ in range(5):
            changed = False
            for k, v in self.blocks.items():
                if k in html_:
                    html_ = html_.replace('<p>' + k + '</p>', v).replace(k, '')
                    changed = True
            if not changed:
                break
        return html_


def convert(src_html, first_h1=True):
    """Return (sections_html list, component summary list, soup)."""
    soup = BeautifulSoup(src_html, 'html.parser')
    meta_soup = BeautifulSoup(src_html, 'html.parser')
    out, summary = [], []
    for i, k in enumerate(top_sections(soup)):
        s = Section(k)
        h = s.convert()
        if not BeautifulSoup(h, 'html.parser').get_text(strip=True) and '<img' not in h:
            continue
        out.append(h)
        summary.append((i, s.found or ['default content']))
    # keep exactly one h1: first heading of the page
    doc = BeautifulSoup(''.join('<section>' + s + '</section>' for s in out), 'html.parser')
    h1s = doc.find_all('h1')
    if first_h1 and not h1s:
        first = doc.find(['h2', 'h3'])
        if first:
            first.name = 'h1'
    for extra in h1s[1:]:
        extra.name = 'h2'
    out = [s.decode_contents() for s in doc.find_all('section', recursive=False)]
    return out, summary, meta_soup
