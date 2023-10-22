'use strict'

let timeoutId;

function handleStart(event) {
  if (event.target.matches('.post-video')) {
    timeoutId = setTimeout(() => {
      const targetVideo = event.target;

      if (!targetVideo.paused) {
        targetVideo.pause();
      }
    }, 200); // 200ミリ秒後に動画を一時停止
  }
}

function handleEnd(event) {
  if (event.target.matches('.post-video')) {
    clearTimeout(timeoutId); // タイムアウトをクリアして、200ミリ秒未満のクリックでの停止を防ぐ
    const targetVideo = event.target;

    if (targetVideo.paused) {
      targetVideo.play();
    }
  }
}

document.body.addEventListener('mousedown', handleStart);
document.body.addEventListener('mouseup', handleEnd);

// タッチデバイス用のイベントリスナーを追加
document.body.addEventListener('touchstart', handleStart);
document.body.addEventListener('touchend', handleEnd);

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

