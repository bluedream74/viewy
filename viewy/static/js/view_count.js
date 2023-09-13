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
              const postId = entry.target.getAttribute('data-post-id');

              fetch(`/posts/increment_view_count/${postId}`, {
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
              .then(data => 
                {}
                )
              .catch(error => console.error(`Fetch error: ${error}`));

          }
      });
  }

  // 全てのpost要素に対してIntersection Observerを設定
  const postElements = document.querySelectorAll('.not-ad');
  postElements.forEach(post => observer.observe(post));

  // DOMの変更を監視するMutation Observerを作成
  const mutationObserver = new MutationObserver(mutationsList => {
    for (let mutation of mutationsList) {
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(node => {
          if (node instanceof HTMLElement && node.classList.contains('not-ad')) {
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
