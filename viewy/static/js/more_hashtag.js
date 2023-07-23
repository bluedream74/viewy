'use strict'


document.addEventListener('DOMContentLoaded', () => {

  // 読み込みトリガーと、データを追加する場所を指定
  const trigger = document.querySelector('.load-trigger');
  const addHere = document.querySelector('.bottom-space');

  let isLoading = false; // セマフォア変数を追加

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

    // ハッシュタグを取得 hashtag_list.htmlの下のdivに隠してある
    const hashtag = document.querySelector('#hashtagContainer').dataset.hashtag;


    const csrftoken = getCookie('csrftoken'); // CSRFトークンを取得
  
    let data = new FormData();
    data.append('last_post_id', lastPostId);
    data.append('hashtag', hashtag);  // Add the hashtag

    fetch(`/posts/get_more_hashtag/`, { //次の投稿を読み込むビューに送信！
      method: 'POST', // メソッドをPOSTに変更
      body: data, // データを送信
      credentials: 'include', // クッキーを含める
      headers: {
        'X-CSRFToken': csrftoken, //これをつけないとブロックされちゃう
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

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

  function loadPreviousPost() {
    console.log('loadPreviousPost called');
    if (isLoading) {
      return;
    }
    isLoading = true;
    console.log('Loading previous post...');

    const allPosts = document.querySelectorAll('.not-ad');
    const firstPostId = allPosts[0].dataset.postId;

    const hashtag = document.querySelector('#hashtagContainer').dataset.hashtag;

    const csrftoken = getCookie('csrftoken');
  
    let data = new FormData();
    data.append('first_post_id', firstPostId);
    data.append('hashtag', hashtag);

    fetch(`/posts/get_more_previous_hashtag/`, {
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

        // Load the first post into view after fetching
        const targetPost = document.querySelector(`[data-post-id='${firstPostId}']`);
        if (targetPost) {
            targetPost.scrollIntoView();
        }
      })
      .catch(error => {
        console.error('Error:', error);
      })
      .finally(() => {
        isLoading = false;
      });
  }

  function isactive(entries) {
    console.log('Intersection Observer triggered');
    if (entries[0].isIntersecting && !isLoading) {
      loadPreviousPost();
    }
  }

  const options = {
    threshold: 0.1,
    rootMargin: '0px 0px 0px 0px',
  };

  const observer = new IntersectionObserver(isactive, options);

  observer.observe(trigger);
});

