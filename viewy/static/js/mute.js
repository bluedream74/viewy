let myplay_muted_status = true;

$(document).ready(function() {
  // 初期状態をミュートかどうか確認して設定
	let isMuted = $('video').prop('muted');
	updateMuteIcons(isMuted);

	let pressStartTime;

	$(document.body).on("mousedown", ".post video, .scroll-tab", function(event) {
    	// .tab-bar や .side-bar でのクリックを無視
		if ($(event.target).closest('.tab-bar, .side-bar, .hide, .modal, .modal-overlay .notification-modal .survey-modal .freeze-notification-modal, .content, .book, .scheduled_post_time, .recommend-tag').length) return;
		pressStartTime = new Date().getTime();
	});

	$(document.body).on("mouseup", ".post video, .scroll-tab", function(event) {
    	// .tab-bar や .side-bar でのクリックを無視
		if ($(event.target).closest('.tab-bar, .side-bar, .hide, .modal, .modal-overlay .notification-modal .survey-modal .freeze-notification-modal, .content, .book, .scheduled_post_time, .recommend-tag').length) return;

		let pressEndTime = new Date().getTime();
		if (pressEndTime - pressStartTime < 200) {
			// 200ミリ秒未満のクリックだった場合
			isMuted = !isMuted; // 状態を反転
			muteVideos(isMuted);
			updateMuteIcons(isMuted);

			//自分のミュート状態
			myplay_muted_status = !myplay_muted_status;
		}
	});


	//アイコンを押したときの挙動を追加
	$(document.body).on("mouseup", ".fa-volume-xmark",".fa-volume-low", function(event) {
		isMuted = !isMuted; // 状態を反転
		muteVideos(isMuted);
		updateMuteIcons(isMuted);

		//自分のミュート状態
		myplay_muted_status = !myplay_muted_status;
	});




	// 動画のミュート状態を一括設定する関数
	function muteVideos(isMuted) {
		let videos = document.querySelectorAll('video');
		videos.forEach(function(video) {
			video.muted = isMuted; 
		});
	}

	// アイコンのミュート状態を一括設定する関数
	function updateMuteIcons(isMuted) {
		let muteContainers = $(".mute-frag").parent();
		muteContainers.removeClass("fa-volume-low fa-volume-xmark");

		if (isMuted) {
			muteContainers.addClass("fa-volume-xmark");
		} else {
			muteContainers.addClass("fa-volume-low");
		}
	}


	// 新たに動画が読み込まれたときにミュート状態を反映させる
	let targetNode = document.body;

	let observer = new MutationObserver(function(mutations) {
		mutations.forEach(function(mutation) {			
			if (mutation.addedNodes && mutation.addedNodes.length > 0) {
				mutation.addedNodes.forEach(function(node) {

					let video = $(node).parents('.post').find('video');
					if (video.length > 0) {

						//デフォはミュート状態のなのでミュート状態ならなにもしない
						//ミュート解除状態ならアイコン/video設定の処理を追加
						if(!myplay_muted_status){

							video.prop('muted',myplay_muted_status);
	
							//アイコンの変更
							let muteContainers = $(".mute-frag").parent();
							muteContainers.removeClass("fa-volume-low fa-volume-xmark");
							muteContainers.addClass("fa-volume-low");
						}
					}
				});
			}
		});
	});

	observer.observe(targetNode, { childList: true, subtree: true });
});