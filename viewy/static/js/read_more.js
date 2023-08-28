'use strict'

document.body.addEventListener('click', function(event) {
  if (event.target.classList.contains('caption')) {
      toggleCaption(event.target);
  }
});

function toggleCaption(captionElement) {
  if (captionElement.classList.contains('caption-expanded')) {
      captionElement.classList.remove('caption-expanded');
  } else {
      captionElement.classList.add('caption-expanded');
  }
}