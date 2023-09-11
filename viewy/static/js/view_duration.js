let postStartTimes = new Map();

function sendDataToServer(postId, duration) {
  // FormDataを使用してPOSTリクエストのデータを作成
  let formData = new FormData();
  formData.append("post_id", postId);
  formData.append("duration", duration);

  // fetch APIを使用して非同期にデータをサーバーに送信
  fetch('/posts/view_duration/', {
      method: 'POST',
      body: formData,
      headers: {
          "X-CSRFToken": getCookie("csrftoken")  // CSRFトークンをヘッダーに追加
      },
  })
  .then(response => {
      if (!response.ok) {
          return response.json().then(data => {
              throw new Error(data.message);
          });
      }
      return response.json();
  })
  .then(data => {
      if (data.message === "Success") {
          console.log("Data sent successfully!");
      } else {
          console.error("Error sending data:", data.message);
      }
  })
  .catch(error => {
      console.error("Error:", error.message);
  });
}


// CSRFトークン取得のための補助関数
function getCookie(name) {
  let value = "; " + document.cookie;
  let parts = value.split("; " + name + "=");
  if (parts.length == 2) return parts.pop().split(";").shift();
}

// IntersectionObserverのコールバック関数
function handleIntersection(entries, observer) {
  entries.forEach(entry => {
      if (entry.isIntersecting && entry.intersectionRatio >= 0.8) {
          // post要素の80%以上がビューポートに入った場合、開始時間を記録
          postStartTimes.set(entry.target, Date.now());
      } else if(postStartTimes.has(entry.target)) {
          // post要素がビューポートから出た場合、表示時間を計算
          const startTime = postStartTimes.get(entry.target);
          const duration = Math.round((Date.now() - startTime) / 1000);


          // サーバーに送信
          sendDataToServer(entry.target.dataset.postId, duration);

          // Mapから開始時間を削除
          postStartTimes.delete(entry.target);
      }
  });
}

// IntersectionObserverのオプションを設定
const options = {
  threshold: 0.8  // 80%以上の要素がビューポートに表示されるとコールバックがトリガーされます
};

// IntersectionObserverを作成
const observer = new IntersectionObserver(handleIntersection, options);

// 各post要素の監視を開始
const posts = document.querySelectorAll('.post');
posts.forEach(post => observer.observe(post));