document.addEventListener("DOMContentLoaded", function () {
  let previewButton = document.querySelector("[name='preview_button']");
  let url = document.querySelector(".preview-url");
  url.style.display = "none";

  let closeButton = document.querySelector(".close-preview");
  let postPreview = document.querySelector(".post-preview");

  closeButton.addEventListener("click", function () {
    postPreview.style.display = "none";

    // すべての<video>要素の再生を停止
    let videos = document.querySelectorAll(".post-video");
    videos.forEach(video => {
      video.pause();
      video.currentTime = 0;  // もし動画を最初から再開させたい場合
    });
  });


  // ミュートトグルのイベントリスナー
  let muteToggle = document.querySelector(".mute label");
  if (muteToggle) {
    muteToggle.addEventListener("click", function () {
      let video = document.querySelector(".post-video");
      let muteCheckbox = this.querySelector(".mute-frag");

      if (video) {
        video.muted = muteCheckbox.checked; // チェックボックスの状態に基づいてミュートを設定
        // アイコンの変更
        if (video.muted) {
          this.className = "fa-solid fa-volume-xmark";
        } else {
          this.className = "fa-solid fa-volume-low";
        }
      }
    });
  }

  if (previewButton) {
    previewButton.addEventListener("click", function (event) {
      event.preventDefault();
      postPreview.style.display = "block";


      // すべての<video>要素を削除
      let existingVideos = document.querySelectorAll("video");
      existingVideos.forEach(video => {
        video.remove();
      });

      let visualsInput = document.querySelector("input[type='file']");  // <-- 追加
      // visualsInputの存在をチェック
      if (!visualsInput) {
        console.error('File inputが見つかりませんでした!');
        return;
      }

      if (visualsInput.files && visualsInput.files.length > 0) {
        let file = visualsInput.files[0];
        if (file.type.match('video.*')) {
          let reader = new FileReader();

          reader.onload = function (e) {
            let newPreview = document.createElement("video");
            newPreview.setAttribute("width", "200px");
            newPreview.setAttribute("height", "400px");
            newPreview.setAttribute("src", e.target.result);
            newPreview.setAttribute("loading", "lazy");
            newPreview.setAttribute("muted", "");
            newPreview.setAttribute("playsinline", "");
            newPreview.setAttribute("loop", "");
            newPreview.className = "post-video";
            newPreview.muted = true;

            let previewBlock = document.querySelector(".post");
            let spinnerElement = previewBlock.querySelector(".spinner");
            if (spinnerElement) {
              spinnerElement.insertAdjacentElement('afterend', newPreview);
            }

            // プレビューボタンをクリックしたときの動画再生
            newPreview.play().catch(error => {
              console.error('Video play on preview button click failed:', error);
            });

            const previewSeekSlider = document.querySelector(".post-preview .custom-controlbar");
            if (previewSeekSlider) {
              setupControlBar(newPreview, previewSeekSlider);
            }
          };
          reader.readAsDataURL(file);
        } else {
          console.log("選択されたファイルはビデオではありません。");
        }
      }

      let adInformationFields = Array.from(document.querySelectorAll(".fieldWrapper input, .fieldWrapper select, .fieldWrapper textarea"));
      let adInformation = {};
      adInformationFields.forEach(field => {
        adInformation[field.name] = field.value;
      });

      // Post Details
      let title = document.querySelector(".title input");
      let url = document.querySelector(".url-set input");
      let hashtags = [
        document.querySelector(".hashtag1 input"),
        document.querySelector(".hashtag2 input"),
        document.querySelector(".hashtag3 input"),
      ];

      let caption = document.querySelector(".caption textarea");

      // Update the preview:
      let previewBlock = document.querySelector(".post");
      if (title && title.value) {
        previewBlock.querySelector(".preview-title").textContent = title.value;
      }
      if (url && url.value) {
        previewBlock.querySelector(".preview-url a").href = url.value;
        previewBlock.querySelector(".preview-url").style.display = "inline-block"; // 追加
      } else {
        previewBlock.querySelector(".preview-url").style.display = "none"; // 追加
      }
      if (caption && caption.value) {
        previewBlock.querySelector(".preview-caption").textContent = caption.value;
      }

      let hashtagElements = previewBlock.querySelectorAll(".hashtag a");

      hashtags.forEach((hashtagInput, index) => {
        if (hashtagInput && hashtagInput.value && hashtagElements[index]) {
          hashtagElements[index].textContent = "#" + hashtagInput.value;
          hashtagElements[index].parentNode.style.display = "inline"; // 追加
        } else {
          hashtagElements[index].parentNode.style.display = "none"; // 追加
        }
      });

    });
  }

});

// 動画のクリックイベントリスナー
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

// 動画が再生されたときのイベントリスナー
document.body.addEventListener('play', (event) => {
  if (event.target.matches('.post-video')) {
    const playButton = event.target.parentNode.querySelector('.play-button');

    playButton.style.display = 'none';

  }
}, true);

// 動画が停止されたときのイベントリスナー
document.body.addEventListener('pause', (event) => {
  if (event.target.matches('.post-video')) {
    const playButton = event.target.parentNode.querySelector('.play-button');

    playButton.style.display = 'block';

  }
}, true);


// まだ見てない部分の色指定
const baseColor = 'rgba(150, 150, 150, 0.539)';
// 見た部分の色指定
const activeColor = 'rgba(255, 255, 255, 0.639)';

// コントロールバーの設定
function setupControlBar(video, seekSlider) {
  video.addEventListener('loadedmetadata', function () {
    seekSlider.max = video.duration;
  });

  video.addEventListener('timeupdate', function () {
    seekSlider.value = video.currentTime;
    updateSlider(seekSlider);
  });

  seekSlider.addEventListener('input', function () {
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