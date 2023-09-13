'use strict'

document.addEventListener('DOMContentLoaded', () => {
    let postStartTimes = new Map();

    function sendDataToServer(postId, duration) {
        let formData = new FormData();
        formData.append("post_id", postId);
        formData.append("duration", duration);

        fetch('/posts/view_duration/', {
            method: 'POST',
            body: formData,
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            },
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.message === "Success") {
            } else {
                console.error("Error sending data:", data.message);
            }
        })
        .catch(error => {
            console.error("Error:", error.message);
        });
    }

    function getCookie(name) {
        let value = "; " + document.cookie;
        let parts = value.split("; " + name + "=");
        if (parts.length == 2) return parts.pop().split(";").shift();
    }

    function handleIntersection(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting && entry.intersectionRatio >= 0.8) {
                postStartTimes.set(entry.target, Date.now());
            } else if(postStartTimes.has(entry.target)) {
                const startTime = postStartTimes.get(entry.target);
                let duration = Math.round((Date.now() - startTime) / 1000);

                // ここでdurationの最大値を制限する
                duration = Math.min(duration, 300); // 300秒（5分）を超えないように制限

                sendDataToServer(entry.target.dataset.postId, duration);
                postStartTimes.delete(entry.target);
            }
        });
    }


    const options = {
        threshold: 0.8
    };

    const observer = new IntersectionObserver(handleIntersection, options);
    const postElements = document.querySelectorAll('.post');
    postElements.forEach(post => observer.observe(post));

    const mutationObserver = new MutationObserver(mutationsList => {
        for (let mutation of mutationsList) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(node => {
                    if (node instanceof HTMLElement && node.classList.contains('post')) {
                        observer.observe(node);
                    }
                });
            }
        }
    });

    const postsContainer = document.querySelector('.screen'); // Change this selector to the parent container of the posts
    mutationObserver.observe(postsContainer, { childList: true, subtree: true });
});