'use strict'

// Modal Open
$('.details-icon').click(function() {
    $('#actionModal').addClass('active');
  });

  
  // Close Modal when Clicking Outside
  $(window).click(function(event) {
      if (!$(event.target).closest('.block-modal-content').length && !$(event.target).hasClass('details-icon')) {
          $('#actionModal').removeClass('active');
      }
  });
  
  // Block/Unblock User
  $('.block').click(function() {  // Updated from '.block-btn' to '.block'
      var url = $(this).data('url');
      var posterName = $(this).data('postername');
      var csrfToken = $(this).data('csrf');
      var isBlocked = $(this).data('blocked') == true;
      var pk = $(this).data('pk');
  
      var confirmationMessage = isBlocked ? posterName + "さんのブロックを解除しますか？" : posterName + "さんをブロックしますか？";
  
      if (confirm(confirmationMessage)) {
          $.ajax({
              type: 'POST',
              url: url,
              data: {
                  'poster_pk': pk,
                  'csrfmiddlewaretoken': csrfToken
              },
              success: function(response) {
                  location.reload();
              },
              error: function(xhr, status, error) {
                  console.error('Error:', error);
              }
          });
      }
  });
  
  // Close Modal when Clicking Outside
  $(window).click(function(event) {
      if ($(event.target).hasClass('block-modal')) {
          $('#actionModal').hide();
      }
  });