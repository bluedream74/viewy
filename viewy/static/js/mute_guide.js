document.addEventListener("DOMContentLoaded", function() {
  // ローカルストレージから訪問状態を確認
  var isFirstVisit = localStorage.getItem("isFirstVisit");

  // 初回訪問時のみミュートガイドを表示
  if (!isFirstVisit) {
    var muteGuide = document.querySelector('.mute-guide');
    muteGuide.classList.add('show-icon');

    // 以降の訪問では表示しないように設定
    localStorage.setItem("isFirstVisit", "false");
  }
});