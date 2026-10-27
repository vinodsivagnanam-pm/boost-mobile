"""Shared migration helpers: configuration, source fetch cache, link mapping,
HTML cleanup for DA, block tables, and DA upload/preview.

Configuration comes from the migration record, not from code:
  MIGRATION_HOST   source host, e.g. www.example.com (required)
  migration/<host>/site.json   destination.repository = "<org>/<site>"
  migration/<host>/urls.csv    source_url -> destination_path (link rewriting)
  migration/<host>/link-map.csv (optional) source_url,destination_path overrides
      (e.g. legacy product URLs -> /products/<urlKey>/<sku>)
  site.json locales (optional) per urls.csv locale: source host, destination
      prefix, language and nav/footer fragments (see MIGRATION.md, Locales)
DA auth: a bearer token in $DA_TOKEN or ~/.da-token (never commit it).
"""
import csv
import hashlib
import html
import json
import os
import re
import subprocess
import urllib.parse

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOST = os.environ.get('MIGRATION_HOST', '')
if not HOST:
    raise SystemExit('Set MIGRATION_HOST to the source host (see MIGRATION.md).')
REC = os.path.join(ROOT, 'migration', HOST)
LIVE_ORIGIN = 'https://' + HOST
SITE_JSON = json.load(open(os.path.join(REC, 'site.json')))
ORG, SITE = SITE_JSON['destination']['repository'].split('/')
LOCALES = SITE_JSON.get('locales', {})
LOCALE_HOSTS = {v['host']: k for k, v in LOCALES.items() if v.get('host')}
CACHE = os.environ.get('MIGRATION_CACHE', os.path.join('/tmp', 'migration-cache', HOST))
E = html.escape

# Elements hidden at the desktop breakpoint duplicate content for smaller screens.
RESPONSIVE_DUPLICATE = ['aem-GridColumn--default--hide']
# Overlays/modals are migrated separately (see /modals/ in MIGRATION.md).
OVERLAY = ['cmp-modal', 'cmp-md-overlay', 'cmp-modal__info', 'cmp-modal-overlay']


def _read_csv(name):
    p = os.path.join(REC, name)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


_rows = None
_links = None


def rows():
    global _rows  # pylint: disable=global-statement
    if _rows is None:
        _rows = {r['source_url'].rstrip('/'): r for r in _read_csv('urls.csv')}
    return _rows


def link_overrides():
    global _links  # pylint: disable=global-statement
    if _links is None:
        _links = {r['source_url'].rstrip('/'): r['destination_path'] for r in _read_csv('link-map.csv')}
    return _links


def fetch(url):
    """Fetch source HTML with a local cache (desktop UA)."""
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest() + '.html')
    if not os.path.exists(f) or os.path.getsize(f) == 0:
        r = subprocess.run(['curl', '-sL', '--max-time', '40', '-A',
                            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',
                            '-o', f, '-w', '%{http_code}', url], capture_output=True, text=True)
        if r.stdout != '200':
            if os.path.exists(f):
                os.remove(f)
            raise RuntimeError('fetch ' + r.stdout + ' ' + url)
    return open(f, errors='ignore').read()


def img_url(src, width=None):
    """Absolute image URL; Scene7 renditions are re-requested at `width` (keeps aspect ratio)."""
    u = urllib.parse.urljoin(LIVE_ORIGIN + '/', src or '')
    if 'scene7.com/is/image/' in u:
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)
        w = width or (q.get('wid') or ['1200'])[0]
        u = u.split('?')[0] + '?fmt=png-alpha&wid=' + str(w)
    return u


def img(src, alt='', width=None):
    return '<img src="' + E(img_url(src, width)) + '" alt="' + E(alt or '') + '">'


def eds_path(path):
    """EDS-safe destination path: lowercase segments of [a-z0-9-] (underscores and other characters become hyphens)."""
    segs = [re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-') for s in path.split('/')]
    return '/' + '/'.join(s for s in segs if s)


def map_link(href, base=LIVE_ORIGIN):
    """Destination for a source link: local path if migrated, else the absolute live URL."""
    if href and href.startswith(('/modals/', '/products/')):
        return href
    if not href or href.startswith(('#', 'tel:', 'mailto:', 'javascript:')):
        return None if (href or '').startswith('javascript:') else href
    u = urllib.parse.urljoin(base + '/', href)
    p = urllib.parse.urlsplit(u)
    clean_u = urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, '', '')).rstrip('/')
    if clean_u in link_overrides():
        return link_overrides()[clean_u]
    r = rows().get(clean_u)
    if (r and r['status'] != 'excluded' and r['destination_path']
            and r['page_classification'] != 'custom' and '<' not in r['destination_path']
            and not p.query):
        d = r['destination_path']
        d = d if ('?' in d or ':' in d) else eds_path(d) or '/'
        return d + (('#' + p.fragment) if p.fragment else '')
    if p.netloc in LOCALE_HOSTS and not p.query:
        # No translated page: fall back to the default-locale page if it was migrated.
        en = map_link(urllib.parse.urlunsplit(('https', HOST, p.path, '', p.fragment)))
        if en and en.startswith('/'):
            return en
    return u


def locale_metadata(locale):
    """Extra metadata rows for pages of a non-default locale (site.json locales)."""
    c = LOCALES.get(locale or '')
    if not c:
        return {}
    return {k.capitalize(): E(c[k]) for k in ('language', 'nav', 'footer') if c.get(k)}


ALLOWED = {'p', 'ul', 'ol', 'li', 'strong', 'em', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br',
           'img', 'sup', 'sub', 's', 'del', 'table', 'thead', 'tbody', 'tr', 'td', 'th'}
RENAME = {'b': 'strong', 'i': 'em', 'strike': 's'}
INLINE = ('a', 'strong', 'em', 'br', 'sup', 'sub', 'img', 's', 'del')


def strip_noise(root):
    """Remove scripts, overlays, and responsive duplicates in place."""
    for t in root.find_all(['script', 'style', 'noscript', 'svg', 'form', 'iframe', 'template']):
        t.decompose()
    for c in root.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for c in OVERLAY + RESPONSIVE_DUPLICATE:
        for t in root.find_all(class_=c):
            t.decompose()
    return root


def clean(el, base=LIVE_ORIGIN, h1=True, arrows=False):
    """Return simplified, DA-safe HTML for el's children. arrows=False drops decorative CTA arrows (\u2192)."""
    soup = BeautifulSoup(str(el), 'html.parser')
    root = soup.find()
    if root is None:
        return ''
    strip_noise(root)
    for t in root.find_all('button'):
        t.decompose()
    for t in list(root.find_all(True)):
        if t.name in RENAME:
            t.name = RENAME[t.name]
        if t.name == 'h1' and not h1:
            t.name = 'h2'
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
            if not src or src.startswith('data:'):
                t.decompose()
                continue
            w = str(t.get('width') or '').replace('px', '')
            attrs['src'] = img_url(src, int(w) if w.isdigit() and int(w) < 600 else None)
            if w.isdigit():
                attrs['width'] = w
            attrs['alt'] = t.get('alt', '')
        if t.name in ('td', 'th') and t.get('colspan'):
            attrs['colspan'] = t['colspan']
        t.attrs = attrs
    for n in list(root.find_all(string=True)):
        v = re.sub(r'\s+', ' ', n if arrows else n.replace('\u2192', ''))
        if v != n:
            n.replace_with(v)
    for t in root.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        if t.contents and isinstance(t.contents[0], NavigableString):
            t.contents[0].replace_with(t.contents[0].lstrip())
        if t.contents and isinstance(t.contents[-1], NavigableString):
            t.contents[-1].replace_with(t.contents[-1].rstrip())
    for t in root.find_all(['strong', 'em']):
        if t.parent and t.parent.name == t.name:
            t.unwrap()
    for t in root.find_all(['strong', 'em', 'a']):
        while t.contents and getattr(t.contents[-1], 'name', None) == 'br':
            t.insert_after(t.contents[-1].extract())
    for t in root.find_all(['p', 'li', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a']):
        if not t.get_text(strip=True).replace('\xa0', '') and not t.find('img'):
            if t.name in ('strong', 'em', 'a') and t.get_text():
                t.replace_with(' ')
            else:
                t.decompose()
    parts, buf = [], ''
    for n in root.contents:
        if isinstance(n, NavigableString) or (isinstance(n, Tag) and n.name in INLINE):
            buf += str(n)
        else:
            if re.sub(r'<br\s*/?>|\s', '', buf):
                parts.append('<p>' + buf.strip() + '</p>')
            buf = ''
            parts.append(str(n))
    if re.sub(r'<br\s*/?>|\s', '', buf):
        parts.append('<p>' + buf.strip() + '</p>')
    out = '\n'.join(p for p in parts if p.strip())
    out = re.sub(r'(\s+)</(a|strong|em)>', r'</\2>\1', out)
    out = re.sub(r'<(a|strong|em)(\s[^>]*)?>(\s+)', r'\3<\1\2>', out)
    out = re.sub(r'\s+</(p|li|h[1-6])>', r'</\1>', out)
    return re.sub(r'<(p|li|h[1-6])(\s[^>]*)?>\s+', r'<\1\2>', out)


def text(el):
    return ' '.join(el.get_text(' ', strip=True).split())


def page(sections):
    body = ''.join('<div>' + s + '</div>' for s in sections if s and s.strip())
    return '<body><header></header><main>' + body + '</main><footer></footer></body>'


def block(name, rows_):
    r = ''.join('<div>' + ''.join('<div>' + c + '</div>' for c in row) + '</div>' for row in rows_)
    return '<div class="' + E(name) + '">' + r + '</div>'


def metadata(soup, extra=None):
    """Metadata block from the source <title>, description and og:image."""
    def meta(**kw):
        m = soup.find('meta', attrs=kw)
        return (m.get('content') or '').strip() if m else ''
    pairs = [['Title', E(soup.title.get_text(strip=True)) if soup.title else ''],
             ['Description', E(meta(name='description'))]]
    og = meta(property='og:image')
    if og:
        pairs.append(['Image', img(og)])
    for k, v in (extra or {}).items():
        pairs.append([E(k), v])
    return block('metadata', [p for p in pairs if p[1]])


def _token():
    t = os.environ.get('DA_TOKEN')
    return t.strip() if t else open(os.path.expanduser('~/.da-token')).read().strip()


def upload(path, doc, preview=True):
    """PUT doc to DA at /<path>.html and optionally preview. Returns (put_status, preview_status)."""
    path = path.strip('/') or 'index'
    tmp = os.path.join('/tmp', '_da_upload_' + str(os.getpid()) + '.html')
    open(tmp, 'w').write(doc)
    auth = 'Authorization: Bearer ' + _token()
    put = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-X', 'PUT', '-H', auth,
                          '-F', 'data=@' + tmp + ';type=text/html',
                          f'https://admin.da.live/source/{ORG}/{SITE}/{path}.html'],
                         capture_output=True, text=True).stdout
    prev = ''
    if preview and put in ('200', '201'):
        prev = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-X', 'POST', '-H', auth,
                               f'https://admin.hlx.page/preview/{ORG}/{SITE}/main/{path}'],
                              capture_output=True, text=True).stdout
    os.remove(tmp)
    return put, prev


def content_file(path):
    """Versioned local copy of the DA source: migration/<host>/content/<path with __>.html."""
    name = (path.strip('/') or 'index').replace('/', '__') + '.html'
    return os.path.join(REC, 'content', name)
