#!/usr/bin/env python3
"""Build translated nav/footer fragments for a locale from the default ones.

  MIGRATION_HOST=www.example.com python3 tools/migrate/localize.py --locale es-US [--dry-run]

Reads site.json locales[<locale>] (host, prefix, nav, footer) and the versioned
default fragments content/nav.html and content/footer.html. Labels are translated
by pairing elements at the same DOM position on the default and locale source
homepages (translation proxies such as MotionPoint keep the DOM identical); labels
without a pair stay unchanged and are reported. Local links are rewritten to the
locale page when urls.csv has one for that locale, and the link to the locale home
becomes a link back to the default home.
"""
import argparse
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib as L  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

BLOCKISH = ['p', 'div', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'ul']


def leaves(url):
    """{(dom path, occurrence): text} for leaf text elements of a source page."""
    s = BeautifulSoup(L.fetch(url), 'html.parser')
    L.strip_noise(s.body)
    seen, out = Counter(), {}
    for el in s.body.find_all(True):
        if el.name != 'a' and el.find(BLOCKISH):
            continue
        t = el.get_text(' ', strip=True)
        if not t:
            continue
        path = '/'.join(p.name + '.' + '.'.join(sorted(p.get('class') or []))
                        for p in reversed(list(el.parents)) if p.name != '[document]') + '/' + el.name
        k = (path, seen[path])
        seen[path] += 1
        out[k] = t
    return out, s


def label_map(default_home, locale_home):
    d, _ = leaves(default_home)
    t, soup = leaves(locale_home)
    m = {}
    for k, text in d.items():
        if k in t and t[k] != text:
            m.setdefault(text.lower(), t[k])
    return m, soup


def match_case(src, dst):
    """Sentence-case all-caps translations when the default label is not all caps;
    words capitalized in the default label (brand names) keep their capital."""
    if not dst.isupper() or src.isupper():
        return dst
    keep = {w.lower() for w in src.split() if w[:1].isupper()}
    words = dst.lower().split(' ')
    out = [w.capitalize() if (i == 0 or w in keep) else w for i, w in enumerate(words)]
    return ' '.join(out)


def localize(doc, m, locale, prefix, back_label):
    soup = BeautifulSoup(doc, 'html.parser')
    dest = {r['destination_path'].rstrip('/') for r in L.rows().values()
            if r.get('locale') == locale and r['status'] not in ('excluded', 'blocked')}
    missing = []
    for a in soup.find_all('a', href=True):
        h = a['href']
        if not h.startswith('/'):
            continue
        path, _, frag = h.partition('#')
        if path.rstrip('/') == prefix:
            a['href'] = '/'
            a.string = back_label
            continue
        cand = prefix + (path if path != '/' else '')
        if cand.rstrip('/') in dest:
            a['href'] = cand + ('#' + frag if frag else '')
    for node in soup.find_all(string=True):
        txt = node.strip()
        if not txt or node.parent.name in ('a',) and node.parent.string == back_label:
            continue
        tr = m.get(txt.lower())
        if tr:
            node.replace_with(node.replace(txt, match_case(txt, tr)))
        elif any(c.isalpha() for c in txt):
            missing.append(txt)
    return str(soup), missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--locale', required=True)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    c = L.LOCALES.get(a.locale)
    if not c:
        raise SystemExit('No site.json locales entry for ' + a.locale)
    prefix = c.get('prefix', '').rstrip('/')
    m, lsoup = label_map(L.LIVE_ORIGIN + '/', 'https://' + c['host'] + '/')
    back = next((x.get_text(strip=True) for x in lsoup.find_all('a', href=True)
                 if x['href'].rstrip('/') == L.LIVE_ORIGIN and x.get_text(strip=True)), 'English')
    print(len(m), 'translated labels; back link label', repr(back))
    for name in ('nav', 'footer'):
        target = c.get(name)
        src = L.content_file('/' + name)
        if not target or not os.path.exists(src):
            print('skip', name)
            continue
        doc, missing = localize(open(src).read(), m, a.locale, prefix, back)
        print(name, '->', target, '| untranslated:', sorted(set(missing)))
        if a.dry_run:
            continue
        open(L.content_file(target), 'w').write(doc)
        print('upload', L.upload(target, doc))


if __name__ == '__main__':
    main()
