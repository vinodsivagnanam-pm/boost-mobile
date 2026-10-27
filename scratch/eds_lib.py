"""Shared helpers: source HTML -> DA-ready HTML, link mapping, DA upload/preview.

Usage: import from scratch scripts. Requires bs4 and ~/.da-token for uploads.
"""
import csv
import html
import os
import subprocess
import urllib.parse

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = 'www.boostmobile.com'
REC = os.path.join(ROOT, 'migration', HOST)
ORG, SITE = 'vinodsivagnanam-pm', 'boost-mobile'
LIVE_ORIGIN = 'https://' + HOST

# Source PDPs present in the sandbox catalog -> drop-in PDP URL
PDP_MAP = {
    LIVE_ORIGIN + '/shop/iphone-16e.html': '/products/iphone-16e/002481',
    LIVE_ORIGIN + '/shop/pixel-10a-002729.html': '/products/google-pixel-10a/002729',
    LIVE_ORIGIN + '/shop/galaxy-a16-5g.html': '/products/samsung-galaxy-a16-5g/002198',
    LIVE_ORIGIN + '/shop/galaxy-a16-5g-002198.html': '/products/samsung-galaxy-a16-5g/002198',
}


def img_url(src, width=None):
    """Absolute image URL; scene7 renditions are re-requested at `width` (keeps aspect ratio)."""
    u = urllib.parse.urljoin(LIVE_ORIGIN + '/', src or '')
    if 'scene7.com/is/image/' in u and width:
        u = u.split('?')[0] + '?fmt=png-alpha&wid=' + str(width)
    return u


def img(src, alt='', width=None):
    return '<img src="' + html.escape(img_url(src, width)) + '" alt="' + html.escape(alt or '') + '">'

_rows = None


def rows():
    global _rows  # pylint: disable=global-statement
    if _rows is None:
        _rows = {r['source_url'].rstrip('/'): r for r in csv.DictReader(open(os.path.join(REC, 'urls.csv')))}
    return _rows


def map_link(href, base=LIVE_ORIGIN):
    """Return the destination for a source link: local path if migrated, else absolute live URL."""
    if href and href.startswith(('/modals/', '/products/')):
        return href  # already a destination path
    if not href or href.startswith(('#', 'tel:', 'mailto:', 'javascript:')):
        return None if (href or '').startswith('javascript:') else href
    u = urllib.parse.urljoin(base + '/', href)
    p = urllib.parse.urlsplit(u)
    clean = urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, '', '')).rstrip('/')
    if clean in PDP_MAP:
        return PDP_MAP[clean]
    r = rows().get(clean)
    if (r and r['status'] != 'excluded' and r['destination_path']
            and r['page_classification'] != 'custom' and '<' not in r['destination_path']
            and not p.query):
        return r['destination_path'] + (('#' + p.fragment) if p.fragment else '')
    return u


ALLOWED = {'p', 'ul', 'ol', 'li', 'strong', 'em', 'a', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'img', 'sup', 'sub', 's', 'del'}
RENAME = {'b': 'strong', 'i': 'em', 'h1': 'h2'}


def clean(el, base=LIVE_ORIGIN):
    """Return simplified HTML string of el's children."""
    soup = BeautifulSoup(str(el), 'html.parser')
    root = soup.find()
    for t in root.find_all(['script', 'style', 'svg', 'button', 'noscript', 'form', 'iframe']):
        t.decompose()
    for t in list(root.find_all(True)):
        if t.name in RENAME:
            t.name = RENAME[t.name]
        if t.name not in ALLOWED:
            t.unwrap()
            continue
        attrs = {}
        if t.name == 'a':
            h = map_link(t.get('href'), base)
            if not h:
                t.unwrap()
                continue
            attrs['href'] = h
        if t.name == 'img':
            src = t.get('src') or t.get('data-src') or ''
            if not src:
                t.decompose()
                continue
            attrs['src'] = urllib.parse.urljoin(base + '/', src)
            attrs['alt'] = t.get('alt', '')
        t.attrs = attrs
    # collapse nested identical inline tags (e.g. strong>strong)
    for t in root.find_all(['strong', 'em']):
        if t.parent and t.parent.name == t.name:
            t.unwrap()
    # move trailing <br> out of inline tags (EDS drops them inside strong/em)
    for t in root.find_all(['strong', 'em', 'a']):
        while t.contents and (getattr(t.contents[-1], 'name', None) == 'br'
                              or (isinstance(t.contents[-1], NavigableString) and not t.contents[-1].strip()
                                  and len(t.contents) > 1 and getattr(t.contents[-2], 'name', None) == 'br')):
            last = t.contents[-1].extract()
            if getattr(last, 'name', None) == 'br':
                t.insert_after(last)
    # drop empty blocks
    for t in root.find_all(['p', 'li', 'strong', 'em', 'h2', 'h3', 'h4']):
        if not t.get_text(strip=True).replace('\xa0', '') and not t.find('img'):
            t.decompose()
    out = root.decode_contents()
    # bare text at root -> wrap in p
    frag = BeautifulSoup(out, 'html.parser')
    parts = []
    buf = ''
    for n in frag.contents:
        if isinstance(n, NavigableString) or (isinstance(n, Tag) and n.name in ('a', 'strong', 'em', 'br', 'sup', 'sub', 'img')):
            buf += str(n)
        else:
            if buf.strip():
                parts.append('<p>' + buf.strip() + '</p>')
            buf = ''
            parts.append(str(n))
    if buf.strip():
        parts.append('<p>' + buf.strip() + '</p>')
    return '\n'.join(p for p in parts if p.strip())


def page(sections):
    """Wrap section HTML strings into a DA document."""
    body = ''.join('<div>' + s + '</div>' for s in sections)
    return '<body><header></header><main>' + body + '</main><footer></footer></body>'


def block(name, rows_):
    """Build a block table. rows_: list of lists of cell HTML."""
    r = ''.join('<div>' + ''.join('<div>' + c + '</div>' for c in row) + '</div>' for row in rows_)
    return '<div class="' + html.escape(name) + '">' + r + '</div>'


def _token():
    return open(os.path.expanduser('~/.da-token')).read().strip()


def upload(path, doc, preview=True):
    """PUT doc to DA at /<path>.html and optionally trigger preview. Returns (put_status, preview_status)."""
    path = path.strip('/')
    tmp = '/tmp/_da_upload.html'
    open(tmp, 'w').write(doc)
    auth = 'Authorization: Bearer ' + _token()
    put = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-X', 'PUT', '-H', auth,
                          '-F', 'data=@' + tmp + ';type=text/html',
                          f'https://admin.da.live/source/{ORG}/{SITE}/{path}.html'], capture_output=True, text=True).stdout
    prev = ''
    if preview:
        prev = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-X', 'POST', '-H', auth,
                               f'https://admin.hlx.page/preview/{ORG}/{SITE}/main/{path}'], capture_output=True, text=True).stdout
    os.remove(tmp)
    return put, prev
