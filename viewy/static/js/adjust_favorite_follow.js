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
    const form = FollowButton.closest('form');
    const posterPk = form.dataset.pk;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const url = form.action;
    const formData = new FormData(form);
    formData.append('csrfmiddlewaretoken', csrftoken);

    fetch(url, {
      method: 'POST',
      body: formData,
    })
    .then(() => {  // 応答を待たないと次のコードが正常に動作しない場合
      const followed = form.querySelector('.fa-solid.fa-check');
      const notFollowed = form.querySelector('.fa-solid.fa-plus');
      if (FollowButton.checked) {
        notFollowed.classList.add('fa-check');
        notFollowed.classList.remove('fa-plus');
      } else {
        followed.classList.remove('fa-check');
        followed.classList.add('fa-plus');
      }
    })
    .catch(error => console.log(error));  // エラー処理を追加
  }
});



{
  const FollowButtons = document.querySelectorAll('.follow-button');
  FollowButtons.forEach(FollowButton => {
    FollowButton.addEventListener('change', () => {
      const form = FollowButton.closest('form');
      const posterPk = form.dataset.pk;
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
          const followCount = data.follow_count;
          const followCountElement = form.querySelector('.follow-count');
          followCountElement.textContent = followCount;

          const followed = form.querySelector('.followed');
          const notFollowed = form.querySelector('.follow');
          if (FollowButton.checked) {
            notFollowed.classList.add('followed');
            notFollowed.classList.remove('follow');
            notFollowed.textContent = 'フォロー中';
          } else {
            followed.classList.remove('followed');
            followed.classList.add('follow');
            followed.textContent = 'フォローする';
          }

        })
        .catch(error => console.log(error));
    });
  });
}

