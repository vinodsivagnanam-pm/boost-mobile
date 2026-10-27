import csv,html
from bs4 import BeautifulSoup
R='/Users/vinodsivagnanam/Library/CloudStorage/OneDrive-Adobe/Documents/Downloads/Codex Projects/Boost - Storefront migration/migration/www.boostmobile.com/'
rows={r['source_url'].rstrip('/'):r for r in csv.DictReader(open(R+'urls.csv'))}
pdp={'https://www.boostmobile.com/shop/iphone-16e.html':'/products/iphone-16e/002481','https://www.boostmobile.com/shop/pixel-10a-002729.html':'/products/google-pixel-10a/002729','https://www.boostmobile.com/shop/devices/handsets?manufacturer=166':'/shop/devices/handsets?filter=cs_manufacturer:Boost'}
def m(u):
    if u.startswith('/'): u='https://www.boostmobile.com'+u
    if u in pdp: return pdp[u],'pdp'
    r=rows.get(u.rstrip('/'))
    if r and r['status']!='excluded' and r['destination_path'] and r['page_classification']!='custom' and '<' not in r['destination_path'] and '?' not in u:
        return r['destination_path'],'local'
    return u,'live'
s=BeautifulSoup(open('home.html',errors='ignore').read(),'html.parser')
f=s.select_one('.footer-v2')
groups=[]
for ul in f.select('ul.footer-section-ul'):
    h=ul.find('h4'); links=[]
    for a in ul.select('li a[href]'):
        href,kind=m(a['href']); links.append((a.get_text(' ',strip=True),href,kind))
    groups.append((h.get_text(strip=True).title(),links))
log=[]
def grp(g):
    out='<h3>'+html.escape(g[0])+'</h3><ul>'
    for t,h,k in g[1]:
        log.append((g[0],t,h,k)); out+='<li><a href="%s">%s</a></li>'%(html.escape(h),html.escape(t))
    return out+'</ul>'
cols=[groups[0:2],groups[2:4],groups[4:7],groups[7:]]
cells=''.join('<div>'+''.join(grp(g) for g in c)+'</div>' for c in cols)
seen=[]
for a in [a for a in f.select('a[href]') if any(d in a['href'] for d in ('facebook','instagram','x.com','tiktok','linkedin'))]:
    x=(a.get('aria-label') or (a.find('img') or {}).get('alt') or a['href'],a['href'])
    if x not in seen: seen.append(x)
soc='<p>Connect with us on social media</p><ul>'+''.join('<li><a href="%s">%s</a></li>'%(h,t) for t,h in seen)+'</ul>'
doc=('<body><header></header><main>'
 '<div><div class="columns"><div>'+cells+'</div></div></div>'
 '<div>'+soc+'<p>© 2026 Boost Mobile®, a division of Boost SubscriberCo L.L.C.</p></div>'
 '</main><footer></footer></body>')
open('da/footer.html','w').write(doc)
for l in log: print(*l,sep=' | ')
print(seen)
