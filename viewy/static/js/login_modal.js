    // 非ログインユーザーへのログイン催促モーダル
    document.addEventListener('DOMContentLoaded', function () {
      const listArea = document.querySelector('.list-area');
      const isAuthenticated = listArea.getAttribute('data-is-authenticated') === 'true';
      const loginModal = document.getElementById('loginModal');
      const closeBtn = document.querySelector('.close-btn');
      const loginBtn = document.querySelector('.login-btn'); // ログインボタンを参照

      // post要素をクリックしたときのイベント
      listArea.addEventListener('click', function (event) {
          if (event.target.closest('.post') && !isAuthenticated) {
              event.preventDefault();
              loginModal.style.display = "flex";
          }
      });

      // モーダルのクローズボタンをクリックしたときのイベント
      closeBtn.addEventListener('click', function () {
          loginModal.style.display = "none";
      });

      // モーダル外のエリアをクリックしたときにモーダルを閉じるイベント
      window.addEventListener('click', function (event) {
          if (event.target === loginModal) {
              loginModal.style.display = "none";
          }
      });

      // ログインボタンをクリックしたときにnextパラメータをURLに追加するイベント
      if (loginBtn) {
          loginBtn.addEventListener('click', function () {
              const returnTo = window.location.href;
              loginBtn.setAttribute('href', `/accounts/regist/?next=${encodeURIComponent(returnTo)}`);
          });
      }
  });