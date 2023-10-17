'use strict';

document.addEventListener('DOMContentLoaded', () => {

  function observeTargets(newTargets) {
    newTargets.forEach(target => {
      observer.observe(target);
    });
  }

  function isactive(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.setAttribute("tabindex", 0);
        entry.target.focus();
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
            const newTargets = node.querySelectorAll('.post, .book');
            if (newTargets.length > 0) {
              observeTargets(newTargets);
            }
          }
        });
      }
    }
  });

  // .screen 要素内のDOM変更を監視
  const screenContainer = document.querySelector('.screen');
  mutationObserver.observe(screenContainer, { childList: true, subtree: true });
});
