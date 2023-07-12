'use strict'

$(document).ready(function() {
  $(".mute-frag").change(function() {
    var postId = $(this).data("post-id");
    var isChecked = $(this).is(":checked");
    var videos = document.querySelectorAll('video');

    // 他のすべてのミュートボタンを連動させる
    $(".mute-frag").not(this).prop("checked", isChecked);

    // チェックボックスが存在する親要素のクラスを変更する
    var muteContainer = $(this).parent();
    if (isChecked) {
      muteContainer.removeClass("fa-volume-low").addClass("fa-volume-xmark");
      videos.forEach(function(video) {
        video.muted = true;// 動画をミュートにする
      })
    } else {
      muteContainer.removeClass("fa-volume-xmark").addClass("fa-volume-low");
      videos.forEach(function(video) {
        video.muted = false;// ミュートを解除する
      })
    }

    // 他のラベルも連動させる
    var otherMuteContainer = $(".mute-frag").not(this).parent();
    if (isChecked) {
      otherMuteContainer.removeClass("fa-volume-low").addClass("fa-volume-xmark");
    } else {
      otherMuteContainer.removeClass("fa-volume-xmark").addClass("fa-volume-low");
    }
  });
});


$(document).ready(function() {
  // ページ読み込み時に保存されたチェックボタンの状態を復元する
  $(".mute-frag").each(function() {
    var isChecked = localStorage.getItem("muteState");
    if (isChecked === "true") {
      $(this).prop("checked", true);
      toggleMute($(this));
    }
  });

  $(".mute-frag").change(function() {
    var isChecked = $(this).is(":checked");
    toggleMute($(this));

    // 他のすべてのミュートボタンを連動させる
    $(".mute-frag").prop("checked", isChecked);

    // 他のラベルも連動させる
    var otherMuteContainer = $(".mute-frag").not(this).parent();
    if (isChecked) {
      otherMuteContainer.removeClass("fa-volume-low").addClass("fa-volume-xmark");
    } else {
      otherMuteContainer.removeClass("fa-volume-xmark").addClass("fa-volume-low");
    }

    // チェックボタンの状態をローカルストレージに保存する
    localStorage.setItem("muteState", isChecked);
  });

  function toggleMute(muteButton) {
    var videos = document.querySelectorAll('video');
    var muteContainer = muteButton.parent();

    if (muteButton.is(":checked")) {
      muteContainer.removeClass("fa-volume-low").addClass("fa-volume-xmark");
      videos.forEach(function(video) {
        video.muted = true; // 動画をミュートにする
      });
    } else {
      muteContainer.removeClass("fa-volume-xmark").addClass("fa-volume-low");
      videos.forEach(function(video) {
        video.muted = false; // ミュートを解除する
      });
    }
  }
});
