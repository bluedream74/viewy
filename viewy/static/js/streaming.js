document.addEventListener('DOMContentLoaded', function() {
  var AWS_S3_CUSTOM_DOMAIN = 'https://d26kmcll34ldze.cloudfront.net/';
  var ua = navigator.userAgent.toLowerCase();
  var isiOS = /iphone|ipad|ipod/.test(ua);
  var isAndroid = /android/.test(ua);
  var isXperia = /xperia/.test(ua); // Xperia端末のチェック

  function setupVideo(video) {
    var index = Array.from(document.querySelectorAll('.video-player')).indexOf(video) + 1;
    var hlsUrl = video.dataset.hlsUrl ? AWS_S3_CUSTOM_DOMAIN + video.dataset.hlsUrl : null;
    var dashUrl = video.dataset.dashUrl ? AWS_S3_CUSTOM_DOMAIN + video.dataset.dashUrl : null;
    var mp4Url = video.dataset.videoUrl; // MP4のURLを直接取得

    // エクスペリアの場合にMP4を優先する
    if (isXperia && mp4Url) {
      video.src = mp4Url;
      video.addEventListener('loadedmetadata', function() {
        console.log('Metadata loaded for MP4 (Xperia):', index);
      });
    } else if (hlsUrl && (isiOS || isAndroid)) {
      if (Hls.isSupported()) {
        var hls = new Hls({
          maxMaxBufferLength: 2
        });
        hls.loadSource(hlsUrl);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, function() {
          console.log('HLS manifest parsed, playing video:', index);
          // HLSで再生を開始しないように削除
        });
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = hlsUrl;
        // 再生を開始しないようにイベントリスナー内のplay()呼び出しを削除
        video.addEventListener('loadedmetadata', function() {
          console.log('Metadata loaded for HLS:', index);
        });
      }
    // DASHの対応をチェック
    } else if (dashUrl) {
      var player = dashjs.MediaPlayer().create();
      player.initialize(video, dashUrl, false);
      player.updateSettings({
        streaming: {
          buffer: {
            bufferTimeAtTopQuality: 2,
          }
        }
      });
      // DASHで再生を開始しないように削除
    // MP4の対応をチェック
    } else if (mp4Url) {
      video.src = mp4Url;
      // 再生を開始しないようにイベントリスナー内のplay()呼び出しを削除
      video.addEventListener('loadedmetadata', function() {
        console.log('Metadata loaded for MP4:', index);
      });
    }
  }

  // インターセクションオブザーバーを設定
  var observer = new IntersectionObserver(function(entries, observer) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        var video = entry.target;
        setupVideo(video);
        observer.unobserve(video);
      }
    });
  }, { threshold: 0.25 });

  // 既存のビデオプレーヤーにオブザーバーを適用
  var videos = document.querySelectorAll('.video-player');
  videos.forEach(function(video) {
    observer.observe(video);
  });

  // DOMの変更を監視する
  var mutationObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(function(node) {
          if (node.nodeType === Node.ELEMENT_NODE) {
            var newVideos = node.querySelectorAll('.video-player');
            newVideos.forEach(function(newVideo) {
              observer.observe(newVideo);
            });
          }
        });
      }
    });
  });

  // .screen要素がある場合はMutationObserverを適用
  var screenElement = document.querySelector('.screen');
  if (screenElement) {
    mutationObserver.observe(screenElement, { childList: true, subtree: true });
  } else {
    console.error('".screen" element not found!');
  }
});