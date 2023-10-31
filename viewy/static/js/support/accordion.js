
document.addEventListener('DOMContentLoaded', function () {

    const headers = document.querySelectorAll('.accordion-header');

    headers.forEach(header => {

        // アコーディオンヘッダー内の<a>タグに対するクリックイベント
        const aTag = header.querySelector('a');
        if (aTag) {
            aTag.addEventListener('click', (event) => {
                event.stopPropagation(); // イベントの伝播を停止
            });
        }

        header.addEventListener('click', () => {
            const parent = header;
            parent.classList.toggle('active');

            // アコーディオンコンテンツの表示状態をトグル
            const content = header.nextElementSibling;
            if (parent.classList.contains('active')) {
                content.style.display = 'block';
            } else {
                content.style.display = 'none';
            }
        });
    });

    // URLからプレを取得する
    const url = window.location.pathname;
    const pretitle = url.split('/')[2];

    const title = url.split('/')[3];

    // URLからサブを取得する
    const subtitle = url.split('/')[4];

    // サブに基づいて対応するアコーディオン項目を選択する
    if (subtitle) {
        const accordionItem = document.querySelector(`.subtitle a[href$="${subtitle}/"]`).parentElement;
        if (accordionItem) {
            accordionItem.classList.add('active');
        }
    }

    // titleに基づいて対応するアコーディオン項目のヘッダーにアクティブをつける
    if (title) {
        const accordionHeaderLink = document.querySelector(`.title a[href$="/${title}/"]`).parentElement;
        if (accordionHeaderLink) {
            accordionHeaderLink.classList.add('active');
        }
    }

    // プレに基づいてアコーディオンセクションを開く
    const accordionHeader = document.querySelector(`.accordion-header[data-pretitle="${pretitle}"]`);
    if (accordionHeader) {
        accordionHeader.click();
    }
});