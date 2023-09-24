function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    let cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      let cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener("DOMContentLoaded", function () {

  // 削除ボタンの処理
  let deleteCampaignButtons = document.querySelectorAll(".delete-campaign-button");

  deleteCampaignButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      let campaignId = this.getAttribute("data-campaign-id");
      let title = this.getAttribute("data-title");  // タイトルを取得
      let confirmMessage = `キャンペーン「${title}」と関連する広告を全て削除しますか。付随するデータは失われます。`;

      if (window.confirm(confirmMessage)) {
        fetch(`/advertisement/delete_ad_campaign/${campaignId}/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              window.location.href = data.redirect_url;
            }
          });
      }
    });
  });
});