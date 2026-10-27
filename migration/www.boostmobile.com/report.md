# Migration report: www.boostmobile.com

Source accessed: 2026-10-27. Starter commit: `ea3f33a`. Status: **migrated to DA.live preview (T1–T17 complete); not published**. Preview: https://main--boost-mobile--vinodsivagnanam-pm.aem.page/

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

Final template classification is in `urls.csv` (`page_classification`) and per-component evidence in `components.csv`; the table above is the discovery-time estimate. Changes after implementation: `account-gateway` became hybrid (content with SSO link-outs), shop-account and shop-auth became excluded link-outs to the carrier SSO, and Spanish pages reuse the English blocks.

## Commerce backend

ACCS sandbox `config.json` committed. The sandbox catalog has 18 products: partial overlap with the source (Galaxy A16 5G, iPhone 16e, Pixel 10a, BYOD plans, Boost Protect). Source PDPs for products missing from the sandbox cannot render live data until the catalog is loaded.

## Decisions

Recorded in `site.json` `decisions`: locator excluded and linked; Spanish and help included; templated PDP/PLP with redirects; carrier flows link out; pages created directly in DA.live.

## Totals

`urls.csv`: 455 rows (337 en-US, 118 es-US).

| Status | Rows | Notes |
| --- | --- | --- |
| verified | 27 | Browser-checked on preview (home, template pilots, PLPs, PDPs, cart, `/help` samples, `/es`, `/es/plans`, an ES blog article) |
| implemented | 367 | Uploaded and previewed; route sweeps returned HTTP 200 with one h1 (except 6 pages without a source h1) |
| excluded | 33 | Carrier flows and SSO link-outs, redirect-only and query-variant URLs, robots-disallowed, empty source |
| blocked | 28 | 26 Commerce rows lack catalog data (23 PDPs, Motorola/tablet/watch PLPs); `yourprivacychoices` (EN and ES) is a client-side privacy form |

By page classification: content 343, hybrid 46, commerce 43, custom 23.

`components.csv`: 507 rows. Content 487, drop-in 9, custom 8, hybrid 2, unresolved 1 (excluded). Drop-ins used: `storefront-pdp`, `storefront-cart`, `storefront-product-discovery` (PLPs), plus `storefront-auth` and the mini cart in the header (hybrid).

## Quality (Lighthouse 12, mobile, aem.page preview, after T16)

| Page | Perf | A11y | Best practices | SEO | LCP | CLS | TBT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | 98 | 94 | 100 | 69 | 2.0 s | 0.007 | 0 ms |
| `/shop/devices/handsets` (PLP) | 90 | 94 | 93 | 69 | 3.4 s | 0 | 20 ms |
| `/products/iphone-16e/002481` (PDP) | 88 | 96 | 96 | 61 | 3.5 s | 0 | 40 ms |
| `/es` | 99 | 94 | 96 | 69 | 1.7 s | 0 | 0 ms |

- SEO: `is-crawlable` fails on every page because `aem.page` preview sends `noindex`; this does not apply to the live domain. The PDP template has no meta description (the drop-in does not set one); add a product-level description at go-live.
- Fixed in T17: brand orange `#fc5400` is 3.3:1 on white, so small orange text (plan-card names, offer-card emphasis) now uses `--color-accent-text: #c94300` (4.9:1); fills and large text keep `#fc5400`. A missing `/default-meta-image.png` (404 on pages without an image, such as the PDP) was added from the source share image.
- Remaining: `heading-order` on the home hero carousel (h1 then h3, as authored on the source); PDP gallery dots are below the 24px target size (drop-in markup); PLP catalog images trigger `image-aspect-ratio`/`image-size-responsive` (catalog assets). Commerce LCP is 3.4–3.5 s on the sandbox; re-measure against the production catalog.

## Remaining blockers and go-live work

- **Catalog:** 23 source PDPs and the Motorola, tablet, and watch PLPs need products and categories in the Commerce catalog. Rerun `pdp.py` and `plp.py` after loading them.
- **CDN redirects at cutover** (not expressible in the EDS redirects sheet): `/l/manufacturer:*`, `?pid=`/`?manufacturer=` variants, `help.boostmobile.com/docs/*` → `/help/*`, `es.boostmobile.com/*` → `/es/*`, and `/shop/customer/*` plus the carrier flows (activation, compatibility check, coverage map, BYOD multiline) to the carrier origin.
- **Third-party and carrier features:** Affirm financing, trade-in, line choice, Boost Protect bundles, the plan-check lead form, newsletter signup, and the privacy-choices form. These stay link-outs or need separate integration work.
- **Content gaps:** licensed brand fonts (fallback stack in use), Plan Details modals on deals cards, the ReadMe search widget, the troubleshooting iframe, and `/modals/plans/*` in Spanish.
- **Localization:** Spanish pages use English Commerce labels and English Commerce pages (no Spanish store view). A multistore `/es/` root is the upgrade path when one exists.
- **Publishing:** nothing is published to `aem.live`; publishing requires an authorized decision and the production Commerce configuration.
