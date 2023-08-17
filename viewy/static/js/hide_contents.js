'use strict';

document.addEventListener('click', function(e) {
  if (e.target.classList.contains('hide-label')) {
    var content = e.target.previousElementSibling;

    if (!content) {
      console.error('Content element not found');
      return;
    }

    toggleSidebarAndCaptions(content, e.target);
  }
});

function toggleSidebarAndCaptions(content, label) {
  var input = label.querySelector('.hide-input');

  if (!input) {
    console.error('Input element not found');
    return;
  }

  if (getComputedStyle(content).opacity !== '0') {
    // 直接スタイルを適用
    content.style.opacity = '0';
    content.style.pointerEvents = 'none';

    label.classList.replace('fa-angle-down', 'fa-angle-up');
    input.checked = true;
  } else {
    // スタイルを元に戻す
    content.style.opacity = '1';
    content.style.pointerEvents = 'auto';

    label.classList.replace('fa-angle-up', 'fa-angle-down');
    input.checked = false;
  }
}
