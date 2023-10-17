'use strict';

document.addEventListener("DOMContentLoaded", function () {

    // post要素を監視するIntersectionObserverを作成
    let observer = new IntersectionObserver(function (entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) { // postが画面に表示されたら
                const book = entry.target.querySelector('.book');
                if (book) {
                    const mangaPages = book.querySelectorAll('.manga-page');
                    if (mangaPages.length > 1) { // 2枚以上のmanga_pageを持つ場合
                        const icon = book.querySelector('.horizontal-slide-icon');
                        if (icon) {
                            icon.classList.add('show-icon'); // iconを表示
                        }
                        observer.disconnect(); // さらなるpostの監視を停止
                    }
                }
            }
        });
    });

    // すべてのpost要素に対してobserverを適用
    const posts = document.querySelectorAll('.post');
    posts.forEach(post => {
        observer.observe(post);
    });

});
