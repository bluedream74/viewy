'use strict'

// Modal Open
$('.details-icon').click(function() {
  $('#actionModal').show();
});

// Close Modal
$('.close').click(function() {
  $('#actionModal').hide();
});

// Block/Unblock User
$('.block-btn').click(function() {
    var url = $(this).data('url');
    var posterName = $(this).data('postername');
    var csrfToken = $(this).data('csrf');
    var isBlocked = $(this).data('blocked');
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

// Optional: Close Modal when Clicking Outside
$(window).click(function(event) {
    if ($(event.target).hasClass('block-modal')) {
        $(event.target).hide();
    }
});