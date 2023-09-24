function getCookie(name) {
  let value = "; " + document.cookie;
  let parts = value.split("; " + name + "=");
  if (parts.length === 2) return parts.pop().split(";").shift();
}

document.addEventListener("DOMContentLoaded", function () {
  let buttons = document.querySelectorAll(".toggle-hidden");

  buttons.forEach(function (button) {
    button.addEventListener("click", function () {
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
          if (data.is_hidden) {
            button.textContent = "停止中";
          } else {
            button.textContent = "公開中";
          }
          button.disabled = false;  // 処理完了後、ボタンを再度有効化
        })
        .catch(err => {
          console.error(err);
          button.disabled = false;  // エラーが発生した場合も、ボタンを再度有効化
        });
    });
  });
});