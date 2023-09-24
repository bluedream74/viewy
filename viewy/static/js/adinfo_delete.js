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
  
  let deleteButtons = document.querySelectorAll(".delete-button");
  
  deleteButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      let adInfoId = this.getAttribute("data-ad-info-id");
      let title = this.getAttribute("data-title");
      let confirmMessage = `広告「${title}」を完全に削除しますか。付随するデータは失われます。`;
      
      if (window.confirm(confirmMessage)) {
        // 非同期 POST リクエストを送信
        fetch(`/advertisement/delete_ad_info/${adInfoId}/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            window.location.reload();  // または遷移先のURLにリダイレクト
          }
        });
      } 
    });
  });
});