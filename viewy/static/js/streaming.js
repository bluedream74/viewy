document.addEventListener('DOMContentLoaded', function() {
  var AWS_S3_CUSTOM_DOMAIN = 'https://d26kmcll34ldze.cloudfront.net/';
  var ua = navigator.userAgent.toLowerCase();
  var isiOS = /iphone|ipad|ipod/.test(ua);

  function setupVideo(video) {
    // videoタグのdata-setの中からそれぞれのマニフェストファイルのパスを取得し、ドメイン等と繋げる
    var index = Array.from(document.querySelectorAll('.video-player')).indexOf(video) + 1;
    var hlsUrl = video.dataset.hlsUrl ? AWS_S3_CUSTOM_DOMAIN + video.dataset.hlsUrl : null;
    var dashUrl = video.dataset.dashUrl ? AWS_S3_CUSTOM_DOMAIN + video.dataset.dashUrl : null;

    // iOSデバイスでHLSを試みる
    if (isiOS && hlsUrl) {
      if (Hls.isSupported()) {
        var hls = new Hls({
          maxMaxBufferLength: 2
        });
        hls.loadSource(hlsUrl);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, function() {
          console.log('HLS manifest parsed, playing video:', index);
        });
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = hlsUrl;
        video.addEventListener('loadedmetadata', function() {
          console.log('Metadata loaded for HLS:', index);
        });
      }
    // それ以外のデバイスでDASHを試みる
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
      console.log('DASH initialized, playing video:', index);
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