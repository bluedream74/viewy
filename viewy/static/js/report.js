'use strict'

document.addEventListener('click', function(event) {
  if (event.target.matches('.not-yet') || event.target.parentNode.matches('.not-yet')) {
    // '.not-yet'クラスを持つ要素自体か、その子要素がクリックされた場合
    var button = event.target.matches('.not-yet') ? event.target : event.target.parentNode; // ボタン要素を取得
    var reportMenu = button.nextElementSibling; // メニューを取得

    if (reportMenu.style.display === 'none' || reportMenu.style.display === '') {
      reportMenu.style.display = 'block'; // メニューを表示
    } else {
      reportMenu.style.display = 'none'; // メニューを非表示
    }
    
    event.stopPropagation(); // クリックイベントの伝播を停止
  } else if (event.target.matches('.report-menu') || event.target.closest('.report-menu')) {
    // メニュー自体か、メニューの子孫要素がクリックされた場合、イベントの伝播を停止
    event.stopPropagation();
  } else {
    // クリックした要素がボタン自体やメニュー内部でない場合、全てのメニューを閉じる
    document.querySelectorAll('.report-menu').forEach(function(menu) {
      if (menu.style.display === 'block') {
        menu.style.display = 'none';
      }
    });
  }
});

// ページの初期状態で、全てのメニューを閉じておく
window.addEventListener('DOMContentLoaded', (event) => {
    document.querySelectorAll('.report-menu').forEach(function(menu) {
      menu.style.display = 'none';
    });
});




document.addEventListener('submit', function(event) {
  var currentForm = event.target;
  
  if (currentForm.matches('.report-menu form')) {
    event.preventDefault(); // フォームのデフォルトの送信動作を無効化
    
    // フォームデータの取得
    var formData = new FormData(currentForm);
    var postID = currentForm.dataset.pk; // 投稿IDを取得
    const url = currentForm.action;
    
    // フォームデータに post_id を追加
    formData.append('post_id', postID);
    
    // フォームデータを非同期で送信
    fetch(url, {
      method: 'POST',
      body: formData
    })
    .then(function(response) {
      return response.json(); // 応答データをJSONとして解析
    })
    .then(function(data) {
    
      // レポートアイコンをチェックマークに変更
      var reportIcon = currentForm.parentElement.previousElementSibling.querySelector('i');
      reportIcon.classList.remove('fa-circle-exclamation');
      reportIcon.classList.add('fa-check-circle');
    
    
      // 応答データの処理
      var formResponse = currentForm.parentNode.querySelector('.formResponse');
      formResponse.innerHTML = data.message; // 応答メッセージを表示
    
    
      // フォームを非表示にする
      currentForm.style.display = 'none';
    })
    .catch(function(error) {
      console.error('エラー:', error);
    });
  }
});
