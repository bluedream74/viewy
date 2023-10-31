document.addEventListener('DOMContentLoaded', function() {
  var AWS_S3_CUSTOM_DOMAIN = 'https://d26kmcll34ldze.cloudfront.net/';
  var ua = navigator.userAgent.toLowerCase();
  var isiOS = /iphone|ipad|ipod/.test(ua);
  var isAndroid = /android/.test(ua);

  function setupVideo(video) {
    var index = Array.from(document.querySelectorAll('.video-player')).indexOf(video) + 1;
    var hlsUrl = video.dataset.hlsUrl ? AWS_S3_CUSTOM_DOMAIN + video.dataset.hlsUrl : null;
    var dashUrl = video.dataset.dashUrl ? AWS_S3_CUSTOM_DOMAIN + video.dataset.dashUrl : null;

    if (hlsUrl && (isiOS || isAndroid)) {
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
          console.log('Metadata loaded, playing video:', index);
        });
      }
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
    }
  }

  var observer = new IntersectionObserver(function(entries, observer) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        var video = entry.target;
        setupVideo(video);
        observer.unobserve(video);
      }
    });
  }, { threshold: 0.25 });

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
              if (!newVideo.classList.contains('initialized')) {
                observer.observe(newVideo);
                newVideo.classList.add('initialized');
              }
            });
          }
        });
      }
    });
  });

  mutationObserver.observe(document.body, { childList: true, subtree: true });
});