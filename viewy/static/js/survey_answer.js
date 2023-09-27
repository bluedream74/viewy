function getCookie(name) {
  var value = "; " + document.cookie;
  var parts = value.split("; " + name + "=");
  if (parts.length == 2) return parts.pop().split(";").shift();
}


$(document).ready(function () {
  $("#survey-submit").click(function () {
    const selected_option = $("input[name='selected_option']:checked").val();
    const csrf_token = getCookie("csrftoken");

    // URLを動的に設定
    const url = `/accounts/survey_answer/${selected_option}/`;

    $.ajax({
      url: url,
      method: "POST",
      headers: {
        'X-CSRFToken': csrf_token
      },
      data: {
        selected_option: selected_option,
      },
      success: function (response) {
        // 成功したときの処理
        $(".unanswered-survey").hide();
        // ここでモーダルを非表示にしてからページを再読み込み
        document.getElementById('SurveyModal').style.display = 'none';
        location.reload();
      },
      error: function (response) {
      }
    });
  });
});


document.addEventListener("DOMContentLoaded", function () {
  const radioButtons = document.querySelectorAll('input[type="radio"]');
  const submitButton = document.getElementById('survey-submit');
  const errorMessage = document.getElementById('error-message');
  const spinner = document.querySelector('#spinner'); // spinner要素を選択
  
  radioButtons.forEach(radio => {
    radio.addEventListener('change', function() {
      submitButton.disabled = false;
      submitButton.style.opacity = 1;
      errorMessage.style.display = 'none'; // ラジオボタンが選択されたらエラーメッセージを隠す
    });
  });
  
  submitButton.addEventListener('click', function(e) {
    const isChecked = Array.from(radioButtons).some(radio => radio.checked);
    if (!isChecked) {
      e.preventDefault(); // フォームの送信を防ぐ
      errorMessage.style.display = 'block'; // エラーメッセージを表示
    }
    else
    spinner.style.display = 'block'; // spinnerを表示
  });

});