'use strict'


document.addEventListener('DOMContentLoaded', () => {

  // 読み込みトリガーと、データを追加する場所を指定
  const trigger = document.querySelector('.load-trigger');
  const addHere = document.querySelector('.bottom-space');

  let isLoading = false; // セマフォア変数を追加

 // コントロールバー関連
  //  カスタムイベントの定義
  const newPostEvent = new Event('newPostAdded')

  const baseColor = '#ffffff';
  const activeColor = 'rgb(41, 239, 239)';

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

  // コントロールバー終了

  // CSRFトークンを取得するための関数
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

  function loadNextPost() {
    console.log('loadNextPost called');
    // 既にロード中の場合はリターン
    if (isLoading) {
      return;
    }
    // ロード中フラグを立てる
    isLoading = true;
    console.log('Loading next post...');

    const allPosts = document.querySelectorAll('.not-ad');
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

  const topTrigger = document.querySelector('.top-load-trigger');
  const topAddHere = document.querySelector('.top-space');
  
  let isTopLoading = false; // セマフォア変数を追加

 // コントロールバー関連
  //  カスタムイベントの定義
  const newPostEvent = new Event('newPostAdded')

  const baseColor = '#ffffff';
  const activeColor = 'rgb(41, 239, 239)';

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

  // コントロールバー終了
  
  function loadPreviousPost() {
    console.log('loadPreviousPost called');
    // 既にロード中の場合はリターン
    if (isTopLoading) {
      return;
    }
    // ロード中フラグを立てる
    isTopLoading = true;
    console.log('Loading previous post...');
  
    const allPosts = document.querySelectorAll('.not-ad');
    const firstPostId = allPosts[0].dataset.postId;

    function getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
    }
    
    const csrftoken = getCookie('csrftoken'); // CSRFトークンを取得


    fetch(`/posts/get_more_previous_favorite/`, {
      method: 'POST',
      body: `first_post_id=${firstPostId}`,
      credentials: 'include',
      headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/x-www-form-urlencoded',
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
        topAddHere.insertAdjacentHTML('afterend', html); 

        // 新しく追加された動画要素にコントロールバーを適用
        document.dispatchEvent(newPostEvent);
        
        // 最初の投稿までスクロール
        const targetPost = document.querySelector(`[data-post-id='${firstPostId}']`);
        if (targetPost) {
            targetPost.scrollIntoView();
        }
      })
  }
  
  function isTopActive(entries) {
    console.log('Top Intersection Observer triggered');
    if (entries[0].isIntersecting && !isTopLoading) {
      loadPreviousPost();
    }
  }
  
  const topOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px 0px 0px',
  };
  
  const topObserver = new IntersectionObserver(isTopActive, topOptions);
  
  topObserver.observe(topTrigger);


});



