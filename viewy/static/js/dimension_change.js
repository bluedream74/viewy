'use strict'

document.addEventListener('DOMContentLoaded', function() {
    const dimensionRadios = document.querySelectorAll('[name="dimension"]');

    dimensionRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            updateDimension(this.value);
        });
    });
});

function updateDimension(dimension) {
    fetch('/accounts/change_dimension/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ dimension: dimension })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("Dimension updated successfully!");

            // data-reload属性の値を取得して、それに基づいてリロードを制御する
            const shouldReload = document.querySelector('.dimension-radio-group').getAttribute('data-reload') === 'true';
            if (shouldReload) {
                location.reload(); // リロード
            }

        } else {
            console.error("Failed to update dimension.");
        }
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        let cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}  