'use strict'

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

  if (getComputedStyle(content).display !== 'none') {
    content.style.display = 'none';
    label.classList.replace('fa-square-minus', 'fa-square-plus');
    input.checked = true;
  } else {
    content.style.display = 'block';
    label.classList.replace('fa-square-plus', 'fa-square-minus');
    input.checked = false;
  }
}
