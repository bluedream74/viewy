'use strict'  


// DOMが完全に読み込まれた時に実行される処理
window.addEventListener('DOMContentLoaded', function() {
  // URLのクエリパラメータを取得
  var urlParams = new URLSearchParams(window.location.search);

  // クエリパラメータが存在する場合
  if (urlParams.has('post_id')) {
    // 投稿のIDを取得
    var postId = urlParams.get('post_id');

    // 投稿までスクロールする関数を呼び出す
    scrollToPost(postId);
  }
});

// 投稿までスクロールする関数
function scrollToPost(postId) {
  var attempts = 0;
  var maxAttempts = 100; // これは10秒間の試行を意味します（100ミリ秒ごとに検査）

  var checkExist = setInterval(function() {
    attempts++;

    // 投稿要素を取得
    var postElement = document.querySelector('[data-post-id="' + postId + '"]');

    // 投稿要素が存在する場合
    if (postElement) {
      // 投稿までスクロールする
      postElement.scrollIntoView();
      // インターバルをクリアする
      clearInterval(checkExist);
    } else if (attempts >= maxAttempts) {
      // 試行回数が上限に達した場合はインターバルをクリアする
      clearInterval(checkExist);
    }
  }, 100); // 100ミリ秒ごとにチェック
}