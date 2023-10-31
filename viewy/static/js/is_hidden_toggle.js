function getCookie(name) {
  let value = "; " + document.cookie;
  let parts = value.split("; " + name + "=");
  if (parts.length === 2) return parts.pop().split(";").shift();
}

document.addEventListener("DOMContentLoaded", function () {
  let buttons = document.querySelectorAll(".toggle-hidden");

  buttons.forEach(function (button) {
    button.addEventListener("click", function () {

      let isCurrentlyHidden = button.classList.contains("stop");
      let releaseButtons = document.querySelectorAll(".toggle-hidden.release");
      let lastVisibleAd = releaseButtons.length === 1 && !isCurrentlyHidden;

      let confirmationMessage;
      if (lastVisibleAd) {
        confirmationMessage = "この広告を停止すると、キャンペーン内のすべての広告が停止され、キャンペーンは永久に停止します。よろしいですか？";
      } else if (isCurrentlyHidden) {
        confirmationMessage = "広告を公開します。よろしいですか？";
      } else {
        confirmationMessage = "広告を停止します。よろしいですか？";
      }

      let userConfirmed = confirm(confirmationMessage);
      if (!userConfirmed) {
        return;  // ユーザーがキャンセルを選んだ場合、処理を中断
      }
      
      button.disabled = true;  // 処理中はボタンを無効化
      let postId = this.getAttribute("data-post-id");

      fetch('/advertisement/is_hidden_toggle/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ "post_id": postId })
      })
        .then(response => response.json())
        .then(data => {
          location.reload(); 
          button.disabled = false;  // 処理完了後、ボタンを再度有効化
        })
        .catch(err => {
          console.error(err);
          button.disabled = false;  // エラーが発生した場合も、ボタンを再度有効化
        });
    });
  });
});