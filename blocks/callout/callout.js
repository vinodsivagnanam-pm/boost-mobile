export default function decorate(block) {
  const content = document.createElement('div');
  content.className = 'callout-content';
  [...block.querySelectorAll(':scope > div > div')].forEach((cell) => content.append(...cell.childNodes));
  block.replaceChildren(content);
  if (block.classList.contains('error') || block.classList.contains('warn')) block.setAttribute('role', 'note');
}
