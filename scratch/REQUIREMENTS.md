# Requirements: migrate www.boostmobile.com to EDS Commerce storefront

## Project state (from repository inspection)

- Boilerplate: `hlxsites/aem-boilerplate-commerce`, commit `ea3f33a`.
- Destination: GitHub `vinodsivagnanam-pm/boost-mobile`, DA.live `vinodsivagnanam-pm/boost-mobile`, starter content present, preview live.
- Commerce: ACCS sandbox (`config.json`), 18 products.
- Drop-ins AI tools MCP not connected in this host; fall back to installed type definitions and docs.

## Discovery summary

See `migration/www.boostmobile.com/report.md` and `urls.csv` (181 in-scope rows, 82,456 locator URLs grouped).

## Open questions

1. Scope of the 82,456 store-locator pages.
2. Scope of `help.boostmobile.com` and `es.boostmobile.com`.
3. Product catalog: migrate PDP/PLP pages only for products in the sandbox, or load source products into the sandbox first.
4. Carrier flows (activation, compatibility check, coverage map, BYOD, account login): link out to the live source, or build placeholders that are clearly marked as not functional.
5. Content delivery: local drafts only, or also create pages in DA.live (requires authoring access).
6. Batch order and depth: template-first (one page per template, then fill) is the default.

## Phase 1: Complete ✅
Date: 2026-10-27

## Decisions (2026-10-27)
- Store locator: excluded; link to live locator.
- help.boostmobile.com → /help/<slug>; es.boostmobile.com → /es/<path>: in scope.
- PDP: single /products/default template + redirects from /shop/*.html; PLP single template.
- Carrier flows (activation, compatibility, coverage, BYOD/multiline, account): link out.
- Content destination: DA.live directly (user authorizes write access).

## Phase 2: Architectural Plan Presented
See migration/www.boostmobile.com/plan.md

## Phase 3: Option A chosen; detailed plan in plan.md §7
