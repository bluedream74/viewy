$(document).on('change', '.recommend-frag', function() {
  const $checkbox = $(this);
  const post_id = $checkbox.closest('.recommend').data('post-id');
  const recommend = $checkbox.prop('checked');

  $.post('/posts/recommend/', {
      post_id: post_id,
      recommend: recommend
  }, function(response) {
      if (response.success) {
          if (response.action === 'added') {
              console.log('Recommend added successfully.');
          } else if (response.action === 'removed') {
              console.log('Recommend removed successfully.');
          }
      } else {
          console.error('Error:', response.error);
          $checkbox.prop('checked', !recommend);  // 失敗した場合、チェックボックスの状態を戻す
      }
  });
});

$(document).ready(function() {

  // モーダルの中身を更新する関数
  function updateRecommendModal(data) {
      var modalWrapper = $('#recommend-modal .recommend-modal-wrapper');
      modalWrapper.empty();

      data.forEach(function(user) {
        var displayName = user.display_name ? user.display_name : user.username; // display_nameが存在すればそれを使用し、なければusernameを使用
        var totalFollowCount = user.follow_count + user.support_follow_count; // follow_countとsupport_follow_countを合算
    
        var userElement = `
            <div class="recommend-user-row">
                <div class="recommend-user-img-wrapper">
                    <a href="/posts/poster_page/${user.username}/">
                        <img src="${user.prf_img_url}" alt="${displayName}'s profile image" class="recommend-user-profile-image">
                    </a>
                </div>
                <div class="recommend-user-info">
                    <a href="/posts/poster_page/${user.username}/" class="recommend-username-link">
                        <div class="recommend-username">${displayName}</div>
                    </a>
                    <div class="recommend-follower-count">${totalFollowCount} followers</div>
                </div>
                <div class="recommend-user-action">
                    ${user.is_followed ? 
                        '<button class="recommend-unfollow-btn" data-user-id="' + user.id + '">フォロー中</button>' : 
                        '<button class="recommend-follow-btn" data-user-id="' + user.id + '">フォローする</button>'}
                </div>
            </div>`;
        modalWrapper.append(userElement);
    });
    
  }

// モーダルの表示
$(document).on('click', '[data-toggle="recommend-modal"]', function() {
    var postId = $(this).data('post-id');

    $.ajax({
        url: '/posts/get_recommend_users/' + postId + '/',
        method: 'GET',
        success: function(data) {
            updateRecommendModal(data);
            $('#recommend-modal').addClass('active');
            $('.modal-overlay').show();
        },
        error: function() {
            alert('Error loading recommend users. Please try again.');
        }
    });
});

// モーダルを閉じる
$(document).on('click', '.modal-overlay', function() {
    $('#recommend-modal').removeClass('active');
    $('.modal-overlay').hide();
});

$(document).on('click', '.recommend-follow-btn, .recommend-unfollow-btn', function() {
    var userId = $(this).data('user-id');
    
    // ボタンを一時的に無効化
    $(this).prop('disabled', true);
    
    // サーバーの応答を待たずにUIをすぐに更新
    if ($(this).hasClass('recommend-follow-btn')) {
        $(this).text('フォロー中').removeClass('recommend-follow-btn').addClass('recommend-unfollow-btn');
    } else if ($(this).hasClass('recommend-unfollow-btn')) {
        $(this).text('フォローする').removeClass('recommend-unfollow-btn').addClass('recommend-follow-btn');
    }
  
    // AJAXリクエストを送信
    $.post('/accounts/follow/' + userId + '/', function(response) {
        // 必要に応じて、ここで応答を処理する追加のコードを追加できます。
        
        // ボタンを再度有効化
        $(this).prop('disabled', false);
    }.bind(this))
    .fail(function() {
        // エラーが発生した場合、UIの変更を元に戻す
        if ($(this).hasClass('recommend-unfollow-btn')) {
            $(this).text('フォローする').removeClass('recommend-unfollow-btn').addClass('recommend-follow-btn');
        } else if ($(this).hasClass('recommend-follow-btn')) {
            $(this).text('フォロー中').removeClass('recommend-follow-btn').addClass('recommend-unfollow-btn');
        }
        
        // ボタンを再度有効化
        $(this).prop('disabled', false);
    }.bind(this));
  });

});