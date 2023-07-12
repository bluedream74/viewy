'use strict'

// Intersection Observerのオプションを設定
const options = {
  root: null,
  rootMargin: '0px',
  threshold: 0.5,
};

// Intersection Observerを作成し、監視対象の要素を指定する
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // 画面内に入った動画要素を再生する
      entry.target.play();
    } else {
      // 画面外に出た動画要素を停止する
      entry.target.pause();
    }
  });
}, options);

// 監視対象の要素を取得し、Intersection Observerに追加する
const videos = document.querySelectorAll('video');
videos.forEach(video => {
  observer.observe(video);
});
