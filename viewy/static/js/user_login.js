'use strict'

document.addEventListener('DOMContentLoaded', function() {
  let specialUserContainer = document.getElementById('specialUserContainer');
  let isSpecialUser = specialUserContainer ? specialUserContainer.dataset.isSpecialUser === 'true' : false;

  if (isSpecialUser) {
    document.getElementById('okButton').addEventListener('click', function () {
      document.getElementById('invitedMessage').style.display = 'none';
    });
  }
});


document.addEventListener('DOMContentLoaded', function() {
  const loginForm = document.querySelector('form'); // フォームのセレクタ
  const spinner = document.getElementById('spinner');
  
  loginForm.addEventListener('submit', function(e) {
    // フォームが有効である場合のみ、spinnerを表示
    if (loginForm.checkValidity()) {
      spinner.style.display = 'block';
    } else {
      // フォームが無効である場合は、submitイベントがキャンセルされ、spinnerは表示されません
      e.preventDefault();
    }
  });
});

