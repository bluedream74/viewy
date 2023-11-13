function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

document.querySelectorAll('.approve-btn').forEach(button => {
  button.addEventListener('click', function () {
    const adId = this.getAttribute('data-ad-id');
    const action = this.getAttribute('data-action');
    const csrfToken = getCookie('csrftoken');
    const url = `/management/approve/${adId}/`;

    fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ ad_id: adId, action: action })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('ネットワークレスポンスが不正です');
        }
        return response.json();
      })
      .then(data => {
        if (data.status === 'success') {
          if (action === 'approve') {
            console.log(`広告ID ${adId} が承認されました`);
          } else {
            console.log(`広告ID ${adId} の承認が拒否されました`);
          }
        } else {
          console.log(`エラー: ${data.message}`);
        }
      })
      .catch(error => console.error('エラーが発生しました:', error));
  });
});