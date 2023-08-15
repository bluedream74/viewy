'use strict'

document.body.addEventListener('click', (event) => {
  if (event.target.matches('.post-video')) {
    const targetVideo = event.target;

    if (targetVideo.paused) {
      targetVideo.play();
    } else {
      targetVideo.pause();
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


