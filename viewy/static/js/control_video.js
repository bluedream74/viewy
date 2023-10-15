'use strict'

let timeoutId;

document.body.addEventListener('mousedown', (event) => {
  if (event.target.matches('.post-video')) {
    timeoutId = setTimeout(() => {
      const targetVideo = event.target;

      if (!targetVideo.paused) {
        targetVideo.pause();
      }
    }, 200); // 200ミリ秒後に動画を一時停止
  }
});

document.body.addEventListener('mouseup', (event) => {
  if (event.target.matches('.post-video')) {
    clearTimeout(timeoutId); // タイムアウトをクリアして、200ミリ秒未満のクリックでの停止を防ぐ
    const targetVideo = event.target;

    if (targetVideo.paused) {
      targetVideo.play();
    }
  }
});

// 停止中の再生ボタン表示の処理
document.body.addEventListener('play', (event) => {
  if (event.target.matches('.post-video')) {
    const playButton = event.target.parentNode.querySelector('.play-button');
    playButton.style.display = 'none';
  }
}, true);

document.body.addEventListener('pause', (event) => {
  if (event.target.matches('.post-video')) {
    const playButton = event.target.parentNode.querySelector('.play-button');
    playButton.style.display = 'block';
  }
}, true);

