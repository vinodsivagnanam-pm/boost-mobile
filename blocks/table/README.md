# Table Block

## Overview

Content block for tabular data (comparisons, rate tables, do/don't lists). Migrated from help-center tables. Raw tables cannot be authored as default content in DA because DA treats every table as a block, so tabular data uses this block.

## Block Structure

| Table (variant) | | |
|---|---|---|
| Column heading | Column heading | Column heading |
| Cell | Cell | Cell |

The first row is the header row. Use the `no-header` variant when there is no header row. Short rows stretch the last cell to fill the row.

## Behavior

- Renders a semantic `<table>` with `thead`/`tbody` and `scope="col"` headings.
- Wide tables scroll horizontally inside a focusable wrapper.
