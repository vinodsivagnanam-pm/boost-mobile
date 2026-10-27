"""ReadMe.io knowledge base (e.g. help.<brand>.com/docs/<slug>) -> EDS document sections.

Same contract as aem_core.convert(html) -> (sections, summary, soup).

  .rm-PageHeader-title           -> h1
  .rm-Markdown headings          -> h2..h6 (body h1 shifted down one level)
  <details><summary>             -> accordion (consecutive items grouped)
  blockquote / .callout_<theme>  -> callout (<theme> variant, e.g. callout info)
  table / .rdmd-table            -> table
  iframe                         -> link to the embedded URL (recorded as a gap in the summary)
  Cloudflare-obfuscated emails   -> mailto links
Everything else becomes default content via lib.clean.
"""
import re
import urllib.parse

from bs4 import BeautifulSoup, Declaration, Doctype, Tag

import lib as L

SPECIAL = ('details', 'blockquote', 'table')
HEADINGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']


def detect(html):
    return 'rm-ReadMe' in html and ('rm-Markdown' in html or 'rm-Header_landing' in html)


def _origin(soup):
    link = soup.find('link', rel='canonical')
    u = urllib.parse.urlsplit(link['href']) if link and link.get('href') else None
    return u.scheme + '://' + u.netloc if u and u.netloc else L.LIVE_ORIGIN


def _cf_decode(enc):
    try:
        key = int(enc[:2], 16)
        return ''.join(chr(int(enc[i:i + 2], 16) ^ key) for i in range(2, len(enc), 2))
    except ValueError:
        return ''


def _prepare(md, soup, gaps):
    for t in md.find_all(['style', 'script', 'meta', 'title', 'link']):
        t.decompose()
    for t in md.select('.heading-anchor, .heading-anchor-icon, .callout-icon'):
        t.decompose()
    for t in md.find_all(string=lambda x: isinstance(x, (Doctype, Declaration))):
        t.extract()
    for t in md.find_all(['html', 'head', 'body', 'ins']):
        t.unwrap()
    for li in md.find_all('li'):
        if li.parent and li.parent.name not in ('ul', 'ol') and not li.find_parent(['ul', 'ol']):
            ul = soup.new_tag('ul')
            li.insert_before(ul)
            nxt = ul.next_sibling
            while nxt is not None and (getattr(nxt, 'name', None) in ('li', 'br') or (not isinstance(nxt, Tag) and not str(nxt).strip())):
                after = nxt.next_sibling
                if getattr(nxt, 'name', None) == 'li':
                    ul.append(nxt.extract())
                else:
                    nxt.extract()
                nxt = after
    for t in md.select('.heading-text'):
        t.unwrap()
    for t in md.find_all('hr'):
        t.decompose()
    for t in md.select('[data-cfemail]'):
        email = _cf_decode(t['data-cfemail'])
        a = t if t.name == 'a' else t.find_parent('a') or t
        new = soup.new_tag('a', href='mailto:' + email)
        new.string = email
        a.replace_with(new if email else '')
    for f in md.find_all('iframe'):
        src = f.get('src', '')
        gaps.append('iframe ' + urllib.parse.urlsplit(src).netloc)
        p = soup.new_tag('p')
        a = soup.new_tag('a', href=src)
        a.string = f.get('title') or src
        p.append(a)
        (f.find_parent('div', class_='rdmd-html') or f).replace_with(p)
    if md.find('h1'):
        for h in md.find_all(HEADINGS):
            h.name = 'h' + str(min(int(h.name[1]) + 1, 6))


def _flatten(node):
    """Yield top-level content nodes, descending into wrappers that hold blocks."""
    for c in list(node.children):
        if isinstance(c, Tag) and c.name not in SPECIAL and c.name in ('div', 'span', 'section', 'figure') \
                and c.find(SPECIAL):
            yield from _flatten(c)
        else:
            yield c


def _label(summary, base):
    for h in summary.find_all(HEADINGS):
        h.unwrap()
    return L.clean(summary, base, h1=False, arrows=True)


def _accordion_row(d, base):
    s = d.find('summary')
    label = _label(s.extract(), base) if s else ''
    return [label or '<p>Details</p>', L.clean(d, base, h1=False, arrows=True)]


def _callout(bq, base):
    theme = next((c.split('_', 1)[1] for c in bq.get('class') or [] if c.startswith('callout_')), '')
    variant = '' if theme in ('', 'default') else ' ' + theme
    return L.block('callout' + variant, [[L.clean(bq, base, h1=False, arrows=True)]]), 'callout' + variant


def _table(t, base):
    rows = []
    for tr in t.find_all('tr'):
        cells = [L.clean(c, base, h1=False, arrows=True) or '' for c in tr.find_all(['th', 'td'], recursive=False)]
        if any(cells):
            rows.append(cells)
    return L.block('table', rows) if rows else ''


def _landing(soup, base):
    """Custom ReadMe landing page: headings, then topic cards (icon + h2 + links) -> cards."""
    root = soup.select_one('.rm-ReadMe') or soup.body
    for t in root.select('header, footer, .rm-Header, .rm-Footer, nav, .rm-SearchModal'):
        t.decompose()
    heads = [L.text(h) for h in root.find_all('h1') if L.text(h)]
    rows = []
    for card in root.find_all('div'):
        h2, im = card.find('h2', recursive=False), card.find('img', recursive=False)
        if not h2 or not im:
            continue
        pic = L.img(im.get('src'), im.get('alt', ''))
        im.decompose()
        body = L.clean(card, base, h1=False, arrows=True)
        rows.append([pic, body])
    if not heads and not rows:
        return [], [], soup
    out = ['<h1>' + L.E(heads[0]) + '</h1>'] if heads else []
    out += ['<p>' + L.E(h) + '</p>' for h in heads[1:]]
    names = ['default content']
    if rows:
        out.append(L.block('cards', rows))
        names.append('cards')
    return ['\n'.join(out)], [(0, names + ['GAP: ReadMe search widget'])], soup


def convert(html):
    soup = BeautifulSoup(html, 'html.parser')
    base = _origin(soup)
    title = soup.select_one('.rm-PageHeader-title')
    excerpt = soup.select_one('.rm-PageHeader-excerpt .rm-Markdown')
    md = (soup.select_one('.rm-Article .content-body .rm-Markdown')
          or next((m for m in soup.select('.rm-Markdown')
                   if m is not excerpt and not m.find_parent(class_=re.compile('WhatsNext'))), None))
    if md is None:
        return _landing(soup, base) if 'rm-Header_landing' in html else ([], [], soup)
    gaps = []
    _prepare(md, soup, gaps)

    out, names, buf, acc = [], [], [], []
    if title and title.get_text(strip=True):
        out.append('<h1>' + L.E(L.text(title)) + '</h1>')
    if excerpt and excerpt.get_text(strip=True):
        out.append(L.clean(excerpt, base, h1=False, arrows=True))

    def flush_buf():
        if buf:
            wrap = soup.new_tag('div')
            for n in buf:
                wrap.append(n)
            h = L.clean(wrap, base, h1=False, arrows=True)
            if h.strip():
                out.append(h)
                names.append('default content')
            buf.clear()

    def flush_acc():
        if acc:
            out.append(L.block('accordion', acc[:]))
            names.append('accordion')
            acc.clear()

    for n in _flatten(md):
        if isinstance(n, Tag) and n.name == 'details':
            flush_buf()
            acc.append(_accordion_row(n, base))
            continue
        if isinstance(n, Tag) and n.name in ('br',) or (not isinstance(n, Tag) and not str(n).strip()):
            continue
        flush_acc()
        if isinstance(n, Tag) and n.name == 'blockquote':
            flush_buf()
            b, name = _callout(n, base)
            out.append(b)
            names.append(name)
        elif isinstance(n, Tag) and (n.name == 'table' or 'rdmd-table' in (n.get('class') or [])):
            flush_buf()
            t = n if n.name == 'table' else n.find('table')
            b = _table(t, base) if t else ''
            if b:
                out.append(b)
                names.append('table')
        else:
            buf.append(n.extract() if isinstance(n, Tag) else n)
    flush_buf()
    flush_acc()
    body = re.sub(r'\n{2,}', '\n', '\n'.join(out))
    if not names:
        return [], [], soup
    summary = [(0, sorted(set(names)) + (['GAP: ' + g for g in gaps] if gaps else []))]
    return [body], summary, soup
