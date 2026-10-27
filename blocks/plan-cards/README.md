# Plan Cards Block

## Overview

Content block that shows mobile plans side by side (scrollable on mobile, a row on desktop). Migrated from the source `cmp-card-shelf` plan cards. It is a content block, not a drop-in. CTAs link to Commerce pages (compatibility check or PLP).

## Block Structure

One row per plan. Cells are recognized by content, so order and count are flexible:

| Plan Cards | | |
|---|---|---|
| **Header**: plan name (first heading or paragraph), price paragraph starting with `$` (use strikethrough for the old price), notes | **Features**: bullet list; an optional icon image at the start of each item | **Actions**: links only. A link to `/modals/...` becomes a "details" text link that opens a modal; other links become primary then secondary buttons |

Extra non-list, non-link cells render as `plan-cards-body`.

## Behavior

- Mobile: horizontal scroll with snap; tablet: two cards visible; desktop (900px+): all cards in one row.
- `/modals/...` links are opened in a dialog by `autolinkModals` in `scripts/scripts.js`.
- Empty rows are skipped.
