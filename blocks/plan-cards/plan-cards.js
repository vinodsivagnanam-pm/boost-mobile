import { createOptimizedPicture } from '../../scripts/aem.js';

function classifyCell(cell, index) {
  if (cell.querySelector('ul, ol')) return 'features';
  const text = cell.textContent.replace(/\s+/g, ' ').trim();
  const linkText = [...cell.querySelectorAll('a')]
    .map((a) => a.textContent.trim()).join(' ').replace(/\s+/g, ' ').trim();
  if (linkText && text === linkText) return 'actions';
  return index === 0 ? 'header' : 'body';
}

function decorateHeader(cell) {
  const first = cell.querySelector('h1, h2, h3, h4, h5, h6, p');
  if (first) {
    let name = first;
    if (first.tagName === 'P') {
      name = document.createElement('h3');
      name.append(...first.childNodes);
      first.replaceWith(name);
    }
    name.classList.add('plan-cards-name');
  }
  // DA may split "<del>$25</del> $10/mo" into two paragraphs; rejoin them.
  cell.querySelectorAll('p').forEach((p) => {
    const next = p.nextElementSibling;
    const onlyDel = p.children.length === 1 && p.querySelector(':scope > del, :scope > s')
      && p.textContent.trim() === p.firstElementChild.textContent.trim();
    if (onlyDel && next?.tagName === 'P') {
      next.prepend(p.firstElementChild, ' ');
      p.remove();
    }
  });
  const price = [...cell.querySelectorAll('p')].find((p) => /^\$/.test(p.textContent.trim()));
  if (price) price.classList.add('plan-cards-price');
}

function decorateFeatures(cell) {
  cell.querySelectorAll('li').forEach((li) => {
    const pic = li.querySelector('picture');
    if (!pic) return;
    const icon = document.createElement('span');
    icon.className = 'plan-cards-feature-icon';
    icon.append(pic);
    li.prepend(icon);
    li.classList.add('has-icon');
  });
}

function decorateActions(cell) {
  let ctaIndex = 0;
  cell.querySelectorAll('a').forEach((a) => {
    const container = a.closest('p');
    const url = new URL(a.href, window.location.href);
    if (url.pathname.startsWith('/modals/')) {
      a.className = 'plan-cards-details';
      if (container) container.className = 'plan-cards-details-container';
      return;
    }
    a.className = ctaIndex === 0 ? 'button primary' : 'button secondary';
    if (container) container.className = 'button-container';
    ctaIndex += 1;
  });
}

/**
 * Plan cards: one row per plan.
 * Cells are classified by content: header (name, price, note),
 * features (list, optional icons), actions (details modal link + CTAs).
 * @param {Element} block
 */
export default function decorate(block) {
  const ul = document.createElement('ul');
  [...block.children].forEach((row) => {
    if (!row.textContent.trim() && !row.querySelector('picture')) return;
    const li = document.createElement('li');
    li.className = 'plan-cards-card';
    [...row.children].forEach((cell, i) => {
      const role = classifyCell(cell, i);
      cell.className = `plan-cards-${role}`;
      if (role === 'header') decorateHeader(cell);
      if (role === 'features') decorateFeatures(cell);
      if (role === 'actions') decorateActions(cell);
      li.append(cell);
    });
    ul.append(li);
  });
  ul.querySelectorAll('picture > img').forEach((img) => {
    if (new URL(img.src, window.location.href).pathname.endsWith('.svg')) {
      img.closest('picture').querySelectorAll('source').forEach((src) => src.remove());
      return;
    }
    img.closest('picture').replaceWith(
      createOptimizedPicture(img.src, img.alt, false, [{ width: '96' }]),
    );
  });
  block.replaceChildren(ul);
}
