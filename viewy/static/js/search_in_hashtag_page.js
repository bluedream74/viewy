'use strict'

let csrfToken = $('meta[name="csrf-token"]').attr('content'); // HTMLのmetaタグから取得する方法

$.ajaxSetup({
  headers: {
    "X-CSRFToken": csrfToken
  }
});

$(document).ready(function () {
  console.log("DOM is loaded!");
  $('.search-bar').on('submit', function (e) {
    e.preventDefault();

    let formData = new FormData(e.target);
    let query = formData.get("query"); // フォームからクエリを取得
    let userLoggedIn = e.target.dataset.user === "true"; // ユーザーログイン状態の確認
    console.log(query);
    console.log(userLoggedIn);
    // 認証されたユーザーの場合のみ検索履歴を保存
    if (userLoggedIn) {
      $.ajax({
        url: '/accounts/save_search_history/',
        method: 'POST',
        data: {
          query: query
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
      saveLocalSearchHistory(query);
    }
    // 検索結果ページへリダイレクト
    window.location.href = `/posts/hashtag/${query}/`;
  });
});