# Migration report: www.boostmobile.com

Source accessed: 2026-10-27. Starter commit: `ea3f33a`. Status: **discovery in progress; no pages implemented**.

## Scope and discovery

| Source | URLs | Treatment |
| --- | --- | --- |
| `en.sitemap.xml` (AEM marketing site) | 118 | In scope |
| `shop/.../sitemap.xml` (Magento shop) | 32 (non-image) | In scope; commerce |
| Homepage navigation, not in any sitemap | 32 | In scope after review (3 excluded as action URLs or robots-disallowed) |
| `locations/sitemap.xml` (store locator) | 82,456 | One template group; scope decision pending |
| `help.boostmobile.com` | 155 | Other origin; out of scope unless authorized |
| `es.boostmobile.com` (Spanish) | not crawled | Other origin; out of scope unless authorized |

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
| shop-plp | 16 | commerce | `product-list-page` block (Product Discovery drop-in) |
| shop-pdp | 26 | commerce | `product-details` block (PDP drop-in) |
| shop-cart / shop-auth | 3 | commerce | Cart and User Auth drop-ins |
| shop-account | 5 | unresolved | Carrier account vs Commerce account; needs decision |
| activation / shop-custom-flow / compatibility / coverage-map | 10 | custom | Carrier services; no drop-in equivalent |
| account-gateway | 2 | unresolved | Carrier billing login |
| store-locator | 2 (+82,456) | custom | Third-party locator |

## Commerce backend

ACCS sandbox `config.json` committed. The sandbox catalog has 18 products: partial overlap with the source (Galaxy A16 5G, iPhone 16e, Pixel 10a, BYOD plans, Boost Protect). Source PDPs for products missing from the sandbox cannot render live data until the catalog is loaded.

## Totals

See `urls.csv`: 181 URL rows (178 pending, 3 excluded). Component inventory (`components.csv`) not started.

## Next pending batch

1. Confirm scope decisions (see `scratch/REQUIREMENTS.md`).
2. Render-inspect one page per template and write `components.csv`.
3. Implement the global header/footer and homepage first.
