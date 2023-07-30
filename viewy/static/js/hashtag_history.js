'use strict'

let csrfToken = $('meta[name="csrf-token"]').attr('content'); // HTMLのmetaタグから取得する方法
console.log(csrfToken);

$.ajaxSetup({
  headers: {
    "X-CSRFToken": csrfToken
  }
});


// ログイン状態を確認する関数
function isUserLoggedIn() {
  return $('.hashtags').data('user') === true;
}

// ローカルストレージから検索履歴を取得する（非ログインユーザー用）
function getLocalSearchHistory() {
  return JSON.parse(localStorage.getItem('search_history') || '[]');
}

// 検索履歴をローカルストレージに保存する
function saveLocalSearchHistory(query) {
  let history = getLocalSearchHistory();
  const index = history.indexOf(query);

  // すでに存在する場合、それを削除
  if (index !== -1) {
    history.splice(index, 1);
  }

  history.push(query);

  // 最新の5件だけを保存する
  if (history.length > 5) {
    history.shift();
  }
  localStorage.setItem('search_history', JSON.stringify(history));
}

$(document).ready(function () {

  // ハッシュタグのリンクにイベントリスナーを追加
  $('.screen').on('click', '.hashtag', function (e) {
    e.preventDefault();  // デフォルトの遷移動作をキャンセル
    const textValue = $(this).text().trim();
    const hashtag = textValue.substring(1);  // 先頭の#を削除してハッシュタグのテキストのみを取得

    const targetHref = `/posts/hashtag/${encodeURIComponent(hashtag)}/`;

    if (isUserLoggedIn()) {
      $.ajax({
        url: '/accounts/save_search_history/',
        method: 'POST',
        data: {
          query: hashtag
        },
        success: function (response) {
          if (response.status === "success") {
            console.log("Search history saved successfully!");
          } else {
            console.error("Error saving search history.");
          }
        }
      });
    } else {
      // 非ログインユーザーの場合、検索履歴をローカルストレージに保存
      saveLocalSearchHistory(hashtag);
    }
    // ハッシュタグに関連する投稿を表示するページへ遷移
    window.location.href = targetHref;
  });
});