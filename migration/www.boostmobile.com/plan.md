# Architecture plan: www.boostmobile.com → EDS Commerce storefront

Status: **Phase 2: proposed, awaiting approval**. Inputs: `urls.csv` (454 rows), `site.json` decisions, and sampled pages (one per template).

## 1. Source component → EDS block mapping

Evidence: the frequency of `cmp-*` classes in one sampled page per template. `components.csv` will record the details for each page.

| Source component (AEM Core / harmony) | Seen on | EDS target | Type | New code? |
| --- | --- | --- | --- | --- |
| `cmp-text`, `cmp-title`, `cmp-image`, `cmp-button`, `cmp-btn-list`, `cmp-separator` | all | Default content (headings, paragraphs, images, buttons, `---`) | content | No |
| Hero container (first full-width image + headline + CTA) | home, plans, brand, deals, add-ons | `hero` | content | Variants only (CSS) |
| `cmp-card-shelf` (+ arrows/pagination) | home, plans, brand, deals, support | `carousel` (scrolling shelf) or `cards` (static grid) | content | Variant: `cards (shelf)` |
| `cmp-container-link` promo tiles | home, plans, deals | `cards` | content | No |
| Plan price cards (inside a card shelf) | plans, plans/byod, home | `plan-cards` (new content block: name, price, features, CTA link-out) | content | **Yes** |
| `cmp-accordion` (FAQ) | plans, brand, add-ons, coverage, support | `accordion` | content | No |
| `cmp-modal`, `cmp-md-overlay` (legal/offer details) | all | `modal` (link to a `/fragments/...` page) | content | No |
| `cmp-experiencefragment` (shared promo/legal) | home, plans, deals, blog, add-ons | `fragment` → `/fragments/<name>` | content | No |
| `cmp-embed` (video/script) | most | `embed` (not in starter) or link | content | **Yes, if video is required** |
| `cmp-breadcrumb` | blog articles | Auto-block from metadata `breadcrumbs` | content | Small `scripts.js` change |
| Mega menu (`cmp-mega`) | global | `header` (nav authored in `/nav`) | content + Commerce (mini-cart, auth) | Restyle + multi-level nav |
| Footer | global | `footer` (`/footer`) | content | Restyle |
| Help article (ReadMe.io) | help | Default content + `table`; `/help` index via query index | content | No |

## 2. Page-template plan

| Template | Rows (en+es) | Classification | Implementation |
| --- | --- | --- | --- |
| home | 1+1 | hybrid | hero, cards, carousel, plan-cards; device shelf = `cards` linking to PDPs (upgrade to `product-recommendations` once Recommendations is configured) |
| plan-landing, deals-landing, brand-landing | 20+20 | hybrid | Content blocks + plan-cards; device links go to the templated PDP |
| add-on-landing, marketing-page, info-page | 46+46 | content | Default content + hero/cards/accordion/fragment |
| blog-landing, blog-article | 49+49 | content | Default content; blog index list from the query index (later); breadcrumbs |
| help-article / help-page | 155 | content | `/help/<slug>`; default content |
| shop-plp | 16 | commerce (drop-in) | One template per category page using the `product-list-page` block (Product Discovery drop-in), pointed at the matching ACCS category |
| shop-pdp | 26 | commerce (drop-in) | Single `/products/default` (`product-details` block, PDP drop-in); folder mapping `/products/` → `/products/default`; `redirects` sheet `/shop/<name>.html` → `/products/<urlKey>/<sku>` |
| shop-cart / shop-auth | 2 | commerce (drop-in) | Existing `/cart`, `/customer/login` (Cart, User Auth drop-ins) + redirects |
| shop-account | 5 | commerce (drop-in) | Existing `/customer/*` account pages (Account drop-in) + redirects; carrier billing stays at the live site |
| activation, compatibility, coverage, BYOD/multiline, account-gateway | 12 | custom → link-out | Not migrated; nav/CTA links point to the live Boost URLs (decision) |
| store-locator | 2 (+82,456) | excluded | Link out |

## 3. Commerce wiring

- Backend: ACCS sandbox (`config.json`), store view `default`. The catalog has 18 SKUs; PDP redirects are generated only for source products that have a matching SKU, and the others are recorded as `blocked: catalog`.
- PDP routing: `scripts/commerce.js` `getSkuFromUrl()` already matches `/products/<urlKey>/<sku>`. Folder mapping requires Config Service/admin access (fallback: a DA `redirects` sheet for the legacy URLs plus a manually created page per SKU).
- No changes to drop-in internals; slot customizations only if the visual parity review requires them (researched first).

## 4. Localization (`/es`)

- Spanish pages mirror the English paths under `/es/...`; `/es/nav`, `/es/footer`, and `/es/placeholders` will be created.
- The starter's multistore support (`scripts/commerce.js` root path detection) can map `/es/` to the same store view until a Spanish store view exists. Commerce labels stay in English unless drop-in language packs are added (recorded as a limitation).

## 5. Execution order (batches)

1. Global: brand tokens in `styles/styles.css` (colors, fonts from the source), `nav` + `footer` content, and the header/footer restyle.
2. Homepage (en), then `/es` homepage.
3. One page per content template → verify → bulk-create the remaining pages of that template.
4. New blocks: `plan-cards` (and `embed` if needed), each with a README and author table.
5. Commerce: PLP pages, the PDP template, the redirects sheet, and cart/auth/account redirects.
6. Help articles (155) and blog (49) in bulk.
7. Spanish mirror of all content pages.

Each batch: create the DA page via the admin API → preview → browser check (desktop/mobile) → `npm run lint` → update the `urls.csv`/`components.csv` statuses → commit.

## 6. Risks and limits

- **Images:** source images are hot-linked during the draft phase and must be uploaded to DA for production (rights confirmed by the user).
- **Legal copy and offers** change often; the migrated text reflects the access date.
- **Catalog gaps:** most source devices are not in the sandbox.
- **Visual parity** is approximate (brand tokens + blocks), not pixel-perfect.
- **Token:** the DA token expires after about 24 hours; renew it via `MIGRATION.md` §6.
- **Performance:** no third-party scripts from the source; target Lighthouse 100 on PDP/PLP.
