'use strict'

document.addEventListener('DOMContentLoaded', () => {
  // Intersection Observerの設定
  const observer = new IntersectionObserver(incrementViewCount, {
      threshold: 0.1
  });

  function incrementViewCount(entries, observer) {
      entries.forEach(entry => {
          // ビューポートに入ったらカウントアップ
          if (entry.isIntersecting) {
              const adId = entry.target.getAttribute('data-ad-id');

              fetch(`/posts/ad_view_count/${adId}`, {
                  method: 'POST',
                  headers: {
                      'X-CSRFToken': getCookie('csrftoken'),
                      'Accept': 'application/json',
                      'Content-Type': 'application/json'
                  },
              })
              .then(response => {
                  if (!response.ok) {
                      throw new Error(`Network response was not ok: ${response.statusText}`);
                  }
                  return response.json();
              })
              .then(data => console.log(data.message))
              .catch(error => console.error(`Fetch error: ${error}`));

              // カウントアップが終わったら監視を停止
              observer.unobserve(entry.target);
          }
      });
  }

  // 全てのpost要素に対してIntersection Observerを設定
  const postElements = document.querySelectorAll('.ad');
  postElements.forEach(post => observer.observe(post));

  // DOMの変更を監視するMutation Observerを作成
  const mutationObserver = new MutationObserver(mutationsList => {
    for (let mutation of mutationsList) {
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(node => {
          if (node instanceof HTMLElement && node.classList.contains('ad')) {
            observer.observe(node);
          }
        });
      }
    }
  });

  // MutationObserverを投稿の親コンテナにバインド
  const postsContainer = document.querySelector('.screen'); // Change this selector to the parent container of the posts
  mutationObserver.observe(postsContainer, { childList: true, subtree: true });

  // CSRFトークンを取得するための関数
  function getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
  }
});


// 広告をクリックした回数をカウント

document.querySelector('.screen').addEventListener('click', event => {
  const ad = event.target.closest('.ad-page');   // 普通に.adにしたら広告に飛ばない範囲を押してもカウントされてしまうから.ad-pageにした

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

  if (ad) {
      const adId = ad.getAttribute('data-ad-id');

      fetch(`/posts/ad_click_count/${adId}`, {
          method: 'POST',
          headers: {
              'X-CSRFToken': getCookie('csrftoken'),
              'Accept': 'application/json',
              'Content-Type': 'application/json'
          },
      })
      .then(response => {
          if (!response.ok) {
              throw new Error(`Network response was not ok: ${response.statusText}`);
          }
          return response.json();
      })
      .then(data => console.log(data.message))
      .catch(error => console.error(`Fetch error: ${error}`));
  }
});
