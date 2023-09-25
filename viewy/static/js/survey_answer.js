function getCookie(name) {
  var value = "; " + document.cookie;
  var parts = value.split("; " + name + "=");
  if (parts.length == 2) return parts.pop().split(";").shift();
}


$(document).ready(function () {
  $("#survey-submit").click(function () {
    const selected_option = $("input[name='selected_option']:checked").val();
    const survey_id = $("#SurveyModal").data("survey-id");
    const csrf_token = getCookie("csrftoken");

    // URLを動的に設定
    const url = `/accounts/survey_answer/${selected_option}/${survey_id}/`;

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
        // エラーが発生したときの処理
        alert("An error occurred");
      }
    });
  });
});