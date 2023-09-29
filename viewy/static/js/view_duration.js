'use strict';

document.addEventListener('DOMContentLoaded', () => {
    let postStartTimes = new Map();
    let processedPosts = new Set();

    function sendDataToServer(postId, duration = null) {
        let formData = new FormData();
        formData.append("post_id", postId);
        formData.append("duration", duration);

        fetch('/posts/view_duration_count/', {
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
                if (data.message !== "Successfully updated post interactions") {
                    console.error("Error sending data:", data.message);
                }
            })
            .catch(error => {
                console.error("Error:", error.message);
            });
    }

    function handleIntersection(entries, observer) {
        entries.forEach(entry => {
            const currentPostId = entry.target.getAttribute('data-post-id');

            if (processedPosts.has(currentPostId)) {
                return;
            }

            if (entry.isIntersecting && entry.intersectionRatio >= 0.8 && !processedPosts.has(currentPostId)) {
                postStartTimes.set(entry.target, Date.now());
            } else if (!entry.isIntersecting && postStartTimes.has(entry.target)) {
                const startTime = postStartTimes.get(entry.target);
                let duration = Math.round((Date.now() - startTime) / 1000);
                duration = Math.min(duration, 300);
                sendDataToServer(currentPostId, duration);
                postStartTimes.delete(entry.target);
                addPostIdToProcessedPosts(currentPostId);
            }
        });
    }

    function addPostIdToProcessedPosts(postId) {
        if (processedPosts.size >= 20) {
            const firstId = processedPosts.values().next().value; // Get the first item
            processedPosts.delete(firstId); // Remove the oldest item
        }
        processedPosts.add(postId); // Add the new post ID
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    const options = {
        threshold: 0.8
    };

    const observer = new IntersectionObserver(handleIntersection, options);
    const postElements = document.querySelectorAll('.post'); // Observe both '.not-ad' and '.post' elements
    postElements.forEach(post => observer.observe(post));

    const mutationObserver = new MutationObserver(mutationsList => {
        for (let mutation of mutationsList) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(node => {
                    if (node instanceof HTMLElement && (node.classList.contains('not-ad') || node.classList.contains('post'))) {
                        observer.observe(node);
                    }
                });
            }
        }
    });

    const postsContainer = document.querySelector('.screen');
    mutationObserver.observe(postsContainer, { childList: true, subtree: true });
});
