document.addEventListener('DOMContentLoaded', function () {
    // URLからパラメータを取得
    const url = window.location.pathname;
    const [pretitle, title, subtitle] = url.split('/').slice(2, 5);

    const headers = document.querySelectorAll('.accordion-header');

    headers.forEach(header => {
        // アコーディオンヘッダー内の<a>タグに対するクリックイベントの処理
        const aTag = header.querySelector('a');
        if (aTag) {
            aTag.addEventListener('click', (event) => event.stopPropagation());
        }

        // ヘッダークリックによるアコーディオンの開閉処理
        header.addEventListener('click', function () {
            const content = this.nextElementSibling;
            const icon = this.querySelector('i');

            if (content.style.display === 'block') {
                content.style.display = 'none';
                icon.classList.replace('fa-chevron-up', 'fa-chevron-down');
            } else {
                content.style.display = 'block';
                icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
            }
        });

        // URLに基づく初期アクティブ状態の設定
        if (header.dataset.pretitle === pretitle) {
            header.classList.add('active'); // 常にactiveを付けたままにする
            const icon = header.querySelector('i');

            if (window.innerWidth > 970) {
                icon.classList.add('fa-chevron-up');
                icon.classList.remove('fa-chevron-down');
                header.nextElementSibling.style.display = 'block';
            } else {
                icon.classList.add('fa-chevron-down');
                icon.classList.remove('fa-chevron-up');
                header.nextElementSibling.style.display = 'none';
            }
        }
    });

    // サブタイトルとタイトルに基づくアコーディオン項目の選択
    if (subtitle) {
        const subtitleLink = document.querySelector(`.subtitle a[href$="${subtitle}/"]`);
        subtitleLink?.parentElement.classList.add('active');
    }
    if (title) {
        const titleLink = document.querySelector(`.title a[href$="/${title}/"]`);
        titleLink?.parentElement.classList.add('active');
    }
});
