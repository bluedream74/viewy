'use strict'


document.addEventListener('DOMContentLoaded', () => {

  // 動画要素の監視を行う関数
  function observeVideos(videos) {
    videos.forEach(video => {
      videoObserver.observe(video);
    });
  }

  // 動画の自動再生用のIntersection Observerを作成
  const videoOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.5,
  };

  const videoObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.play().catch(error => {
          console.error('Video play failed:', error);
        });
      } else {
        entry.target.pause();
      }
    });
  }, videoOptions);

  // 初回の動画要素を監視 DOM操作が行われてない最初の十個にも反映させる
  const initialVideos = document.querySelectorAll('video');
  observeVideos(initialVideos);

  // DOMの変更を監視するMutation Observerを作成
  const mutationObserver = new MutationObserver(mutationsList => {
    for (let mutation of mutationsList) {
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(node => {
          if (node instanceof HTMLElement && node.querySelector('video')) {
            const newVideos = node.querySelectorAll('video');
            observeVideos(newVideos);
          }
        });
      }
    }
  });

  // Bind MutationObserver to a container that contains the videos
  const videosContainer = document.querySelector('.screen'); // Change this selector to the parent container of the videos
  mutationObserver.observe(videosContainer, { childList: true, subtree: true });

});