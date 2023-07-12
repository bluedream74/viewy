'use strict';

// 指定した個数見終わったらページを遷移する
{
  const target = document.querySelector('.trigger');

  function isactive(entries) {

    if (entries[0].isIntersecting) {
        location.reload();
      }
  }

  const options = {
    threshold: 1,
  };

  const observer = new IntersectionObserver(isactive, options);

  observer.observe(target);
}