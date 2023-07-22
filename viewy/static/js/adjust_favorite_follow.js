'use strict'


document.addEventListener('change', event => {
  if (event.target.matches('.like-button')) {
    const likeButton = event.target;
    const form = likeButton.closest('form');
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
        const favoriteCount = data.favorite_count;
        const favoriteCountElement = form.querySelector('.favorite-count');
        favoriteCountElement.textContent = favoriteCount;

        const heartIconNotLiked = form.querySelector('.not-liked');
        const heartIconLiked = form.querySelector('.liked');
        if (likeButton.checked) {
          heartIconNotLiked.classList.remove('not-liked');
          heartIconNotLiked.classList.add('liked');
          heartIconNotLiked.classList.remove('fa-regular');
          heartIconNotLiked.classList.add('fa-solid');
        } else {
          heartIconLiked.classList.add('not-liked');
          heartIconLiked.classList.remove('liked');
          heartIconLiked.classList.add('fa-regular');
          heartIconLiked.classList.remove('fa-solid');
        }
      })
      .catch(error => console.log(error));
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

