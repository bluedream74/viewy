function getCookie(name) {
  var value = "; " + document.cookie;
  var parts = value.split("; " + name + "=");
  if (parts.length == 2) return parts.pop().split(";").shift();
}

let isProcessing = false; // 連打を防ぐためのフラグ




document.addEventListener("DOMContentLoaded", function () {
  // おすすめユーザー（RU）の場所クリックカウント
  // Recommended User List の処理
  const userList = document.querySelector(".recommended-user-list");

  userList.addEventListener("click", function (event) {
    const user = event.target.closest(".recommended-user");
    if (!user) return;

    if (isProcessing) {
      return;
    }

    isProcessing = true;

    const index = [...userList.children].indexOf(user);
    const clickCounterName = 'ru' + (index + 1);
    const csrfToken = getCookie("csrftoken");

    const data = new URLSearchParams();
    data.append("name", clickCounterName);
    data.append("csrfmiddlewaretoken", csrfToken);

    navigator.sendBeacon(`/management/click_count/${clickCounterName}/`, data);

    window.location.href = user.querySelector("a").href;
  });

  // // おすすめハッシュタグ（HH）の場所クリックカウント
  const listArea = document.querySelector('.list-area');
    
  listArea.addEventListener('click', function(event) {
      
      // イベントのターゲットが.post-clickableかどうかを確認
      const post = event.target.closest('.post-clickable');
      
      if (!post) return;
      
      if (isProcessing) {
          return;
      }

      isProcessing = true;

      const countName = post.getAttribute('data-count-name');
      if (!countName) return;

      const csrfToken = getCookie("csrftoken");

      const data = new URLSearchParams();
      data.append("name", countName);
      data.append("csrfmiddlewaretoken", csrfToken);

      navigator.sendBeacon(`/management/click_count/${countName}/`, data);
  });

  // ページの visibility が変更されたときのイベントを追加
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") {
      isProcessing = false;
    }
  });
});