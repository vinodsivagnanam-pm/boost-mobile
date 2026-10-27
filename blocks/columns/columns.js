export default function decorate(block) {
  const cols = [...block.firstElementChild.children];
  block.classList.add(`columns-${cols.length}-cols`);

  // small source images (icons, badges) keep their authored size instead of filling the column
  block.querySelectorAll('img[width]').forEach((img) => {
    const w = parseInt(img.getAttribute('width'), 10);
    if (w > 0 && w <= 200) {
      img.classList.add('icon');
      img.style.width = `${w}px`;
    }
  });

  // setup image columns
  [...block.children].forEach((row) => {
    [...row.children].forEach((col) => {
      const pic = col.querySelector('picture');
      if (pic) {
        const picWrapper = pic.closest('div');
        if (picWrapper && picWrapper.children.length === 1) {
          // picture is only content in column
          picWrapper.classList.add('columns-img-col');
        }
      }
    });
  });
}
