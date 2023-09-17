'use strict'


document.addEventListener('change', event => {
  if (event.target.matches('.like-button')) {
    const likeButton = event.target;
    // ボタンを無効化
    likeButton.disabled = true;

    const form = likeButton.closest('form');
    const heartIcon = form.querySelector('.fa-heart');
    const favoriteCountElement = form.querySelector('.favorite-count');

    // クリック時にクラスをすぐ切り替える
    let favoriteCount = parseInt(favoriteCountElement.textContent, 10);
    if (likeButton.checked) {
      favoriteCount += 1;
      heartIcon.classList.remove('not-liked', 'fa-regular');
      heartIcon.classList.add('liked', 'fa-solid');
    } else {
      favoriteCount -= 1;
      heartIcon.classList.add('not-liked', 'fa-regular');
      heartIcon.classList.remove('liked', 'fa-solid');
    }

    // ページ上で即座にカウントを更新
    favoriteCountElement.textContent = favoriteCount;

    const postPk = form.dataset.pk;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const url = form.action;
    const formData = new FormData(form);
    formData.append('csrfmiddlewaretoken', csrftoken);

    fetch(url, {
      method: 'POST',
      body: formData,
    })
      .then(response => response.json())
      .then(data => {
        // 応答を受け取った後、ボタンを再度有効化
        likeButton.disabled = false;
        // サーバーからの応答を受けてカウントを更新（必要に応じて）
        favoriteCountElement.textContent = data.favorite_count;
      })
      .catch(error => {
        console.log(error);
        // エラーが発生した場合でも、ボタンを再度有効化
        likeButton.disabled = false;
      });
  }
});


document.addEventListener('change', event => {
  if (event.target.matches('.mini-follow-button')) {
    const FollowButton = event.target;

    // ボタンを一時的に無効化
    FollowButton.disabled = true;
    // ボタンが押された後、それ以上ボタンが押せないようにする
    FollowButton.style.pointerEvents = 'none';
    // カーソルを通常の矢印カーソルに設定
    FollowButton.style.cursor = 'default';

    const followPosterDiv = FollowButton.closest('.follow-poster');
    // フェードアウトアニメーションを適用
    followPosterDiv.classList.add('fade-out');



    const form = FollowButton.closest('form');
    const posterPk = form.dataset.pk;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const url = form.action;
    const formData = new FormData(form);
    formData.append('csrfmiddlewaretoken', csrftoken);

    const notFollowed = form.querySelector('.fa-solid.fa-plus');
    if (FollowButton.checked) {
      notFollowed.classList.add('fa-check');
      notFollowed.classList.remove('fa-plus');
    }

    fetch(url, {
      method: 'POST',
      body: formData,
    })
      .then(() => {

      })
      .catch(error => {
        console.log(error);
      });
  }
});




const FollowButtons = document.querySelectorAll('.follow-button');
FollowButtons.forEach(FollowButton => {
  FollowButton.addEventListener('change', () => {
    const form = FollowButton.closest('form');
    const followCountElement = form.querySelector('.follow-count');
    let currentFollowCount = parseInt(followCountElement.textContent);
    const posterPk = form.dataset.pk;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const url = form.action;
    const formData = new FormData(form);
    formData.append('csrfmiddlewaretoken', csrftoken);

    // ボタンを一時的に無効化
    FollowButton.disabled = true;

    // クラスの付け替えを直接ここで行う
    const followed = form.querySelector('.followed');
    const notFollowed = form.querySelector('.follow');
    if (FollowButton.checked) {
      notFollowed.classList.add('followed');
      notFollowed.classList.remove('follow');
      notFollowed.textContent = 'フォロー中';
      followCountElement.textContent = currentFollowCount + 1;
    } else {
      followed.classList.remove('followed');
      followed.classList.add('follow');
      followed.textContent = 'フォローする';
      followCountElement.textContent = currentFollowCount - 1;
    }

    fetch(url, {
      method: 'POST',
      body: formData,
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        followCountElement.textContent = data.follow_count;
        // 応答を受け取った後、ボタンを再度有効化
        FollowButton.disabled = false;
      })
      .catch(error => {
        console.log(error);

        // エラーが発生した場合、UIの状態を元に戻す
        if (FollowButton.checked) {
          followed.classList.add('followed');
          followed.classList.remove('follow');
          followed.textContent = 'フォローする';
          followCountElement.textContent = currentFollowCount;
        } else {
          notFollowed.classList.remove('followed');
          notFollowed.classList.add('follow');
          notFollowed.textContent = 'フォロー中';
          followCountElement.textContent = currentFollowCount;
        }
        // エラーが発生した場合でも、ボタンを再度有効化
        FollowButton.disabled = false;
      });
  });
});


