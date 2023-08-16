$(document).ready(function() {
  // 初期状態をミュートかどうか確認して設定
  let isMuted = $('video').prop('muted');
  updateMuteIcons(isMuted);

  $(document).on("change", ".mute-frag", function() {
    let isChecked = $(this).is(":checked");

    // 他のすべてのミュートボタンを連動させる
    $(".mute-frag").not(this).prop("checked", isChecked);

    if (isChecked) {
      isMuted = true;
    } else {
      isMuted = false;
    }

    muteVideos(isMuted);
    updateMuteIcons(isMuted);
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
          if (node.tagName === 'VIDEO') {
            node.muted = isMuted;
          }
        });
      }
    });
  });

  observer.observe(targetNode, { childList: true, subtree: true });
});
