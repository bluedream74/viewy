'use strict'

document.addEventListener('click', function(e) {
  // Check if the clicked element is a hide label
  if (e.target.tagName === 'LABEL' && e.target.id.startsWith('hide-label-')) {
    var postId = e.target.id.split('-')[2];  // Get the post id from the label id
    toggleSidebarAndCaptions(postId);
  }
});

function toggleSidebarAndCaptions(postId) {
  var content = document.getElementById('content-' + postId);
  var label = document.getElementById('hide-label-' + postId);
  var input = document.getElementById('hide-input-' + postId);

  // Check if the content is currently visible
  if (content.style.display !== 'none') {
    // If the content is visible, hide it and change the label
    content.style.display = 'none';
    label.className = 'fa-regular fa-square-plus';
    input.checked = true;
  } else {
    // If the content is hidden, show it and change the label back
    content.style.display = 'block';
    label.className = 'fa-regular fa-square-minus';
    input.checked = false;
  }
}
