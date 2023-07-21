'use strict'

document.addEventListener("DOMContentLoaded", function() {
  var lazyloadMedia = document.querySelectorAll(".lazyload");    
  var lazyloadThrottleTimeout;
  
  function lazyload () {
    if(lazyloadThrottleTimeout) {
      clearTimeout(lazyloadThrottleTimeout);
    }    

    lazyloadThrottleTimeout = setTimeout(function() {
        var scrollTop = window.pageYOffset;
        lazyloadMedia.forEach(function(media) {
            if(media.offsetTop < (window.innerHeight + scrollTop)) {
              if (media.tagName.toLowerCase() === 'img') {
                media.src = media.dataset.src;
              } else if (media.tagName.toLowerCase() === 'video') {
                media.src = media.dataset.src;
                media.load();
              }
              media.classList.remove('lazyload');
            }
        });
        if(lazyloadMedia.length == 0) { 
          document.removeEventListener("scroll", lazyload);
          window.removeEventListener("resize", lazyload);
          window.removeEventListener("orientationChange", lazyload);
        }
    }, 20);
  }
  
  document.addEventListener("scroll", lazyload);
  window.addEventListener("resize", lazyload);
  window.addEventListener("orientationChange", lazyload);
});
