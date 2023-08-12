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
    content.classList.add('hidden');
    label.classList.replace('fa-angle-down', 'fa-angle-up');
    input.checked = true;

    // 完全に非表示にする
    setTimeout(function() {
      if (content.classList.contains('hidden')) {
        content.style.display = 'none';
      }
    }, 500); // トランジションと同じ時間
  } else {
    content.style.display = 'block';
    content.classList.remove('hidden');
    label.classList.replace('fa-angle-up', 'fa-angle-down');
    input.checked = false;
  }
}
