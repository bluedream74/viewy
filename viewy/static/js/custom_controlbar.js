'use strict'

document.addEventListener('DOMContentLoaded', function() {
  var videos = document.querySelectorAll('.post-video');
  var sliders = document.querySelectorAll('.custom-controlbar');
  var baseColor = 'rgba(150, 150, 150, 0.539)';
  var activeColor = 'rgba(255, 255, 255, 0.639)';

  for (var i = 0; i < videos.length; i++) {
    (function(i) {
      var video = videos[i];
      var seekSlider = sliders[i];

      if(video && seekSlider) {
        video.addEventListener('loadedmetadata', function() {
          seekSlider.max = video.duration;
        });

        video.addEventListener('timeupdate', function() {
          seekSlider.value = video.currentTime;
          updateSlider(seekSlider);
        });

        seekSlider.addEventListener('input', function() {
          video.currentTime = seekSlider.value;
        });

        function updateSlider(slider) {
          var progress = (slider.value / slider.max) * 100;
          slider.style.background = `linear-gradient(to right, ${activeColor} ${progress}%, ${baseColor} ${progress}%)`;
        }

        // Run once to set initial state
        updateSlider(seekSlider);
      }
    })(i);
  }
});






