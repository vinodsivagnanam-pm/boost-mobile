import { createOptimizedPicture } from '../../scripts/aem.js';

export default function decorate(block) {
  /* change to ul, li */
  const ul = document.createElement('ul');
  [...block.children].forEach((row) => {
    const li = document.createElement('li');
    while (row.firstElementChild) li.append(row.firstElementChild);
    [...li.children].forEach((div) => {
      if (div.children.length === 1 && div.querySelector('picture')) div.className = 'cards-card-image';
      else div.className = 'cards-card-body';
    });
    ul.append(li);
  });
  ul.querySelectorAll('picture > img').forEach((img) => {
    const w = parseInt(img.getAttribute('width'), 10);
    const pic = createOptimizedPicture(img.src, img.alt, false, [{ width: '750' }]);
    // small source images (icons, badges) keep their authored size
    if (w > 0 && w <= 200) {
      const optimized = pic.querySelector('img');
      optimized.classList.add('icon');
      optimized.style.width = `${w}px`;
    }
    img.closest('picture').replaceWith(pic);
  });
  block.replaceChildren(ul);
}
