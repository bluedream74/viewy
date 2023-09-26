'use strict'

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}


let isClickable = true;

$('.screen').on('click', '.ad-click', function(e) {
  if (!isClickable) return;
  isClickable = false;
  const postID = $(this).closest('.post').data('post-id');
  const csrfToken = getCookie('csrftoken');
  const url = `/advertisement/update_ad_click_count/${postID}/`;

  const data = new FormData();
  data.append('csrfmiddlewaretoken', csrfToken);

  if (navigator.sendBeacon) {
    navigator.sendBeacon(url, data);
  } else {
    // Fallback to traditional AJAX in case sendBeacon isn't supported
    $.ajax({
      url,
      method: 'POST',
      data: {
        csrfmiddlewaretoken: csrfToken
      }
    });
  }
  setTimeout(() => {
    isClickable = true;
  }, 4000);
});