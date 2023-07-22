'use strict'

// body要素にイベントリスナーを設定
document.body.addEventListener('click', (event) => {
  // クリックされた要素がビデオ要素かどうかを判定
  if (event.target.matches('.post-video')) {
    const targetVideo = event.target;

    // ビデオが再生中なら一時停止、一時停止中なら再生を行う
    if (targetVideo.paused) {
      targetVideo.play();
    } else {
      targetVideo.pause();
    }
  }
});

