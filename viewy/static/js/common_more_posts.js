'use strict'

// まだ見てない部分の色指定
export const baseColor = 'rgba(150, 150, 150, 0.539)';
// 見た部分の色指定
export const activeColor = 'rgba(255, 255, 255, 0.639)';

// コントロールバーの設定
export function setupControlBar(video, seekSlider) {
  video.addEventListener('loadedmetadata', function() {
    seekSlider.max = video.duration;
  });

  video.addEventListener('timeupdate', function() {
    seekSlider.value = video.currentTime;
    updateSlider(seekSlider);
  });

  seekSlider.addEventListener('input', function() {
    video.currentTime = seekSlider.value;
  });

  // 透明なヒットエリアを作成
  var hitArea = document.createElement('div');
  hitArea.classList.add('hit-area');
  seekSlider.parentElement.insertBefore(hitArea, seekSlider.nextSibling);

  // ヒットエリアにドラッグ動作のイベントリスナを追加
  hitArea.addEventListener('mousedown', startDrag);
  hitArea.addEventListener('touchstart', startDrag);
  
  function startDrag(event) {
    event.preventDefault(); // ブラウザのデフォルトのタッチ動作を防ぎます

    var isDragging = false; // 最初はfalseに設定

    var initialClientX = (event.touches ? event.touches[0].clientX : event.clientX);
    var initialSliderValue = parseFloat(seekSlider.value);

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('touchmove', onMouseMove);

    document.addEventListener('mouseup', endDrag);
    document.addEventListener('touchend', endDrag);

    function onMouseMove(event) {
        if (!isDragging) {
            isDragging = true; // 最初のmousemoveまたはtouchmoveイベントでtrueに設定
            updateSliderValue(event);
        } else {
            updateSliderValue(event);
        }
    }

    function updateSliderValue(event) {
        var currentX = (event.touches ? event.touches[0].clientX : event.clientX);
        var rect = hitArea.getBoundingClientRect();
        var dx = currentX - initialClientX;
        var changeInValue = (dx / rect.width) * parseFloat(seekSlider.getAttribute('max'));
        var newValue = initialSliderValue + changeInValue;

        newValue = Math.min(Math.max(newValue, 0), parseFloat(seekSlider.getAttribute('max')));

        seekSlider.value = newValue;
        video.currentTime = newValue;
        updateSlider(seekSlider);
    }

    function endDrag() {
        isDragging = false;

        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('touchmove', onMouseMove);

        document.removeEventListener('mouseup', endDrag);
        document.removeEventListener('touchend', endDrag);
    }
}
  

  function updateSlider(slider) {
    var progress = (slider.value / slider.max) * 100;
    slider.style.background = `linear-gradient(to right, ${activeColor} ${progress}%, ${baseColor} ${progress}%)`;
  }

  // Run once to set initial state
  updateSlider(seekSlider);
}

// コントロールバーを動画に適応させる処理
export function applyControlBarToNewVideos() {
  const videos = document.querySelectorAll('.post-video:not(.initialized)');
  const sliders = document.querySelectorAll('.custom-controlbar:not(.initialized)');

  videos.forEach((video, i) => {
    const seekSlider = sliders[i];
    if (video && seekSlider) {
      video.classList.add('initialized');
      seekSlider.classList.add('initialized');
      setupControlBar(video, seekSlider);
    }
  });
}

// csrfトークン用のクッキーの設定
export function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}
