'use strict'

// ビデオ要素を取得
const targetVideos = document.querySelectorAll('.post-video');

targetVideos.forEach(targetVideo => {
  // ビデオがクリックされたときに再生/一時停止を切り替える
  targetVideo.addEventListener('click', () => {
    if (targetVideo.paused) {
      targetVideo.play();
    } else {
      targetVideo.pause();
    }
  });
});
