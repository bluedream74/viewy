let csrf_token = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

document.body.addEventListener('click', function(event) {
  let modal = document.getElementById('others-modal');
  let overlay = document.querySelector('.modal-overlay');
  let modalWrapper = modal.querySelector('.modal-wrapper'); 
  let newContents = document.querySelectorAll('.modal-content-new');
  let createForm = document.querySelector('.create-collection-form');
  let collectionList = document.querySelector('.collections-list');

  // オーバーレイがクリックされた場合、またはモーダル外部がクリックされた場合
  if (event.target === overlay ||
      (event.target !== modal && 
      !event.target.closest('.ellipsis') && 
      !event.target.closest('.modal-content') &&
      !event.target.closest('.modal-wrapper'))||
      event.target.closest('#no-block')){

      modal.classList.remove('active');
      overlay.style.display = "none";
      setTimeout(function() {
          modalWrapper.style.transform = ''; 
          createForm.style.display = 'none';
          createForm.style.opacity = '0';
          createForm.style.right = '-100%';
          collectionList.style.paddingTop = '';

          newContents.forEach(content => {
              content.style.display = 'none';
          });
      }, 300);
      return; // 早期return
  }

  if (event.target.matches('.ellipsis')) {
    let ellipsis = event.target;
    let post_id = ellipsis.dataset.postId;
    let isReported = ellipsis.dataset.reported === 'true'; // 通報されているかどうか

    // 通報のオプションを設定
    let reportOption;
    if (isReported) {
        reportOption = `
        <div class="option">
            <i class="fa-solid fa-exclamation option-icon"></i>
            通報済み
        </div>
        `;
    } else {
        reportOption = `
        <div class="option" id="report-post">
            <i class="fa-solid fa-exclamation option-icon" style="color: orangered;"></i>
            通報する
        </div>
        `;
    }

    let reportContainer = document.querySelector('.modal .report-option-container'); // モーダル内の適切な場所を指定
    reportContainer.innerHTML = reportOption;

    // 通報フォームに投稿IDを設定
    let reportForm = document.querySelector('.report-menu form');
    reportForm.dataset.pk = post_id;
    

    modal.dataset.postId = post_id;
    // .block要素にpost_idを設定
    let blockElement = document.querySelector('.block-options');
    blockElement.dataset.postId = post_id;

    fetch(`/posts/get_collections_for_post/${post_id}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        },
    })
    .then(response => response.json())
    .then(data => {
        let collectionIdsForPost = data.collection_ids;

        document.querySelectorAll('.collection-choice').forEach(choice => {
            let choiceId = parseInt(choice.getAttribute('data-collection-id'));
            let checkIcon = choice.querySelector('.fa-check');

            if (!checkIcon) return;

            if (collectionIdsForPost.includes(choiceId)) {
                checkIcon.classList.add('already');
                checkIcon.style.display = "";
            } else {
                checkIcon.classList.remove('already');
                checkIcon.style.display = "none";
            }
        });

        // モーダルとオーバーレイの表示切替
        if (modal.classList.contains('active')) {
            modal.classList.remove('active');
            overlay.style.display = "none";
        } else {
            modal.classList.add('active');
            overlay.style.display = "block";
        }
    });
}

// .optionのクリック処理
let option = event.target.closest('.option');
if (option && option.id) { // ここでIDの存在を確認します
  let targetContent = option.id;
  let newContents = document.querySelectorAll('.modal-content-new');

  // Hide all new modal contents
  newContents.forEach(content => {
    content.style.display = 'none';
  });

  // If the 'report-post' option is clicked, reset the report form
  if (targetContent === 'report-post') {
    let reportForm = document.querySelector('.report-menu form');
    let formResponse = reportForm.parentNode.querySelector('.formResponse');
    
    // Reset the form fields
    reportForm.reset();
    
    // Make the form visible again
    reportForm.style.display = '';
    
    // Clear the response message
    formResponse.innerHTML = '';
    formResponse.classList.remove('response-message');
  }

  // Display the correct new modal content based on the clicked option
  document.querySelector(`.${targetContent}-content`).style.display = 'block';

  // Move the modal contents to the left
  modalWrapper.style.transform = 'translateX(-100%)';
}
});

// Add block event listener
document.querySelector('.block-options').addEventListener('click', function(event) {
    if (event.target.dataset.action === 'block') {
        const blockElement = document.querySelector('.block-options'); // これを修正
        const postId = blockElement.dataset.postId;

        // ここでpostIdの値をconsole.logで出力
        console.log(postId);

        blockPoster(postId);
    } else {
        // ブロックをキャンセルする場合の処理、例えばモーダルを閉じるなど
    }
});

function blockPoster(postId) {
  fetch(`/accounts/block_poster/${postId}/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
        document.querySelector('.block-response').textContent = "ブロックしました";
        document.querySelector('.block-options').style.display = 'none';

        // ブロックが完了したらページを再読み込み
        window.location.reload();
    } else {
        document.querySelector('.block-response').textContent = "エラーが発生しました";
    }
  });
}


document.addEventListener("DOMContentLoaded", function() {

    let newCollectionElement = document.querySelector('.new-collection');
    newCollectionElement.addEventListener('click', function() {
        let createForm = document.querySelector('.create-collection-form');
        let collectionList = document.querySelector('.collections-list');
    
        // コレクションリストのpadding-topを増やしてスペースを作成
        collectionList.style.paddingTop = "28px";
    
        // フォームを表示する
        createForm.style.display = 'block';
    
        // フォームをレンダリングに十分な時間を与えるための小さな遅延
        setTimeout(() => {
            createForm.style.opacity = '1';
            createForm.style.right = '0';
        }, 200); // 200ミリ秒の遅延
    });
  
    let collectionList = document.querySelector('.collections-list');
  
    console.log("Adding event listener");
    collectionList.addEventListener('click', function(event) {
      let choice = event.target.closest('.collection-choice');
      if (!choice) return; // `.collection-choice` がクリックされていない場合、何もしない
  
      console.log("Click event triggered");
      let checkmark = choice.querySelector('.fa-solid.fa-check');
          
      let collection_id = choice.dataset.collectionId;
      let modal = document.getElementById('others-modal');
      let post_id = modal.dataset.postId;
  
      if(checkmark.classList.contains('already')) {
          // 既に追加されている場合、削除のアクションを実行
          removeFromCollection(collection_id, post_id, checkmark);
      } else {
          // まだ追加されていない場合、追加のアクションを実行
          addToCollection(collection_id, post_id, checkmark);
      }
    });
  });

function removeFromCollection(collection_id, post_id, checkmark) {
  fetch('/posts/remove_from_collection/', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrf_token
      },
      body: `collection_id=${collection_id}&post_id=${post_id}`
  })
  .then(response => response.json())
  .then(data => {
      if (data.message === 'Removed successfully') {
          checkmark.style.opacity = '0';       // チェックマークの透明度を0に設定
          checkmark.classList.remove('already'); // 「already」クラスを削除
          checkmark.classList.remove('active');  // 「active」クラスも削除
      } else {
          console.error(data.message);
      }
  })
  .catch(error => {
      console.error('Error:', error);
  });
}

function addToCollection(collection_id, post_id, checkmark) {
    fetch('/posts/add_to_collection/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrf_token
        },
        body: `collection_id=${collection_id}&post_id=${post_id}`
    })
    .then(response => {
        // レスポンスの内容タイプをチェック
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json();
        } else {
            throw new Error("Invalid content-type received: " + contentType);
        }
    })
    .then(data => {
        if (data.message === 'Added successfully') {
            checkmark.style.opacity = '1'; 
            checkmark.style.display = 'block'; 
            checkmark.classList.add('already');
            checkmark.classList.add('active');
        } else {
            console.error(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

document.getElementById('create-collection-btn').addEventListener('click', function() {
  let newCollectionName = document.getElementById('new-collection-name').value;
  let modal = document.getElementById('others-modal');
  let post_id = modal.dataset.postId;

  if(newCollectionName.trim() === "") {
      alert("コレクション名を入力してください。");
      return;
  }

  fetch('/posts/create_collection_and_add_post/', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrf_token
      },
      body: `collectionName=${newCollectionName}&postId=${post_id}`
  })
  .then(response => response.json())
  .then(data => {
        if(data.status === "success") {
            // 新しいコレクションの要素を作成
            let newCollectionElem = document.createElement('div');
            newCollectionElem.className = 'collection-choice-container';

            // 1. レスポンスから新しいコレクションのIDを取得
            let newCollectionId = data.collection_id;

            // 2. 新しいコレクション要素に `data-collection-id` 属性を追加
            newCollectionElem.setAttribute('data-collection-id', newCollectionId);
  
            // 内部divを作成
            let innerDivElem = document.createElement('div');
            innerDivElem.className = 'collection-choice'; 

            // レスポンスから新しいコレクションのIDを取得して、それをdata-collection-id属性として使用
            innerDivElem.setAttribute('data-collection-id', newCollectionId);
  
          // アイコンを作成
          let collectionIconElem = document.createElement('i');
          collectionIconElem.className = 'fa-regular fa-bookmark collection-icon';
          innerDivElem.appendChild(collectionIconElem);
  
          // コレクション名のテキストを制限
          let trimmedCollectionName = data.collectionName;
          if(trimmedCollectionName.length > 20) {
              trimmedCollectionName = trimmedCollectionName.substring(0, 20) + '...';
          }

          // コレクション名のテキストノードを作成
          let collectionNameTextNode = document.createTextNode(trimmedCollectionName);
          innerDivElem.appendChild(collectionNameTextNode);
  
          // チェックマークのアイコンを作成
          let checkIconElem = document.createElement('i');
          checkIconElem.className = 'fa-solid fa-check already';
          innerDivElem.appendChild(checkIconElem);
  
          // 新しいコレクション要素に内部divを追加
          newCollectionElem.appendChild(innerDivElem);
  
            // 新規コレクションの要素の次の位置に新しいコレクション要素を挿入
            let collectionsList = document.querySelector('.collections-list');
            let newCollectionPlaceholder = document.querySelector('.new-collection').parentElement;
            collectionsList.insertBefore(newCollectionElem, newCollectionPlaceholder.nextElementSibling);
  
      } else {
          alert("コレクションの作成または投稿の追加に失敗しました。");
      }
  });
});