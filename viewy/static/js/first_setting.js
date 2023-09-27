document.addEventListener('DOMContentLoaded', function () {
  var submitButton = document.getElementById('submitSettings');
  var spinner = document.querySelector('.spinner');

  submitButton.addEventListener('click', function () {
    // 選択されている性別と次元を取得
    var selectedGenderRadio = document.querySelector('input[name="gender"]:checked');
    var selectedDimension = document.querySelector('input[name="dimension"]:checked').value;

    if (!selectedGenderRadio) {
      alert('性別を選択してください。');
      return;
    }

    var selectedGender = selectedGenderRadio.value;

    // データをサーバーに送信
    var formData = new FormData();
    formData.append('gender', selectedGender);
    formData.append('dimension', selectedDimension);

    // spinnerのz-indexを最前面に設定
    spinner.style.zIndex = '1001';

    fetch('/accounts/first_setting/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          // ここでモーダルを非表示にしてからページを再読み込み
          document.getElementById('firstSettingModal').style.display = 'none';
          location.reload();
        } else {
          console.error('Error:', data.status);
        }
      })
      .catch(error => {
        console.error('Error:', error);
      });
  });
});

function getCookie(name) {
  var value = "; " + document.cookie;
  var parts = value.split("; " + name + "=");
  if (parts.length == 2) return parts.pop().split(";").shift();
}