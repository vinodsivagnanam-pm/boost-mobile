# Migration report: www.boostmobile.com

Source accessed: 2026-10-27. Starter commit: `ea3f33a`. Status: **discovery complete; scope decided; no pages implemented**.

## Scope and discovery

| Source | URLs | Treatment |
| --- | --- | --- |
| `en.sitemap.xml` (AEM marketing site) | 118 | In scope |
| `shop/.../sitemap.xml` (Magento shop) | 32 (non-image) | In scope; commerce |
| Homepage navigation, not in any sitemap | 32 | In scope after review (3 excluded as action URLs or robots-disallowed) |
| `locations/sitemap.xml` (store locator) | 82,456 | Excluded; link to live locator |
| `help.boostmobile.com` (ReadMe.io) | 155 | In scope; migrate to `/help/<slug>` |
| `es.boostmobile.com` (Spanish, MotionPoint proxy) | 118 | In scope; migrate to `/es/<path>` |

Deduplication: fragments removed, trailing slashes removed, tracking parameters (`_gl`, `utm_*`, `gclid`) removed; other query strings kept. `robots.txt` disallows `/learn`, `/en2`, `/threat-test`, `/welcome`, `/primary`, `/myaccount`, `/promo`, and Magento system paths. `/promo/focusgroup` is listed in the sitemap but disallowed, so it is excluded.

## Source platform

- Marketing pages: AEM Sites with `harmony-*` templates and Core Components (`cmp-text`, `cmp-accordion`, `cmp-card-shelf`, `cmp-image`, `cmp-button`, `cmp-modal`, `cmp-embed`, mega menu, experience fragments).
- Shop: Adobe Commerce (Magento 2, theme `Dop/Boostmobile`) under `/shop`, with custom carrier flows (activation, compatibility check, BYOD, multiline).
- Store locator: separate platform under `/locations`.

## Template map (provisional)

| Template | URLs | Page classification | Likely implementation |
| --- | --- | --- | --- |
| home | 1 | hybrid | Content blocks (hero, cards, carousel) + product shelf |
| plan-landing | 10 | hybrid | Content blocks; plan cards may need a Commerce block or custom |
| deals-landing | 3 | hybrid | Content blocks + product cards |
| brand-landing | 7 | hybrid | Content blocks + product shelf |
| add-on-landing | 14 | content | Content blocks |
| marketing-page / info-page | 33 | content | Default content + content blocks |
| blog-landing / blog-article | 49 | content | Default content, article list, breadcrumbs |
| shop-plp | 16 | commerce | Single PLP template, `product-list-page` block (Product Discovery drop-in) |
| shop-pdp | 26 | commerce | Single `/products/default` template (PDP drop-in) + redirects from `/shop/*.html` |
| shop-cart / shop-auth | 3 | commerce | Cart and User Auth drop-ins |
| shop-account | 5 | unresolved | Carrier account vs Commerce account; needs decision |
| activation / shop-custom-flow / compatibility / coverage-map | 10 | custom | Link out to live Boost flows (decision) |
| account-gateway | 2 | unresolved | Carrier billing login |
| store-locator | 2 (+82,456) | custom | Excluded; link out |
| help-article / help-page | 155 | content | Default content, article template |
| Spanish mirror (`/es`) | 118 | per English template | Same blocks, localized content and placeholders |

## Commerce backend

ACCS sandbox `config.json` committed. The sandbox catalog has 18 products: partial overlap with the source (Galaxy A16 5G, iPhone 16e, Pixel 10a, BYOD plans, Boost Protect). Source PDPs for products missing from the sandbox cannot render live data until the catalog is loaded.

## Decisions

Recorded in `site.json` `decisions`: locator excluded and linked; Spanish and help included; templated PDP/PLP with redirects; carrier flows link out; pages created directly in DA.live.

## Totals

See `urls.csv`: 454 URL rows (448 pending, 6 excluded; 336 en-US, 118 es-US). Component inventory (`components.csv`) not started.

## Next pending batch

1. Obtain DA.live write authorization (token kept outside the repository).
2. Render-inspect one page per template and write `components.csv`.
3. Implement the global header/footer and homepage first.
