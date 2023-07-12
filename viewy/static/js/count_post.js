'use strict'

const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

function incrementPostCount(postId) {
  fetch('/view_count/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrftoken,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ post_id: postId }),
  })
    .then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error('カウントの増加に失敗しました');
      }
    })
    .then(data => {
      if (data.exceeded_limit) {
        window.location.href = '/upgrade-membership/';
      } else {
        // カウントの増加に成功した場合の処理
        // ここにポスト表示などの処理を追加する
      }
    })
    .catch(error => {
      console.error(error);
    });
}

const postElements = document.querySelectorAll('.post');
const observer = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const postId = entry.target.getAttribute('data-post-id');
      incrementPostCount(postId);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.9 });

postElements.forEach(element => {
  observer.observe(element);
});
