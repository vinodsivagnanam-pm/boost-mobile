import sys,re,json
from bs4 import BeautifulSoup
def comps(el):
    return [c for c in el.get('class',[]) if re.fullmatch(r'cmp-[a-z\-]+',c)]
def sections(path):
    s=BeautifulSoup(open(path,errors='ignore').read(),'html.parser')
    for x in s.select('header, footer, .cmp-mega, .experiencefragment.header, .experiencefragment.footer, script, style, noscript'): x.decompose()
    root=s.select_one('.root.container') or s.body
    # descend while single child
    cur=root
    while True:
        kids=[k for k in cur.find_all(recursive=False) if k.get_text(strip=True) or k.find('img')]
        if len(kids)==1: cur=kids[0]; continue
        if len(kids)==2 and 'experiencefragment' in ' '.join(kids[1].get('class',[])): cur=kids[0]; continue
        break
    out=[]
    for i,k in enumerate(kids):
        cls=' '.join(k.get('class',[]))[:60]
        all_c=set()
        for e in k.find_all(True):
            for c in comps(e):
                if '--' not in c: all_c.add(c)
        hd=[' '.join(x.get_text(' ',strip=True).split())[:50] for x in k.find_all(re.compile('^h[1-3]$'))]
        hd=list(dict.fromkeys(hd))[:3]
        out.append(dict(i=i,cls=cls,comps=sorted(all_c-{'cmp-container','cmp-modal','cmp-modal-overlay'}),img=len(k.find_all('img')),a=len(k.find_all('a')),h=hd,
            txt=' '.join(k.get_text(' ',strip=True).split())[:80]))
    return out
if __name__=='__main__':
    for r in sections(sys.argv[1]): print(r)


def section_elements(path):
    """Return (soup, [top-level section elements]) using the same descent as sections()."""
    s = BeautifulSoup(open(path, errors='ignore').read(), 'html.parser')
    for x in s.select('header, footer, .cmp-mega, .experiencefragment.header, .experiencefragment.footer, script, style, noscript'):
        x.decompose()
    cur = s.select_one('.root.container') or s.body
    while True:
        kids = [k for k in cur.find_all(recursive=False) if k.get_text(strip=True) or k.find('img')]
        if len(kids) == 1:
            cur = kids[0]; continue
        if len(kids) == 2 and 'experiencefragment' in ' '.join(kids[1].get('class', [])):
            cur = kids[0]; continue
        return s, kids
