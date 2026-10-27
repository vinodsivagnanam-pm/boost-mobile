"""Homepage (/) -> DA /index. Section mapping per components.csv home-s00..s16."""
import re
from bs4 import BeautifulSoup
import eds_lib as L
from sections import section_elements
from plancards_gen import plan_cards, DETAILS

E = L.html.escape
SRC = '/tmp/boost/home.html'


def a(href, text):
    return '<a href="' + E(L.map_link(href) or href) + '">' + E(text) + '</a>'


def p(x):
    return '<p>' + x + '</p>'


def txt(el):
    return ' '.join(el.get_text(' ', strip=True).split())


def uniq_paras(root):
    """Visible text paragraphs/headings in order, deduped (source repeats content per breakpoint)."""
    out, seen = [], set()
    for el in root.select('.cmp-text p, .cmp-text h1, .cmp-text h2, .cmp-text h3, .cmp-title__text'):
        if el.find_parent(class_='cmp-modal__info'):
            continue
        t = txt(el)
        if t and t not in seen:
            seen.add(t)
            out.append(el)
    return out


def buttons(root):
    out, seen = [], set()
    for b in root.select('a.cmp-button'):
        if b.find_parent(class_='cmp-modal__info') or not b.get('href'):
            continue
        label = txt(b).replace('→', '').strip()
        if (label, b['href']) in seen:
            continue
        seen.add((label, b['href']))
        out.append((label, b['href']))
    return out


def para_html(el, tag=None):
    c = L.clean(el)
    inner = c.decode_contents() if hasattr(c, 'decode_contents') else str(c)
    inner = re.sub(r'^<p>(.*)</p>$', r'\1', inner.strip(), flags=re.S)
    t = tag or ('p' if el.name in ('p', 'div', 'span') else el.name)
    if t == 'h1':
        t = 'h1'
    return '<' + t + '>' + inner + '</' + t + '>'


def build():
    soup, ks = section_elements(SRC)
    sec = []

    # S00 hero carousel: two promos. Background | text + CTA | product image
    hero_rows = [
        [L.img('https://s7d1.scene7.com/is/image/dish/Sponge_Splatter_Background_Big', 'Orange background', 1600),
         '<h1>$10/MO FOR YOUR FIRST 6 MONTHS</h1><h3>Then $25/mo Forever</h3>'
         + p('<strong>' + a('https://www.boostmobile.com/plans/affordable-phone-plan', 'Shop Now') + '</strong>')
         + p('Terms apply.<sup>1</sup>'),
         L.img('https://s7d1.scene7.com/is/image/dish/Whats_Your_Plan_Tyson_Boxing_Extra_Small',
               'Mike Tyson in a grey hoodie throwing a punch towards the camera, with the words "WHAT\'S YOUR PLAN?" on his boxing glove.', 700)],
        [L.img('https://s7d1.scene7.com/is/image/dish/16e-portin-blue-halfbanner-mobile', 'Light blue background', 1600),
         '<h2>iPHONE 16e</h2>' + p('<del>$599.99</del> <strong>$29.99</strong>')
         + p('With our Unlimited Premium Plan when you keep your number')
         + p('<strong>' + a('/shop/iphone-16e.html', 'Shop Now') + '</strong>') + p('Terms Apply.<sup>4</sup>'),
         L.img('https://s7d1.scene7.com/is/image/dish/iPhone_16e_Black_Hero_Vertical_Apple_Intelligence', 'iPhone 16e', 574)],
    ]
    sec.append(L.block('carousel (hero)', hero_rows))

    # S01 quick links: icon + link
    ql = []
    for an in ks[1].select('a'):
        im = an.find('img')
        if not an.get('href') or any(an['href'] == r[1] for r in ql):
            continue
        ql.append((im, an['href'], txt(an)))
    sec.append(L.block('cards (quick-links)', [[L.img(im.get('src'), im.get('alt')) if im else '', p(a(h, t))] for im, h, t in ql]))

    # S02 intro + S03 plan cards
    s2 = uniq_paras(ks[2])
    sec.append(''.join(para_html(e, 'h2' if e.name == 'h2' else 'p') for e in s2) + plan_cards(soup))

    # S05 Affirm phone financing (Affirm flow unresolved -> live links)
    sec.append(L.block('columns', [[
        L.img('https://s7d1.scene7.com/is/image/dish/50-mo-sticker-hp', '$50/mo', 844),
        p('Our Most Popular Phone For') + '<h2>$25/mo</h2>' + p('with 0% APR for 24 mo. On Our Unlimited Plan')
        + p(L.img('https://s7d1.scene7.com/is/image/dish/affirm.logo3', 'affirm', 100))
        + p('<strong>' + a('https://www.boostmobile.com/shop/buy/permalink/entry/?planId=DSHHAR25&portIn=1&deviceId=195950051681&wayToPay=full', 'Get This Deal') + '</strong>')
        + p(a('/phone-financing-affirm', 'See How Affirm Works'))
        + p('Terms Apply. Subject to Credit Check.**')]]))

    # S06 + S07 testimonials
    s6 = uniq_paras(ks[6])
    t_rows = []
    for c in ks[7].select('.card-container'):
        ps = [x for x in uniq_paras(c)]
        link = c.find('a', href=True)
        quote, name = (txt(ps[0]), txt(ps[-1])) if len(ps) > 1 else (txt(c), '')
        t_rows.append([L.img('https://s7d1.scene7.com/is/image/dish/5_star_rating', 'Five star review', 200),
                       p(E(quote)) + p('<strong>' + E(name) + '</strong>')
                       + (p(a(link['href'], 'Read review')) if link else '')])
    sec.append(''.join(para_html(e) if e.name != 'h2' else '<h2>' + E(txt(e)) + '</h2>' for e in s6)
               + L.block('cards (testimonials)', t_rows)
               + p(L.img('https://s7d1.scene7.com/is/image/dish/Trustpilot-logolockup-black', 'Reviewed on Trustpilot', 670)))

    # S08 razr promo
    sec.append(L.block('columns (promo)', [[
        '<h2>motorola razr - 2025</h2>' + p('<del>$599.99</del> <strong>$29.99</strong>')
        + p('When you prepay for 2 months of our Unlimited Premium Plan and keep your number')
        + p('<strong>' + a('/shop/razr-2025.html', 'Shop Now') + '</strong>') + p('Terms apply.<sup>5</sup>'),
        L.img('https://s7d1.scene7.com/is/image/dish/Razr_25_Desktop_Banner', 'MOTO RAZR 25', 500)]]))

    # S09 + S10 features + S11 CTA
    s9 = uniq_paras(ks[9])
    feats = []
    imgs = [i for i in ks[10].find_all('img')]
    paras = uniq_paras(ks[10])
    for n, im in enumerate(imgs[:3]):
        title, body = paras[2 * n:2 * n + 2]
        feats.append([L.img(im.get('src'), im.get('alt'), 216), '<h3>' + E(txt(title)) + '</h3>' + p(E(txt(body)))])
    cta = buttons(ks[11])
    sec.append(''.join('<h2>' + E(txt(e)) + '</h2>' if e.name == 'h2' else p(E(txt(e))) for e in s9)
               + L.block('cards (features)', feats)
               + ''.join(p('<strong>' + a(h, t) + '</strong>') for t, h in cta))

    # S12 online offers
    offers = []
    for c in ks[12].select('.card-container'):
        ps = uniq_paras(c)
        im = c.find('img')
        body = '<p><em>' + E(txt(ps[0])) + '</em></p><h3>' + E(txt(ps[1])) + '</h3>' + ''.join(para_html(x) for x in ps[2:])
        plan = txt(ps[1]).lower()
        acts = ''
        if plan in DETAILS:
            acts += p(a(DETAILS[plan], 'Plan Details'))
        for t, h in buttons(c):
            acts += p('<strong>' + a(h, t) + '</strong>')
        offers.append([L.img(im.get('src'), im.get('alt'), 600) if im else '', body + acts])
    sec.append('<h2>Save When You Shop Online</h2>' + L.block('cards (offers)', offers))

    # S13 multi-line
    sec.append(L.block('columns', [[
        L.img('https://s7d1.scene7.com/is/image/dish/multi-line_phone', 'Orange Phone', 880),
        '<h2>SAVE UP TO $2,400 A YEAR</h2>' + p('Add up to 10 lines to get maximum savings!')
        + p('<strong>' + a('/plans/multiline', 'Save Now') + '</strong>')]]))

    # S14 in-store deals: source shelf renders client-side and is empty in the captured HTML
    sec.append('<h2>Shop In-Store Deals</h2>' + p(a('https://www.boostmobile.com/locations/locator/', 'Find a store near you')))

    # S16 Boost Cares
    s16 = uniq_paras(ks[16])
    sec.append(L.block('columns (promo)', [[
        ''.join('<h2>' + E(txt(e)) + '</h2>' if n == 0 else p(E(txt(e))) for n, e in enumerate(s16))
        + ''.join(p('<strong>' + a(h, t) + '</strong>') for t, h in buttons(ks[16])),
        L.img('https://s7d1.scene7.com/is/image/dish/Boost_Cares_Lifestyle_desktopV2a', 'Woman helping sort through donations', 824)]])
        + p(a('/modals/legal/additional-disclaimers', 'Additional disclaimers')))

    meta_desc = soup.find('meta', attrs={'name': 'description'})
    meta = L.block('metadata', [['Title', E(soup.title.get_text(strip=True))],
                                ['Description', E(meta_desc.get('content', '') if meta_desc else '')]])
    sec[-1] += meta
    return L.page(sec)


if __name__ == '__main__':
    doc = build()
    open(L.os.path.join(L.REC, 'content', 'index.html'), 'w').write(doc)
    print(len(doc), L.upload('/index', doc))
