$(document).ready(function () {
  // 初期状態をミュートかどうか確認して設定
  let isMuted = $('video').prop('muted');
  updateMuteIcons(isMuted);

  let pressStartTime;

  function handleEventStart(event) {
    pressStartTime = new Date().getTime();
    if ($(event.target).closest('.tab-bar, .side-bar, .hide, .modal, .modal-overlay, .content, .book, .scheduled_post_time, .recommend-tag').length) return;
  }

  function handleEventEnd(event) {
    // タッチイベントの場合、デフォルトの動作（コンテキストメニューの表示など）をキャンセル
    if (event.type === 'touchend' && $(event.target).closest('video').length) {
      event.preventDefault();
    }

    // .tab-bar や .side-bar でのクリックを無視
    if ($(event.target).closest('.tab-bar, .side-bar, .hide, .modal, .modal-overlay, .content, .book, .scheduled_post_time, .recommend-tag').length) return;

    let pressEndTime = new Date().getTime();

    // 長押しの場合、ミュートの切り替えをスキップ
    if (pressEndTime - pressStartTime > 200) {
      return;
    }

    // 状態を反転
    isMuted = !isMuted;
    muteVideos(isMuted);
    updateMuteIcons(isMuted);
  }

  // mouseup、mousedown、touchstart、touchendのイベントにハンドラを適用
  $(document.body).on("mousedown touchstart", handleEventStart);
  $(document.body).on("mouseup touchend", handleEventEnd);

  // 動画のミュート状態を一括設定する関数
  function muteVideos(isMuted) {
    let videos = document.querySelectorAll('video');
    videos.forEach(function (video) {
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

  let observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      if (mutation.addedNodes && mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(function (node) {
          if (node.tagName === 'VIDEO') {
            node.muted = isMuted;
          }
        });
      }
    });
  });

  observer.observe(targetNode, { childList: true, subtree: true });
});