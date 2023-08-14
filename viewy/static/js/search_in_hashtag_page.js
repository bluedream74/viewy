'use strict'

let csrfToken = $('meta[name="csrf-token"]').attr('content'); // HTMLのmetaタグから取得する方法

$.ajaxSetup({
  headers: {
    "X-CSRFToken": csrfToken
  }
});


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