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
| `cmp-embed` (script wrapper; no video found in samples) | most | Usually dropped (wrapper for promo text) | content | No |
| Plan-check lead form (`leadgenform-v2`) | home, plans | Link-out | custom | No |
| PDP trade-in, line choice, Boost Protect, Affirm | shop PDP | Link-out / unresolved | custom | Recorded in `components.csv` |
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
| shop-cart | 1 | commerce (drop-in) | Existing `/cart` (Cart drop-in) + redirect |
| shop-auth / shop-account | 6 | custom → link-out | Source redirects to carrier PingFederate SSO (`id.boostmobile.com`); link out. Starter `/customer/*` drop-in pages remain for Commerce-only accounts (T1 finding) |
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

## 7. Detailed task plan (Phase 3, Option A)

Status values match `MIGRATION.md` §5. Each task finishes with a browser check (desktop 1280px and mobile 375px), `npm run lint`, record updates, and a commit. The "Depends on" column lists the tasks that must finish first.

| ID | Task | Files / destinations | Acceptance criteria | Depends on |
| --- | --- | --- | --- | --- |
| T1 | Component inventory | `components.csv` | One render-inspected page per template; every source component mapped to a block, default content, link-out, or `unresolved` with a reason | — |
| T2 | Brand tokens | `styles/styles.css`, `styles/fonts.css`, `fonts/` | Source colors, type scale, and button styles captured as CSS custom properties; fonts are self-hosted only if the license allows (otherwise a documented fallback stack); no CLS from fonts | T1 |
| T3 | Global nav content | DA `/nav` | Top-level menu items and second-level links from the source mega menu; carrier flows and the locator point to absolute live URLs; utility links (cart, sign in) intact | T1 |
| T4 | Header restyle | `blocks/header/header.css` (+ JS only if multi-level panels need it) | Mega menu works with mouse, keyboard, and on mobile (hamburger); mini-cart and auth drop-ins still function | T2, T3 |
| T5 | Footer | DA `/footer`, `blocks/footer/footer.css` | Link columns, social links, legal text; matches the source layout at both breakpoints | T2 |
| T6 | Shared fragments | DA `/fragments/*` | Experience fragments and legal modals reused by more than one page exist once and are referenced via `fragment`/`modal` | T1 |
| T7 | `plan-cards` block | `blocks/plan-cards/{js,css,README.md}` | Author table: name, price, price note, features list, CTA link; defensive against missing cells; native DOM only; README documents the table | T2 |
| T8 | Block variants | `blocks/{hero,cards,carousel}/*.css` | Hero variants and shelf/grid card styles match the source sections used on the homepage | T2 |
| T9 | Homepage (en) | DA `/index` | All homepage sections present in source order; images load; CTAs resolve (internal → migrated pages, carrier flows → live URLs); `urls.csv` row `previewed` | T4, T5, T6, T7, T8 |
| T10 | Content template pilots | DA: one each for plan, deals, brand, add-on, marketing, info, blog-landing, blog-article | Each pilot verified; any new gap is added to `components.csv` and fixed before bulk work | T9 |
| T11 | Bulk content pages (en) | DA, about 115 pages | Created via a repeatable converter script (`tools/migrate/` excluded via `.hlxignore` if it is local-only); each page previewed (200); failures logged as `blocked` with a reason | T10 |
| T12 | Help articles | DA `/help/*` (155) + `/help` index | Converted from the ReadMe.io markup; internal help links rewritten to `/help/<slug>` | T10 |
| T13 | Commerce: PLPs | DA `/shop/...` category pages (16) | `product-list-page` renders sandbox products for categories that exist in ACCS; categories with no match are recorded as `blocked: catalog` | T4 |
| T14 | Commerce: PDP routing | DA `/products/default`, `redirects` sheet; folder mapping | `/products/<urlKey>/<sku>` renders for a sandbox SKU (for example `iphone-16e/002481`); legacy `/shop/<name>.html` redirects for matched SKUs; folder mapping applied (needs admin access; otherwise flagged) | T4 |
| T15 | Commerce: cart redirect + SSO link-outs | DA `redirects`, `/nav` | `/shop/checkout/cart` → `/cart`; sign-in/account links point to the live carrier SSO (T1 finding) | T14 |
| T16 | Spanish locale | DA `/es/nav`, `/es/footer`, `/es/placeholders`, `/es/**` (118) | The same pipeline as T9–T11 using es.boostmobile.com content; internal links stay under `/es`; Commerce `/es` root works (or is documented as a limitation) | T11 |
| T17 | QA and report | `report.md`, `urls.csv`, `components.csv` | Lighthouse on home/PLP/PDP recorded; accessibility spot check; final totals; remaining blockers listed | T12–T16 |

User checkpoints: after T9 (homepage look and feel), after T10 (template pilots), and before T11/T12/T16 bulk creation.
