'use strict'


document.addEventListener('DOMContentLoaded', () => {

   // 読み込みトリガーと、データを追加する場所を指定
  const trigger = document.querySelector('.load-trigger');
  const addHere = document.querySelector('.bottom-space');
  if (!trigger || !addHere) {
    console.error('Trigger or insertion point not found!');
    return;
  }
  let isLoading = false; // セマフォア変数を追加



  // 以下コントロールバー関連

  //  カスタムイベントの定義
  const newPostEvent = new Event('newPostAdded')

  const baseColor = 'rgba(150, 150, 150, 0.539)';
  const activeColor = 'rgba(255, 255, 255, 0.639)';

  function setupControlBar(video, seekSlider) {
    video.addEventListener('loadedmetadata', () => {
      seekSlider.max = video.duration;
    });

    video.addEventListener('timeupdate', () => {
      seekSlider.value = video.currentTime;
      const progress = (seekSlider.value / seekSlider.max) * 100;
      seekSlider.style.background = `linear-gradient(to right, ${activeColor} ${progress}%, ${baseColor} ${progress}%)`;
    });

    seekSlider.addEventListener('input', () => {
      video.currentTime = seekSlider.value;
    });
  }

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

  // 最初の投稿にコントロールバーの設定を適用
  applyControlBarToNewVideos();

  //  カスタムイベントのリッスンと処理の実行
  document.addEventListener('newPostAdded', applyControlBarToNewVideos);


  function loadNextPost() {
    // 既にロード中の場合はリターン
    if (isLoading) return;

    // ロード中フラグを立てる
    isLoading = true;

    // CSRFトークンを取得するための関数
    function getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
    }
    const csrftoken = getCookie('csrftoken'); // CSRFトークンを取得

    fetch(`/posts/get_more_posts/`, { //次の投稿を読み込むビューに送信！
      credentials: 'include', // クッキーを含める
      headers: {
        'X-CSRFToken': csrftoken //これをつけないとブロックされちゃう
      }
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

        // 以下コントロールバー関連

        // 新しい投稿を追加した際にカスタムイベントを発行
        // 新しく追加された動画要素にコントロールバーを適用
        document.dispatchEvent(newPostEvent);

        // 以上コントロールバー関連終わり

        // スクロール領域を手動(力技)で更新する
        const screenElement = document.querySelector('.screen');
        screenElement.style.display = 'none';
        screenElement.offsetHeight; // 強制的な再描画をトリガー
        screenElement.style.display = '';
        
      })
      .catch(error => console.error('Error:', error))

      .finally(() => {
        // ロードが完了したらフラグを戻す
        isLoading = false;
      });
  }


  //トリガーをビューポートに入ったかどうかを監視

  function isactive(entries) {
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