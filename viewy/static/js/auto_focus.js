'use strict';

document.addEventListener('DOMContentLoaded', () => {

  function toggleVisibility(contentElement, labelElement) {
    const input = labelElement ? labelElement.querySelector('.hide-input') : null;

    if (contentElement.style.opacity === '0') {
      contentElement.style.opacity = '1';
      contentElement.style.pointerEvents = 'auto';
      if (labelElement) {
        labelElement.classList.replace('fa-angle-up', 'fa-angle-down');
        if (input) input.checked = false;
      }
    } else {
      contentElement.style.opacity = '0';
      contentElement.style.pointerEvents = 'none';
      if (labelElement) {
        labelElement.classList.replace('fa-angle-down', 'fa-angle-up');
        if (input) input.checked = true;
      }
    }
  }
  // 画面上のクリックイベントを処理する関数
  document.addEventListener('click', function (e) {
    const content = e.target.closest('.content');
    const label = e.target.classList.contains('hide-label') ? e.target : null;

    if (content) {
      e.stopPropagation();
      return;
    }

    if (label) {
      const contentElement = label.previousElementSibling;
      toggleVisibility(contentElement, label);
    }
  });

  // 特定の要素がクリックされたときに実行される関数
  function handleClick(event) {

    const element = event.currentTarget;
  
    if (element.dataset.isAdvertisement === 'True' || event.target.closest('[data-is-advertisement="True"]')) {
      console.log("Advertisement detected. Content will not be hidden on click.");
      return;
    }
    if (event.target.closest('.content')) {
      return;
    }
    const contentElement = element.querySelector('.content');
    const labelElement = element.querySelector('.hide-label');

    if (element.matches('.post') && !element.querySelector('.book')) {
      return;
    }

    if (contentElement) toggleVisibility(contentElement, labelElement);
  }
  // 新しい要素を監視対象として追加する関数
  function observeTargets(newTargets) {
    newTargets.forEach(target => {
      console.log("Observing target: ", target);
      observer.observe(target);

      console.log("Advertisement attribute of the observed target: ", target.dataset.isAdvertisement);

      if (target.matches('.book, .post') || target.querySelector('.book, .post')) {
        target.addEventListener('click', handleClick);
      }
    });
  }
  // 交差を検出したときに実行される関数
  function isactive(entries) {
    entries.forEach(entry => {
      const element = entry.target;
      if (entry.isIntersecting) {
        element.setAttribute("tabindex", 0);
        element.focus();

        const contentElement = element.querySelector('.content');
        const labelElement = element.querySelector('.hide-label');

        // ここで広告かどうかをチェック
        if (element.dataset.isAdvertisement === 'True') {
          console.log("Advertisement detected. Content will not be hidden automatically.");
          return;
        }

        if ((element.querySelector('.book') || element.classList.contains('book')) && contentElement) {
          setTimeout(() => {
            if (contentElement.style.opacity !== '0') {
              contentElement.style.transition = "opacity 0.3s ease";
              toggleVisibility(contentElement, labelElement);
            }
          }, 3000);
        }
        observer.unobserve(element);
      }
    });
  }

  const options = {
    threshold: 1,
  };

  const observer = new IntersectionObserver(isactive, options);

  // 初回の .post と .book 要素を監視
  const initialTargets = document.querySelectorAll('.post, .book');
  observeTargets(initialTargets);

  // DOMの変更を監視するMutation Observerを作成
  const mutationObserver = new MutationObserver(mutationsList => {
    for (let mutation of mutationsList) {
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(node => {
          if (node instanceof HTMLElement) {
            setTimeout(() => {
              let newTargets = Array.from(node.querySelectorAll('.book, .post'));

              if (node.matches('.book, .post')) {
                newTargets.push(node);
              }

              observeTargets(newTargets);
            }, 200);
          }
        });
      }
    }
  });

  // .screen 要素内のDOM変更を監視
  const screenContainer = document.querySelector('.screen');
  mutationObserver.observe(screenContainer, { childList: true, subtree: true });
});
