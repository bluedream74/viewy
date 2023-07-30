'use strict'

let csrfToken = $('meta[name="csrf-token"]').attr('content'); // HTMLのmetaタグから取得する方法

$.ajaxSetup({
  headers: {
    "X-CSRFToken": csrfToken
  }
});


// ログイン状態を確認する関数
function isUserLoggedIn() {
  return $('.search-bar').data('user') === true;
}

// データベースから検索履歴を取得する（ログインユーザー用）
function getDBSearchHistory() {
  return new Promise((resolve, reject) => {
    $.ajax({
      url: '/accounts/search_history/',
      method: 'GET',
      success: function (data) {
        resolve(data.history);
      },
      error: function (textStatus, errorThrown) {
        console.error(`Error fetching search history: ${textStatus} - ${errorThrown}`);
        reject(errorThrown);
      }
    });
  });
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



// 検索履歴を表示する関数
function displaySearchHistory() {

  if (isUserLoggedIn()) {
    // ログインユーザーの場合、ローカルストレージの検索履歴をクリアする
    clearLocalSearchHistory();

    getDBSearchHistory().then(historyData => {
      populateSearchHistory(historyData);
    }).catch(error => {
      console.error("Error fetching search history:", error);
    });
  } else {
    let history = getLocalSearchHistory().reverse();
    populateSearchHistory(history);
  }
}


$(document).ready(function () {

  // ページ読み込み時に検索履歴を表示
  displaySearchHistory();


  // 検索ボタンクリック時に検索履歴を保存
  $('.search-bar').on('submit', function (e) {
    e.preventDefault(); // フォームのデフォルトの送信動作をキャンセル
    const query = $('#search').val(); // 検索ボックスからクエリを取得

    if (isUserLoggedIn()) {
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

// 検索履歴の内容を#search-history要素に追加する関数
function populateSearchHistory(history) {

  $('#search-history').empty();
  history.forEach((item) => {
    let query = item.query || item;
    let linkItem = $('<a>').text(`#${query}`).attr('href', `/posts/hashtag/${query}/`);

    linkItem.click(function (e) {
      e.preventDefault();


      if (isUserLoggedIn()) {
        // ログインユーザーの場合、クリックされたクエリを再度保存
        $.ajax({
          url: '/accounts/save_search_history/',
          method: 'POST',
          data: {
            query: query
          },
          success: function (response) {
            if (response.status !== "success") {
              console.error("エラーだよん、検索履歴をアップデートできなかったよん");
            }
          }
        });
      } else {
        saveLocalSearchHistory(query);
      }
      window.location.href = $(this).attr('href');
    });
    $('#search-history').append(linkItem);
  });

  // ここで×ボタンの表示状態を更新
  updateXmarkVisibility();
}

// ローカルストレージから検索履歴をクリアする
function clearLocalSearchHistory() {
  localStorage.removeItem('search_history');
}



// ×ボタンで検索履歴を非表示
$(document).ready(function () {

  // ページ読み込み時に×ボタンを更新
  updateXmarkVisibility();

  $('.fa-solid.fa-xmark').click(function () {
    if (isUserLoggedIn()) {
      // ログインユーザーの場合
      $.ajax({
        type: "POST",
        url: "/accounts/hide_search_histories/",
        success: function (data) {
          if (data.status == "success") {
            $('#search-history a').slice(0, 5).remove();

            // ここで×ボタンの表示状態を更新
            updateXmarkVisibility();
          } else {
            alert("検索履歴を削除できませんでした");
          }
        },
        error: function (textStatus, errorThrown) {
          alert("Error hiding search histories: " + textStatus + ": " + errorThrown);
        }
      });
    } else {
      // 非ログインユーザーの場合、ローカルストレージから検索履歴をクリアする
      clearLocalSearchHistory();
      $('#search-history').empty();
      updateXmarkVisibility();
    }
  });
});

// ×ボタンの表示/非表示を更新する関数
function updateXmarkVisibility() {
  if ($('#search-history').find('a').length === 0) {
    $('.fa-solid.fa-xmark').hide();
  } else {
    $('.fa-solid.fa-xmark').show();
  }
}


$(document).ready(function () {

  // ハッシュタグのリンクにイベントリスナーを追加
  $('.hashtag').on('click', function (e) {
    console.log("Hashtag link clicked!");
    e.preventDefault();  // デフォルトの遷移動作をキャンセル
    const hashtag = $(this).text().substring(1);  // 先頭の#を削除してハッシュタグのテキストのみを取得
    console.log(hashtag);
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
    window.location.href = $(this).attr('href');
  });
});