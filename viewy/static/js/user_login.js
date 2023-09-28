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
  const loginButton = document.querySelector('.button'); // ログインボタンのセレクタ
  const spinner = document.getElementById('spinner');
  
  loginButton.addEventListener('click', function() {
    spinner.style.display = 'block';
  });
});
