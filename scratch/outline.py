import sys,re
from bs4 import BeautifulSoup
h=open(sys.argv[1],errors='ignore').read()
s=BeautifulSoup(h,'html.parser')
root=s.select_one('.root.container') or s.body
for t in root.find_all(['header','footer','nav']): pass
def comp(el):
    for c in el.get('class',[]):
        if re.fullmatch(r'cmp-[a-z\-]+',c): return c
def walk(el,d):
    for ch in el.find_all(recursive=False):
        c=comp(ch)
        if c in ('cmp-modal','cmp-modal-overlay','cmp-md-overlay','cmp-card-shelf-arrows','cmp-card-shelf-pagination','cmp-card-shelf-overlay'): continue
        if c and c!='cmp-container':
            txt=' '.join(ch.get_text(' ',strip=True).split())[:90]
            imgs=len(ch.find_all('img')); links=len(ch.find_all('a'))
            hd=[x.get_text(strip=True)[:40] for x in ch.find_all(re.compile('^h[1-4]$'))][:3]
            print('  '*d+f'{c} img={imgs} a={links} h={hd} | {txt}')
            if c in ('cmp-card-shelf','cmp-accordion','cmp-experiencefragment','cmp-tabs','cmp-carousel'): continue
            walk(ch,d+1)
        else:
            walk(ch,d+(1 if c else 0))
walk(root,0)
