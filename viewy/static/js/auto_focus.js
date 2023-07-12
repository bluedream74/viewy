'use strict';
{
  const targets = document.querySelectorAll('.post, .book');

  function isactive(entries) {

    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.setAttribute("tabindex", 0);
        entry.target.focus();
      }
    });
  }

  const options = {
    threshold: 1,
  };

  const observer = new IntersectionObserver(isactive, options);

  targets.forEach(target => {
    observer.observe(target);
  });
}