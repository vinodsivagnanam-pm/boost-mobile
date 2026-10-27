import sys,csv,re,ast,subprocess
sys.path.insert(0,'scratch'); from sections import sections
samples={ # template: (source_url, file)
 'home':('https://www.boostmobile.com/','home.html'),
 'plan-landing':('https://www.boostmobile.com/plans','s_plans.html'),
 'deals-landing':('https://www.boostmobile.com/deals','s_deals.html'),
 'brand-landing':('https://www.boostmobile.com/brand/apple','s_brand_apple.html'),
 'add-on-landing':('https://www.boostmobile.com/add-ons/mobile-hotspot','s_add-ons_mobile-hotspot.html'),
 'marketing-page':('https://www.boostmobile.com/amazon-support','s_amazon-support.html'),
 'info-page':('https://www.boostmobile.com/30-day-money-back-guarantee','s_30-day-money-back-guarantee.html'),
 'blog-landing':('https://www.boostmobile.com/boost-blog','s_boost-blog.html'),
 'blog-article':('https://www.boostmobile.com/boost-blog/mobile-101/what-is-an-esim','s_boost-blog_mobile-101_what-is-an-esim.html'),
 'account-gateway':('https://www.boostmobile.com/errors/account','s_errors_account.html'),
}
def classify(t,i,d):
    c={x[4:] for x in d['comps']}; h=' '.join(d['h']).lower(); txt=d['txt']
    if 'breadcrumb' in c: return 'content','breadcrumb','breadcrumbs (auto-block from metadata)','Small scripts.js change'
    if 'accordion' in c: return 'content','accordion','accordion',''
    if 'card-shelf' in c and ('comes with' in h or re.search(r'\$\d+/mo',txt) and 'unlimited' in txt.lower()): return 'content','card-shelf of plan cards','plan-cards','New block (T7)'
    if 'card-shelf' in c and txt.startswith('"'): return 'content','card-shelf of testimonials','carousel',''
    if 'card-shelf' in c: return 'content','card-shelf of promo/device cards','carousel (or cards shelf variant)','Device cards link to templated PDP'
    if 'container-link' in c: return 'content','linked tiles','cards',''
    if 'experiencefragment' in c and 'card-shelf' not in c: return 'content','experience fragment','fragment','Shared /fragments page (T6)'
    if i==0 and 'image' in c and ('text' in c or 'title' in c): return 'content','first section image + headline','hero',''
    if 'image' in c and 'text' in c and d['img']>=2: return 'content','image + text + CTA layout','columns',''
    if c<= {'button'}: return 'content','CTA button','default content (button)',''
    if c<= {'image'}: return 'content','image','default content (image)',''
    if not c and t=='blog-landing': return 'content','article teaser grid','cards (or query-index list)','Blog index list later'
    return 'content','text/heading/buttons','default content',''
w=csv.writer(open('migration/www.boostmobile.com/components.csv','w',newline=''))
w.writerow('source_url,component_id,region,classification,evidence,block,dropin_package,implementation_path,status,blocker'.split(','))
def row(u,cid,reg,cl,ev,blk,pkg='',path='',st='pending',bl=''): w.writerow([u,cid,reg,cl,ev,blk,pkg,path,st,bl])
G='https://www.boostmobile.com/'
row(G,'global-header','header','hybrid','cmp-mega mega menu + utility links; mini-cart and sign-in','header','@dropins/storefront-cart, @dropins/storefront-auth','blocks/header; DA /nav')
row(G,'global-footer','footer','content','footer experience fragment with link columns, social, legal','footer','','blocks/footer; DA /footer')
row(G,'global-legal-modal','overlay','content','cmp-modal / cmp-md-overlay legal and offer details on every page','modal','','blocks/modal; DA /fragments/*')
row(G,'global-plan-check-form','overlay','custom','form#leadgenform-v2 POST /shop/buy/plans/check (carrier eligibility) on home and plans','link-out','','','pending','Carrier service; link out per decision')
for t,(u,f) in samples.items():
    for d in sections('/tmp/boost/'+f):
        if d['txt'].strip().lower() in ('anchor','disclaimers anchor'): continue
        cl,ev,blk,note=classify(t,d['i'],d)
        if 'leadgen' in d['cls']: cl,blk='custom','link-out'
        ev=f"{ev}; comps={'+'.join(x[4:] for x in d['comps'] if 'shelf-' not in x)}; h={'|'.join(d['h'][:2])}"
        row(u,f"{t}-s{d['i']:02d}",'main',cl,ev,blk,'','',  'pending',note if cl!='content' else '')
# commerce
P='https://www.boostmobile.com/shop/iphone-16.html'
row(P,'shop-pdp-core','main','drop-in','Magento configurable product: gallery, title, color/storage swatches, price-box, box-tocart','product-details','@dropins/storefront-pdp','blocks/product-details; DA /products/default')
row(P,'shop-pdp-tradein','main','custom','#tradeInBlock trade-in required flow','link-out','','','pending','Carrier trade-in service; no drop-in equivalent')
row(P,'shop-pdp-line-choice','main','custom','#portIn / #new number choice, multiline_express_activation','link-out','','','pending','Carrier activation logic')
row(P,'shop-pdp-protect','main','custom','Boost Protect (AppleCare) upsell modal #add-boost-protect-button','unresolved','','','pending','Could be a related product/bundle in Commerce; needs catalog modeling')
row(P,'shop-pdp-affirm','main','custom','Affirm "as low as" messaging #als_pdp','unresolved','','','pending','Third-party financing script; requires Affirm account')
L='https://www.boostmobile.com/shop/devices/handsets'
row(L,'shop-plp-core','main','drop-in','Magento category: filters, sorter, toolbar-amount, products-grid','product-list-page','@dropins/storefront-product-discovery','blocks/product-list-page')
row(L,'shop-plp-badges','main','custom','"Store-to-Door" badge and Affirm as-low-as per tile','unresolved','','','pending','Needs product attribute + slot; verify slots via researcher')
row('https://www.boostmobile.com/shop/catalog/category/view/id/262','shop-plp-dead','main','unresolved','URL redirects to homepage','none','','','excluded','Source redirects to /; add redirect only')
C='https://www.boostmobile.com/shop/checkout/cart'
row(C,'shop-cart-core','main','drop-in','.cart-container / .cart-empty','commerce-cart','@dropins/storefront-cart','blocks/commerce-cart; DA /cart')
row(C,'shop-cart-esim-notice','main','content','smartwatch eSIM notice above cart','default content','','DA /cart')
A='https://www.boostmobile.com/shop/customer/account/login'
row(A,'shop-auth-sso','main','custom','Redirects to id.boostmobile.com PingFederate OAuth (client BoostWeb)','link-out','','','pending','Carrier SSO, not Commerce customer auth; Commerce auth drop-in would be a separate identity')
row('https://www.boostmobile.com/shop/customer/account','shop-account-sso','main','custom','Redirects to id.boostmobile.com PingFederate OAuth','link-out','','','pending','Carrier account; link out')
H='https://help.boostmobile.com/docs/200gb-nyc-offer'
row(H,'help-article-body','main','content','ReadMe.io article.rm-Article markdown (headings, lists, links)','default content','','DA /help/<slug>')
row('https://help.boostmobile.com/page/iphone-comparison','help-page-body','main','content','ReadMe.io custom page','default content (+columns)','','DA /help/iphone-comparison')
