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

        // 透明なヒットエリアを作成
        var hitArea = document.createElement('div');
        hitArea.classList.add('hit-area');
        seekSlider.parentElement.insertBefore(hitArea, seekSlider.nextSibling);

        // ヒットエリアにドラッグ動作のイベントリスナを追加
        hitArea.addEventListener('mousedown', startDrag);
        hitArea.addEventListener('touchstart', startDrag);
        
        function startDrag(event) {
            event.preventDefault(); // これを追加してブラウザのデフォルトのタッチ動作を防ぎます
        
            var isDragging = true;
        
            var initialClientX = (event.touches ? event.touches[0].clientX : event.clientX);
            var initialSliderValue = parseFloat(seekSlider.value);

            var rect = hitArea.getBoundingClientRect();
            var newValue = ((initialClientX - rect.left) / rect.width) * parseFloat(seekSlider.getAttribute('max'));
            newValue = Math.min(Math.max(newValue, 0), parseFloat(seekSlider.getAttribute('max')));
            seekSlider.value = newValue;
            video.currentTime = newValue;
            updateSlider(seekSlider);
        
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('touchmove', onMouseMove);
        
            document.addEventListener('mouseup', endDrag);
            document.addEventListener('touchend', endDrag);
        
            function onMouseMove(event) {
                event.preventDefault(); // これも同様にデフォルトのタッチ動作を防ぐために追加
        
                var currentX = (event.touches ? event.touches[0].clientX : event.clientX);
        
                if (isDragging) {
                    var rect = hitArea.getBoundingClientRect();
        
                    var dx = currentX - initialClientX;
                    var changeInValue = (dx / rect.width) * parseFloat(seekSlider.getAttribute('max'));
        
                    var newValue = initialSliderValue + changeInValue;
        
                    newValue = Math.min(Math.max(newValue, 0), parseFloat(seekSlider.getAttribute('max')));
        
                    seekSlider.value = newValue;
                    video.currentTime = newValue;
                    updateSlider(seekSlider);
                }
            }
        
            function endDrag() {
                isDragging = false;
        
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('touchmove', onMouseMove);
        
                document.removeEventListener('mouseup', endDrag);
                document.removeEventListener('touchend', endDrag);
            }
        }
        

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






