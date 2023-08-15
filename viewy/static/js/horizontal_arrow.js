'use sirict'

document.addEventListener("DOMContentLoaded", function () {
  let icon = document.querySelector('.horizontal-slide-icon');
  if (icon) { // iconが存在する場合のみ、オブザーバーを設定
    let observer = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) {
        icon.classList.add('show-icon');
        // 以降の交差を無視
        observer.disconnect();
      }
    });
    observer.observe(icon);
  }
});