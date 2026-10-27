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

- **Modals (T6):** source `cmp-modal__info` overlays reused on 2+ pages became DA pages under `/modals/plans/*` (plan details and deal lists) and `/modals/legal/additional-disclaimers`; see `fragments.json` for source modal IDs. `/fragments/` links are inlined by auto-blocking, so overlays use `/modals/` and `scripts/scripts.js` `autolinkModals` opens same-origin `/modals/...` links in the `modal` dialog. Single-use modals are migrated with their page. Generator: `scratch/modals_gen.py` with `scratch/eds_lib.py` (shared converter, link mapper, DA upload); move to a committed `tools/migrate/` before handoff.
- **Plan cards (T7):** new content block `blocks/plan-cards` (README documents the model: one row per plan; cells recognized by content: header, features list with optional icons, action links). The "Full Plan Details" button (source modal embedded per card) links to `/modals/plans/*-details`. Plan-shelf detection: a `.cmp-card-shelf` whose card names match known plans; offer/deal shelves use `cards` variants (T8). DA splits `<del>` old price into its own paragraph; the block rejoins it. SVG icons skip `createOptimizedPicture`. Generator: `scratch/plancards_gen.py`. Test page: `/drafts/plan-cards`. Verified at 375px and 719px; 900px+ row layout verified by CSS only.
- **Block variants (T8):** variants are CSS on existing blocks, not new blocks: `carousel (hero)` (authored order is kept and slides are not shuffled; a picture-only third column becomes `.carousel-slide-media`), `cards (quick-links|testimonials|features|offers)`, `columns (promo)`. Details buttons on offer cards link to `/modals/plans/*`; `map_link` keeps paths that start with `/modals/` and `/products/` unchanged.
- **Homepage (T9):** generator `scratch/home_gen.py` → DA `/index` (source copy in `content/index.html`). There are 16 sections in source order. Affirm, razr, iPhone 15, and carrier flows link out to the live site. The source "Shop In-Store Deals" shelf renders client-side and is empty in the server HTML, so it was migrated as a heading plus a store-locator link. Verified at about 1000px: 10 blocks load, 50 images with none broken, and the details modals open. The overflow of the header nav-tools (scrollWidth 1273) is tracked in T4.
- **Header (T4):** CSS only. Between 900 and 1279px, long nav labels wrap, padding is tighter, and the phone number is hidden, so there is no horizontal overflow (verified at 1007px). Below 600px the logo is 72px, the phone number is shown on one line at 12px, and the wishlist icon is hidden (it is reachable from the account menu); brand, phone, cart, search, and account fit in 375px. Mega menu: hamburger `aria-label`/`aria-controls` toggle, mobile submenus expand, desktop `.nav-drop` opens with Enter and closes with Escape.
- **Template pilots (T10):** the portable converter is `tools/migrate/` (documented in `MIGRATION.md`), with site hints in `converter.json` and `link-map.csv`. Pilots were uploaded, previewed, and verified in the browser at about 1000px: `/30-day-money-back-guarantee`, `/plans`, `/deals`, `/brand/apple`, `/add-ons/mobile-hotspot`, `/amazon-support`, `/boost-blog`, and `/boost-blog/mobile-101/what-is-an-esim`. Every block loads, there are no broken images or horizontal overflow, and each page has one h1 in main. Converter fixes made during the pilots: strip HTML comments and container background images (`.cmp-container__background-content`); drop authoring-only labels (`drop_labels`); preserve whitespace-only `<b> </b>` spacers; product shelves use `cards (offers)`. Known gaps: the "Plan Details" triggers on deal cards are modal buttons without a URL, so they render as text (`deals-plan-details`); blog landing teasers are default content, not a listing block.
- **Bulk English content (T11):** 107 additional en-US pages were converted, uploaded, and previewed: info-page, plan-landing, brand-landing, deals-landing, blog-landing, add-on-landing, marketing-page, and blog-article. Spot checks in the browser covered `/plans/byod`, `/reviews`, `/cares`, `/phone-financing-affirm`, and `/deals`. Two destinations were normalized because EDS paths reject underscores and uppercase: `/contract_buyout/terms_and_conditions` became `/contract-buyout/terms-and-conditions`, and `best-budget-5G-phones-of-2026` became `best-budget-5g-...`. Both need redirects in T15. `/contract-buyout`, `/pride`, and `/dlccapp/tnc` have no h1 because their sources contain no headings, so no h1 was invented. `/yourprivacychoices` is a client-side embedded privacy form and is recorded as `custom`/`blocked`. Fixes made during this pass: quote-only shelves are now `cards (testimonials)` (13 pages re-run), and small icon images keep their authored width in `columns` and `cards`.
- **Help center (T12):** 154 ReadMe.io help articles were converted by `tools/migrate/readme.py`, uploaded, and previewed under `/help/<slug>`, and the custom ReadMe landing page became `/help` (heading plus a `cards` topic grid). The nav and footer "Support" links now point to `/help`. Two new content blocks were added: `callout` (info/success/warn/error) and `table` (DA turns raw tables into blocks). `/help/page/iphone-comparison` is `excluded` because its ReadMe body is null. Gaps: the ReadMe search widget on `/help` and the `troubleshooting-hub` iframe (`boost.sds.modeaondemand.com`) are rendered as links and recorded in `reason`. A local `.plain.html` sweep of all 155 routes found HTTP 200 and one h1 each. It also caught 58 articles that had been converted from the excerpt instead of the body; after the fix, the eight remaining short pages are short in the source (PDF/link hubs). Browser checks covered `/help`, one table, one callout, and one accordion page. Help-center redirects (`help.boostmobile.com/docs/*` → `/help/*`) are part of T15.
- **PLPs (T13):** `tools/migrate/plp.py` reads `plp.json` and creates `product-list-page` pages with `urlpath` set to the ACCS category from the Catalog Service `categories` facet. Implemented: `/shop/devices/handsets` (`phones`) and brand pages `/shop/devices/handsets/{apple,google,samsung}` (`phones/<brand>-…`). The source brand URLs `/l/manufacturer:<brand>` contain a colon, so they moved to `/<brand>` and need redirects in T15. Blocked because the sandbox catalog has no matching category: Motorola, tablets, and watches. Excluded with redirect only: `/shop/devices` and category ids 262/265/266, because the source redirects them to `/`. Also excluded: the `?pid=` and `?manufacturer=` query variants, whose canonical is handsets. Nav brand links now point to the brand PLPs (Motorola keeps the filter link). The Store-to-Door and Affirm tile badges are blocked by missing catalog attributes. Browser checks on `aem.page` covered rendering, PDP links, images, and the facet that filters the URL to `cs_manufacturer:Google`. On `http://localhost`, the protocol-relative catalog image URLs load over http and fail in the canvas browser, so verify Commerce images on https preview.
- **PDP (T14):** The DA `/products/default` template was replaced with a clean `product-details` and breadcrumb metadata page, saved in `content/products__default.html`. The boilerplate demo cards, `enrichment`, and the demo Recommendations `recId` were removed; Recommendations come back when a unit exists for this catalog. The folder mapping `/products/` → `/products/default` was set through the Config Service `folders.json` with the DA token, which has site admin rights. `tools/migrate/pdp.py` matched 3 of 26 source PDPs: Galaxy A16 5G 002198, iPhone 16e 002481, and Pixel 10a 002729. The other 23 are `blocked: catalog`. Browser checks on `aem.page` covered rendering all 3 products with gallery, price, options, and JSON-LD. On iPhone 16e, choosing colour and memory enabled Add to Cart, and adding the item updated the mini cart to 1 item. `tools/migrate/redirects.py` generated 13 rules in the DA `redirects` sheet and kept the existing Apple Pay `.well-known` row. The rules cover legacy PDP `.html` URLs, normalized paths, `/shop/devices`, and category ids 262/265/266. Verified 301s on preview. Not expressible as EDS redirects, so they need CDN redirects at cutover: the `/l/manufacturer:*` colon paths, the `?pid=`/`?manufacturer=` query variants, and `help.boostmobile.com`.

- **Footer (T5):** the DA `/footer` source is versioned in `content/footer.html` and was generated by `scratch/footer_gen.py`. Inventory pages use relative destination paths; featured devices missing from the sandbox, the locator, help root, and careers link to the live site. The newsletter signup form is not migrated (custom; no subscription backend). The sandbox includes Boost Protect SKUs (000699/000700, 001156/001161), which could resolve the PDP Boost Protect upsell in T12.

- **Nav (T3):** the DA `/nav` source is versioned in `content/nav.html`. Brand links filter the handsets PLP with `?filter=cs_manufacturer:<Brand>` (sandbox facet); Motorola has no sandbox products. Activation, compatibility, coverage map, locator, and help link to the live site. The phone number sits in the tools section because the header requires a non-empty third nav section.

- **Fonts:** the source uses licensed Neue Haas Grotesk Text Pro (body) and Druk (display). Tokens name them first, but no font files are committed; browsers fall back to Helvetica Neue/Arial and roboto-condensed until the brand owner supplies licensed web fonts (T2).

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
