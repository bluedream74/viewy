'use strict';

document.addEventListener('DOMContentLoaded', function() {
  function handleBookScroll(event) {
    const book = event.target;
    const mangaPages = book.querySelectorAll('.manga-page');
    const currentPageDisplay = book.parentNode.querySelector('#current-page');
    const pageWidth = mangaPages[0].offsetWidth;
    let currentPage = 1 - Math.floor(book.scrollLeft / pageWidth);

    currentPageDisplay.textContent = currentPage;
  }

  // 初期に存在する.book要素に対してイベントリスナーを設定
  const books = document.querySelectorAll('.book');
  books.forEach(function(book) {
    book.addEventListener('scroll', handleBookScroll);
  });

  // .screen要素の変更を監視して、新しい.book要素に対してイベントリスナーを設定
  const screen = document.querySelector('.screen');
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      mutation.addedNodes.forEach(function(addedNode) {
        if (addedNode.nodeType === Node.ELEMENT_NODE) {
          const books = addedNode.querySelectorAll('.book');
          books.forEach(function(book) {
            book.addEventListener('scroll', handleBookScroll);
          });
        }
      });
    });
  });

  observer.observe(screen, { childList: true, subtree: true });
});