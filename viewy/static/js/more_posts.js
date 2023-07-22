'use strict'


document.addEventListener('DOMContentLoaded', () => {

  // 動画要素の監視を行う関数
  function observeVideos(videos) {
    videos.forEach(video => {
      videoObserver.observe(video);
    });
  }

  // 動画の自動再生用のIntersection Observerを作成
  const videoOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.5,
  };

  const videoObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.play().catch(error => {
          console.error('Video play failed:', error);
        });
      } else {
        entry.target.pause();
      }
    });
  }, videoOptions);

  // 初回の動画要素を監視 DOM操作が行われてない最初の十個にも反映させる
  const initialVideos = document.querySelectorAll('video');
  observeVideos(initialVideos);

  // DOMの変更を監視するMutation Observerを作成
  const mutationObserver = new MutationObserver(mutationsList => {
    for (let mutation of mutationsList) {
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(node => {
          if (node instanceof HTMLElement && node.querySelector('video')) {
            const newVideos = node.querySelectorAll('video');
            observeVideos(newVideos);
          }
        });
      }
    }
  });

  // Bind MutationObserver to a container that contains the videos
  const videosContainer = document.querySelector('.screen'); // Change this selector to the parent container of the videos
  mutationObserver.observe(videosContainer, { childList: true, subtree: true });

});


document.addEventListener('DOMContentLoaded', () => {

  const trigger = document.querySelector('.load-trigger');
  const addHere = document.querySelector('.bottom-space');
  let isLoading = false; // セマフォア変数を追加

  function loadNextPost() {
    console.log('loadNextPost called');
    // 既にロード中の場合はリターン
    if (isLoading) {
      return;
    }
    // ロード中フラグを立てる
    isLoading = true;
    console.log('Loading next post...');

    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

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
        console.log('データの中身はこれだよ→:', data);
        const html = data.html;
        addHere.insertAdjacentHTML('beforebegin', html);

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