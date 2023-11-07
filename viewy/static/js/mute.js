$(document).ready(function() {
  // 初期状態をミュートかどうか確認して設定
  let isMuted = $('video').prop('muted');
  updateMuteIcons(isMuted);

  let pressStartTime;

  $(document.body).on("mousedown", ".post video", function(event) {
    // .tab-bar や .side-bar でのクリックを無視
    if ($(event.target).closest('.tab-bar, .side-bar, .hide, .modal, .modal-overlay .notification-modal .survey-modal .freeze-notification-modal, .content, .book, .scheduled_post_time, .recommend-tag').length) return;

    pressStartTime = new Date().getTime();
  });

  $(document.body).on("mouseup", ".post video", function(event) {
    // .tab-bar や .side-bar でのクリックを無視
    if ($(event.target).closest('.tab-bar, .side-bar, .hide, .modal, .modal-overlay .notification-modal .survey-modal .freeze-notification-modal, .content, .book, .scheduled_post_time, .recommend-tag').length) return;

    let pressEndTime = new Date().getTime();

    if (pressEndTime - pressStartTime < 200) {
      // 200ミリ秒未満のクリックだった場合
      isMuted = !isMuted; // 状態を反転
      muteVideos(isMuted);
      updateMuteIcons(isMuted);
    }
  });

  // 動画のミュート状態を一括設定する関数
  function muteVideos(isMuted) {
    let videos = document.querySelectorAll('video');
    videos.forEach(function(video) {
      video.muted = isMuted; 
    });
  }

  // アイコンのミュート状態を一括設定する関数
  function updateMuteIcons(isMuted) {
    let muteContainers = $(".mute-frag").parent();
    muteContainers.removeClass("fa-volume-low fa-volume-xmark");

    if (isMuted) {
      muteContainers.addClass("fa-volume-xmark");
    } else {
      muteContainers.addClass("fa-volume-low");
    }
  }

  // 新たに動画が読み込まれたときにミュート状態を反映させる
  let targetNode = document.body;

  let observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.addedNodes && mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(function(node) {
          if (node.tagName === 'VIDEO' && $(node).parents('.post').length) {
            node.muted = isMuted;
          }
        });
      }
    });
  });

  observer.observe(targetNode, { childList: true, subtree: true });
});