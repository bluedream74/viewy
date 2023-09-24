document.addEventListener("DOMContentLoaded", function () {
  let buttons = document.querySelectorAll(".view-button");
  buttons.forEach(function (button) {
    button.addEventListener("click", function () {
      let postId = this.getAttribute("data-post-id");
      fetch(`/advertisement/ad_view_button/${postId}/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then(data => {
          let adinfoBlock = document.querySelector('.adinfo');
          let existingBook = adinfoBlock.querySelector('.book');
          let existingVideos = adinfoBlock.querySelectorAll('.post-video');
          // 前のコンテンツを削除
          if (existingBook) {
            existingBook.remove();
          }
  
          existingVideos.forEach(video => {
            video.remove();
          });

          let post = data.post;

          let mediaHtml = '';
          if (post.ismanga) {
            mediaHtml = '<div class="book">';
            post.visuals.forEach(visual => {
              mediaHtml += `<div class="manga-page">
                              <img class="page-content" src="${visual.url}" alt="${post.title}">
                            </div>`;
            });
            mediaHtml += '</div>';
          } else {
            post.videos.forEach((video, index) => {
              mediaHtml += `<video id="postVideo${index + 1}" class="post-video" width="200px" height="400px" src="${video.url}" loading="lazy" playsinline loop muted></video>
                            <input id="seekSlider${index + 1}" class="custom-controlbar" type="range" min="0" step="0.1" value="0">
                            <br>`;
            });
          }
          let posterName = displayname ? displayname : username;
          let otherHtml = `
            <div class="content">
              <div class="side-bar">
                <div class="poster">
                  <div>
                    <a class="poster_username">
                      <img class="poster-img" src="{{user.prf_img.url}}" alt="{{user.prf_img}}">
                    </a>
                  </div>
                </div>
        
                <div class="follow-poster">
                  <a class="fa-solid fa-plus fa-2xs " style="color: black;"></a>
                </div>
        
                <div class="favorite">
                  <a class="fa-regular fa-heart not-liked" style="color: rgb(255, 255, 255);"></a>
                </div>
        
        
                <div class="emotes" data-formatted-total-emote="{{ post.emote_total_count }}">
                  <div class="emote emote-icon">
                    <i class="fa-regular fa-face-smile"></i>
                    <span class="emote-count total-count">0</span>
                  </div>
                  </div>
                </div>
        
        
        
                <div class="mute">
                  <label class="fa-solid fa-volume-xmark">
                    <input type="checkbox" class="mute-frag" checked>
                  </label>
                </div>
                <div class="space-for-hide"></div>
                  </div>
                  <div class="captions">
                  <div class="poster-name">
                  <div class="content">
                  <div class="poster-name">
                    <a class="poster-name">＠${posterName}</a>
                    <span class="ad-tag">広告</span>
                  </div>
                    <span class="ad-tag">広告</span>
                  </div>
                  <div class="title">
                  </div>
          
                  <div class="caption"></div>
                  <div class="hashtags">
          
                    <span class="url"><a href="" target="_blank">
                        <i class="fas fa-link"></i>
                      </a></span>
                    <span class="hashtag"><a></a></span>
                    <span class="hashtag"><a></a></span>
                    <span class="hashtag"><a></a></span>
          
                  </div>
                </div>
          
                <div class="report not-yet">
                  <i class="fa-solid fa-circle-exclamation"></i>
                </div>
          
              </div>
          
          
              <label class="hide-label fa-solid fa-angle-down hide">
                <input class="hide-input" type="checkbox" style="display: none;">
              </label>
          
          
              <div class="page-count">
                <span id="current-page">1</span>/<span class="total-page">?</span>
              </div>
          
              <div class="play-button">
                <i class="fa-solid fa-play"></i>
              </div>
            </div>
          `;

          adinfoBlock.innerHTML = mediaHtml + otherHtml;
        });
    });
  });
});
