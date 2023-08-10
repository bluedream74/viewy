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

        fetch(`/posts/wideads_view_count/${adId}`, { // WideAdsのエンドポイントへ
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

  // 全てのWideAds要素に対してIntersection Observerを設定
  const widePostElements = document.querySelectorAll('.wide-ad'); // クラス名をWideAd用に変更
  widePostElements.forEach(post => observer.observe(post));

  // 全ての広告を監視するために使用するMutation Observerは同じ

  // CSRFトークンを取得するための関数
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }
});


// WideAdsをクリックした回数をカウント

document.querySelector('.screen').addEventListener('click', event => {
  const ad = event.target.closest('.wide-ad'); // セレクタをWideAds用に変更

  // CSRFトークンを取得するための関数
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

  if (ad) {
    const adId = ad.getAttribute('data-ad-id');



    fetch(`/posts/wideads_click_count/${adId}`, { // WideAdsのエンドポイントへ
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