let csrf_token = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

document.body.addEventListener('click', function(event) {
  let modal = document.getElementById('others-modal');
  let overlay = document.querySelector('.modal-overlay');

  // オーバーレイがクリックされた場合、モーダルを閉じる
  if (event.target === overlay) {
      modal.classList.remove('active');
      overlay.style.display = "none";
      return; // 早期return
  }

  if (event.target.matches('.ellipsis')) {
      let ellipsis = event.target;
      let post_id = ellipsis.dataset.postId;
      modal.dataset.postId = post_id;

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
});

window.onclick = function(event) {
  let modal = document.getElementById('others-modal');
  let modalWrapper = modal.querySelector('.modal-wrapper'); // モーダルのラッパーを取得
  let newContents = document.querySelectorAll('.modal-content-new'); // 新しいモーダルのコンテンツを取得
  let createForm = document.querySelector('.create-collection-form'); // フォームを取得
  let collectionList = document.querySelector('.collections-list'); // コレクションリストを取得

  if (
    event.target !== modal && 
    !event.target.closest('.ellipsis') && 
    !event.target.closest('.modal-content') &&
    !event.target.closest('.modal-wrapper') // モーダルのラッパーやその子要素をクリックした場合にもモーダルを閉じないように
  ) {
      modal.classList.remove('active');
      
      // 300ミリ秒後にモーダルの位置とフォームのスタイルをリセット
      setTimeout(function() {
          modalWrapper.style.transform = ''; // モーダルの位置をリセット
          createForm.style.display = 'none'; // フォームを非表示
          createForm.style.opacity = '0';    // フォームの不透明度をリセット
          createForm.style.right = '-100%';  // フォームの位置をリセット
          collectionList.style.paddingTop = ''; // コレクションリストのpadding-topをリセット

          // 全ての新しいモーダルコンテンツを非表示にする
          newContents.forEach(content => {
              content.style.display = 'none';
          });
      }, 300);
  }
}

document.addEventListener("DOMContentLoaded", function() {
  let options = document.querySelectorAll('.option');
  let modalWrapper = document.querySelector('.modal-wrapper');
  
  options.forEach(option => {
      option.addEventListener('click', function() {
          let targetContent = option.id;
          let newContents = document.querySelectorAll('.modal-content-new');
          
          // Hide all new modal contents
          newContents.forEach(content => {
              content.style.display = 'none';
          });

          // Display the correct new modal content based on the clicked option
          document.querySelector(`.${targetContent}-content`).style.display = 'block';

          // Move the modal contents to the left
          modalWrapper.style.transform = 'translateX(-100%)';
      });
  });
});


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
      }, 200); // 10ミリ秒の遅延
  });

  let collectionChoices = document.querySelectorAll('.collections-list .collection-choice');

  collectionChoices.forEach(choice => {
    choice.addEventListener('click', function() {
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
  .then(response => response.json())
  .then(data => {
      if (data.message === 'Added successfully') {
          checkmark.style.opacity = '1'; 
          checkmark.style.display = 'block'; // displayをblockに設定
          checkmark.classList.add('already'); // 「already」クラスを追加
          checkmark.classList.add('active'); // 「active」クラスも追加
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
          newCollectionElem.className = 'collection-choice';
  
          // 内部divを作成
          let innerDivElem = document.createElement('div');
  
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