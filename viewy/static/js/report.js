'use strict'

var reportButtons = document.querySelectorAll('.not-yet');

reportButtons.forEach(function(button) {
  button.addEventListener('click', function(event) {
    var reportMenu = this.nextElementSibling; // メニューを取得

    if (reportMenu.style.display === 'none') {
      reportMenu.style.display = 'block'; // メニューを表示
    } else {
      reportMenu.style.display = 'none'; // メニューを非表示
    }

    // ドキュメント全体に対してクリックイベントを監視
    document.addEventListener('click', function(e) {
      // クリックされた要素がメニュー内の要素であるか、ボタン自体であるかを判定
      if (!reportMenu.contains(e.target) && e.target !== button) {
        reportMenu.style.display = 'none'; // メニューを非表示
      }
    });

    // クリックイベントの伝播を停止し、親要素へのイベント伝播を防止
    event.stopPropagation();
  });
});



document.querySelectorAll('.report-menu form').forEach(function(currentForm) {
  currentForm.addEventListener('submit', function(event) {
    event.preventDefault(); // フォームのデフォルトの送信動作を無効化

    // フォームデータの取得
    var formData = new FormData(this);
    var postID = this.dataset.pk; // 投稿IDを取得
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
  });
});
