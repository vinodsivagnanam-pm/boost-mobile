/**
 * Table block: each row becomes a table row. The first row is a header row
 * unless the block has the `no-header` variant.
 */
export default function decorate(block) {
  const table = document.createElement('table');
  const hasHeader = !block.classList.contains('no-header');
  const rows = [...block.children];
  const width = Math.max(...rows.map((r) => r.children.length), 1);
  let tbody = table;
  rows.forEach((row, i) => {
    const header = hasHeader && i === 0;
    if (header || i === (hasHeader ? 1 : 0)) {
      tbody = document.createElement(header ? 'thead' : 'tbody');
      table.append(tbody);
    }
    const tr = document.createElement('tr');
    const cells = [...row.children];
    cells.forEach((cell, c) => {
      const td = document.createElement(header ? 'th' : 'td');
      if (header) td.scope = 'col';
      if (c === cells.length - 1 && cells.length < width) td.colSpan = width - cells.length + 1;
      td.append(...cell.childNodes);
      tr.append(td);
    });
    tbody.append(tr);
  });
  const wrapper = document.createElement('div');
  wrapper.className = 'table-scroll';
  wrapper.tabIndex = 0;
  wrapper.append(table);
  block.replaceChildren(wrapper);
}
