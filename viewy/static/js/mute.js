'use strict'

$(document).ready(function() {
  // 初期状態をミュートかどうか確認して設定
  var isMuted = $('video').prop('muted');
  updateMuteIcons(isMuted);

  $(document).on("change", ".mute-frag", function() {
    var isChecked = $(this).is(":checked");

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
    var videos = document.querySelectorAll('video');
    videos.forEach(function(video) {
      video.muted = isMuted; 
    });
  }

  // アイコンのミュート状態を一括設定する関数
  function updateMuteIcons(isMuted) {
    var muteContainers = $(".mute-frag").parent();
    muteContainers.removeClass("fa-volume-low fa-volume-xmark");

    if (isMuted) {
      muteContainers.addClass("fa-volume-xmark");
    } else {
      muteContainers.addClass("fa-volume-low");
    }
  }

  // 新たに動画が読み込まれたときにミュート状態を反映させる
  $(document).on('DOMNodeInserted', 'video', function() {
    this.muted = isMuted;
  });
});