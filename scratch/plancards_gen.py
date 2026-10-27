"""Convert source .cmp-card-shelf plan cards into a `plan-cards` block table."""
import re
from bs4 import BeautifulSoup
import eds_lib as L

DETAILS = {'unlimited': '/modals/plans/unlimited-details', 'unlimited+': '/modals/plans/unlimited-plus-details',
           'unlimited premium': '/modals/plans/unlimited-premium-details',
           'global connection': '/modals/plans/global-connection-details'}


def is_plan_shelf(shelf):
    names = [p.get_text(strip=True).lower() for p in shelf.select('.card-container .cmp-text p:first-child')]
    return any(n in DETAILS for n in names)


def card_rows(shelf):
    out = []
    for c in shelf.select(':scope > .card-container'):
        texts = [t for t in c.select('.cmp-text') if not t.find_parent(class_='cmp-modal__info')]
        ps = [t.find('p') for t in texts[:3] if t.find('p')]
        if not ps:
            continue
        name = ps[0].get_text(strip=True)
        header = '<h3>' + L.html.escape(name) + '</h3>' + ''.join(str(L.clean(p)) for p in ps[1:])
        items = []
        for it in c.select('.text-icon-item'):
            img = it.find('img')
            txt = ' '.join(it.get_text(' ', strip=True).split())
            icon = ''
            if img and img.get('src'):
                icon = '<img src="' + L.map_link(img['src']) + '" alt="">'
            items.append('<li>' + icon + L.html.escape(txt) + '</li>')
        feats = '<ul>' + ''.join(items) + '</ul>' if items else ''
        acts = []
        d = DETAILS.get(name.lower())
        if d:
            acts.append('<p><a href="' + d + '">Full Plan Details</a></p>')
        for a in c.select('a.cmp-button'):
            if a.find_parent(class_='cmp-modal__info') or not a.get('href'):
                continue
            label = ' '.join(a.get_text(' ', strip=True).replace('→', '').split())
            acts.append('<p><a href="' + L.map_link(a['href']) + '">' + L.html.escape(label) + '</a></p>')
        out.append([header, feats, ''.join(acts)])
    return out


def plan_cards(soup):
    shelf = next((s for s in soup.select('.cmp-card-shelf') if is_plan_shelf(s)), None)
    return L.block('plan-cards', card_rows(shelf)) if shelf else None


if __name__ == '__main__':
    s = BeautifulSoup(open('/tmp/boost/s_plans.html', errors='ignore').read(), 'html.parser')
    b = plan_cards(s)
    print(b[:1500])
    doc = L.page(['<h2>Plan cards test</h2>' + b])
    open('../migration/www.boostmobile.com/content/drafts__plan-cards.html', 'w').write(doc)
    print(L.upload('/drafts/plan-cards', doc))
