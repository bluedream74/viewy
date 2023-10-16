'use strict'


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
      // 応答データの処理
      var formResponse = currentForm.parentNode.querySelector('.formResponse');
      formResponse.innerHTML = data.message; // 応答メッセージを表示

      // 3秒後にモーダルを非表示にする処理を追加
      setTimeout(function() {
        let modal = document.getElementById('others-modal');
        let overlay = document.querySelector('.modal-overlay');
        
        modal.classList.remove('active');
        overlay.style.display = "none";
      }, 3000);
      
      // フォームを非表示にする
      currentForm.style.display = 'none';
    })
    .catch(function(error) {
      console.error('エラー:', error);
    });
  }
});
