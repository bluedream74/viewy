'use strict'

// body要素にイベントリスナーを設定
document.body.addEventListener('click', (event) => {
  // クリックされた要素がビデオ要素かどうかを判定
  if (event.target.matches('.post-video')) {
    const targetVideo = event.target;
    const playButton = targetVideo.nextElementSibling; // 隣接する再生ボタンを取得

    // ビデオが再生中なら一時停止、一時停止中なら再生を行う
    if (targetVideo.paused) {
      targetVideo.play();
      playButton.style.opacity = '0'; // ボタンを非表示
    } else {
      targetVideo.pause();
      playButton.style.opacity = '0.7'; // ボタンを表示
    }
  }
});

