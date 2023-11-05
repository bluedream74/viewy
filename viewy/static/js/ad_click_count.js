'use strict'

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}


let isClickable = true;

$('.screen').on('click', '.ad-click', function (e) {
  e.preventDefault();
  // クリックされた要素自体がaタグか、子要素にaタグを持っているかをチェック
  var $target = $(this).closest('.ad-click').find('a').first();
  var targetUrl = $target.attr('href');

  // targetUrlがundefinedの場合は、クリックされた要素自体のhrefをチェック
  if (typeof targetUrl === 'undefined') {
    targetUrl = $(this).attr('href');
  }
  if (!isClickable) return;
  isClickable = false;
  const postID = $(this).closest('.post').data('post-id');
  const csrfToken = getCookie('csrftoken');
  const url = `/advertisement/ad_click_count/${postID}/`;

  $.ajax({
    url: url,
    method: 'POST',
    data: {
      csrfmiddlewaretoken: csrfToken
    },
    success: function (response) {
      if (response.status === 'success') {
        window.location.href = targetUrl;
      } else {
        console.error(response.message);
      }
    },
    error: function (xhr, status, error) {
      console.error(`Error updating click count: ${error}`);
    },
    complete: function () {
      setTimeout(() => {
        isClickable = true;
      }, 4000);
    }
  });
});