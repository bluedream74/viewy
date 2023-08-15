'use strict'

document.body.addEventListener('click', (event) => {
  if (event.target.matches('.post-video')) {
    const targetVideo = event.target;
    const playButton = targetVideo.nextElementSibling; // 隣接する再生ボタンを取得

    if (targetVideo.paused) {
      targetVideo.play();
      playButton.style.opacity = '0'; // ボタンを非表示
    } else {
      targetVideo.pause();
      playButton.style.opacity = '0.7'; // ボタンを表示
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


