# Callout Block

## Overview

Content block for a highlighted note, tip, or warning inside article text. Migrated from ReadMe.io callouts and blockquotes in the help center. It is a content block, not a drop-in.

## Block Structure

| Callout (variant) |
|---|
| Any default content: headings, paragraphs, lists, links |

Variants: none (neutral), `info`, `success`, `warn`, `error`. Extra rows or cells are merged in order.

## Behavior

- All cells are merged into one `.callout-content` container.
- `warn` and `error` callouts get `role="note"`.
