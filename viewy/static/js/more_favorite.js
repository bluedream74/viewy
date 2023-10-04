'use strict'

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

// コントロールバーを動画に適応させる処理
function applyControlBarToNewVideos() {
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
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

document.addEventListener('DOMContentLoaded', () => {

  // 読み込みトリガーと、データを追加する場所を指定
  const trigger = document.querySelector('.load-trigger');
  const addHere = document.querySelector('.bottom-space');

  let isLoading = false; // セマフォア変数を追加

  // コントロールバー関連
  //  カスタムイベントの定義
  const newPostEvent = new Event('newPostAdded')

  // 最初の投稿にコントロールバーの設定を適用
  applyControlBarToNewVideos();

  //  カスタムイベントのリッスンと処理の実行
  document.addEventListener('newPostAdded', applyControlBarToNewVideos);

  // コントロールバー終了

  function loadNextPost() {
    console.log('loadNextPost called');
    // 既にロード中の場合はリターン
    if (isLoading) {
      return;
    }
    // ロード中フラグを立てる
    isLoading = true;
    console.log('Loading next post...');

    const allPosts = document.querySelectorAll('.post:not([data-is-advertisement="True"])');
    const lastPostId = allPosts[allPosts.length - 1].dataset.postId;

    const csrftoken = getCookie('csrftoken'); // CSRFトークンを取得

    fetch(`/posts/get_more_favorite/`, { //次の投稿を読み込むビューに送信！
      method: 'POST', // メソッドをPOSTに変更
      body: `last_post_id=${lastPostId}`, // 最後の投稿のIDを送信
      credentials: 'include', // クッキーを含める
      headers: {
        'X-CSRFToken': csrftoken, //これをつけないとブロックされちゃう
        'Content-Type': 'application/x-www-form-urlencoded', // 追加
      },
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok: ' + response.statusText);
        }
        return response.json();
      })
      .then(data => {
        const html = data.html;
        addHere.insertAdjacentHTML('beforebegin', html);

        // 新しく追加された動画要素にコントロールバーを適用
        document.dispatchEvent(newPostEvent);

        // スクロール領域を手動(力技)で更新する
        const screenElement = document.querySelector('.screen');
        screenElement.style.display = 'none';
        screenElement.offsetHeight; // 強制的な再描画をトリガー
        screenElement.style.display = '';
      })
      .catch(error => {
        console.error('Error:', error);
      })
      .finally(() => {
        // ロードが完了したらフラグを戻す
        isLoading = false;
      });
  }


  //トリガーをビューポーに入ったかどうかを監視
  function isactive(entries) {
    console.log('Intersection Observer triggered');
    if (entries[0].isIntersecting && !isLoading) {
      loadNextPost();
    }
  }

  const options = {
    threshold: 0.1,
    rootMargin: '0px 0px 0px 0px',
  };

  const observer = new IntersectionObserver(isactive, options);

  observer.observe(trigger);
});



document.addEventListener('DOMContentLoaded', () => {

  const trigger = document.querySelector('.top-load-trigger');
  const addHere = document.querySelector('.top-space');

  let isLoading = false;

  const newPostEvent = new Event('newPostAdded')

  applyControlBarToNewVideos();
  document.addEventListener('newPostAdded', applyControlBarToNewVideos);
  // コントロールバー終了

  function loadPreviousPost() {
    console.log('loadPreviousPost called');
    if (isLoading) {
      return;
    }
    isLoading = true;
    console.log('Loading previous post...');

    const allPosts = document.querySelectorAll('.not-ad');
    const firstPostId = allPosts[0].dataset.postId;

    const csrftoken = getCookie('csrftoken');

    let data = new FormData();
    data.append('first_post_id', firstPostId);

    fetch(`/posts/get_more_previous_favorite/`, {
      method: 'POST',
      body: data,
      credentials: 'include',
      headers: {
        'X-CSRFToken': csrftoken,
      },
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok: ' + response.statusText);
        }
        return response.json();
      })
      .then(data => {
        const html = data.html;
        addHere.insertAdjacentHTML('afterend', html);

        // Apply control bar to the new video elements
        document.dispatchEvent(newPostEvent);

        // Wait for a little bit longer to ensure DOM is properly updated
        requestAnimationFrame(() => {
          const targetPost = document.querySelector(`[data-post-id='${firstPostId}']`);
          if (targetPost) {
            targetPost.scrollIntoView();

            // Check in the next frame
            requestAnimationFrame(() => {
              const targetRect = targetPost.getBoundingClientRect();
              if (targetRect.top < 0 || targetRect.bottom > window.innerHeight) {
                // If the post is still not in the viewport, force scroll again
                targetPost.scrollIntoView();
              }
            });
          }
        });
      })
      .catch(error => {
        console.error('Error:', error);
      })
      .finally(() => {
        // ロードが完了したらフラグを戻す
        isLoading = false;
      });
  }

  let timer;

  function isActive(entries) {
    console.log('Intersection Observer triggered');
    console.log('isIntersecting:', entries[0].isIntersecting);
    console.log('isLoading:', isLoading);

    if (entries[0].isIntersecting && !isLoading) {
      timer = setTimeout(() => {
        loadPreviousPost();
      }, 500);  // 0.5秒後にloadPreviousPostを呼び出す
    } else if (!entries[0].isIntersecting) {
      clearTimeout(timer);  // 要素がビューポートから出た場合、タイマーをクリア
    }
  }

  const options = {
    threshold: 0.1,
    rootMargin: '0px 0px 0px 0px',
  };

  const observer = new IntersectionObserver(isActive, options);

  observer.observe(trigger);
});



